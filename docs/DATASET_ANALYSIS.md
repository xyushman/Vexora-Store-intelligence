# DATASET_ANALYSIS

## Camera Role Assignments
- **CAM 3**: Designated as the entry/exit camera for the store.
- **CAM 5**: Positioned over the billing/queue area. Used to measure queue depth, abandonment, and conversion.
- **CAM 4**: Points towards the backroom. Identified as staff-only area.

## Store ID Canonical Mapping
The system accepts multiple aliases for the primary test store but consistently resolves them to the canonical ID `ST1008`.
- `STORE_BLR_002` -> `ST1008`
- `Brigade_Bangalore` -> `ST1008`

## Timezone Handling
- POS timestamps are provided in `Asia/Kolkata` local time (`%d-%m-%Y %H:%M:%S`).
- The pipeline parses these into timezone-aware datetimes and immediately converts them to UTC before storage in the database to align with the CCTV event timestamps, which are generated in UTC (`Z`).

## Staff Detection Heuristic
Traditional staff detection using uniform color thresholds (HSV) failed due to poor lighting and inconsistent apron coloring across cameras.
We implemented a robust spatial heuristic: if a unique `visitor_id` spends > 60% of their total `dwell_ms` within the `BILLING` or `CHECKOUT` polygon zones, they are classified as staff. This successfully filters cashiers from conversion metrics.
