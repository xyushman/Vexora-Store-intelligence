# Store Intelligence

A complete pipeline from raw video to live store analytics. 

## Quick Start

The architecture is fully containerized and uses SQLite WAL mode. 

Run the following 5 commands to spin up the API and verify everything is working:

```bash
git clone <your-private-repo-url>
cd store-intelligence
docker compose up -d
bash pipeline/run.sh /path/to/clips
curl http://localhost:8000/stores/ST1008/metrics
```

### Detection Pipeline Execution
To run the detection pipeline against new clips, use the `pipeline/run.sh` script, providing the path to the video clips folder:
```bash
bash pipeline/run.sh /path/to/clips
```
The output will be structured as `events.jsonl` files stored in the `pipeline/output/` directory, which can then be posted to the `/events/ingest` endpoint.

### Live Dashboard
A live dashboard tracking unique visitors, conversion rate, and queue depth updates in real time via Server-Sent Events (SSE). 
Access the dashboard at:
[http://localhost:8000/dashboard/ST1008](http://localhost:8000/dashboard/ST1008)
