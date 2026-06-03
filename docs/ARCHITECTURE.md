# Vexora Architecture

## End-to-End Flow
`CCTV → Detection (YOLOv8) → Tracking (ByteTrack) → ReID (torchreid/OSNet) → Event Generation → FastAPI Ingest → SQLite WAL → Analytics Engine → Next.js Dashboard`

## Components

| Component | Responsibility | Data Flow | Scalability | Failure Handling | Testing |
|-----------|----------------|-----------|-------------|------------------|---------|
| **YOLOv8 + ByteTrack** | Real-time object detection and tracking | Video frames -> Bounding Boxes | Edge-bound by GPU | Drops frames if lag exceeds 500ms | Pipeline Unit Tests |
| **torchreid (OSNet)** | Cross-camera person re-identification | Bounding Box crops -> Embeddings -> Global ID | Batched inference | Falls back to single-camera tracking | ReID Acc metrics |
| **Staff AI Filter** | Gemini API & HSV filtering to remove staff | Crop -> Gemini API -> Boolean | Rate limited by Google API | Falls back to HSV color heuristics | Visual Inspection |
| **Ingest API** | Receives structured semantic events | JSON POST -> SQLite | Scales to 1000s req/sec | Retries on DB lock | `smoke_api.sh` |
| **SQLite WAL** | Persistent local storage | Disk I/O | Perfect for edge. Concurrency via WAL. | Disk full alerts via anomaly engine | SQLite integrity checks |
| **FastAPI Backend** | Computes funnels, heatmaps, live metrics, SSE | DB Read -> JSON/SSE | Horizontally scalable | Degraded states reported in `/health` | Pytest |
| **Next.js Dashboard** | 3D UI visualization & live charts | HTTP/SSE -> React Three Fiber | High performance | Reconnecting SSE streams | Manual |

## Storage Design
- `stores` (id, name, city, timezone)
- `store_aliases` (alias, canonical_id)
- `events` (event_id, visitor_id, store_id, event_type, zone_id, dwell_ms, ...) -> Index on `(store_id, timestamp)`
- `sessions` (visitor_id, store_id, first_seen, last_seen, is_staff, converted)
- `pos_transactions` (transaction_id, store_id, timestamp_utc, basket_value)

## Analytics Logic
- **Unique Visitors**: Distinct `visitor_id` in `sessions` today WHERE `is_staff = 0`.
- **Conversion Rate**: Distinct `visitor_id` linked to `pos_transactions` / Unique Visitors.
- **Queue Depth**: Latest `BILLING_QUEUE_JOIN` minus `BILLING_QUEUE_EXIT` count.
- **Abandonment**: Visitors with `BILLING_QUEUE_JOIN` but no transaction, followed by `EXIT`.

## Scalability Path
Currently built for **Challenge-Scale** (single edge-device per store). 
For **Production-Scale**, SQLite would be replaced with Postgres + Kafka for central aggregation, while tracking models would be moved to dedicated TensorRT inference servers.
