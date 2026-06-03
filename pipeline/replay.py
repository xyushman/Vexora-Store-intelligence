import argparse
import json
import time
import requests
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Replay events to API")
    parser.add_argument("--events", required=True, help="Path to events JSONL file")
    parser.add_argument("--api", required=True, help="API URL")
    parser.add_argument("--speed", type=float, default=10.0, help="Replay speed multiplier")
    parser.add_argument("--realtime", action="store_true", help="Simulate real-time by forcing speed to 1.0")
    args = parser.parse_args()

    if args.realtime:
        args.speed = 1.0

    events = []
    with open(args.events, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON line: {e}")

    # Sort events by timestamp
    def get_ts(ev):
        ts_str = ev.get('timestamp', '')
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)

    events.sort(key=get_ts)
    
    api_endpoint = f"{args.api.rstrip('/')}/events/ingest"

    for i in range(len(events)):
        ev = events[i]
        
        if i > 0:
            ts_curr = get_ts(ev)
            ts_prev = get_ts(events[i-1])
            gap = (ts_curr - ts_prev).total_seconds()
            if gap > 0:
                sleep_time = gap / args.speed
                time.sleep(sleep_time)

        # POST event as a batch of 1
        try:
            resp = requests.post(api_endpoint, json={"events": [ev]}, headers={"Content-Type": "application/json"})
            status = resp.status_code
        except Exception as e:
            status = f"Error: {e}"

        ts_str = ev.get('timestamp')
        event_type = ev.get('event_type')
        visitor_id = ev.get('visitor_id')
        print(f"[{ts_str}] Emitted {event_type} for {visitor_id} -> HTTP {status}")

if __name__ == "__main__":
    main()
