# PROMPT: Enhanced /health endpoint with STALE_FEED detection
# CHANGES MADE: Created health router

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import time

from ..db.database import get_db
from ..schemas import HealthResponse, StoreHealthStatus
from ..middleware.rate_limiter import limiter

router = APIRouter()
START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
@limiter.limit("20/minute")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Returns health status with DB connectivity and feed staleness check.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"
        
    res = await db.execute(text("SELECT MAX(timestamp) FROM events"))
    latest_event = res.scalar()
    
    feed_status = "NO_DATA"
    age_seconds = None
    status = "ok"
    
    if latest_event:
        try:
            latest_dt = datetime.fromisoformat(latest_event.replace("Z", "+00:00")).replace(tzinfo=None)
            age_seconds = int((datetime.utcnow() - latest_dt).total_seconds())
            if age_seconds > 600:
                feed_status = "STALE_FEED"
                status = "degraded"
            else:
                feed_status = "LIVE"
        except Exception:
            pass
            
    if db_status == "error":
        status = "down"

    return {
        "status": status,
        "database": db_status,
        "feed_status": feed_status,
        "latest_event_age_seconds": age_seconds,
        "trace_id": getattr(request.state, "trace_id", "unknown")
    }
