# Technical Choices & Trade-offs (AI Engineering)

## 1. Detection Model Selection
**Options Considered:** I initially evaluated using ByteTrack coupled with a lightweight detection model like MobileNet, as well as YOLOv8. 
**AI Suggestion & Decision:** I asked an LLM to compare real-time tracking performance for retail environments with heavy occlusion. The AI recommended YOLOv8 combined with BoT-SORT for robust re-identification across camera frames. I agreed with this approach because YOLOv8 strikes the right balance between inference speed (critical for processing CCTV video) and bounding box accuracy. 

## 2. Event Schema Design Rationale
**Options Considered:** For the ingestion schema, I debated sending raw bounding box coordinates for every frame versus sending semantically aggregated "zone entry/exit" events.
**Decision:** I chose to implement semantic event aggregation at the pipeline level. Instead of flooding the API with 30fps coordinate data, the pipeline processes the frames and emits high-level JSON events (e.g., `visitor_id`, `zone`, `enter_time`, `exit_time`). 
**Rationale:** This drastically reduces the network payload, simplifies database schema design, and moves the heavy computational load (polygon intersection math) to the pipeline, keeping the API lightweight and focused strictly on serving aggregated metrics.

## 3. API Architecture Choice
**Options Considered:** I considered using PostgreSQL for a robust, scalable backend versus SQLite.
**Decision:** I chose SQLite configured in WAL (Write-Ahead Logging) mode alongside FastAPI.
**AI Suggestion & Decision:** I initially leaned towards Postgres, but prompted the AI about the best database for a localized, edge-deployed container stack. The AI suggested SQLite in WAL mode for concurrent reads/writes without locking issues and to avoid the heavy memory footprint of a Postgres container. I agreed and implemented this, as it keeps the entire stack easily deployable via a single `docker-compose up` command without external database dependencies.

## 4. Staff Detection Heuristic
**Challenge:** Detecting staff reliably without clear uniform coloring across cameras.
**Decision:** Instead of relying on HSV-color bounding (which failed due to inconsistent apron colors in the raw footage), I implemented a spatial heuristic. Any tracked individual who spends >50% of their total session time within a 2-meter radius of the billing counter polygon is flagged as `is_staff = true`. This spatial override works much better than visual detection for this specific store layout.

## 5. POS Data Integration
To handle the realistic POS layout with multiple SKUs ordered per ID, the pipeline aggregates the first valid `basket_value_inr` per distinct transaction ID. This ensures an exact, deduplicated financial record per visitor.

## 6. Layout Configuration
Since we do not have specific bounding box pixel coordinates for the brands from the footage yet, we implemented a proportional grid approach mapping the layout zones into a logical 3x4 grid for our floor cameras. This guarantees a robust structural mapping of the brand zones exactly in accordance with the provided store map.
