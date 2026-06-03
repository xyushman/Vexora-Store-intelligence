#!/usr/bin/env bash
set -euo pipefail

CLIPS_DIR=${1:?"Usage: $0 <clips_dir>"}
STORE_ID=${2:-"ST1008"}
API_URL=${API_URL:-"http://localhost:8000"}

echo "[$(date -u +%FT%TZ)] Starting pipeline for $STORE_ID"
echo "[$(date -u +%FT%TZ)] Clips dir: $CLIPS_DIR"

POS_FILE="data/pos_transactions.csv"
if [ ! -f "$POS_FILE" ]; then
    echo "Warning: $POS_FILE not found. Looking for alternatives..."
    ALT_POS=$(ls *Brigade*.csv 2>/dev/null | head -n 1 || true)
    if [ -n "$ALT_POS" ]; then
        POS_FILE="$ALT_POS"
        echo "Using alternative POS file: $POS_FILE"
    else
        echo "No POS file found, this might cause an error in detect.py"
    fi
fi

python pipeline/detect.py \
  --clips "$CLIPS_DIR" \
  --store "$STORE_ID" \
  --layout data/store_layout.json \
  --pos "$POS_FILE" \
  --output pipeline/output/

echo "[$(date -u +%FT%TZ)] Detection complete. Replaying events to API..."

python pipeline/replay_events.py \
  --events "pipeline/output/${STORE_ID}_events.jsonl" \
  --api-base-url "$API_URL" \
  --speed 10

echo "[$(date -u +%FT%TZ)] Done. Check dashboard at http://localhost:3000"
