#!/bin/bash

# Raindrop Auto-Tagger Daily Runner
# This script runs the Raindrop auto-tagger with embedded credentials

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/daily_logs"
PYTHON_PATH="/usr/bin/python3"  # Adjust if needed

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Set timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/daily_run_$TIMESTAMP.log"

echo "========================================" >> "$LOG_FILE"
echo "Starting Raindrop Auto-Tagger" >> "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Change to script directory
cd "$SCRIPT_DIR"

# Export credentials (set these as environment variables)
# NEVER commit actual credentials to version control!
export RAINDROP_TOKEN="${RAINDROP_TOKEN:-your_raindrop_token_here}"
export CLAUDE_API_KEY="${CLAUDE_API_KEY:-your_claude_api_key_here}"

# Check if credentials are set
if [ "$RAINDROP_TOKEN" = "your_raindrop_token_here" ] || [ "$CLAUDE_API_KEY" = "your_claude_api_key_here" ]; then
    echo "Error: API credentials not set!" >> "$LOG_FILE"
    echo "Please set RAINDROP_TOKEN and CLAUDE_API_KEY environment variables" >> "$LOG_FILE"
    exit 1
fi

# Run the Python script and capture output
$PYTHON_PATH raindrop_auto_tagger.py >> "$LOG_FILE" 2>&1

# Check exit status
if [ $? -eq 0 ]; then
    echo "Script completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "Script failed with error at $(date)" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"

# Optional: Keep only last 30 days of logs
find "$LOG_DIR" -name "daily_run_*.log" -mtime +30 -delete

# Optional: Send notification (uncomment if you want macOS notifications)
# osascript -e 'display notification "Raindrop auto-tagging completed" with title "Raindrop Tagger"'