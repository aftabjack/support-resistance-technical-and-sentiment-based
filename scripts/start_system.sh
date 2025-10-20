#!/bin/bash

# Live S/R Dashboard - System Startup Script
# Starts all required services for the dashboard

set -e

echo "=========================================="
echo "🚀 Starting Live S/R Dashboard"
echo "=========================================="
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Check Redis
echo "📊 Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis started"
    else
        echo "❌ Failed to start Redis. Please start manually."
        exit 1
    fi
fi
echo ""

# Create logs directory
mkdir -p logs

# Start Kline Stream
echo "📈 Starting Kline Stream..."
nohup python src/data_collection/bybit_kline_stream.py > logs/kline_stream.log 2>&1 &
KLINE_PID=$!
echo $KLINE_PID > logs/kline_stream.pid
echo "✅ Kline stream started (PID: $KLINE_PID)"
echo ""

# Start Options Tracker
echo "📊 Starting Options Tracker..."
nohup python src/data_collection/bybit_options_tracker.py > logs/options_tracker.log 2>&1 &
OPTIONS_PID=$!
echo $OPTIONS_PID > logs/options_tracker.pid
echo "✅ Options tracker started (PID: $OPTIONS_PID)"
echo ""

# Wait for data collection
echo "⏳ Waiting 15 seconds for data collection..."
sleep 15

# Generate S/R data
echo "🎯 Generating S/R data..."
python src/sr_detectors/sr_detector_technical.py --all --mode basic --save > /dev/null 2>&1 &
python src/sr_detectors/sr_detector_sentiment.py --all --mode basic > /dev/null 2>&1 &
wait
echo "✅ S/R data generated"
echo ""

# Start Web App
echo "🌐 Starting Web Dashboard..."
nohup python src/webapp/app.py > logs/webapp.log 2>&1 &
WEBAPP_PID=$!
echo $WEBAPP_PID > logs/webapp.pid
echo "✅ Web dashboard started (PID: $WEBAPP_PID)"
echo ""

echo "=========================================="
echo "✅ System Started Successfully!"
echo "=========================================="
echo ""
echo "📊 Dashboard: http://localhost:8080/live"
echo ""
echo "📝 Services:"
echo "  - Kline Stream: PID $KLINE_PID"
echo "  - Options Tracker: PID $OPTIONS_PID"
echo "  - Web Dashboard: PID $WEBAPP_PID"
echo ""
echo "📋 Logs:"
echo "  tail -f logs/kline_stream.log"
echo "  tail -f logs/options_tracker.log"
echo "  tail -f logs/webapp.log"
echo ""
echo "🛑 Stop: ./scripts/stop_system.sh"
echo ""
