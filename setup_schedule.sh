#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$DIR/run_daily.sh" "$DIR/scraper.py" "$DIR/build_map.py" 2>/dev/null || true

if [ "$(uname -s)" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/com.chanicua.santiago-house-hunter.plist"
  mkdir -p "$HOME/Library/LaunchAgents" "$DIR/logs"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.chanicua.santiago-house-hunter</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$DIR/run_daily.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>4</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$DIR/logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$DIR/logs/launchd.err.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "Installed macOS LaunchAgent for daily 4:00 AM run:"
  echo "  $PLIST"
elif command -v crontab >/dev/null 2>&1; then
  CRON_LINE="0 4 * * * DISPLAY=\${DISPLAY:-:0} $DIR/run_daily.sh"
  (crontab -l 2>/dev/null | grep -v "run_daily.sh" | grep -v "CRON_TZ=America/Santiago" || true; echo "$CRON_LINE") | crontab -
  echo "Installed daily 4:00 AM local cron job:"
  crontab -l | tail -n 2
else
  echo "Neither launchctl (macOS) nor crontab (Linux) was found. Schedule '$DIR/run_daily.sh' at 4:00 AM via your OS scheduler."
  exit 1
fi
