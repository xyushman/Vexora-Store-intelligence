# Dataset Analysis & Heuristics

## Camera Role Assignments
- **CAM 3 (Entry)**: Designated as the primary entry/exit camera for the store. It calculates overall footfall and establishes the initial ByteTrack/ReID signatures for visitors.
- **CAM 4 (Floor)**: Points towards the backroom and aisles. Used to measure dwell times across brand zones.
- **CAM 5 (Billing)**: Positioned over the billing/queue area. Used to measure queue depth, abandonment, and final conversion linkage.

## Store ID Canonical Mapping
The system accepts multiple aliases for the primary test store but consistently resolves them to the canonical ID `ST1008` in the database.
- `STORE_BLR_002` -> `ST1008`
- `Brigade_Bangalore` -> `ST1008`

## Timezone Handling
- Point-of-Sale (POS) timestamps are provided in `Asia/Kolkata` local time (`%d-%m-%Y %H:%M:%S`).
- The Python pipeline parses these into timezone-aware datetimes and instantly converts them to UTC before storage in the SQLite database. This flawlessly aligns them with the CCTV event timestamps, which are generated natively in UTC (`Z`).

## YOLO False Positive Filtering
Because retail stores contain large promotional posters and reflective surfaces, standard YOLOv8 models frequently misidentify faces on posters as live humans. 
We introduced robust spatial heuristics in `detect.py`:
- `h / w > 1.1`: Enforces aspect ratio checks (standing humans are taller than they are wide), eliminating square posters.
- `h > frame_height * 0.15`: Eliminates tiny background reflections.

## Staff Detection Heuristic
Traditional staff detection using only uniform color thresholds (HSV) failed due to poor lighting and inconsistent apron coloring across cameras.
To fix this, we implemented a dual-layer approach:
1. **Google Gemini Vision API**: Takes a crop of the person's torso and uses generative AI to confidently determine if they are wearing a retail staff uniform.
2. **HSV Color Masking**: A fallback mechanism that searches for the specific purple brand color in the bounding box if the API is rate-limited.
This successfully filters cashiers and floor staff from conversion metrics.
