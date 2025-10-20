#!/bin/bash

# Refresh Options Tracker - Daily at 8 AM UTC
# Stops and restarts options tracker to fetch fresh options data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/logs/options_tracker.pid"
LOG_FILE="$PROJECT_ROOT/logs/options_tracker.log"

echo "=================================================="
echo "Options Tracker Refresh - $(date)"
echo "=================================================="

# Check if options tracker is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⏹  Stopping existing options tracker (PID: $PID)..."
        kill $PID
        sleep 2

        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠  Force killing options tracker..."
            kill -9 $PID
        fi

        rm -f "$PID_FILE"
        echo "✓ Options tracker stopped"
    else
        echo "⚠  PID file exists but process not running, cleaning up..."
        rm -f "$PID_FILE"
    fi
else
    echo "ℹ  Options tracker not running"
fi

# Start options tracker
echo "🚀 Starting options tracker with fresh options data..."
cd "$PROJECT_ROOT"
nohup python src/bybit_options_tracker.py > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$PID_FILE"

# Verify it started
sleep 3
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✓ Options tracker started successfully (PID: $NEW_PID)"
    echo "✓ Fresh options data will be fetched from Bybit API"
    echo "📊 Log: $LOG_FILE"
else
    echo "❌ Failed to start options tracker"
    rm -f "$PID_FILE"
    exit 1
fi

echo "=================================================="
echo "✓ Options refresh complete"
echo "=================================================="
