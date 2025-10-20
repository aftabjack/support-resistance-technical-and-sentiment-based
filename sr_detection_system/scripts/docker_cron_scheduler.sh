#!/bin/sh

# Docker Cron Scheduler for Options Refresh
# Runs inside a Docker container and restarts options-tracker daily at 8 AM UTC

echo "=========================================="
echo "Docker Options Refresh Scheduler Started"
echo "Target time: 8:00 AM UTC daily"
echo "=========================================="

while true; do
    # Get current time in UTC
    CURRENT_HOUR=$(date -u +%H)
    CURRENT_MINUTE=$(date -u +%M)
    CURRENT_SECOND=$(date -u +%S)

    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] Scheduler running..."

    # Check if it's 8 AM UTC (hour 08, any minute in first 5 minutes)
    if [ "$CURRENT_HOUR" = "08" ] && [ "$CURRENT_MINUTE" -lt "05" ]; then
        echo "=========================================="
        echo "⏰ It's 8 AM UTC! Time to refresh options"
        echo "=========================================="

        echo "🔄 Restarting options-tracker container..."
        docker restart sr-options-tracker

        if [ $? -eq 0 ]; then
            echo "✓ Options tracker restarted successfully"
            echo "✓ Fresh options data will be fetched from Bybit API"
        else
            echo "❌ Failed to restart options tracker"
        fi

        echo "=========================================="
        echo "Next refresh: Tomorrow at 8:00 AM UTC"
        echo "=========================================="

        # Sleep for 1 hour to avoid multiple restarts in the same hour
        echo "Sleeping for 1 hour..."
        sleep 3600
    else
        # Calculate seconds until next 8 AM UTC
        CURRENT_SECONDS=$((10#$CURRENT_HOUR * 3600 + 10#$CURRENT_MINUTE * 60 + 10#$CURRENT_SECOND))
        TARGET_SECONDS=$((8 * 3600))  # 8 AM = 28800 seconds

        if [ $CURRENT_SECONDS -lt $TARGET_SECONDS ]; then
            # 8 AM is today
            SECONDS_UNTIL=$((TARGET_SECONDS - CURRENT_SECONDS))
        else
            # 8 AM is tomorrow
            SECONDS_UNTIL=$((86400 - CURRENT_SECONDS + TARGET_SECONDS))
        fi

        HOURS_UNTIL=$((SECONDS_UNTIL / 3600))
        MINUTES_UNTIL=$(((SECONDS_UNTIL % 3600) / 60))

        echo "Next refresh in: ${HOURS_UNTIL}h ${MINUTES_UNTIL}m"

        # Sleep for 5 minutes, then check again
        sleep 300
    fi
done
