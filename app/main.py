import os
import time
import json
import logging
from uuid import uuid4
from sqlite3 import OperationalError
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import setup_db, load_pos_transactions, get_db
from .models import (
    IngestRequest, IngestResponse, MetricsResponse, FunnelResponse,
    HeatmapResponse, AnomaliesResponse, HealthResponse
)
from .ingestion import ingest_events
from .metrics import get_metrics
from .funnel import get_funnel
from .heatmap import get_heatmap
from .anomalies import get_anomalies
from .stream import stream_store
from .health import get_health

logger = logging.getLogger("store_intelligence")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_db()
    load_pos_transactions()
    yield

app = FastAPI(title="Store Intelligence API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(json.dumps({
            "trace_id": trace_id,
            "error": type(e).__name__,
            "detail": str(e)
        }))
        return JSONResponse(status_code=500,
                           content={"error": "internal_server_error"})
    latency_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info(json.dumps({
        "trace_id": trace_id,
        "store_id": request.path_params.get("store_id", "N/A"),
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "latency_ms": latency_ms,
        "event_count": getattr(request.state, "event_count", None)
    }))
    response.headers["X-Trace-Id"] = trace_id
    return response

@app.exception_handler(OperationalError)
async def db_error_handler(request: Request, exc: OperationalError):
    logger.error(json.dumps({
        "trace_id": getattr(request.state, "trace_id", "unknown"),
        "error": "db_unavailable"
    }))
    return JSONResponse(status_code=503,
                       content={"error": "database_unavailable", "retry_after": 30})

@app.post("/events/ingest", response_model=IngestResponse)
async def ingest(request: Request, body: IngestRequest, db=Depends(get_db)):
    result = await ingest_events(body, db)
    request.state.event_count = len(body.events)
    return result

@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
async def metrics(store_id: str, db=Depends(get_db)):
    return await get_metrics(store_id, db)

@app.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
async def funnel(store_id: str, db=Depends(get_db)):
    return await get_funnel(store_id, db)

@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
async def heatmap(store_id: str, db=Depends(get_db)):
    return await get_heatmap(store_id, db)

@app.get("/stores/{store_id}/anomalies", response_model=AnomaliesResponse)
async def anomalies(store_id: str, db=Depends(get_db)):
    return await get_anomalies(store_id, db)

@app.get("/stores/{store_id}/stream")
async def stream(store_id: str):
    return await stream_store(store_id, get_db)

@app.get("/health", response_model=HealthResponse)
async def health(db=Depends(get_db)):
    return await get_health(db)
