import os
import sys
import json
import time
import uuid
import argparse
import base64
import hashlib
import threading
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import cv2
import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

try:
    import torch
    _old_load = torch.load
    def _safe_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return _old_load(*args, **kwargs)
    torch.load = _safe_load
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics is not installed. Please install it.")
    sys.exit(1)

try:
    import torchreid
    from torchreid.utils import FeatureExtractor
    HAS_TORCHREID = True
except ImportError:
    HAS_TORCHREID = False
    print("Warning: torchreid not found. Using fallback Re-ID.")

try:
    from google import genai
    from google.genai import types
    if os.environ.get("GEMINI_API_KEY"):
        gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    else:
        gemini_client = None
except ImportError:
    gemini_client = None

# --- Pydantic Schema ---
class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: int = 1

class EventSchema(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: int = 0
    is_staff: bool = False
    confidence: float
    metadata: EventMetadata

# --- Globals ---
pending_abandon = {}
abandon_lock = threading.Lock()

# store_id -> [ { visitor_id, embedding, last_seen_ts } ]
shared_embeddings = {}
embeddings_lock = threading.Lock()

def abandonment_worker(pos_path):
    while True:
        try:
            time.sleep(10)
            now = datetime.now(timezone.utc)
            to_remove = []
            
            with abandon_lock:
                for visitor_id, data in pending_abandon.items():
                    left_ts = data["left_billing_ts"]
                    if (now - left_ts).total_seconds() >= 300:
                        found_txn = False
                        try:
                            if os.path.exists(pos_path):
                                df = pd.read_csv(pos_path)
                                df_store = df[df['store_id'] == data['store_id']]
                                for _, row in df_store.iterrows():
                                    txn_ts_str = row['timestamp']
                                    if txn_ts_str.endswith('Z'):
                                        txn_ts_str = txn_ts_str[:-1] + '+00:00'
                                    txn_ts = datetime.fromisoformat(txn_ts_str)
                                    delta = (txn_ts - left_ts).total_seconds()
                                    if abs(delta) < 300:
                                        found_txn = True
                                        break
                        except Exception as e:
                            print(f"Error reading POS data: {e}")
                            
                        if not found_txn:
                            ev = EventSchema(
                                event_id=str(uuid.uuid4()),
                                store_id=data["store_id"],
                                camera_id=data["camera_id"],
                                visitor_id=visitor_id,
                                event_type="BILLING_QUEUE_ABANDON",
                                timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                                zone_id="BILLING",
                                dwell_ms=0,
                                is_staff=False,
                                confidence=1.0,
                                metadata=EventMetadata(session_seq=1)
                            )
                            out_file = data.get("output_file")
                            if out_file:
                                os.makedirs(os.path.dirname(out_file), exist_ok=True)
                                with open(out_file, 'a') as f:
                                    f.write(ev.model_dump_json() + "\n")
                                    
                        to_remove.append(visitor_id)
            
            with abandon_lock:
                for vid in to_remove:
                    if vid in pending_abandon:
                        del pending_abandon[vid]
        except Exception as e:
            print(f"Abandonment thread error: {e}")

def get_staff_hsv_conf(frame, bbox):
    x1, y1, x2, y2 = map(int, bbox)
    h, w = y2 - y1, x2 - x1
    if h <= 0 or w <= 0:
        return False, 0.0
    
    torso_y1 = y1 + int(0.4 * h)
    torso_y2 = y1 + int(0.7 * h)
    torso_crop = frame[torso_y1:torso_y2, x1:x2]
    
    if torso_crop.size == 0:
        return False, 0.0
        
    hsv = cv2.cvtColor(torso_crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([100, 76, 0]), np.array([130, 255, 255]))
    ratio = cv2.countNonZero(mask) / (torso_crop.shape[0] * torso_crop.shape[1])
    
    if ratio > 0.1:
        return True, 0.85
    return False, 0.1

def check_staff_gemini(frame, bbox):
    if not gemini_client:
        return False
    x1, y1, x2, y2 = map(int, bbox)
    h = y2 - y1
    torso_y1 = y1 + int(0.4 * h)
    torso_y2 = y1 + int(0.7 * h)
    torso_crop = frame[torso_y1:torso_y2, x1:x2]
    if torso_crop.size == 0:
        return False
    
    _, buffer = cv2.imencode('.jpg', torso_crop)
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=buffer.tobytes(), mime_type='image/jpeg'),
                "Is this person wearing a retail staff uniform? Answer only: yes or no"
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                temperature=0.0
            )
        )
        if response and response.text:
            ans = response.text.strip().lower()
            return ans.startswith('yes')
        return False
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_EXHAUSTED" not in error_msg and "NoneType" not in error_msg:
            print(f"Gemini API error: {error_msg}")
        return False

extractor = None
if HAS_TORCHREID:
    try:
        extractor = FeatureExtractor(
            model_name='osnet_x0_25',
            model_path='',
            device='cpu'
        )
    except Exception as e:
        print(f"Error loading torchreid extractor: {e}")
        extractor = None

def get_embedding(frame, bbox):
    if not extractor:
        return None
    x1, y1, x2, y2 = map(int, bbox)
    crop = frame[max(0, y1):y2, max(0, x1):x2]
    if crop.size == 0:
        return None
    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    features = extractor([crop_rgb])
    if features is not None and len(features) > 0:
        return features[0].cpu().numpy()
    return None

def cosine_sim(a, b):
    if a is None or b is None: return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

def main():
    parser = argparse.ArgumentParser(description="Run detection pipeline")
    parser.add_argument("--clips", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--pos", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # Start abandonment worker
    threading.Thread(target=abandonment_worker, args=(args.pos,), daemon=True).start()

    os.makedirs(args.output, exist_ok=True)
    out_file = os.path.join(args.output, f"{args.store}_events.jsonl")
    
    with open(args.layout, 'r') as f:
        layout_data = json.load(f)
        
    zones = {}
    for z in layout_data.get("zones", []):
        if "polygon" in z:
            zones[z["zone_id"]] = Polygon(z["polygon"])
            
    reentry_window_s = layout_data.get("reentry_window_s", 300)

    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"Error loading YOLO model: {e}")
        sys.exit(1)
        
    with embeddings_lock:
        shared_embeddings[args.store] = []

    clips = [f for f in os.listdir(args.clips) if f.endswith('.mp4')]
    if not clips:
        print(f"Warning: No .mp4 files found in {args.clips}")
        return

    for clip_name in sorted(clips):
        clip_path = os.path.join(args.clips, clip_name)
        
        # Infer camera role
        name_upper = clip_name.upper()
        if "CAM 1" in name_upper:
            camera_role = "entry"
            camera_id = "CAM_ENTRY_01"
        elif "CAM 2" in name_upper or "CAM 3" in name_upper:
            camera_role = "floor"
            camera_id = f"CAM_FLOOR_{clip_name.split('.')[0][-1]}"
        elif "CAM 4" in name_upper or "CAM 5" in name_upper:
            camera_role = "billing"
            camera_id = f"CAM_BILLING_{clip_name.split('.')[0][-1]}"
        else:
            camera_role = "unknown"
            camera_id = f"CAM_UNKNOWN"

        print(f"Processing {clip_name} as {camera_id} ({camera_role})")

        cap = cv2.VideoCapture(clip_path)
        if not cap.isOpened():
            print(f"Error opening {clip_path}")
            continue
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: fps = 25.0
        
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        entry_line_y = frame_height * 0.5
        
        # Clip start time mock: current time minus video length, or just current time
        clip_start_ts = datetime.now(timezone.utc)
        
        track_states = {} # track_id -> dict of state
        staff_cache = {}  # track_id -> is_staff
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0: total_frames = "unknown"
        
        results_gen = model.track(source=clip_path, tracker="bytetrack.yaml", classes=[0], conf=0.25, stream=True)
        
        frame_idx = 0
        events_emitted = 0
        
        try:
            for r in results_gen:
                frame_idx += 1
                frame_time = clip_start_ts + timedelta(seconds=frame_idx / fps)
                ts_str = frame_time.isoformat().replace('+00:00', 'Z')
                
                boxes = r.boxes
                if boxes is None or len(boxes) == 0:
                    if frame_idx % 100 == 0:
                        print(f"[frame {frame_idx}/{total_frames}] store={args.store} tracks=0 events_emitted={events_emitted}")
                    continue
                    
                active_tracks_in_frame = set()
                
                for box in boxes:
                    if box.id is None:
                        continue
                    track_id = int(box.id.item())
                    conf = float(box.conf.item())
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    
                    h = y2 - y1
                    w = x2 - x1
                    if w <= 0 or h <= 0:
                        continue
                    # Aspect ratio check: Real standing people have h/w > 1.1
                    if h / w < 1.1:
                        continue
                    # Size check: Ignore very small detections (e.g. reflections or distant posters)
                    if h < frame_height * 0.15:
                        continue
                    
                    active_tracks_in_frame.add(track_id)
                    
                    # Generate visitor_id and check Re-ID / Dedup
                    if track_id not in track_states:
                        emb = get_embedding(r.orig_img, (x1, y1, x2, y2))
                        
                        visitor_id = None
                        assigned_event = "ENTRY"
                        
                        if HAS_TORCHREID and emb is not None:
                            # 1. Dedup cross-camera
                            found_dedup = False
                            with embeddings_lock:
                                for rec in shared_embeddings[args.store]:
                                    # Active entry tracks in last 60s
                                    if (frame_time - rec['last_seen_ts']).total_seconds() < 60:
                                        if cosine_sim(emb, rec['embedding']) > 0.80:
                                            visitor_id = rec['visitor_id']
                                            found_dedup = True
                                            break
                            if not found_dedup:
                                # 2. Re-entry check
                                with embeddings_lock:
                                    for rec in shared_embeddings[args.store]:
                                        if (frame_time - rec['last_seen_ts']).total_seconds() < reentry_window_s:
                                            if rec['status'] == 'EXITED' and cosine_sim(emb, rec['embedding']) > 0.75:
                                                visitor_id = rec['visitor_id']
                                                assigned_event = "REENTRY"
                                                break
                                                
                        if not visitor_id:
                            # New visitor
                            vid_hash = hashlib.sha256((args.store + str(track_id) + str(clip_start_ts.timestamp())).encode()).hexdigest()[:6]
                            visitor_id = f"VIS_{vid_hash}"
                            
                        track_states[track_id] = {
                            "visitor_id": visitor_id,
                            "last_y": cy,
                            "zones": set(),
                            "zone_join_time": {},
                            "embedding": emb,
                            "last_seen_ts": frame_time,
                            "deduped": (visitor_id is not None and assigned_event != "ENTRY" and assigned_event != "REENTRY")
                        }
                        
                        # Register in shared embeddings
                        with embeddings_lock:
                            shared_embeddings[args.store].append({
                                "visitor_id": visitor_id,
                                "embedding": emb,
                                "last_seen_ts": frame_time,
                                "status": "ACTIVE"
                            })
                            
                        if not track_states[track_id]["deduped"]:
                            # Emit ENTRY / REENTRY (Wait, spec says ENTRY/EXIT only for entry camera. Dedup check avoids duplicate ENTRY)
                            if camera_role == "entry":
                                pass # Handled by crossing line below
                            else:
                                pass # No line crossing on floor cams, they just appear. Emit nothing for appearance itself unless needed.
                                
                    state = track_states[track_id]
                    state["last_seen_ts"] = frame_time
                    visitor_id = state["visitor_id"]
                    
                    # Update embedding last_seen
                    with embeddings_lock:
                        for rec in shared_embeddings[args.store]:
                            if rec['visitor_id'] == visitor_id:
                                rec['last_seen_ts'] = frame_time
                                break
                    
                    # Staff Check
                    if track_id not in staff_cache:
                        is_staff, staff_conf = get_staff_hsv_conf(r.orig_img, (x1, y1, x2, y2))
                        if staff_conf < 0.6:
                            is_staff = check_staff_gemini(r.orig_img, (x1, y1, x2, y2))
                        staff_cache[track_id] = is_staff
                    is_staff = staff_cache[track_id]
                    
                    def emit(ev_type, zone_id=None, dwell=0):
                        ev = EventSchema(
                            event_id=str(uuid.uuid4()),
                            store_id=args.store,
                            camera_id=camera_id,
                            visitor_id=visitor_id,
                            event_type=ev_type,
                            timestamp=ts_str,
                            zone_id=zone_id,
                            dwell_ms=dwell,
                            is_staff=is_staff,
                            confidence=conf,
                            metadata=EventMetadata(session_seq=1)
                        )
                        with open(out_file, 'a') as f:
                            f.write(ev.model_dump_json() + "\n")
                        return 1
                    
                    # Line crossing (Entry cam)
                    if camera_role == "entry":
                        last_y = state["last_y"]
                        if last_y < entry_line_y and cy >= entry_line_y:
                            events_emitted += emit("ENTRY")
                        elif last_y >= entry_line_y and cy < entry_line_y:
                            events_emitted += emit("EXIT")
                            with embeddings_lock:
                                for rec in shared_embeddings[args.store]:
                                    if rec['visitor_id'] == visitor_id:
                                        rec['status'] = "EXITED"
                                        break
                                        
                        state["last_y"] = cy

                    # Zone logic
                    current_zones = set()
                    
                    if camera_role == "billing":
                        current_zones.add("BILLING")
                    elif camera_role == "entry":
                        current_zones.add("ENTRY")
                    elif camera_role == "floor":
                        col = int(cx / max(1, (frame_width / 4)))
                        row = int(cy / max(1, (frame_height / 3)))
                        for z in layout_data.get("zones", []):
                            if z.get("camera") == camera_id and z.get("grid_position") == [row, col]:
                                current_zones.add(z["zone_id"])
                                
                    pt = Point(cx, cy)
                    for zid, poly in zones.items():
                        if poly.contains(pt):
                            current_zones.add(zid)
                            
                    # Entered new zones
                    for zid in current_zones - state["zones"]:
                        events_emitted += emit("ZONE_ENTER", zid)
                        state["zone_join_time"][zid] = frame_time
                        if zid == "BILLING":
                            # Emit BILLING_QUEUE_JOIN
                            events_emitted += emit("BILLING_QUEUE_JOIN", zid)
                            
                    # Left zones
                    for zid in state["zones"] - current_zones:
                        dwell = int((frame_time - state["zone_join_time"][zid]).total_seconds() * 1000)
                        events_emitted += emit("ZONE_EXIT", zid, dwell)
                        if zid == "BILLING":
                            with abandon_lock:
                                pending_abandon[visitor_id] = {
                                    "left_billing_ts": frame_time,
                                    "store_id": args.store,
                                    "camera_id": camera_id,
                                    "output_file": out_file
                                }
                                
                    # Dwell 30s
                    for zid in current_zones:
                        dwell_sec = (frame_time - state["zone_join_time"][zid]).total_seconds()
                        if dwell_sec >= 30.0 and int(dwell_sec) % 30 == 0:
                            # Emit every 30s approximately. Let's do a simple check. We'll track last dwell emitted.
                            last_dwell_emitted = state.get(f"last_dwell_{zid}", 0)
                            if dwell_sec - last_dwell_emitted >= 30:
                                events_emitted += emit("ZONE_DWELL", zid, int(dwell_sec * 1000))
                                state[f"last_dwell_{zid}"] = dwell_sec
                                
                    state["zones"] = current_zones
                    
                if frame_idx % 100 == 0:
                    print(f"[frame {frame_idx}/{total_frames}] store={args.store} tracks={len(active_tracks_in_frame)} events_emitted={events_emitted}")
                    
        except Exception as e:
            print(f"Error processing clip {clip_name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
