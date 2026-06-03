# Vexora Architecture

## End-to-End Flow
`CCTV → Detection (YOLOv8) → Tracking (ByteTrack) → ReID (torchreid/OSNet) → Event Generation → Ingest API → SQLite → Analytics → FastAPI → Streamlit`

## Components

| Component | Responsibility | Data Flow | Scalability | Failure Handling | Testing |
|-----------|----------------|-----------|-------------|------------------|---------|
| **YOLOv8 + ByteTrack** | Real-time object detection and tracking | Video frames -> Bounding Boxes | Edge-bound by GPU | Drops frames if lag exceeds 500ms | Pipeline Unit Tests |
| **torchreid (OSNet)** | Cross-camera person re-identification | Bounding Box crops -> Embeddings -> Global ID | Batched inference | Falls back to single-camera tracking | ReID Acc metrics |
| **Ingest API** | Receives structured semantic events | JSON POST -> SQLite | Scales to 1000s req/sec | Retries on DB lock | `smoke_api.sh` |
| **SQLite WAL** | Persistent local storage | Disk I/O | Perfect for edge. Concurrency via WAL. | Disk full alerts via anomaly engine | SQLite integrity checks |
| **FastAPI Analytics** | Computes funnels, heatmaps, live metrics | DB Read -> JSON | Horizontally scalable | Degraded states reported in `/health` | Pytest |
| **Streamlit Dashboard** | UI visualization | HTTP GET -> UI | Standard Streamlit scalability | UI retry loops | Manual |
| **Anomaly Engine** | Rule-based detection + Claude insights | DB -> Anthropic API -> JSON | Batched background tasks | Falls back to rule-only on API failure | Mock API Tests |

## Storage Design
- `stores` (id, name, city, timezone)
- `store_aliases` (alias, canonical_id)
- `events` (event_id, visitor_id, store_id, event_type, zone_id, dwell_ms, ...) -> Index on `(store_id, timestamp)`
- `sessions` (visitor_id, store_id, first_seen, last_seen, is_staff, converted)
- `pos_transactions` (transaction_id, store_id, timestamp_utc, basket_value)
- `conversion_history`
- `anomaly_log`

## Analytics Logic
- **Unique Visitors**: Distinct `visitor_id` in `sessions` today WHERE `is_staff = 0`.
- **Conversion Rate**: Distinct `visitor_id` linked to `pos_transactions` / Unique Visitors.
- **Queue Depth**: Latest `BILLING_QUEUE_JOIN` minus `BILLING_QUEUE_EXIT` count.
- **Abandonment**: Visitors with `BILLING_QUEUE_JOIN` but no transaction, followed by `EXIT`.

## Anomaly Rules
1. **QUEUE_SPIKE**: > 8 people in queue without exit. (CRITICAL)
2. **CONVERSION_DROP**: > 15% drop below 7-day average. (WARN)
3. **DEAD_ZONE**: No visits to a known zone for > 30 minutes. (WARN)
4. **STALE_FEED**: Latest event is > 10 minutes old. (CRITICAL)

## Scalability Path
Currently built for **Challenge-Scale** (single edge-device per store). 
For **Production-Scale**, SQLite would be replaced with Postgres + Kafka for central aggregation, while tracking models would be moved to dedicated TensorRT inference servers.
