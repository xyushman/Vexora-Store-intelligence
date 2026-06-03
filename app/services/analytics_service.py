# PROMPT: Implement compute_funnel and compute_heatmap
# CHANGES MADE: Created analytics_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

async def compute_funnel(db: AsyncSession, store_id: str) -> dict:
    """
    Returns funnel data
    """
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id = :sid AND event_type = 'ENTRY'
          AND visitor_id NOT IN (SELECT visitor_id FROM sessions WHERE store_id = :sid AND is_staff = 1)
    """), {"sid": store_id})
    stage1 = res.scalar() or 0
    
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id = :sid AND event_type = 'ZONE_ENTER' 
          AND zone_id NOT IN ('BILLING', 'BILLING_COUNTER', 'CHECKOUT')
          AND visitor_id NOT IN (SELECT visitor_id FROM sessions WHERE store_id = :sid AND is_staff = 1)
    """), {"sid": store_id})
    stage2 = res.scalar() or 0
    
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM events
        WHERE store_id = :sid 
          AND (event_type = 'BILLING_QUEUE_JOIN' OR zone_id IN ('BILLING', 'BILLING_COUNTER', 'CHECKOUT'))
          AND visitor_id NOT IN (SELECT visitor_id FROM sessions WHERE store_id = :sid AND is_staff = 1)
    """), {"sid": store_id})
    stage3 = res.scalar() or 0
    
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id = :sid AND is_staff = 0 AND converted = 1
    """), {"sid": store_id})
    stage4 = res.scalar() or 0
    
    def drop(curr, prev):
        if prev > 0:
            return round(((prev - curr) / prev) * 100, 1)
        return 0.0

    overall = round((stage4 / stage1 * 100), 1) if stage1 > 0 else 0.0
    
    return {
        "store_id": store_id,
        "stages": [
            {"stage": "entry", "count": stage1, "drop_off_pct": None},
            {"stage": "zone_visit", "count": stage2, "drop_off_pct": drop(stage2, stage1)},
            {"stage": "billing_queue", "count": stage3, "drop_off_pct": drop(stage3, stage2)},
            {"stage": "purchase", "count": stage4, "drop_off_pct": drop(stage4, stage3)}
        ],
        "overall_conversion_pct": overall
    }

async def compute_heatmap(db: AsyncSession, store_id: str, window_minutes: int) -> dict:
    """
    Returns heatmap data
    """
    res = await db.execute(text("""
        SELECT COUNT(DISTINCT visitor_id) FROM sessions
        WHERE store_id = :sid AND last_seen >= datetime('now', :win)
    """), {"sid": store_id, "win": f"-{window_minutes} minutes"})
    sessions_in_window = res.scalar() or 0
    
    confidence = "LOW" if sessions_in_window < 20 else "HIGH"
    
    res = await db.execute(text("""
        SELECT zone_id, COUNT(DISTINCT visitor_id) as visit_count, AVG(dwell_ms)/1000.0 as avg_dwell
        FROM events
        WHERE store_id = :sid 
          AND zone_id IS NOT NULL 
          AND event_type IN ('ZONE_ENTER', 'ZONE_DWELL')
          AND timestamp >= datetime('now', :win)
          AND visitor_id NOT IN (SELECT visitor_id FROM sessions WHERE store_id = :sid AND is_staff = 1)
        GROUP BY zone_id
    """), {"sid": store_id, "win": f"-{window_minutes} minutes"})
    
    zones = []
    max_raw = 0.0
    
    zone_rows = res.fetchall()
    for r in zone_rows:
        raw_score = r.visit_count * 0.4 + (r.avg_dwell or 0) * 0.6
        if raw_score > max_raw:
            max_raw = raw_score
            
    for r in zone_rows:
        raw_score = r.visit_count * 0.4 + (r.avg_dwell or 0) * 0.6
        score = round((raw_score / max_raw) * 100) if max_raw > 0 else 0
        zones.append({
            "zone_id": r.zone_id,
            "visit_count": r.visit_count,
            "avg_dwell_seconds": round(r.avg_dwell or 0, 1),
            "score": score
        })
        
    return {
        "store_id": store_id,
        "window_minutes": window_minutes,
        "data_confidence": confidence,
        "zones": zones
    }
