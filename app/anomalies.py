import aiosqlite
from datetime import datetime, timezone
from .models import AnomaliesResponse, Anomaly
from .metrics import get_metrics

async def get_anomalies(store_id: str, db: aiosqlite.Connection) -> AnomaliesResponse:
    active_anomalies = []
    
    def utcnow_iso():
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    async with db.execute("""
        SELECT MAX(queue_depth) FROM events
        WHERE store_id=? AND event_type='BILLING_QUEUE_JOIN'
          AND timestamp > datetime('now','-10 minutes')
    """, (store_id,)) as cursor:
        row = await cursor.fetchone()
        max_queue = int(row[0]) if row and row[0] is not None else 0
        
    if max_queue >= 5:
        active_anomalies.append(Anomaly(
            type="BILLING_QUEUE_SPIKE",
            severity="CRITICAL",
            detected_at=utcnow_iso(),
            detail={"current_queue_depth": max_queue},
            suggested_action="Open an additional billing counter immediately."
        ))

    try:
        metrics = await get_metrics(store_id, db)
        today_rate = metrics.conversion_rate
        
        async with db.execute("""
            SELECT AVG(conversion_rate) FROM conversion_history
            WHERE store_id=? AND date >= date('now','-7 days')
        """, (store_id,)) as cursor:
            row = await cursor.fetchone()
            baseline_avg = float(row[0]) if row and row[0] is not None else 0.0
            
        if baseline_avg > 0 and today_rate < baseline_avg * 0.80:
            active_anomalies.append(Anomaly(
                type="CONVERSION_DROP",
                severity="WARN",
                detected_at=utcnow_iso(),
                detail={
                    "today_rate": today_rate, 
                    "baseline_7d_avg": baseline_avg,
                    "drop_pct": round((1 - today_rate/baseline_avg)*100, 1)
                },
                suggested_action="Review floor staff placement and entry zone signage."
            ))
    except Exception as e:
        import logging
        logging.getLogger("store_intelligence").warning(f"Failed to check CONVERSION_DROP anomaly: {e}")

    async with db.execute("""
        SELECT zone_id, MAX(timestamp) as last_seen FROM events
        WHERE store_id=? AND is_staff=0 AND event_type='ZONE_ENTER'
          AND date(timestamp)=date('now')
        GROUP BY zone_id
        HAVING last_seen < datetime('now','-30 minutes')
    """, (store_id,)) as cursor:
        rows = await cursor.fetchall()
        
    if rows:
        for row in rows:
            zone_id = row[0]
            last_seen = row[1]
            active_anomalies.append(Anomaly(
                type="DEAD_ZONE",
                severity="INFO",
                detected_at=utcnow_iso(),
                detail={"zone_id": zone_id, "last_activity": last_seen},
                suggested_action=f"Check camera feed for zone {zone_id}. Consider repositioning merchandise or staff."
            ))

    return AnomaliesResponse(
        store_id=store_id,
        active_anomalies=active_anomalies
    )
