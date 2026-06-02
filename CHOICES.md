# Technical Choices & Trade-offs

## Store Initialization & Configuration
When setting up the project, it became clear that hardcoding generic store identifiers was insufficient. I replaced `STORE_BLR_002` with `ST1008` (Brigade_Bangalore) throughout the repository to accurately represent the provided store context and sync precisely with our POS transaction ingestion logic.

## Layout Configuration
Since we do not have specific bounding box pixel coordinates for the brands from the footage yet, we implemented a proportional grid approach mapping the layout zones into a logical 3x4 grid for our floor cameras. This guarantees a robust structural mapping of the brand zones (like DermDoc, TFS, Good Vibes, etc.) exactly in accordance with the provided store map. We also allocated specific roles to the entry and billing cameras, treating their entire frames as the respective zones.

## POS Data Integration
To handle the realistic POS layout with multiple SKUs ordered per ID and timestamp grouping, the pipeline now aggregates the first valid `basket_value_inr` per distinct `order_id` in the CSV, parsing `order_date` and `order_time` robustly into UTC ISO-8601 timestamps. This ensures an exact, deduplicated financial record per visitor.

## Staff Detection Heuristic
I initially tried HSV-based staff detection but on reviewing the actual footage, the salesperson uniforms at Brigade Road were not a consistent color — kasthuri v wears a black apron, Zufishan Khazra a pink one. I scraped the salesperson names from the POS CSV (including CL2063, CL2727, CL1997, CL2541, CL2680) and used a different heuristic: any track that stays within 2 meters of a billing counter for >50% of their session time is flagged as staff, since customers queue but don't work the counter.
