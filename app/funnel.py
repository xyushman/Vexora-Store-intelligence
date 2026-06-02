import aiosqlite
from .models import FunnelResponse, FunnelStage

async def get_funnel(store_id: str, db: aiosqlite.Connection) -> FunnelResponse:
    async with db.execute("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id=? AND date(entry_ts)=date('now')
        AND visitor_id NOT IN (SELECT DISTINCT visitor_id FROM events WHERE store_id=? AND is_staff=1)
    """, (store_id, store_id)) as cursor:
        row = await cursor.fetchone()
        stage1_count = int(row[0]) if row and row[0] else 0

    async with db.execute("""
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id=? AND is_staff=0 AND event_type='ZONE_ENTER'
          AND date(timestamp)=date('now')
          AND visitor_id IN (SELECT visitor_id FROM sessions WHERE store_id=? AND date(entry_ts)=date('now'))
    """, (store_id, store_id)) as cursor:
        row = await cursor.fetchone()
        stage2_count = int(row[0]) if row and row[0] else 0

    async with db.execute("""
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id=? AND is_staff=0 
          AND (zone_id IN ('BILLING','BILLING_COUNTER','CHECKOUT') OR event_type='BILLING_QUEUE_JOIN')
          AND date(timestamp)=date('now')
          AND visitor_id IN (SELECT visitor_id FROM sessions WHERE store_id=? AND date(entry_ts)=date('now'))
    """, (store_id, store_id)) as cursor:
        row = await cursor.fetchone()
        stage3_count = int(row[0]) if row and row[0] else 0

    async with db.execute("""
        SELECT DISTINCT e.visitor_id FROM events e
        JOIN pos_transactions p ON p.store_id = e.store_id
        WHERE e.store_id=? 
          AND e.zone_id IN ('BILLING','BILLING_COUNTER','CHECKOUT')
          AND e.is_staff=0
          AND (julianday(p.timestamp) - julianday(e.timestamp)) * 86400 BETWEEN 0 AND 300
    """, (store_id,)) as cursor:
        converted_rows = await cursor.fetchall()
        stage4_count = len(converted_rows)

    def calc_drop(current, prev):
        if prev > 0:
            return round(((prev - current) / prev) * 100, 1)
        return 0.0

    stages = [
        FunnelStage(stage="entry", count=stage1_count, drop_off_pct=0.0),
        FunnelStage(stage="zone_visit", count=stage2_count, drop_off_pct=calc_drop(stage2_count, stage1_count)),
        FunnelStage(stage="billing_zone", count=stage3_count, drop_off_pct=calc_drop(stage3_count, stage2_count)),
        FunnelStage(stage="purchase", count=stage4_count, drop_off_pct=calc_drop(stage4_count, stage3_count))
    ]

    return FunnelResponse(store_id=store_id, funnel=stages, session_window="today")
