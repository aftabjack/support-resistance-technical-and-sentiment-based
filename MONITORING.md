# Monitoring & Reliability Guide

This guide explains how to prevent the "stale data" issue and keep your dashboard running reliably.

## The Problem

**Symptom:** Dashboard shows outdated prices (hours or days old)

**Root Cause:** Data collection process crashed but left a "stale PID file" that prevented automatic restart

## 4-Layer Protection Strategy

### Layer 1: Health Check Script ✅

**What it does:**
- Validates processes are actually running (not just PID files)
- Checks data freshness (warns if > 30 minutes old)
- Auto-restarts crashed processes
- Detects PID reuse (when OS recycles old PID numbers)

**Setup:**
```bash
# Test manually
./scripts/healthcheck.sh

# Expected output:
# [2025-10-19 19:30:00] OK: bybit_kline_stream.py (PID: 91378) is running
# [2025-10-19 19:30:00] OK: Data for 15.BTCUSDT is fresh (age: 245s)
# [2025-10-19 19:30:00] ========== Health Check PASSED ==========
```

**Features:**
- ✅ Validates PID + process name (prevents PID reuse issues)
- ✅ Checks data age for all symbols
- ✅ Auto-restart on failure
- ✅ Email alerts (optional - set `ALERT_EMAIL` env var)

---

### Layer 2: Enhanced Health API 🔍

**What it does:**
- HTTP endpoint that monitors data freshness
- Can be monitored by external services (UptimeRobot, Pingdom, etc.)

**Endpoint:** `GET /health`

**Responses:**
```json
// Healthy
{
  "status": "healthy",
  "redis": "connected",
  "data_age_seconds": 156,
  "timestamp": "2025-10-19T19:30:00"
}

// Degraded (warnings)
{
  "status": "degraded",
  "redis": "connected",
  "data_age_seconds": 2500,
  "warnings": ["Kline data is stale (2500s old)"],
  "timestamp": "2025-10-19T19:30:00"
}

// Unhealthy
{
  "status": "unhealthy",
  "redis": "disconnected",
  "error": "Connection refused"
}
```

**Monitor with curl:**
```bash
# Check every minute
watch -n 60 'curl -s http://localhost:8080/health | jq .'
```

---

### Layer 3: Automated Monitoring (Cron) ⏰

**What it does:**
- Runs health check every 5 minutes automatically
- Logs results to `logs/healthcheck.log`
- Auto-restarts crashed processes

**Setup:**
```bash
# One-time setup
./scripts/setup_cron.sh

# View cron jobs
crontab -l

# View health check logs
tail -f logs/healthcheck.log
```

**Cron schedule:** `*/5 * * * *` (every 5 minutes)

**What it monitors:**
- Process health (kline stream, options tracker, webapp)
- Data freshness (< 30 minutes for kline data)
- Auto-restart on failure

---

### Layer 4: Systemd Service (Production) 🚀

**What it does:**
- Automatically starts services on boot
- Auto-restart on crash
- Proper logging to journald
- Dependencies on Redis

**Setup (Linux only):**
```bash
# 1. Copy service file
sudo cp scripts/sr-dashboard.service /etc/systemd/system/

# 2. Edit paths (change username and paths)
sudo nano /etc/systemd/system/sr-dashboard.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable auto-start on boot
sudo systemctl enable sr-dashboard

# 5. Start service
sudo systemctl start sr-dashboard

# 6. Check status
sudo systemctl status sr-dashboard

# 7. View logs
sudo journalctl -u sr-dashboard -f
```

**Benefits:**
- ✅ Auto-start on server reboot
- ✅ Auto-restart on crash (10 retries with 10s delay)
- ✅ Proper process supervision
- ✅ Centralized logging

---

## Quick Fix for Stale Data

If you notice stale data, run these commands:

```bash
# 1. Check what's wrong
./scripts/healthcheck.sh

# 2. Manual restart
./scripts/stop_system.sh
./scripts/start_system.sh

# 3. Verify data is fresh
curl http://localhost:8080/health | jq .
```

---

## Recommended Setup

**For Development:**
```bash
# Manual monitoring
watch -n 60 'curl -s http://localhost:8080/health | jq .'
```

**For Production:**
```bash
# Setup automated monitoring
./scripts/setup_cron.sh

# Optional: Setup systemd (Linux)
sudo cp scripts/sr-dashboard.service /etc/systemd/system/
# (edit paths, then enable)

# Optional: Setup external monitoring
# Use UptimeRobot, Pingdom, or similar to monitor:
#   http://your-server:8080/health
```

---

## Monitoring Checklist

- [ ] Health check script runs every 5 minutes (`setup_cron.sh`)
- [ ] `/health` endpoint monitored externally (optional)
- [ ] Email alerts configured (`ALERT_EMAIL` env var)
- [ ] Systemd service installed (Linux production)
- [ ] Logs rotated (`logrotate` configured)

---

## Troubleshooting

### "Already running" but process doesn't exist

**Cause:** Stale PID file

**Fix:**
```bash
rm -f logs/*.pid
./scripts/start_system.sh
```

### Data is 30+ minutes old

**Check:**
```bash
# Is kline stream running?
ps aux | grep bybit_kline_stream

# Check logs
tail -50 logs/kline_stream.log

# Check Redis data
redis-cli zrevrange "15.BTCUSDT" 0 0 WITHSCORES
```

**Fix:**
```bash
./scripts/healthcheck.sh  # Auto-restart
```

### Process keeps crashing

**Check logs:**
```bash
tail -100 logs/kline_stream.log
tail -100 logs/options_tracker.log
```

**Common causes:**
- Network issues (can't reach Bybit API)
- Redis disconnected
- API rate limits
- Invalid API keys (if using authenticated endpoints)

---

## Alert Integrations

### Email Alerts

```bash
# Set email for alerts
export ALERT_EMAIL="your@email.com"

# Test
./scripts/healthcheck.sh
```

### Slack/Discord Webhook

Add to `healthcheck.sh`:
```bash
# After line "if [ $errors -gt 0 ]; then"
WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"SR Dashboard: $errors errors detected\"}" \
  "$WEBHOOK_URL"
```

### External Monitoring (UptimeRobot, Pingdom)

1. Monitor: `http://your-server:8080/health`
2. Alert when status ≠ 200 or response doesn't contain `"status": "healthy"`
3. Check interval: 5 minutes

---

## Data Freshness SLA

| Data Type | Max Age | Action |
|-----------|---------|--------|
| Kline data | 30 min | Auto-restart stream |
| S/R data | 10 min | Regenerate S/R |
| Options data | 5 min | Check options tracker |

---

## Log Rotation

Create `/etc/logrotate.d/sr-dashboard`:
```
/Users/danish/PycharmProjects/options_trading/live_sr_dashboard/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 danish danish
}
```

---

## Summary

**Minimum viable monitoring:**
```bash
./scripts/setup_cron.sh  # 5-minute health checks
```

**Production-grade monitoring:**
```bash
./scripts/setup_cron.sh           # Local health checks
sudo systemctl enable sr-dashboard # Auto-restart
# + External monitoring service
# + Slack/email alerts
```

This ensures your dashboard stays online and data stays fresh! 🚀
