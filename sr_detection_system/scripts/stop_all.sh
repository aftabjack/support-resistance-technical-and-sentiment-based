#!/bin/bash

# Stop All Services Script
# S/R Detection System

echo "🛑 Stopping S/R Detection System..."
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Stop Kline Stream
if [ -f "logs/kline_stream.pid" ]; then
    KLINE_PID=$(cat logs/kline_stream.pid)
    echo "🛑 Stopping Kline Stream (PID: $KLINE_PID)..."

    if kill $KLINE_PID > /dev/null 2>&1; then
        echo "✅ Kline stream stopped"
    else
        echo "⚠️  Kline stream process not found (may have already stopped)"
    fi

    rm logs/kline_stream.pid
else
    echo "⚠️  Kline stream PID file not found"
fi
echo ""

# Stop Options Tracker
if [ -f "logs/options_tracker.pid" ]; then
    OPTIONS_PID=$(cat logs/options_tracker.pid)
    echo "🛑 Stopping Options Tracker (PID: $OPTIONS_PID)..."

    if kill $OPTIONS_PID > /dev/null 2>&1; then
        echo "✅ Options tracker stopped"
    else
        echo "⚠️  Options tracker process not found (may have already stopped)"
    fi

    rm logs/options_tracker.pid
else
    echo "⚠️  Options tracker PID file not found"
fi
echo ""

# Alternative: Kill by process name (if PID files don't exist)
echo "🔍 Checking for any remaining processes..."

KLINE_PROCS=$(ps aux | grep "bybit_kline_stream_ultra.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$KLINE_PROCS" ]; then
    echo "🛑 Found kline stream processes: $KLINE_PROCS"
    kill $KLINE_PROCS
    echo "✅ Stopped kline stream processes"
fi

OPTIONS_PROCS=$(ps aux | grep "bybit_options_tracker.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$OPTIONS_PROCS" ]; then
    echo "🛑 Found options tracker processes: $OPTIONS_PROCS"
    kill $OPTIONS_PROCS
    echo "✅ Stopped options tracker processes"
fi

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "💡 To restart:"
echo "  ./scripts/start_all.sh"
echo ""
echo "💡 To stop Redis:"
echo "  redis-cli shutdown"
echo ""
