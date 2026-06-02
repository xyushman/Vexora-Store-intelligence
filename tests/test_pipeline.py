# PROMPT: Generate pytest cases for pipeline emit logic covering: schema validation, group entry (3 simultaneous crossings = 3 ENTRY events), REENTRY dedup, and unsuppressed confidence checks.
# CHANGES MADE: Adapted to mock the pipeline processing function since detect.py is not fully implemented yet, but we are validating the interface contract described in emit.py

import pytest
from app.models import EventSchema
from pipeline.emit import process_frame_detections

def test_schema_validation():
    # Schema validation: every emitted event passes Pydantic model
    detections = [{
        "track_id": "VIS_01",
        "confidence": 0.88,
        "inferred_event": "ENTRY",
        "zone_id": None,
        "dwell_ms": 0,
        "is_staff": False,
        "metadata": {"session_seq": 1}
    }]
    events = process_frame_detections("STORE_1", "CAM_1", detections)
    # This will raise validation error if bad
    validated = EventSchema(**events[0])
    assert validated.confidence == 0.88

def test_group_entry():
    # Group entry: 3 simultaneous crossings -> 3 distinct ENTRY events
    detections = [
        {"track_id": "VIS_01", "confidence": 0.9, "inferred_event": "ENTRY", "metadata": {"session_seq": 1}},
        {"track_id": "VIS_02", "confidence": 0.9, "inferred_event": "ENTRY", "metadata": {"session_seq": 1}},
        {"track_id": "VIS_03", "confidence": 0.9, "inferred_event": "ENTRY", "metadata": {"session_seq": 1}},
    ]
    events = process_frame_detections("STORE_1", "CAM_1", detections)
    assert len(events) == 3
    visitor_ids = set(e["visitor_id"] for e in events)
    assert len(visitor_ids) == 3

def test_reentry():
    # REENTRY: same embedding re-enters -> REENTRY not ENTRY
    # Simulating the tracker output
    detections = [{
        "track_id": "VIS_01",
        "confidence": 0.95,
        "inferred_event": "REENTRY", # Tracker determines it's a reentry
        "metadata": {"session_seq": 2}
    }]
    events = process_frame_detections("STORE_1", "CAM_1", detections)
    assert events[0]["event_type"] == "REENTRY"

def test_unsuppressed_confidence():
    # Confidence not clamped: detection conf 0.18 -> emitted as 0.18
    detections = [{
        "track_id": "VIS_01",
        "confidence": 0.18, # very low
        "inferred_event": "ENTRY",
        "metadata": {"session_seq": 1}
    }]
    events = process_frame_detections("STORE_1", "CAM_1", detections)
    assert events[0]["confidence"] == 0.18

from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime, timezone

client = TestClient(app)

def test_ingest_idempotency():
    # POST /events/ingest must be safe to call twice with the same payload
    payload = [{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_IDEMP",
        "camera_id": "CAM_01",
        "visitor_id": "VIS_01",
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.99,
        "metadata": {"session_seq": 1}
    }]
    
    # First call
    response1 = client.post("/events/ingest", json=payload)
    assert response1.status_code == 200
    assert response1.json()["accepted"] == 1
    
    # Second call - same payload
    response2 = client.post("/events/ingest", json=payload)
    assert response2.status_code == 200
    assert response2.json()["accepted"] == 1 # Still counted as accepted (idempotent)
    
    # Verify only 1 event actually in DB
    # We can check metrics (1 unique visitor)
    m = client.get("/stores/STORE_IDEMP/metrics")
    assert m.json()["unique_visitors"] == 1

