# PROMPT: "Write pytest tests for this module to verify correctness and handle edge cases."
# CHANGES MADE: Added additional assertions for edge cases not covered by the initial Gemini output.
# PROMPT: Generate pytest test cases for metrics endpoints covering the four explicit edge cases: empty store, all-staff clip, zero purchases, and re-entry in funnel.
# CHANGES MADE: Adapted the payload to match the specific Pydantic EventSchema used in this project. Added specific assertions for conversion rate and unique visitors.

from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime, timezone

client = TestClient(app)

def test_get_metrics_empty_store():
    # 1. Empty Store Edge Case
    response = client.get("/stores/STORE_EMPTY_001/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["unique_visitors"] == 0
    assert data["conversion_rate"] == 0.0

def test_all_staff_clip():
    # 2. All-staff clip Edge Case
    event_id = str(uuid.uuid4())
    payload = [{
        "event_id": event_id,
        "store_id": "STORE_STAFF_001",
        "camera_id": "CAM_01",
        "visitor_id": "STAFF_01",
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dwell_ms": 0,
        "is_staff": True, # This flag should exclude them from customer metrics
        "confidence": 0.99,
        "metadata": {}
    }]
    # Ingest staff event
    client.post("/events/ingest", json={"events": payload} if isinstance(payload, list) else payload)
    
    # Query metrics
    response = client.get("/stores/STORE_STAFF_001/metrics")
    assert response.status_code == 200
    assert response.json()["unique_visitors"] == 0 # Excluded

def test_zero_purchases():
    # 3. Zero purchases Edge Case
    event_id = str(uuid.uuid4())
    payload = [{
        "event_id": event_id,
        "store_id": "STORE_NO_BUY_001",
        "camera_id": "CAM_01",
        "visitor_id": "VIS_02",
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.99,
        "metadata": {}
    }]
    client.post("/events/ingest", json={"events": payload} if isinstance(payload, list) else payload)
    
    response = client.get("/stores/STORE_NO_BUY_001/metrics")
    assert response.status_code == 200
    # Must not crash, should return 0.0 cleanly
    assert response.json()["conversion_rate"] == 0.0

def test_reentry_in_funnel():
    # 4. Re-entry in Funnel Edge Case
    visitor_id = "VIS_REENTRY_01"
    store_id = "STORE_REENTRY_001"
    payload = [
        # First Entry
        {
            "event_id": str(uuid.uuid4()),
            "store_id": store_id,
            "camera_id": "CAM_01",
            "visitor_id": visitor_id,
            "event_type": "ENTRY",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.99,
            "metadata": {}
        },
        # Re-entry
        {
            "event_id": str(uuid.uuid4()),
            "store_id": store_id,
            "camera_id": "CAM_01",
            "visitor_id": visitor_id,
            "event_type": "REENTRY",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.99,
            "metadata": {}
        }
    ]
    client.post("/events/ingest", json={"events": payload} if isinstance(payload, list) else payload)
    
    # Query funnel
    response = client.get(f"/stores/{store_id}/funnel")
    assert response.status_code == 200
    data = response.json()
    # Unique visitors should be 1, despite 2 entry events (ENTRY + REENTRY)
    assert data["entry"]["count"] == 1

