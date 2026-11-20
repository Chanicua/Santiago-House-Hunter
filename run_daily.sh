#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

STAMP="$(date -u +%Y-%m-%d_%H-%M-%S)"
LOG_FILE="$LOG_DIR/daily_${STAMP}.log"

echo "=== Santiago House Hunter Run: $STAMP UTC ===" | tee -a "$LOG_FILE"
python3 "$DIR/scraper.py" 2>&1 | tee -a "$LOG_FILE"
python3 "$DIR/build_map.py" 2>&1 | tee -a "$LOG_FILE"
echo "=== Completed ===" | tee -a "$LOG_FILE"
