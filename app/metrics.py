import aiosqlite
from datetime import datetime, timezone
from .models import MetricsResponse

async def get_metrics(store_id: str, db: aiosqlite.Connection) -> MetricsResponse:
    async with db.execute("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id=? AND date(entry_ts)=date('now') AND visitor_id NOT IN (
          SELECT DISTINCT visitor_id FROM events 
          WHERE store_id=? AND is_staff=1
        )
    """, (store_id, store_id)) as cursor:
        row = await cursor.fetchone()
        unique_visitors = int(row[0]) if row and row[0] else 0

    async with db.execute("""
        SELECT DISTINCT e.visitor_id FROM events e
        JOIN pos_transactions p ON p.store_id = e.store_id
        WHERE e.store_id=? 
          AND e.zone_id IN ('BILLING','BILLING_COUNTER','CHECKOUT')
          AND e.is_staff=0
          AND (julianday(p.timestamp) - julianday(e.timestamp)) * 86400 BETWEEN 0 AND 300
    """, (store_id,)) as cursor:
        converted_rows = await cursor.fetchall()
        converted_count = len(converted_rows)
        
    conversion_rate = float(converted_count) / unique_visitors if unique_visitors > 0 else 0.0

    async with db.execute("""
        SELECT zone_id, AVG(dwell_ms) FROM events
        WHERE store_id=? AND is_staff=0 AND zone_id IS NOT NULL
          AND event_type='ZONE_DWELL' AND date(timestamp)=date('now')
        GROUP BY zone_id
    """, (store_id,)) as cursor:
        dwell_rows = await cursor.fetchall()
        avg_dwell_per_zone = {row[0]: float(row[1]) for row in dwell_rows} if dwell_rows else {}

    async with db.execute("""
        SELECT queue_depth FROM events
        WHERE store_id=? AND event_type='BILLING_QUEUE_JOIN'
          AND timestamp > datetime('now','-5 minutes')
        ORDER BY timestamp DESC LIMIT 1
    """, (store_id,)) as cursor:
        row = await cursor.fetchone()
        queue_depth_current = int(row[0]) if row and row[0] is not None else 0

    async with db.execute("""
        SELECT COUNT(*) FROM events 
        WHERE store_id=? AND event_type='BILLING_QUEUE_ABANDON' AND date(timestamp)=date('now')
    """, (store_id,)) as cursor:
        row = await cursor.fetchone()
        abandon_count = int(row[0]) if row and row[0] else 0

    async with db.execute("""
        SELECT COUNT(*) FROM events 
        WHERE store_id=? AND event_type='BILLING_QUEUE_JOIN' AND date(timestamp)=date('now')
    """, (store_id,)) as cursor:
        row = await cursor.fetchone()
        join_count = int(row[0]) if row and row[0] else 0

    abandonment_rate = float(abandon_count) / join_count if join_count > 0 else 0.0

    computed_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    return MetricsResponse(
        store_id=store_id,
        window="today",
        unique_visitors=unique_visitors,
        conversion_rate=conversion_rate,
        avg_dwell_per_zone=avg_dwell_per_zone,
        queue_depth_current=queue_depth_current,
        abandonment_rate=abandonment_rate,
        computed_at=computed_at
    )
