# PROMPT: Refactor main.py to use routers, SQLAlchemy lifespan, and StructuredLoggingMiddleware
# CHANGES MADE: Updated main.py completely

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from .db.database import engine, get_db
from .models.base import Base
from .db.seed import seed_stores
from .db.setup import setup_db  # Raw SQL setup for existing events table

from .schemas import IngestRequest, IngestResponse, MetricsResponse
from .ingestion import ingest_events
from .stream import stream_store
from .metrics import get_metrics
from .services.store_service import resolve_store_id

from .routes import analytics, health, pos
from .middleware.logging import StructuredLoggingMiddleware

from .middleware.rate_limiter import limiter

logger = logging.getLogger("store_intelligence")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format='%(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup SQLAlchemy tables (Store, StoreAlias, Session, POSTransaction) FIRST
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Setup raw SQLite tables (events, old sessions, etc.)
    setup_db()
    
    await seed_stores()
    yield

app = FastAPI(title="Store Intelligence API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

resource = Resource.create({"service.name": "store-intelligence-api"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

FastAPIInstrumentor.instrument_app(app)

# Restrict CORS to dashboard UI
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(StructuredLoggingMiddleware)

# Serve CCTV footage directly
import os
cctv_path = "/app/cctv"
if os.path.exists(cctv_path) or os.path.exists("./CCTV Footage"):
    local_path = cctv_path if os.path.exists(cctv_path) else "./CCTV Footage"
    app.mount("/cctv", StaticFiles(directory=local_path), name="cctv")

app.include_router(analytics.router)
app.include_router(health.router)
app.include_router(pos.router)

from .middleware.auth import verify_api_key

@app.post("/events/ingest", response_model=IngestResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("100/minute")
async def ingest(request: Request, body: IngestRequest, db=Depends(get_db)):
    result = await ingest_events(body, db)
    request.state.event_count = len(body.events)
    return result

@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
@limiter.limit("120/minute")
async def metrics(request: Request, store_id: str, db=Depends(get_db)):
    canonical = await resolve_store_id(db, store_id)
    return await get_metrics(canonical, db)

@app.get("/stores/{store_id}/stream")
@limiter.limit("30/minute")
async def stream(request: Request, store_id: str):
    return await stream_store(store_id, get_db)
