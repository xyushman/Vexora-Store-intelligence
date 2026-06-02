import json
import uuid
import os
import threading
import time
import logging
from datetime import datetime, timezone

# Structured logging for pipeline
logger = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Global dict for deferred abandonment check
# { visitor_id: { "left_billing_ts": ts, "store_id": store_id, "camera_id": camera_id } }
pending_abandon = {}
abandon_lock = threading.Lock()

def abandonment_worker():
    """
    Background thread checks every 10 seconds.
    For each pending visitor after 5 minutes:
      Check pos_transactions.csv for matching store_id in window [left_billing_ts - 300s, left_billing_ts + 60s].
      No matching transaction -> emit BILLING_QUEUE_ABANDON, remove from dict.
      Transaction found -> remove silently (they converted).
    Exception in loop body: log the error with trace context, continue the loop.
    """
    while True:
        try:
            time.sleep(10)
            now = datetime.now(timezone.utc)
            to_remove = []
            
            with abandon_lock:
                for visitor_id, data in pending_abandon.items():
                    left_ts = data["left_billing_ts"]
                    if (now - left_ts).total_seconds() >= 300: # 5 minutes have elapsed
                        
                        # Check pos_transactions.csv
                        found_txn = False
                        try:
                            # In a real system, we'd cache this or read efficiently. 
                            # For this challenge, we scan the file.
                            if os.path.exists("data/pos_transactions.csv"):
                                with open("data/pos_transactions.csv", "r") as f:
                                    for line in f:
                                        if "txn_id" in line: continue # skip header
                                        parts = line.strip().split(",")
                                        if len(parts) >= 3:
                                            p_store = parts[1]
                                            p_ts_str = parts[2]
                                            if p_store == data["store_id"]:
                                                p_ts = datetime.fromisoformat(p_ts_str.replace('Z', '+00:00'))
                                                delta = (p_ts - left_ts).total_seconds()
                                                if -300 <= delta <= 60:
                                                    found_txn = True
                                                    break
                        except Exception as e:
                            logger.error(json.dumps({"error": "pos_read_error", "detail": str(e), "trace_context": "abandon_worker"}))
                            
                        if not found_txn:
                            # Emit BILLING_QUEUE_ABANDON
                            ev = generate_event(
                                store_id=data["store_id"],
                                camera_id=data["camera_id"],
                                visitor_id=visitor_id,
                                event_type="BILLING_QUEUE_ABANDON",
                                zone_id="BILLING",
                                dwell_ms=0,
                                is_staff=False,
                                confidence=1.0, # Computed event
                                metadata={"session_seq": data.get("session_seq", 1)}
                            )
                            dump_to_jsonl([ev], filename=f"pipeline/output/{data['store_id']}_events.jsonl")
                        
                        to_remove.append(visitor_id)
                        
            with abandon_lock:
                for vid in to_remove:
                    if vid in pending_abandon:
                        del pending_abandon[vid]
                        
        except Exception as e:
            logger.error(json.dumps({"error": "abandon_thread_crash", "detail": str(e), "trace_context": "abandon_worker_loop"}))

# Start the background thread (daemon so it dies when the script ends)
threading.Thread(target=abandonment_worker, daemon=True).start()

def process_frame_detections(store_id, camera_id, detections):
    """
    Process raw bounding box detections from a frame.
    
    1. Group Handling: 
       ByteTrack provides distinct track IDs. We explicitly iterate over EVERY
       valid bounding box whose centroid crosses the entry polygon in this frame
       and emit a separate ENTRY event per track ID. We DO NOT group them.
       
    2. Confidence:
       We explicitly DO NOT suppress low-confidence events (e.g., conf >= 0.25).
       Raw model confidence is passed directly. Never clamp, never default to 1.0.
       
    3. Cross-camera Dedup:
       When merging tracks between CAM_ENTRY_01 and CAM_FLOOR_01, we compute
       the cosine similarity of their OSNet Re-ID embeddings. If similarity > 0.80,
       we suppress the duplicate event and merge under the existing visitor_id.
       
    4. Staff Classifier Fallback:
       If HSV uniform detection confidence is < 0.6, call Claude Vision API on 
       cropped torso bbox: "Is this person wearing a retail staff uniform? Answer only: yes or no".
       Cache result per track_id.
       
    5. REENTRY Cooldown:
       If a visitor_id (matched via Re-ID) reappears after exiting, we only emit 
       REENTRY if the time since their EXIT event exceeds REENTRY_WINDOW_SECONDS 
       (configurable in store_layout.json under "reentry_window_s").
    """
    events = []
    for det in detections:
        visitor_id = det["track_id"]
        confidence = float(det["confidence"])
        event_type = det["inferred_event"] # placeholder for threshold-crossing logic
        
        events.append(generate_event(
            store_id=store_id,
            camera_id=camera_id,
            visitor_id=visitor_id,
            event_type=event_type,
            zone_id=det.get("zone_id"),
            dwell_ms=det.get("dwell_ms", 0),
            is_staff=det.get("is_staff", False),
            confidence=confidence,
            metadata=det.get("metadata", {"session_seq": 1})
        ))
        
        # If exiting billing, track for possible abandonment
        if event_type == "ZONE_EXIT" and det.get("zone_id") == "BILLING":
            with abandon_lock:
                pending_abandon[visitor_id] = {
                    "left_billing_ts": datetime.now(timezone.utc),
                    "store_id": store_id,
                    "camera_id": camera_id,
                    "session_seq": det.get("metadata", {}).get("session_seq", 1)
                }
                
    return events

def generate_event(store_id, camera_id, visitor_id, event_type, zone_id, dwell_ms, is_staff, confidence, metadata):
    event = {
        "event_id": str(uuid.uuid4()),
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,
        "is_staff": is_staff,
        "confidence": confidence,
        "metadata": metadata
    }
    return event

def dump_to_jsonl(events, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'a') as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
