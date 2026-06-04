# Technical Choices & Trade-offs

## AI-Assisted Decisions
**AI Used:** Google Gemini

### 1. Detection Model Selection
**Options Considered:** I initially evaluated using ByteTrack coupled with a lightweight detection model like MobileNet, as well as YOLOv8. 
**Gemini Suggestion & Decision:** I asked Gemini to compare real-time tracking performance for retail environments with heavy occlusion and reflections. Gemini recommended YOLOv8 combined with BoT-SORT/ByteTrack. I agreed with this approach because YOLOv8 strikes the right balance between inference speed (critical for processing 5 CCTV videos simultaneously) and bounding box accuracy. 

### 2. Event Schema Design Rationale
**Options Considered:** For the ingestion schema, I debated sending raw bounding box coordinates for every frame (30fps) versus sending semantically aggregated "zone entry/exit" events.
**Decision:** I chose to implement semantic event aggregation at the pipeline level. Instead of flooding the API with raw coordinate data, the pipeline processes the frames and emits high-level JSONL events (e.g., `ZONE_ENTER`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`). 
**Rationale:** This drastically reduces the network payload, simplifies database schema design, and moves the heavy computational load (polygon intersection math) to the pipeline, keeping the FastAPI edge backend extremely lightweight.

### 3. API Architecture Choice
**Options Considered:** I considered using PostgreSQL for a robust, scalable backend versus SQLite.
**Decision:** I chose SQLite configured in WAL (Write-Ahead Logging) mode alongside FastAPI.
**Gemini Suggestion & Decision:** I initially leaned towards Postgres, but prompted Gemini about the best database for a localized, edge-deployed container stack. Gemini suggested SQLite in WAL mode for concurrent reads/writes without locking issues and to avoid the heavy memory footprint of a Postgres container. I agreed and implemented this, as it keeps the entire stack easily deployable via a single `docker-compose up` command.

## 4. Staff Detection Heuristic
**Challenge:** Detecting staff reliably without clear uniform coloring across cameras (aprons look different under varying store lighting).
**Decision:** We implemented a dual-layer approach. 
1. **Google Gemini Vision API**: The pipeline crops the detected person's torso and queries the Gemini Vision API to confidently determine if they are wearing a retail staff uniform. 
2. **HSV Color Masking**: A fallback mechanism that searches for the specific purple brand color in the bounding box if the API is rate-limited. This completely filters cashiers and floor staff from skewing conversion metrics.

## 5. False Positive Mitigation (Posters & Reflections)
**Challenge:** Retail stores contain large promotional posters. Standard YOLOv8 models frequently misidentify faces on these posters as live humans.
**Decision:** We introduced robust spatial heuristics: `h / w > 1.1` (enforcing aspect ratio checks since standing humans are taller than they are wide) and `h > frame_height * 0.15` (eliminating tiny background reflections). This successfully cleans up the tracking data.

## 6. Live Dashboard UI
Instead of using Streamlit, we built a custom Next.js frontend using React Three Fiber to render a live 3D digital twin of the store. Data is fed directly from the FastAPI backend via Server-Sent Events (SSE) for instantaneous, zero-refresh updates.
