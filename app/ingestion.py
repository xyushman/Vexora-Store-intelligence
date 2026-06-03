# PROMPT: Refactor ingestion to use AsyncSession and call update_session hook
# CHANGES MADE: Updated ingest_events

import sqlite3
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .schemas import IngestRequest, IngestResponse
from .services.session_service import update_session

async def ingest_events(request: IngestRequest, db: AsyncSession) -> IngestResponse:
    accepted = 0
    rejected = 0
    errors = []

    for event in request.events:
        try:
            is_staff_int = 1 if event.is_staff else 0
            
            await db.execute(text("""
                INSERT OR IGNORE INTO events 
                (event_id, store_id, camera_id, visitor_id, event_type, timestamp, zone_id, dwell_ms, is_staff, confidence, queue_depth, sku_zone, session_seq)
                VALUES (:event_id, :store_id, :camera_id, :visitor_id, :event_type, :timestamp, :zone_id, :dwell_ms, :is_staff, :confidence, :queue_depth, :sku_zone, :session_seq)
            """), {
                "event_id": event.event_id, "store_id": event.store_id, "camera_id": event.camera_id, "visitor_id": event.visitor_id, 
                "event_type": event.event_type, "timestamp": event.timestamp, "zone_id": event.zone_id, "dwell_ms": event.dwell_ms, 
                "is_staff": is_staff_int, "confidence": event.confidence, "queue_depth": event.metadata.queue_depth, 
                "sku_zone": event.metadata.sku_zone, "session_seq": event.metadata.session_seq
            })
            
            # Session logic is fully handled by update_session hook
                
            await update_session(db, event.dict())
            accepted += 1
        except Exception as e:
            errors.append({"event_id": event.event_id, "reason": str(e)})
            rejected += 1
            
    await db.commit()
            
    return IngestResponse(accepted=accepted, rejected=rejected, errors=errors)
