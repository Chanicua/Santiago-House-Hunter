#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$DIR/run_daily.sh" "$DIR/scraper.py" "$DIR/build_map.py" 2>/dev/null || true

CRON_LINE="CRON_TZ=America/Santiago
0 7 * * * $DIR/run_daily.sh"

if command -v crontab >/dev/null 2>&1; then
  (crontab -l 2>/dev/null | grep -v "run_daily.sh" | grep -v "CRON_TZ=America/Santiago" || true; echo "$CRON_LINE") | crontab -
  echo "Installed daily 7:00 AM America/Santiago cron job:"
  crontab -l | tail -n 3
else
  echo "crontab not found. On macOS you can use launchd, or run via GitHub Actions (.github/workflows/daily_search.yml)."
fi
