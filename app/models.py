from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict
from uuid import uuid4
from datetime import datetime

class EventMetadata(BaseModel):
    queue_depth: Optional[int] = None
    sku_zone: Optional[str] = None
    session_seq: int = 0

class StoreEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: Literal["ENTRY","EXIT","ZONE_ENTER","ZONE_EXIT","ZONE_DWELL",
                        "BILLING_QUEUE_JOIN","BILLING_QUEUE_ABANDON","REENTRY"]
    timestamp: str
    zone_id: Optional[str] = None
    dwell_ms: int = 0
    is_staff: bool
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: EventMetadata

    @field_validator('timestamp')
    @classmethod
    def validate_iso8601(cls, v):
        try:
            ts_str = v.replace('Z', '+00:00')
            datetime.fromisoformat(ts_str)
        except ValueError:
            raise ValueError('Invalid ISO-8601 format')
        return v

class IngestRequest(BaseModel):
    events: List[StoreEvent] = Field(max_length=500)

class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    errors: List[dict]

class ZoneMetric(BaseModel):
    zone_id: str
    avg_dwell_ms: float
    visit_count: int

class MetricsResponse(BaseModel):
    store_id: str
    window: str = "today"
    unique_visitors: int
    conversion_rate: float
    avg_dwell_per_zone: Dict[str, float]
    queue_depth_current: int
    abandonment_rate: float
    computed_at: str

class FunnelStage(BaseModel):
    stage: str
    count: int
    drop_off_pct: float

class FunnelResponse(BaseModel):
    store_id: str
    funnel: List[FunnelStage]
    session_window: str = "today"

class HeatmapZone(BaseModel):
    zone_id: str
    visit_freq: int
    avg_dwell_ms: float

class HeatmapResponse(BaseModel):
    store_id: str
    data_confidence: Literal["HIGH", "LOW"]
    zones: List[HeatmapZone]

class Anomaly(BaseModel):
    type: str
    severity: Literal["INFO", "WARN", "CRITICAL"]
    detected_at: str
    detail: dict
    suggested_action: str

class AnomaliesResponse(BaseModel):
    store_id: str
    active_anomalies: List[Anomaly]

class StoreHealthStatus(BaseModel):
    last_event_ts: Optional[str]
    feed_status: Literal["LIVE", "STALE_FEED", "NO_DATA"]

class HealthResponse(BaseModel):
    status: str
    stores: Dict[str, StoreHealthStatus]
    db_status: Literal["ok", "degraded"]
    uptime_seconds: int
