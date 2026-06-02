#!/usr/bin/env bash
set -euo pipefail

CLIPS_DIR=${1:?"Usage: $0 <clips_dir>"}
STORE_ID=${2:-"ST1008"}
API_URL=${API_URL:-"http://localhost:8000"}

echo "[$(date -u +%FT%TZ)] Starting pipeline for $STORE_ID"
echo "[$(date -u +%FT%TZ)] Clips dir: $CLIPS_DIR"

python pipeline/detect.py \
  --clips "$CLIPS_DIR" \
  --store "$STORE_ID" \
  --layout data/store_layout.json \
  --pos data/pos_transactions.csv \
  --output pipeline/output/

echo "[$(date -u +%FT%TZ)] Detection complete. Replaying events to API..."

python pipeline/replay.py \
  --events "pipeline/output/${STORE_ID}_events.jsonl" \
  --api "$API_URL" \
  --speed 10

echo "[$(date -u +%FT%TZ)] Done. Check dashboard at http://localhost:3000"
