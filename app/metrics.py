# PROMPT: Refactor metrics to use AsyncSession
# CHANGES MADE: Updated get_metrics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timezone
from .schemas import MetricsResponse

async def get_metrics(store_id: str, db: AsyncSession) -> MetricsResponse:
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id=:sid AND date(first_seen)=date('now') AND visitor_id NOT IN (
          SELECT DISTINCT visitor_id FROM events 
          WHERE store_id=:sid AND is_staff=1
        )
    """), {"sid": store_id})
    unique_visitors = res.scalar() or 0

    res = await db.execute(text("""
        SELECT DISTINCT e.visitor_id FROM events e
        JOIN pos_transactions p ON p.store_id = e.store_id
        WHERE e.store_id=:sid 
          AND e.zone_id IN ('BILLING','BILLING_COUNTER','CHECKOUT')
          AND e.is_staff=0
          AND (julianday(p.timestamp_utc) - julianday(e.timestamp)) * 86400 BETWEEN 0 AND 300
    """), {"sid": store_id})
    converted_count = len(res.fetchall())
        
    conversion_rate = float(converted_count) / unique_visitors if unique_visitors > 0 else 0.0

    res = await db.execute(text("""
        SELECT zone_id, AVG(dwell_ms) FROM events
        WHERE store_id=:sid AND is_staff=0 AND zone_id IS NOT NULL
          AND event_type='ZONE_DWELL' AND date(timestamp)=date('now')
        GROUP BY zone_id
    """), {"sid": store_id})
    dwell_rows = res.fetchall()
    avg_dwell_per_zone = {row[0]: float(row[1]) for row in dwell_rows} if dwell_rows else {}

    res = await db.execute(text("""
        SELECT queue_depth FROM events
        WHERE store_id=:sid AND event_type='BILLING_QUEUE_JOIN'
          AND timestamp > datetime('now','-5 minutes')
        ORDER BY timestamp DESC LIMIT 1
    """), {"sid": store_id})
    qd = res.scalar()
    queue_depth_current = int(qd) if qd is not None else 0

    res = await db.execute(text("""
        SELECT COUNT(*) FROM events 
        WHERE store_id=:sid AND event_type='BILLING_QUEUE_ABANDON' AND date(timestamp)=date('now')
    """), {"sid": store_id})
    abandon_count = res.scalar() or 0

    res = await db.execute(text("""
        SELECT COUNT(*) FROM events 
        WHERE store_id=:sid AND event_type='BILLING_QUEUE_JOIN' AND date(timestamp)=date('now')
    """), {"sid": store_id})
    join_count = res.scalar() or 0

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
