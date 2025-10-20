# 🚀 START HERE - S/R Detection System

**Your complete S/R detection system is ready!**

---

## 📁 Project Location

```
/Users/danish/PycharmProjects/options_trading/sr_detection_system/
```

Everything you need is in this single folder:
- ✅ All Python scripts
- ✅ Configuration files
- ✅ Startup/shutdown scripts
- ✅ Docker setup
- ✅ Full documentation
- ✅ Ready for Git and deployment

---

## ⚡ Quick Start (3 Steps)

### Step 1: Navigate to Project
```bash
cd /Users/danish/PycharmProjects/options_trading/sr_detection_system
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Start Everything
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all services
./scripts/start_all.sh
```

**Done!** Your system is now running 🎉

---

## ✅ What's Included

### 🔧 Core System
- **Kline Streaming** - Real-time candlestick data (1m, 5m, 15m, 60m, 240m, Daily)
- **Options Tracking** - Real-time options data (BTC, ETH, SOL)
- **S/R Detection** - Support & Resistance detection (18 combinations)
- **Redis Storage** - Fast in-memory database

### 📦 Deployment Ready
- **Local Scripts** - `start_all.sh` / `stop_all.sh`
- **Docker Support** - `docker-compose.yml` for containerized deployment
- **Git Ready** - `.gitignore` included

### 📚 Documentation
- `START_HERE.md` ← You are here
- `QUICKSTART.md` - 5-minute quick start guide
- `README.md` - Complete documentation
- `DEPLOYMENT_GUIDE.md` - Production deployment guide
- `CRON_SETUP.md` - Daily options refresh setup
- `docs/` - Full specifications and reports

---

## 📊 Verify It's Working

### 🌐 **BEST WAY: Open Web Visualizer**
```
http://localhost:8080
```
**Just open this in your browser!** Interactive charts with real-time S/R levels.

See `WEB_VISUALIZER_GUIDE.md` for full details.

### Alternative (Command Line)
```bash
# Check if services are running
ps aux | grep bybit

# Check Redis data
redis-cli KEYS "*BTCUSDT" | wc -l
# Should show 6-7 keys

# Check S/R data
redis-cli KEYS "sr:technical:basic:*" | wc -l
# Should show 18 keys

# View S/R with nice formatting
python scripts/view_sr.py BTCUSDT 15
```

---

## 📖 Documentation Guide

**Start here:**
1. `START_HERE.md` ← You are here
2. `QUICKSTART.md` - Get running in 5 minutes
3. `README.md` - Full system documentation

**For deployment:**
4. `DEPLOYMENT_GUIDE.md` - Local, Docker, Cloud deployment

**For deep dive:**
5. `docs/PHASE1_COMPLETION_REPORT.md` - What's implemented
6. `docs/SYSTEM_STATUS.md` - Current system status
7. `docs/COMPLETE_SR_SPECIFICATION.md` - Full technical spec

---

## 🎯 Common Tasks

### Start the System
```bash
./scripts/start_all.sh
```

### Stop the System
```bash
./scripts/stop_all.sh
```

### Update S/R Data
```bash
python src/sr_core/sr_detector_technical.py --all --mode basic --save
```

### Query S/R Data

**Best way (human-friendly):**
```bash
# View S/R with nice formatting
python scripts/view_sr.py BTCUSDT 15

# List all available data
python scripts/view_sr.py
```

**Alternative (raw JSON):**
```bash
# Get all S/R keys
redis-cli KEYS "sr:technical:basic:*"

# Get specific S/R
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .

# Get top 3 resistance
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[:3]'
```

**📖 Complete Guide:** See `HOW_TO_VIEW_SR.md` for all methods and examples

### View Logs
```bash
tail -f logs/kline_stream.log
tail -f logs/options_tracker.log
```

### Refresh Options Data Daily (Cron Job)
```bash
# Set up daily refresh at 8 AM UTC (when new options are added)
# See CRON_SETUP.md for detailed instructions

# Test refresh manually
./scripts/refresh_options.sh

# Or for Docker
./scripts/refresh_options_docker.sh
```

---

## 🐳 Docker Deployment

```bash
# Start with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Includes:**
- ✅ Automatic daily options refresh at 8 AM UTC
- ✅ **Web Visualizer at http://localhost:8080** 🌐

See `DOCKER_CRON_SUMMARY.md` for details.

---

## 📂 Project Structure

```
sr_detection_system/
├── src/                    # All Python scripts
├── config/                 # Configuration files
├── scripts/                # Start/stop scripts
├── docs/                   # Documentation (17 files)
├── logs/                   # Log files
├── requirements.txt        # Dependencies
├── Dockerfile             # Docker image
├── docker-compose.yml     # Docker orchestration
├── START_HERE.md          # This file
├── QUICKSTART.md          # Quick start guide
├── README.md              # Full documentation
└── DEPLOYMENT_GUIDE.md    # Deployment guide
```

---

## 🎓 What This System Does

### Real-Time Data Collection
- Streams kline (candlestick) data from Bybit
- Tracks options data (Open Interest, Volume, Greeks)
- Stores everything in Redis for fast access

### S/R Detection
- **Technical S/R** - Based on price action
  - Swing High/Low detection
  - Round Number detection
  - Interval-specific (different for 1m, 5m, 15m, etc.)

- **Sentiment S/R** (Coming in Phase 3)
  - OI Walls
  - Max Pain
  - Volume Hotspots

### Output
- 18 S/R combinations (6 intervals × 3 symbols)
- Stored in Redis with 5-minute TTL
- Average processing time: 33ms (3x faster than target!)

---

## 📊 Current Status

### ✅ Completed (Phase 1)
- Technical S/R (BASIC mode)
- Swing High/Low detection
- Round Number detection
- All 18 combinations working
- Local and Docker deployment ready

### 🔄 In Progress
- Phase 2: Volume Profile (MEDIUM mode)

### 📅 Planned
- Phase 3-4: Sentiment S/R (options-based)
- Phase 5: Combined system
- Phase 8: Web visualizer

---

## 🛠️ Next Steps

**Choose your path:**

### 1. **Start Using It Now**
```bash
./scripts/start_all.sh
# Then query S/R data from Redis
```

### 2. **Deploy to Production**
Read: `DEPLOYMENT_GUIDE.md`

### 3. **Push to Git**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/sr-detection-system.git
git push -u origin main
```

### 4. **Continue Development**
- Phase 2: Add Volume Profile
- Phase 3: Add Sentiment S/R
- Phase 8: Build web visualizer

---

## 💡 Tips

### Performance
- Current: 33ms avg per S/R detection
- Target: <100ms (we're 3x faster!)
- Can process all 18 combinations in ~600ms

### Storage
- Klines: 18 Redis keys (1,000 candles each)
- Options: 1,360+ Redis keys
- S/R: 18 Redis keys (5-minute TTL)
- Total: ~1,400 keys, ~50MB memory

### Customization
- Edit `config/config.json` for symbols/intervals
- Edit `config/sr_config_technical.json` for S/R settings
- Modify detection methods in `src/sr_methods_technical/`

---

## 🆘 Need Help?

### Quick Fixes
```bash
# Restart everything
./scripts/stop_all.sh
./scripts/start_all.sh

# Check Redis
redis-cli ping

# Check processes
ps aux | grep bybit

# View logs
tail -f logs/kline_stream.log
```

### Documentation
- `QUICKSTART.md` - Quick start guide
- `README.md` - Full documentation
- `DEPLOYMENT_GUIDE.md` - Deployment help
- `docs/SYSTEM_STATUS.md` - Current status

### Troubleshooting
See "Troubleshooting" section in `README.md`

---

## 🎉 You're All Set!

Your S/R detection system is:
- ✅ Fully organized in one folder
- ✅ Ready to run locally
- ✅ Ready for Docker deployment
- ✅ Ready for Git
- ✅ Ready for production
- ✅ Fully documented

**Start with:** `./scripts/start_all.sh`

**Then explore:** `QUICKSTART.md` → `README.md` → `docs/`

**Happy trading!** 📈

---

## 📧 Questions?

Check the docs first:
1. `QUICKSTART.md`
2. `README.md`
3. `DEPLOYMENT_GUIDE.md`
4. `docs/` folder

Still stuck? Open an issue on GitHub.

---

**Built with ❤️ for crypto traders**
