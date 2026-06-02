# CHOICES.md

## 1. Detection Model Choice
**Options Considered**: YOLOv8, YOLOv9, RT-DETR, or an end-to-end VLM like GPT-4V.
**What AI Suggested**: The AI recommended YOLOv8 (specifically the YOLOv8s INT8 optimized model) because it offers an optimal balance between mature ecosystem support, high FPS on edge devices (like Jetson), and strong baseline accuracy for pedestrian detection.
**What I Chose**: I chose YOLOv8.
**Why**: YOLOv8 handles partial occlusions (e.g., in crowded billing queues) gracefully when combined with a robust tracker like ByteTrack. A VLM was ruled out for frame-by-frame object detection due to extreme latency constraints (requiring <66ms per frame), making YOLOv8 the most pragmatic engineering choice.

## 2. Event Schema Design Rationale
**Options Considered**: A flat JSON structure vs. a strict Pydantic model with a nested metadata dictionary.
**What AI Suggested**: The AI suggested using Pydantic v2 with a rigid core schema and a flexible `metadata` block.
**What I Chose**: I implemented the Pydantic v2 approach.
**Why**: The scoring criteria mandates exact schema compliance. A rigid core schema guarantees that `event_id`, `timestamp`, and `visitor_id` are always present and properly typed for the ingestion layer. However, events like `BILLING_QUEUE_JOIN` require highly specific fields like `queue_depth`, which don't apply to a `ZONE_ENTER` event. The nested metadata dictionary provides extensibility without breaking the rigid schema contract.

## 3. Staff Classifier Fallback (Fragility Mitigation)
**Options Considered**: Pure HSV color masking vs. spatial heuristics vs. VLM secondary checks.
**What AI Suggested**: The AI highlighted that HSV uniform detection breaks under mixed/fluorescent lighting (a stated edge case) and suggested using a VLM for secondary verification or spatial heuristics.
**What I Chose**: I chose a spatial heuristic approach for staff classification.
**Why**: A VLM call per frame is too expensive. Instead, the pipeline tracks bounding box trajectories over time. Store staff have distinct spatial behavior—they traverse all zones repeatedly (entry -> floor -> billing -> floor), whereas customers follow a linear funnel. By analyzing the zone-transition frequency of a `visitor_id` over a 5-minute window, the pipeline can reliably classify `is_staff=true` even if lighting degrades the uniform's color signature.

## 4. API Architecture Choice
**Options Considered**: PostgreSQL + Kafka stream processing vs. SQLite in WAL mode.
**What AI Suggested**: The AI initially suggested a complex enterprise setup (Kafka, ClickHouse, Flink), but upon re-evaluation against the challenge constraints, suggested SQLite in WAL (Write-Ahead Logging) mode.
**What I Chose**: SQLite in WAL mode with a FastAPI backend.
**Why**: The primary acceptance gate is that `docker-compose up` must start the API cleanly without manual intervention. SQLite requires zero standalone containers, vastly reducing the risk of failure on the reviewer's machine. WAL mode enables the necessary concurrent reads (for the live dashboard and metrics endpoints) and writes (from the `POST /events/ingest` batches) without database locking issues, perfectly matching the pragmatic scope of a 40-store take-home challenge.
