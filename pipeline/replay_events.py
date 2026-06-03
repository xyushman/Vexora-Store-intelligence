# PROMPT: Implement event replay script that sends JSONL events to the ingest API, with optional real-time simulation and speed multiplier
# CHANGES MADE: Created replay_events.py with --realtime, --speed, --batch-size flags

import argparse, json, time, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

BATCH_SIZE = 500

def replay(events_path: str, api_base_url: str, realtime: bool, speed: float, shift_to_now: bool):
    lines = Path(events_path).read_text().splitlines()
    events = [json.loads(l) for l in lines if l.strip()]
    print(f"Loaded {len(events)} events from {events_path}")

    if not events:
        return

    time_shift_delta = timedelta(0)
    if shift_to_now:
        first_event_ts = parse_ts(events[0]["timestamp"])
        time_shift_delta = datetime.now(timezone.utc) - first_event_ts
        print(f"Shifting all timestamps by delta: {time_shift_delta}")

    batch, prev_ts = [], None
    accepted = rejected = duplicate = 0
    
    # Use batch size of 1 for realtime so events show up instantly
    actual_batch_size = 1 if realtime else BATCH_SIZE

    for i, event in enumerate(events):
        orig_ts = parse_ts(event["timestamp"])
        
        # Apply time shift if enabled
        shifted_ts = orig_ts + time_shift_delta
        event["timestamp"] = shifted_ts.isoformat().replace("+00:00", "Z")

        if realtime and prev_ts is not None:
            curr_ts = event.get("timestamp")
            if curr_ts and prev_ts:
                gap = (parse_ts(curr_ts) - parse_ts(prev_ts)).total_seconds()
                sleep = max(0, gap / speed)
                if sleep > 0:
                    time.sleep(sleep)
                    
        prev_ts = event.get("timestamp")
        batch.append(event)

        if len(batch) >= actual_batch_size or i == len(events) - 1:
            try:
                resp = requests.post(
                    f"{api_base_url}/events/ingest",
                    json={"events": batch},
                    headers={"X-API-Key": "vexora-test-key-123"},
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    accepted  += data.get("accepted", 0)
                    rejected  += data.get("rejected", 0)
                    duplicate += data.get("duplicate", 0)
                    if realtime:
                        print(f"Sent {len(batch)} event(s)... (Total accepted: {accepted})")
                else:
                    print(f"[ERROR] batch {i // actual_batch_size}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"[ERROR] request failed: {e}")
            batch = []

    print(f"Done. accepted={accepted} duplicate={duplicate} rejected={rejected}")

def parse_ts(ts_str):
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--events",       required=True)
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    parser.add_argument("--realtime",     action="store_true")
    parser.add_argument("--speed",        type=float, default=1.0)
    parser.add_argument("--shift-to-now", action="store_true", help="Shift all event timestamps so the first event starts right now")
    args = parser.parse_args()
    replay(args.events, args.api_base_url, args.realtime, args.speed, args.shift_to_now)
