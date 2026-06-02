import aiosqlite
from .models import HeatmapResponse, HeatmapZone

async def get_heatmap(store_id: str, db: aiosqlite.Connection) -> HeatmapResponse:
    async with db.execute("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id=? AND date(entry_ts)=date('now')
    """, (store_id,)) as cursor:
        row = await cursor.fetchone()
        session_count = int(row[0]) if row and row[0] else 0
        
    data_confidence = "LOW" if session_count < 20 else "HIGH"

    async with db.execute("""
        SELECT zone_id, COUNT(DISTINCT visitor_id) as visit_count, AVG(dwell_ms) as avg_dwell
        FROM events
        WHERE store_id=? AND is_staff=0 AND zone_id IS NOT NULL
          AND event_type IN ('ZONE_ENTER','ZONE_DWELL')
          AND date(timestamp)=date('now')
        GROUP BY zone_id
    """, (store_id,)) as cursor:
        rows = await cursor.fetchall()
        
    zones = []
    if rows:
        max_visits = max(row[1] for row in rows) or 1
        for row in rows:
            zone_id = row[0]
            visit_count = int(row[1])
            avg_dwell = float(row[2]) if row[2] is not None else 0.0
            visit_freq = round((visit_count / max_visits) * 100)
            zones.append(HeatmapZone(
                zone_id=zone_id,
                visit_freq=visit_freq,
                avg_dwell_ms=avg_dwell
            ))

    return HeatmapResponse(
        store_id=store_id,
        data_confidence=data_confidence,
        zones=zones
    )
