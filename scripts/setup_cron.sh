#!/bin/bash
# Setup cron job for health monitoring
# Run this once: ./scripts/setup_cron.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HEALTHCHECK="$SCRIPT_DIR/healthcheck.sh"

# Make healthcheck executable
chmod +x "$HEALTHCHECK"

# Add to crontab (run every 5 minutes)
CRON_JOB="*/5 * * * * cd $PROJECT_DIR && $HEALTHCHECK >> logs/healthcheck.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -F "$HEALTHCHECK" > /dev/null; then
    echo "✓ Cron job already exists"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✓ Cron job added: Health check every 5 minutes"
    echo "  Log file: $PROJECT_DIR/logs/healthcheck.log"
fi

echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e  # then delete the line with 'healthcheck.sh'"
echo ""
echo "To test health check manually:"
echo "  $HEALTHCHECK"
