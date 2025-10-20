# Cron Job Setup - Daily Options Refresh

**Automatically refresh options data daily at 8 AM UTC** 🕐

---

## Why This Is Needed

Bybit adds new options contracts daily (usually by 8 AM UTC). To track these new options:
- Options tracker must be restarted to fetch fresh symbol list from API
- This ensures your system tracks all active options contracts
- Prevents missing data from newly added options

---

## Setup Instructions

### Step 1: Open Crontab

```bash
crontab -e
```

### Step 2: Add Cron Job

Add this line to run daily at 8 AM UTC:

```cron
0 8 * * * /Users/danish/PycharmProjects/options_trading/sr_detection_system/scripts/refresh_options.sh >> /Users/danish/PycharmProjects/options_trading/sr_detection_system/logs/cron_refresh.log 2>&1
```

**What this does:**
- `0 8 * * *` - Run at 8:00 AM UTC every day
- Executes `refresh_options.sh` script
- Logs output to `logs/cron_refresh.log`

### Step 3: Verify Cron Job

```bash
# List active cron jobs
crontab -l

# Should show the refresh_options.sh line
```

### Step 4: Test Manually

```bash
# Test the script manually first
./scripts/refresh_options.sh

# Check if it worked
tail -20 logs/options_tracker.log
```

---

## Alternative Time Zones

If you want to run at a different time:

### 8 AM EST (1 PM UTC)
```cron
0 13 * * * /Users/danish/PycharmProjects/options_trading/sr_detection_system/scripts/refresh_options.sh >> /Users/danish/PycharmProjects/options_trading/sr_detection_system/logs/cron_refresh.log 2>&1
```

### 8 AM PST (4 PM UTC)
```cron
0 16 * * * /Users/danish/PycharmProjects/options_trading/sr_detection_system/scripts/refresh_options.sh >> /Users/danish/PycharmProjects/options_trading/sr_detection_system/logs/cron_refresh.log 2>&1
```

### Every 12 Hours
```cron
0 8,20 * * * /Users/danish/PycharmProjects/options_trading/sr_detection_system/scripts/refresh_options.sh >> /Users/danish/PycharmProjects/options_trading/sr_detection_system/logs/cron_refresh.log 2>&1
```

---

## What Happens During Refresh

The `refresh_options.sh` script:

1. ✅ **Stops** existing options tracker gracefully
2. ✅ **Cleans up** PID files
3. ✅ **Starts** options tracker (fetches fresh options from Bybit API)
4. ✅ **Verifies** new process is running
5. ✅ **Logs** everything to `logs/cron_refresh.log`

**No data loss**: Redis data persists, only the tracker process restarts.

---

## Monitoring

### Docker (Built-in Scheduler)

```bash
# View scheduler logs (real-time)
docker-compose logs -f options-scheduler

# View scheduler status
docker-compose ps options-scheduler

# Check when next refresh will happen
docker-compose logs options-scheduler | grep "Next refresh"

# View options tracker logs after refresh
docker-compose logs -f options-tracker
```

### Local (Host-Based Cron)

```bash
# View Cron Logs
tail -f logs/cron_refresh.log

# View Options Tracker Logs
tail -f logs/options_tracker.log

# Check Latest Refresh Time
grep "Options Tracker Refresh" logs/cron_refresh.log | tail -1
```

### Verify Options Count (Both Docker & Local)

```bash
# Check how many options are being tracked
redis-cli KEYS "option:*" | wc -l

# Should increase after new options are added
```

---

## Docker Setup

### ✅ Automatic (Recommended)

**Good news!** If you're using Docker, the scheduler is **already built-in** and runs automatically.

The `docker-compose.yml` includes an `options-scheduler` service that:
- ✅ Runs automatically when you start with `docker-compose up -d`
- ✅ Checks time every 5 minutes
- ✅ Restarts options-tracker at 8 AM UTC daily
- ✅ Logs to container output (view with `docker-compose logs options-scheduler`)

**No manual setup needed!** Just start with Docker Compose and it works.

### Manual (If Host-Based Cron Needed)

If you prefer host-based cron instead of the built-in scheduler:

#### Create `scripts/refresh_options_docker.sh`:

```bash
#!/bin/bash
cd /Users/danish/PycharmProjects/options_trading/sr_detection_system
docker-compose restart options-tracker
echo "✓ Docker options tracker restarted at $(date)"
```

#### Cron Job for Docker:

```cron
0 8 * * * /Users/danish/PycharmProjects/options_trading/sr_detection_system/scripts/refresh_options_docker.sh >> /Users/danish/PycharmProjects/options_trading/sr_detection_system/logs/cron_refresh.log 2>&1
```

**Note**: If using the built-in scheduler (recommended), you don't need this.

---

## Troubleshooting

### Cron Job Not Running

```bash
# Check if cron service is running
# macOS
launchctl list | grep cron

# Linux
systemctl status cron
```

### Permission Denied

```bash
# Make sure script is executable
chmod +x scripts/refresh_options.sh

# Check script path is absolute
ls -la scripts/refresh_options.sh
```

### Script Runs but Options Not Updating

```bash
# Check if Bybit API is accessible
python -c "import requests; r=requests.get('https://api.bybit.com/v5/market/instruments-info?category=option&baseCoin=BTC'); print(r.status_code, len(r.json()['result']['list']))"

# Should print: 200 <number_of_options>
```

### No Cron Logs

```bash
# Check cron log path exists
mkdir -p logs
touch logs/cron_refresh.log

# Test cron job manually
./scripts/refresh_options.sh
```

---

## Removing Cron Job

If you want to remove the automatic refresh:

```bash
# Edit crontab
crontab -e

# Delete the refresh_options.sh line
# Save and exit
```

---

## Best Practices

1. **Run at 8:05 AM UTC** (5 minutes after options update) to ensure new contracts are available
   ```cron
   5 8 * * * /path/to/refresh_options.sh >> /path/to/cron_refresh.log 2>&1
   ```

2. **Monitor the logs** regularly to ensure refreshes are successful

3. **Keep Redis running** - The refresh only restarts the options tracker, not Redis

4. **Test monthly** - Manually run the refresh script to ensure it works

---

## Summary

✅ **Created**: `scripts/refresh_options.sh`
✅ **Cron Job**: Daily at 8 AM UTC
✅ **Purpose**: Fetch fresh options data from Bybit
✅ **Logs**: `logs/cron_refresh.log`

**Next Step**: Add the cron job to your crontab:
```bash
crontab -e
# Add the line from Step 2 above
```

---

## Questions?

- Check `README.md` for full documentation
- View `DEPLOYMENT_GUIDE.md` for deployment help
- Open an issue on GitHub

---

**Happy trading!** 📈
