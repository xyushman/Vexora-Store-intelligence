# Store Intelligence Architecture Design

This document details the architectural principles and design decisions for the Purplle Tech Challenge. The core philosophy of this implementation is pragmatism: choosing the simplest, most reliable tools that perfectly meet the requirements of the containerized assignment.

The pipeline is split into a Computer Vision detection layer (edge) that produces structured `events.jsonl` payloads, and a robust FastAPI backend (cloud) that handles ingestion, correlation, and metric aggregations.

## AI-Assisted Decisions

Throughout this challenge, I leveraged AI heavily to validate trade-offs and shape the architecture. Here are three specific examples:

1. **Database Selection**: I prompted an LLM to evaluate SQLite WAL mode vs PostgreSQL for a containerized hiring challenge. The AI highlighted that PostgreSQL requires a separate container, increasing the risk of startup failure during the grading process if RAM constraints are tight. It suggested SQLite with WAL (Write-Ahead Logging) mode enabled. I agreed with this suggestion, as WAL mode easily handles the required concurrency (simultaneous batch ingestion and metric reads) without any configuration overhead, satisfying the requirement that `docker-compose up` cleanly starts everything.

2. **BILLING_QUEUE_ABANDON Logic**: I initially considered having the pipeline wait 5 minutes to emit the ABANDON event. The AI pointed out that this violates separation of concerns: the pipeline only sees video frames, not POS data. The AI suggested emitting a `ZONE_EXIT` event from the pipeline and implementing a deferred background check in the API. I agreed and implemented `app/correlator.py`, which is triggered to look for `ZONE_EXIT` events in the billing zone that lack matching POS transactions within a ±5 minute window.

3. **Funnel Session Deduplication**: When building the `/funnel` endpoint, I prompted the AI to optimize my SQL query to avoid double-counting visitors who re-enter. The AI suggested writing a massive raw SQL CTE query. I disagreed and overrode this, choosing instead to lean on SQLAlchemy's ORM capabilities. I utilized a subquery on the `sessions` table (where `visitor_id` is naturally distinct and `entry_ts` defines the canonical start) and joined it against the events table. This resulted in far more readable, maintainable code than the AI's complex raw SQL block.
