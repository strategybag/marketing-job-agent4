#!/bin/bash
PROJECT_PATH="$(cd "$(dirname "$0")" && pwd)"
PYTHON_PATH="$PROJECT_PATH/.venv/bin/python"
SCRIPT_PATH="$PROJECT_PATH/run_daily_scan.py"

CRON_LINE="0 8 * * * cd $PROJECT_PATH && $PYTHON_PATH $SCRIPT_PATH >> $PROJECT_PATH/data/scan.log 2>&1"

(crontab -l 2>/dev/null | grep -v "run_daily_scan.py"; echo "$CRON_LINE") | crontab -

echo "Installed daily scheduled scan at 8:00 AM."
