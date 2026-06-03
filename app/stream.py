# PROMPT: Refactor stream.py to use AsyncSession
# CHANGES MADE: Updated stream_store

import json
import asyncio
import logging
from datetime import datetime, timezone
from sse_starlette.sse import EventSourceResponse

from .metrics import get_metrics
from .services.anomaly_service import AnomalyEngine
from .services.store_service import resolve_store_id

logger = logging.getLogger("store_intelligence")

async def stream_store(store_id: str, db_factory):
    async def generator():
        while True:
            try:
                # get_db is an async generator
                async for db in db_factory():
                    canonical = await resolve_store_id(db, store_id)
                    metrics = await get_metrics(canonical, db)
                    engine = AnomalyEngine(db)
                    anomalies = await engine.detect_all(canonical)
                    payload = {
                        "metrics": metrics.model_dump(),
                        "anomalies": anomalies,
                        "ts": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    }
                    yield {"data": json.dumps(payload)}
                    break # only need one yield per db tick
            except Exception as e:
                logger.error(json.dumps({"event": "sse_error", "store_id": store_id, "error": str(e)}))
            await asyncio.sleep(2)
            
    return EventSourceResponse(generator())
