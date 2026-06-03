# PROMPT: Implement rule-based anomaly detection for queue spikes, conversion drops, dead zones, and stale feeds. Use Claude (anthropic SDK) for insight generation.
# CHANGES MADE: Created AnomalyEngine with 4 detection rules + Claude insight layer

from google import genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

ANOMALY_RULES = {
    "QUEUE_SPIKE":       {"threshold": 8,   "severity": "CRITICAL"},
    "CONVERSION_DROP":   {"threshold": 0.15, "severity": "WARN"},
    "DEAD_ZONE":         {"minutes": 30,     "severity": "WARN"},
    "STALE_FEED":        {"minutes": 10,     "severity": "CRITICAL"},
}

class AnomalyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = genai.Client()

    async def detect_all(self, store_id: str) -> list[dict]:
        anomalies = []
        anomalies += await self._check_queue_spike(store_id)
        anomalies += await self._check_conversion_drop(store_id)
        anomalies += await self._check_dead_zones(store_id)
        anomalies += await self._check_stale_feed(store_id)
        for a in anomalies:
            if a["severity"] == "CRITICAL":
                try:
                    a["insight"] = await self._get_claude_insight(a)
                except Exception as e:
                    a["insight"] = f"Failed to generate insight: {e}"
        return anomalies

    async def _check_queue_spike(self, store_id: str) -> list[dict]:
        res = await self.db.execute(text("""
            SELECT COUNT(DISTINCT visitor_id) FROM events e1
            WHERE store_id = :sid AND event_type = 'BILLING_QUEUE_JOIN'
            AND timestamp >= datetime('now', '-30 minutes')
            AND NOT EXISTS (
                SELECT 1 FROM events e2 
                WHERE e2.visitor_id = e1.visitor_id 
                AND e2.store_id = :sid
                AND e2.event_type = 'BILLING_QUEUE_EXIT'
                AND e2.timestamp > e1.timestamp
            )
        """), {"sid": store_id})
        count = res.scalar() or 0
        thresh = ANOMALY_RULES["QUEUE_SPIKE"]["threshold"]
        if count > thresh:
            return [{
                "anomaly_type": "QUEUE_SPIKE",
                "severity": ANOMALY_RULES["QUEUE_SPIKE"]["severity"],
                "description": f"Queue depth is {count} (threshold: {thresh})",
                "suggested_action": "Open additional billing counter",
                "detected_at": datetime.utcnow().isoformat() + "Z"
            }]
        return []

    async def _check_conversion_drop(self, store_id: str) -> list[dict]:
        res = await self.db.execute(text("""
            SELECT 
                SUM(CASE WHEN date(first_seen) = date('now') AND converted = 1 THEN 1 ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN date(first_seen) = date('now') THEN 1 ELSE 0 END), 0) as today_rate,
                SUM(CASE WHEN date(first_seen) >= date('now', '-7 days') AND date(first_seen) < date('now') AND converted = 1 THEN 1 ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN date(first_seen) >= date('now', '-7 days') AND date(first_seen) < date('now') THEN 1 ELSE 0 END), 0) as avg_7d
            FROM sessions
            WHERE store_id = :sid AND is_staff = 0
        """), {"sid": store_id})
        row = res.fetchone()
        if row and row.today_rate is not None and row.avg_7d is not None:
            if row.avg_7d - row.today_rate > ANOMALY_RULES["CONVERSION_DROP"]["threshold"]:
                return [{
                    "anomaly_type": "CONVERSION_DROP",
                    "severity": ANOMALY_RULES["CONVERSION_DROP"]["severity"],
                    "description": f"Conversion rate today ({row.today_rate:.1%}) is significantly below 7-day avg ({row.avg_7d:.1%})",
                    "suggested_action": "Investigate checkout process for issues",
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                }]
        return []

    async def _check_dead_zones(self, store_id: str) -> list[dict]:
        res = await self.db.execute(text("""
            SELECT DISTINCT zone_id FROM events 
            WHERE store_id = :sid AND timestamp >= datetime('now', '-1 day') 
            AND zone_id IS NOT NULL
            AND zone_id NOT IN (
                SELECT DISTINCT zone_id FROM events 
                WHERE store_id = :sid AND event_type = 'ZONE_ENTER' 
                AND timestamp >= datetime('now', :win)
            )
        """), {"sid": store_id, "win": f"-{ANOMALY_RULES['DEAD_ZONE']['minutes']} minutes"})
        zones = [r.zone_id for r in res.fetchall()]
        ans = []
        for z in zones:
            ans.append({
                "anomaly_type": "DEAD_ZONE",
                "severity": ANOMALY_RULES["DEAD_ZONE"]["severity"],
                "description": f"Zone {z} has had no visitors in the last {ANOMALY_RULES['DEAD_ZONE']['minutes']} minutes",
                "suggested_action": f"Check if {z} is blocked or needs restaffing",
                "detected_at": datetime.utcnow().isoformat() + "Z"
            })
        return ans

    async def _check_stale_feed(self, store_id: str) -> list[dict]:
        res = await self.db.execute(text("""
            SELECT MAX(timestamp) FROM events WHERE store_id = :sid
        """), {"sid": store_id})
        last_ts_str = res.scalar()
        if last_ts_str:
            last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
            gap = (datetime.utcnow() - last_ts).total_seconds()
            if gap > ANOMALY_RULES["STALE_FEED"]["minutes"] * 60:
                return [{
                    "anomaly_type": "STALE_FEED",
                    "severity": ANOMALY_RULES["STALE_FEED"]["severity"],
                    "description": f"Latest event is {int(gap/60)} minutes old",
                    "suggested_action": "Check camera or edge pipeline connection",
                    "detected_at": datetime.utcnow().isoformat() + "Z"
                }]
        return []

    async def _get_claude_insight(self, anomaly: dict) -> str:
        prompt = f"Retail store anomaly detected: {anomaly}. Give a 1-2 sentence business insight and one specific recommended action."
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
