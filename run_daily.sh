#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"

STAMP="$(date -u +%Y-%m-%d_%H-%M-%S)"
LOG_FILE="$LOG_DIR/daily_${STAMP}.log"

echo "=== Santiago House Hunter Local Run: $STAMP UTC ===" | tee -a "$LOG_FILE"

if [ "${NO_PUSH:-0}" != "1" ] && git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$DIR" pull --rebase origin main 2>&1 | tee -a "$LOG_FILE" || true
fi

if [ "${NO_BROWSER:-0}" = "1" ]; then
  python3 "$DIR/scraper.py" 2>&1 | tee -a "$LOG_FILE"
else
  python3 "$DIR/scraper.py" --browser 2>&1 | tee -a "$LOG_FILE"
fi

python3 "$DIR/build_map.py" 2>&1 | tee -a "$LOG_FILE"

if [ "${NO_PUSH:-0}" != "1" ] && git -C "$DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$DIR" add data/listings.json data/history.json data/geocode_cache.json output/map.html
  if ! git -C "$DIR" diff --staged --quiet; then
    git -C "$DIR" commit -m "chore: local house update $(date +%Y-%m-%d)" 2>&1 | tee -a "$LOG_FILE"
    git -C "$DIR" push origin main 2>&1 | tee -a "$LOG_FILE"
  else
    echo "[INFO] No listing changes to push." | tee -a "$LOG_FILE"
  fi
fi

echo "=== Completed ===" | tee -a "$LOG_FILE"
