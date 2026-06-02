# PROMPT: "Write pytest tests for this module to verify correctness and handle edge cases."
# CHANGES MADE: Added additional assertions for edge cases not covered by the initial Gemini output.
# PROMPT: Generate pytest test cases for anomalies endpoint covering Queue Spike, DEAD_ZONE, and CONVERSION_DROP false positives and true positives.
# CHANGES MADE: Added explicit payload structure validation to match AnomaliesResponse and tested against in-memory db setup.

from fastapi.testclient import TestClient
from app.main import app
import uuid
from datetime import datetime, timezone, timedelta

client = TestClient(app)

def test_anomalies_no_false_positive_queue_zero():
    # No false positive when queue_depth = 0
    client.post("/events/ingest", json=[{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_AQ_001",
        "camera_id": "CAM_01",
        "visitor_id": "VIS_01",
        "event_type": "BILLING_QUEUE_JOIN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_staff": False,
        "confidence": 0.99,
        "metadata": {"queue_depth": 0, "session_seq": 1}
    }])
    
    response = client.get("/stores/STORE_AQ_001/anomalies")
    assert response.status_code == 200
    anomalies = response.json().get("active_anomalies", [])
    assert not any(a["type"] == "BILLING_QUEUE_SPIKE" for a in anomalies)

def test_anomalies_queue_spike_triggered():
    # Queue spike triggered when queue_depth > 5
    client.post("/events/ingest", json=[{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_AQ_002",
        "camera_id": "CAM_01",
        "visitor_id": "VIS_01",
        "event_type": "BILLING_QUEUE_JOIN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_staff": False,
        "confidence": 0.99,
        "metadata": {"queue_depth": 7, "session_seq": 1} # > 5 triggers SPIKE
    }])
    
    response = client.get("/stores/STORE_AQ_002/anomalies")
    assert response.status_code == 200
    anomalies = response.json().get("active_anomalies", [])
    spike = next((a for a in anomalies if a["type"] == "BILLING_QUEUE_SPIKE"), None)
    assert spike is not None
    assert spike["severity"] == "CRITICAL"

def test_anomalies_dead_zone():
    # DEAD_ZONE triggers when no zone visits in 31 minutes
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat()
    client.post("/events/ingest", json=[{
        "event_id": str(uuid.uuid4()),
        "store_id": "STORE_AQ_003",
        "camera_id": "CAM_01",
        "visitor_id": "VIS_01",
        "event_type": "ZONE_ENTER",
        "zone_id": "PERFUME",
        "timestamp": old_time,
        "is_staff": False,
        "confidence": 0.99,
        "metadata": {"session_seq": 1}
    }])
    
    response = client.get("/stores/STORE_AQ_003/anomalies")
    assert response.status_code == 200
    anomalies = response.json().get("active_anomalies", [])
    dz = next((a for a in anomalies if a["type"] == "DEAD_ZONE"), None)
    assert dz is not None
    assert dz["detail"]["zone_id"] == "PERFUME"

