#!/bin/bash

# Start All Services Script
# S/R Detection System

echo "🚀 Starting S/R Detection System..."
echo ""

# Check if Redis is running
echo "📊 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started successfully"
    else
        echo "❌ Failed to start Redis. Please start it manually."
        exit 1
    fi
fi
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"
echo ""

# Check if logs directory exists
if [ ! -d "logs" ]; then
    mkdir logs
    echo "✅ Created logs directory"
fi

# Start Kline Stream
echo "📈 Starting Kline Stream..."
nohup python src/bybit_kline_stream_ultra.py > logs/kline_stream.log 2>&1 &
KLINE_PID=$!
echo "✅ Kline stream started (PID: $KLINE_PID)"
echo $KLINE_PID > logs/kline_stream.pid
echo ""

# Wait a bit for kline stream to initialize
sleep 3

# Start Options Tracker
echo "📊 Starting Options Tracker..."
nohup python src/bybit_options_tracker.py > logs/options_tracker.log 2>&1 &
OPTIONS_PID=$!
echo "✅ Options tracker started (PID: $OPTIONS_PID)"
echo $OPTIONS_PID > logs/options_tracker.pid
echo ""

# Wait for data collection to start
echo "⏳ Waiting for data collection to start (15 seconds)..."
sleep 15

# Generate initial S/R data
echo "🎯 Generating initial S/R data..."
python src/sr_core/sr_detector_technical.py --all --mode basic --save
echo ""

echo "✅ All services started successfully!"
echo ""
echo "📋 Service Status:"
echo "  - Redis: Running"
echo "  - Kline Stream: PID $KLINE_PID (logs/kline_stream.log)"
echo "  - Options Tracker: PID $OPTIONS_PID (logs/options_tracker.log)"
echo ""
echo "📊 Check data:"
echo "  redis-cli KEYS \"*BTCUSDT\" | wc -l"
echo "  redis-cli KEYS \"sr:technical:basic:*\" | wc -l"
echo ""
echo "📝 View logs:"
echo "  tail -f logs/kline_stream.log"
echo "  tail -f logs/options_tracker.log"
echo ""
echo "🛑 Stop all services:"
echo "  ./scripts/stop_all.sh"
echo ""
