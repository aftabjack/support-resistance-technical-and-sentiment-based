#!/bin/bash
# Health Check Script - Monitors data freshness and process health
# Run this via cron every 5 minutes: */5 * * * * /path/to/healthcheck.sh

REDIS_HOST="localhost"
REDIS_PORT="6379"
MAX_AGE_SECONDS=1800  # 30 minutes
ALERT_EMAIL="${ALERT_EMAIL:-}"  # Set via environment variable

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if process is running
check_process() {
    local pid_file=$1
    local process_name=$2

    if [ ! -f "$pid_file" ]; then
        log "WARNING: PID file $pid_file not found"
        return 1
    fi

    local pid=$(cat "$pid_file")

    # Check if PID exists
    if ! ps -p "$pid" > /dev/null 2>&1; then
        log "ERROR: Process $process_name (PID: $pid) is not running"
        rm -f "$pid_file"
        return 1
    fi

    # Verify it's actually our process (check command name)
    if ! ps -p "$pid" -o command= | grep -q "$process_name"; then
        log "ERROR: PID $pid exists but is not $process_name (PID reuse detected)"
        rm -f "$pid_file"
        return 1
    fi

    log "OK: $process_name (PID: $pid) is running"
    return 0
}

# Check data freshness
check_data_freshness() {
    local key=$1
    local symbol=$2

    # Get latest candle timestamp
    local data=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" zrevrange "$key" 0 0 WITHSCORES 2>/dev/null | tail -1)

    if [ -z "$data" ]; then
        log "WARNING: No data found for $key"
        return 1
    fi

    # Convert from milliseconds to seconds
    local last_update=$((data / 1000))
    local now=$(date +%s)
    local age=$((now - last_update))

    if [ $age -gt $MAX_AGE_SECONDS ]; then
        log "ERROR: Data for $key is stale (age: ${age}s, max: ${MAX_AGE_SECONDS}s)"
        log "  Last update: $(date -r $last_update)"
        return 1
    fi

    log "OK: Data for $key is fresh (age: ${age}s)"
    return 0
}

# Auto-restart function
restart_service() {
    local service=$1
    log "Attempting to restart $service..."

    cd "$(dirname "$0")/.." || exit 1

    if [ "$service" = "kline" ]; then
        ./scripts/start_system.sh 2>&1 | grep -E "(kline|error)" | head -5
    fi
}

# Main health check
main() {
    log "========== Health Check Started =========="

    local errors=0

    # Check kline stream process
    if ! check_process "logs/kline_stream.pid" "bybit_kline_stream.py"; then
        errors=$((errors + 1))
        restart_service "kline"
    fi

    # Check options tracker process
    if ! check_process "logs/options_tracker.pid" "bybit_options_tracker.py"; then
        errors=$((errors + 1))
    fi

    # Check webapp process
    if ! check_process "logs/webapp.pid" "app.py"; then
        errors=$((errors + 1))
    fi

    # Check data freshness for key symbols
    for symbol in BTCUSDT ETHUSDT SOLUSDT; do
        if ! check_data_freshness "15.$symbol" "$symbol"; then
            errors=$((errors + 1))
        fi
    done

    # Alert if errors found
    if [ $errors -gt 0 ]; then
        log "========== Health Check FAILED ($errors errors) =========="

        # Send alert email if configured
        if [ -n "$ALERT_EMAIL" ]; then
            echo "Health check failed with $errors errors. Check logs for details." | \
                mail -s "SR Dashboard Health Check Failed" "$ALERT_EMAIL"
        fi

        exit 1
    else
        log "========== Health Check PASSED =========="
        exit 0
    fi
}

main "$@"
