#!/usr/bin/env bash
# PROMPT: Smoke test all API endpoints after deployment
# CHANGES MADE: Created smoke_api.sh covering ingest, metrics, funnel, heatmap, anomalies, health

set -euo pipefail
BASE="${API_BASE_URL:-http://localhost:8000}"
STORE="${STORE_ID:-ST1008}"
PASS=0; FAIL=0

check() {
    local name="$1"; local url="$2"; local expected="$3"
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$code" = "$expected" ]; then
        echo "  PASS  $name ($code)"; ((PASS++))
    else
        echo "  FAIL  $name (got $code, expected $expected)"; ((FAIL++))
    fi
}

echo "=== Vexora Smoke Test ==="
check "health"    "$BASE/health"                              200
check "metrics"   "$BASE/stores/$STORE/metrics"               200
check "funnel"    "$BASE/stores/$STORE/funnel"                200
check "heatmap"   "$BASE/stores/$STORE/heatmap"               200
check "anomalies" "$BASE/stores/$STORE/anomalies"             200

# Alias resolution
check "alias STORE_BLR_002" "$BASE/stores/STORE_BLR_002/metrics" 200
check "alias Brigade_Bangalore" "$BASE/stores/Brigade_Bangalore/metrics" 200

# Ingest a minimal test event
RESP=$(curl -s -X POST "$BASE/events/ingest" \
  -H "Content-Type: application/json" \
  -d '{"events":[{"event_id":"smoke-001","store_id":"ST1008","visitor_id":"V_SMOKE","event_type":"ENTRY","timestamp":"2026-01-01T10:00:00Z","camera_id":"CAM3","confidence":0.9,"metadata":{"queue_depth":0,"sku_zone":"","session_seq":1}}]}')
echo "$RESP" | grep -q '"accepted":1' && { echo "  PASS  ingest"; ((PASS++)); } || { echo "  FAIL  ingest: $RESP"; ((FAIL++)); }

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
