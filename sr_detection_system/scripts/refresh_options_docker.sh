#!/bin/bash

# Refresh Options Tracker (Docker) - Daily at 8 AM UTC
# Restarts Docker container to fetch fresh options data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=================================================="
echo "Docker Options Tracker Refresh - $(date)"
echo "=================================================="

cd "$PROJECT_ROOT"

# Restart options tracker container
echo "🔄 Restarting options-tracker container..."
docker-compose restart options-tracker

if [ $? -eq 0 ]; then
    echo "✓ Options tracker container restarted successfully"
    echo "✓ Fresh options data will be fetched from Bybit API"

    # Wait a bit and check status
    sleep 5
    echo ""
    echo "📊 Container status:"
    docker-compose ps options-tracker

    echo ""
    echo "📝 Recent logs:"
    docker-compose logs --tail=10 options-tracker
else
    echo "❌ Failed to restart options tracker container"
    exit 1
fi

echo "=================================================="
echo "✓ Docker options refresh complete"
echo "=================================================="
