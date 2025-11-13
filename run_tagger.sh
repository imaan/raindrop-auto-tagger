#!/bin/bash

# Raindrop Auto-Tagger Wrapper Script
# This script sets up environment variables and runs the auto-tagger
# Perfect for cron jobs or scheduled tasks

# ============================================================================
# CONFIGURATION - Replace these with your actual tokens
# ============================================================================

export RAINDROP_TOKEN='your_raindrop_token_here'
export CLAUDE_API_KEY='your_claude_api_key_here'

# ============================================================================
# SCRIPT SETTINGS
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Log directory (creates if doesn't exist)
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"

# Date for log naming
DATE=$(date +%Y%m%d_%H%M%S)

# ============================================================================
# EXECUTION
# ============================================================================

echo "========================================================================"
echo "Starting Raindrop Auto-Tagger at $(date)"
echo "========================================================================"
echo ""

# Navigate to script directory
cd "$SCRIPT_DIR"

# Run the Python script and capture output
python3 raindrop_auto_tagger.py 2>&1 | tee "${LOG_DIR}/cron_run_${DATE}.log"

EXIT_CODE=$?

echo ""
echo "========================================================================"
echo "Finished at $(date)"
echo "Exit code: $EXIT_CODE"
echo "Log saved to: ${LOG_DIR}/cron_run_${DATE}.log"
echo "========================================================================"

# Optional: Send desktop notification (macOS)
# Uncomment if you want notifications
# if command -v osascript &> /dev/null; then
#     if [ $EXIT_CODE -eq 0 ]; then
#         osascript -e 'display notification "Successfully tagged bookmarks!" with title "Raindrop Auto-Tagger"'
#     else
#         osascript -e 'display notification "Error occurred. Check logs." with title "Raindrop Auto-Tagger"'
#     fi
# fi

# Optional: Send desktop notification (Linux)
# Uncomment if you want notifications
# if command -v notify-send &> /dev/null; then
#     if [ $EXIT_CODE -eq 0 ]; then
#         notify-send "Raindrop Auto-Tagger" "Successfully tagged bookmarks!"
#     else
#         notify-send "Raindrop Auto-Tagger" "Error occurred. Check logs." --urgency=critical
#     fi
# fi

exit $EXIT_CODE
