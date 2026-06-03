# PROMPT: Session-Level Deduplication and Staff Exclusion
# CHANGES MADE: Created update_session hook

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from ..models.session import Session
from datetime import datetime

async def update_session(db: AsyncSession, event: dict):
    """
    Called after each event is ingested.
    - Upsert session by visitor_id + store_id
    - If event_type = ENTRY and session already has a last_seen > 30min ago → re_entry = True
    - Staff heuristic: if visitor has > 60% of dwell time in billing zone → is_staff = True
    - If visitor_id linked to a pos_transaction → converted = True
    All metrics endpoints must filter WHERE is_staff = False.
    """
    vid = event.get("visitor_id")
    sid = event.get("store_id")
    etype = event.get("event_type")
    ts_str = event.get("timestamp")
    
    if not ts_str:
        return
        
    ts_str_clean = ts_str.replace('Z', '+00:00')
    ts = datetime.fromisoformat(ts_str_clean)
    
    res = await db.execute(select(Session).where(Session.visitor_id == vid, Session.store_id == sid))
    sess = res.scalars().first()
    
    if not sess:
        sess = Session(
            visitor_id=vid,
            store_id=sid,
            first_seen=ts,
            last_seen=ts,
            entry_count=1 if etype == "ENTRY" else 0
        )
        db.add(sess)
    else:
        # Ensure timezone-aware datetime for comparison
        last_seen = sess.last_seen
        if last_seen and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=ts.tzinfo)

        if etype == "ENTRY" and last_seen:
            gap = (ts - last_seen).total_seconds()
            if gap > 1800:
                sess.re_entry = True
                sess.entry_count += 1
                
        if not sess.first_seen or ts < sess.first_seen.replace(tzinfo=ts.tzinfo):
            sess.first_seen = ts
        if not last_seen or ts > last_seen:
            sess.last_seen = ts
            
    await db.flush()
    
    res = await db.execute(text("""
        SELECT 
            SUM(CASE WHEN zone_id IN ('BILLING', 'BILLING_COUNTER', 'CHECKOUT') THEN dwell_ms ELSE 0 END) as billing_dwell,
            SUM(dwell_ms) as total_dwell
        FROM events 
        WHERE visitor_id = :vid AND store_id = :sid
    """), {"vid": vid, "sid": sid})
    
    dwell_row = res.fetchone()
    if dwell_row and dwell_row[1] and dwell_row[1] > 0:
        if (dwell_row[0] or 0) / dwell_row[1] > 0.6:
            sess.is_staff = True
            
    res = await db.execute(text("""
        SELECT 1 FROM events e
        JOIN pos_transactions p ON p.store_id = e.store_id
        WHERE e.visitor_id = :vid AND e.store_id = :sid
        AND (julianday(p.timestamp_utc) - julianday(e.timestamp)) * 86400 BETWEEN 0 AND 300
        LIMIT 1
    """), {"vid": vid, "sid": sid})
    if res.fetchone():
        sess.converted = True

    await db.commit()
