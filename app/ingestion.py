import sqlite3
import aiosqlite
from .models import IngestRequest, IngestResponse

async def ingest_events(request: IngestRequest, db: aiosqlite.Connection) -> IngestResponse:
    accepted = 0
    rejected = 0
    errors = []

    for event in request.events:
        try:
            is_staff_int = 1 if event.is_staff else 0
            
            await db.execute("""
                INSERT OR IGNORE INTO events 
                (event_id, store_id, camera_id, visitor_id, event_type, timestamp, zone_id, dwell_ms, is_staff, confidence, queue_depth, sku_zone, session_seq)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.store_id, event.camera_id, event.visitor_id, 
                event.event_type, event.timestamp, event.zone_id, event.dwell_ms, 
                is_staff_int, event.confidence, event.metadata.queue_depth, 
                event.metadata.sku_zone, event.metadata.session_seq
            ))
            
            if event.event_type in ("ENTRY", "REENTRY"):
                is_reentry = 1 if event.event_type == "REENTRY" else 0
                await db.execute("""
                    INSERT OR IGNORE INTO sessions (visitor_id, store_id, entry_ts, is_reentry)
                    VALUES (?, ?, ?, ?)
                """, (event.visitor_id, event.store_id, event.timestamp, is_reentry))
                
            elif event.event_type == "EXIT":
                await db.execute("""
                    UPDATE sessions SET exit_ts = ? 
                    WHERE visitor_id=? AND store_id=? AND exit_ts IS NULL
                """, (event.timestamp, event.visitor_id, event.store_id))
                
            accepted += 1
        except sqlite3.Error as e:
            errors.append({"event_id": event.event_id, "reason": str(e)})
            rejected += 1
            
    await db.commit()
            
    return IngestResponse(accepted=accepted, rejected=rejected, errors=errors)
