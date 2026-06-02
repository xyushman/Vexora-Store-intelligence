import aiosqlite
from datetime import datetime, timezone
from .models import HealthResponse, StoreHealthStatus

START_TIME = datetime.utcnow()

async def get_health(db: aiosqlite.Connection) -> HealthResponse:
    try:
        await db.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "degraded"

    utcnow = datetime.utcnow()
    stores = {}
    
    async with db.execute("""
        SELECT store_id, MAX(timestamp) as last_event_ts FROM events GROUP BY store_id
    """) as cursor:
        rows = await cursor.fetchall()

    if rows:
        for row in rows:
            store_id = row[0]
            last_event_ts_str = row[1]
            
            try:
                ts_str_clean = last_event_ts_str.replace('Z', '+00:00')
                last_event_ts = datetime.fromisoformat(ts_str_clean).replace(tzinfo=None)
                lag = (utcnow - last_event_ts).total_seconds()
            except Exception:
                lag = 0
                
            feed_status = "STALE_FEED" if lag > 600 else "LIVE"
            
            stores[store_id] = StoreHealthStatus(
                last_event_ts=last_event_ts_str,
                feed_status=feed_status
            )
            
    async with db.execute("SELECT DISTINCT store_id FROM conversion_history") as cursor:
        known_stores = await cursor.fetchall()
        for k_row in known_stores:
            s_id = k_row[0]
            if s_id not in stores:
                stores[s_id] = StoreHealthStatus(
                    last_event_ts=None,
                    feed_status="NO_DATA"
                )

    uptime_seconds = int((datetime.utcnow() - START_TIME).total_seconds())
    status = "ok" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=status,
        stores=stores,
        db_status=db_status,
        uptime_seconds=uptime_seconds
    )
