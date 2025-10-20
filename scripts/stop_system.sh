#!/bin/bash

# Live S/R Dashboard - System Stop Script
# Stops all running services

set -e

echo "=========================================="
echo "🛑 Stopping Live S/R Dashboard"
echo "=========================================="
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Stop Web App
if [ -f logs/webapp.pid ]; then
    PID=$(cat logs/webapp.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "🌐 Stopping Web Dashboard (PID: $PID)..."
        kill $PID
        rm logs/webapp.pid
        echo "✅ Web dashboard stopped"
    fi
fi

# Stop Options Tracker
if [ -f logs/options_tracker.pid ]; then
    PID=$(cat logs/options_tracker.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "📊 Stopping Options Tracker (PID: $PID)..."
        kill $PID
        rm logs/options_tracker.pid
        echo "✅ Options tracker stopped"
    fi
fi

# Stop Kline Stream
if [ -f logs/kline_stream.pid ]; then
    PID=$(cat logs/kline_stream.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "📈 Stopping Kline Stream (PID: $PID)..."
        kill $PID
        rm logs/kline_stream.pid
        echo "✅ Kline stream stopped"
    fi
fi

echo ""
echo "✅ All services stopped"
echo ""
