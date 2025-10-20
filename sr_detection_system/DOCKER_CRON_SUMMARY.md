# Docker Cron Setup - Summary

## ✅ What Was Added

Your Docker setup now includes **automatic daily options refresh** at 8 AM UTC!

---

## 🆕 New Service: `options-scheduler`

### What It Does
- 🕐 Monitors time every 5 minutes
- 🔄 Automatically restarts `options-tracker` at 8 AM UTC daily
- 📊 Fetches fresh options data from Bybit API
- 📝 Logs all activity

### How It Works
1. Uses `docker:cli` image (lightweight, has Docker commands)
2. Mounts Docker socket to control other containers
3. Runs `scripts/docker_cron_scheduler.sh` continuously
4. Calculates time until next 8 AM UTC
5. Restarts options-tracker precisely at 8 AM

---

## 📁 New Files Created

### 1. `scripts/docker_cron_scheduler.sh`
**Purpose**: Scheduler script that runs inside Docker container

**Features**:
- Checks current time every 5 minutes
- Calculates time until next 8 AM UTC
- Shows countdown: "Next refresh in: 6h 23m"
- Restarts options-tracker at 8:00-8:05 AM UTC
- Sleeps for 1 hour after restart to avoid duplicates

### 2. `docker-compose.yml` (Updated)
**Added**: New `options-scheduler` service

```yaml
options-scheduler:
  image: docker:cli
  container_name: sr-options-scheduler
  depends_on:
    - options-tracker
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - ./scripts/docker_cron_scheduler.sh:/scheduler.sh:ro
    - ./logs:/logs
  command: sh /scheduler.sh
  restart: unless-stopped
```

### 3. `scripts/refresh_options_docker.sh`
**Purpose**: Manual refresh script for Docker (if needed)

**Usage**: `./scripts/refresh_options_docker.sh`

### 4. Documentation Updated
- ✅ `CRON_SETUP.md` - Added Docker automatic scheduler section
- ✅ `DEPLOYMENT_GUIDE.md` - Added options-scheduler to services list
- ✅ `START_HERE.md` - Added cron job reference

---

## 🚀 How to Use

### Automatic (Recommended)

Just start with Docker Compose - the scheduler runs automatically:

```bash
docker-compose up -d
```

**That's it!** The scheduler is now running and will refresh options daily at 8 AM UTC.

### Verify It's Working

```bash
# Check scheduler status
docker-compose ps options-scheduler

# View scheduler logs
docker-compose logs -f options-scheduler

# See when next refresh will happen
docker-compose logs options-scheduler | grep "Next refresh"
```

**Example Output**:
```
[2025-10-17 12:34:56 UTC] Scheduler running...
Next refresh in: 19h 25m
```

### Monitor Options Refresh

```bash
# Watch for refresh activity (will show at 8 AM UTC)
docker-compose logs -f options-scheduler

# When refresh happens, you'll see:
===========================================
⏰ It's 8 AM UTC! Time to refresh options
===========================================
🔄 Restarting options-tracker container...
✓ Options tracker restarted successfully
✓ Fresh options data will be fetched from Bybit API
===========================================
Next refresh: Tomorrow at 8:00 AM UTC
===========================================
```

---

## 📊 What Containers Are Running

After `docker-compose up -d`, you'll have **5 containers**:

1. **sr-redis** - Redis database (port 6379)
2. **sr-kline-stream** - Kline data collection
3. **sr-options-tracker** - Options data tracking
4. **sr-detector** - S/R detection (every 5 min)
5. **sr-options-scheduler** - Daily options refresh (8 AM UTC) ← NEW!

---

## 🔍 Monitoring

### Check All Services
```bash
docker-compose ps
```

### View All Logs
```bash
docker-compose logs -f
```

### View Scheduler Only
```bash
docker-compose logs -f options-scheduler
```

### Check Options Count (Before/After Refresh)
```bash
# Check how many options are tracked
redis-cli KEYS "option:*" | wc -l

# Should increase after 8 AM UTC when new options are added
```

---

## ⏰ When Does It Run?

- **Time**: 8:00 AM UTC daily
- **Check Interval**: Every 5 minutes
- **Restart Window**: 8:00-8:05 AM (5-minute window to catch the time)
- **Sleep After**: 1 hour (prevents multiple restarts)

### Time Zone Conversions

| Location | Local Time |
|----------|------------|
| UTC | 8:00 AM |
| EST (New York) | 3:00 AM |
| PST (Los Angeles) | 12:00 AM (Midnight) |
| IST (India) | 1:30 PM |
| SGT (Singapore) | 4:00 PM |
| GMT (London) | 8:00 AM |

---

## 🛠️ Manual Refresh (If Needed)

### From Host
```bash
./scripts/refresh_options_docker.sh
```

### From Inside Container
```bash
docker restart sr-options-tracker
```

### From Docker Compose
```bash
docker-compose restart options-tracker
```

---

## 🆚 Local vs Docker Cron

### Docker (Automatic - Recommended) ✅
- ✅ Built-in to docker-compose
- ✅ No manual setup needed
- ✅ Works on any OS (Linux, macOS, Windows)
- ✅ Portable with the project
- ✅ Logs viewable with docker-compose
- ✅ Auto-starts with containers

### Local (Host-Based Cron)
- ⚠️ Requires manual crontab setup
- ⚠️ OS-specific (cron on Linux/macOS, Task Scheduler on Windows)
- ⚠️ Not portable
- ✅ More control
- ✅ Lighter resource usage (no extra container)

**Recommendation**: Use Docker automatic scheduler (already configured!).

---

## 🔧 Customization

### Change Refresh Time

Edit `scripts/docker_cron_scheduler.sh`:

```bash
# Change this line (currently 08 = 8 AM UTC)
if [ "$CURRENT_HOUR" = "08" ] && [ "$CURRENT_MINUTE" -lt "05" ]; then
```

**Examples**:
- 6 AM UTC: Change `"08"` to `"06"`
- 10 AM UTC: Change `"08"` to `"10"`
- Noon UTC: Change `"08"` to `"12"`

Then restart:
```bash
docker-compose restart options-scheduler
```

### Change Check Interval

Edit `scripts/docker_cron_scheduler.sh`:

```bash
# Currently checks every 5 minutes (300 seconds)
sleep 300
```

Change to:
- Every minute: `sleep 60`
- Every 10 minutes: `sleep 600`
- Every hour: `sleep 3600`

---

## ❌ Disable Automatic Refresh

If you don't want automatic refresh:

### Temporary (Stop Scheduler)
```bash
docker-compose stop options-scheduler
```

### Permanent (Remove from docker-compose)
```bash
# Edit docker-compose.yml and comment out options-scheduler service
# Then:
docker-compose up -d
```

---

## 🆘 Troubleshooting

### Scheduler Not Running
```bash
# Check status
docker-compose ps options-scheduler

# Should show "Up"
# If not, check logs:
docker-compose logs options-scheduler
```

### Scheduler Can't Restart Options Tracker
**Error**: "Cannot connect to the Docker daemon"

**Fix**: Make sure Docker socket is mounted:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock  # This line is critical
```

### Options Not Refreshing
```bash
# Check if scheduler is running
docker-compose ps options-scheduler

# Check if it's the right time
date -u  # Should be close to 8:00 AM UTC

# Manually trigger refresh to test
docker-compose restart options-tracker

# Check options tracker logs
docker-compose logs -f options-tracker
```

### Wrong Time Zone
The scheduler uses UTC time. If your host is in a different timezone, that's fine - the scheduler always uses UTC internally.

```bash
# Check UTC time
date -u

# Check when 8 AM UTC is in your timezone
TZ=UTC date
```

---

## 📖 Documentation

- **Full Setup Guide**: `CRON_SETUP.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Quick Start**: `QUICKSTART.md`
- **Main Documentation**: `README.md`

---

## ✅ Summary

**You're all set!** When you run `docker-compose up -d`, you get:

1. ✅ All services running (Redis, kline, options, S/R detector)
2. ✅ Automatic daily options refresh at 8 AM UTC
3. ✅ Zero manual configuration needed
4. ✅ Logs viewable with `docker-compose logs`
5. ✅ Restart-safe (scheduler auto-restarts with containers)

**Just run and forget!** 🚀

---

## 🎉 What's Next

Your system now:
- ✅ Collects kline data 24/7
- ✅ Tracks options data 24/7
- ✅ Refreshes options list daily at 8 AM UTC
- ✅ Detects S/R levels every 5 minutes
- ✅ Stores everything in Redis

**Everything is automated!** Just monitor the logs and enjoy the data.

---

**Questions?** Check `CRON_SETUP.md` or `DEPLOYMENT_GUIDE.md`

**Happy Trading!** 📈
