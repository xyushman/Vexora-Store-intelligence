import json
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from sse_starlette.sse import EventSourceResponse

from .metrics import get_metrics
from .anomalies import get_anomalies

logger = logging.getLogger("store_intelligence")

async def stream_store(store_id: str, db_factory):
    async def generator():
        while True:
            try:
                @asynccontextmanager
                async def wrapped_db():
                    async for db in db_factory():
                        yield db
                        
                async with wrapped_db() as db:
                    metrics = await get_metrics(store_id, db)
                    anomalies = await get_anomalies(store_id, db)
                    payload = {
                        "metrics": metrics.model_dump(),
                        "anomalies": [a.model_dump() for a in anomalies.active_anomalies],
                        "ts": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                    }
                    yield {"data": json.dumps(payload)}
            except Exception as e:
                logger.error(json.dumps({"event": "sse_error", "store_id": store_id, "error": str(e)}))
            await asyncio.sleep(2)
            
    return EventSourceResponse(generator())
