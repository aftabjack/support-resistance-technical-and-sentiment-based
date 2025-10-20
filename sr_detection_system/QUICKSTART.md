# Quick Start Guide - S/R Detection System

**Get up and running in 5 minutes!** 🚀

---

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Redis** installed
3. **Git** (if cloning from repository)

---

## 🚀 Quick Start (Local)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd sr_detection_system

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Start Redis

```bash
# macOS (Homebrew)
brew services start redis

# Or run manually
redis-server
```

### Step 3: Start All Services

```bash
# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Start everything
./scripts/start_all.sh
```

**This will:**
- ✅ Start Redis (if not running)
- ✅ Start kline data collection
- ✅ Start options data tracking
- ✅ Generate initial S/R data

### Step 4: Verify It's Working

```bash
# Check Redis keys
redis-cli KEYS "*BTCUSDT" | wc -l
# Should show 7+ keys

# Check S/R data
redis-cli KEYS "sr:technical:basic:*" | wc -l
# Should show 18 keys

# View S/R for BTCUSDT 15min
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .
```

### Step 5: Stop All Services

```bash
./scripts/stop_all.sh
```

---

## 🐳 Quick Start (Docker)

### Step 1: Build and Start

```bash
cd sr_detection_system

# Start all services with Docker Compose
docker-compose up -d
```

**This will:**
- ✅ Start Redis container
- ✅ Start kline stream container
- ✅ Start options tracker container
- ✅ Start S/R detector (runs every 5 minutes)

### Step 2: Verify It's Working

```bash
# View logs
docker-compose logs -f

# Check Redis (from host)
redis-cli -h localhost KEYS "sr:technical:basic:*"

# Or exec into Redis container
docker exec -it sr-redis redis-cli KEYS "sr:technical:basic:*"
```

### Step 3: Stop Everything

```bash
docker-compose down
```

---

## 📊 Query S/R Data

### Get All S/R Keys
```bash
redis-cli KEYS "sr:technical:basic:*"
```

### Get BTCUSDT 15min S/R
```bash
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .
```

### Get Top 3 Resistance Levels
```bash
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[:3]'
```

### Example Output:
```json
[
  {
    "price": 111702.47,
    "strength": 1.0,
    "touches": 2161,
    "method": "swing_resi",
    "merged_count": 14
  },
  {
    "price": 112783.49,
    "strength": 1.0,
    "touches": 1272,
    "method": "swing_resi",
    "merged_count": 13
  },
  {
    "price": 113796.33,
    "strength": 1.0,
    "touches": 630,
    "method": "swing_resi",
    "merged_count": 11
  }
]
```

---

## 🔄 Update S/R Data

### Manual Update (All Symbols/Intervals)
```bash
python src/sr_core/sr_detector_technical.py --all --mode basic --save
```

### Update Specific Symbol/Interval
```bash
python src/sr_core/sr_detector_technical.py \
  --symbol BTCUSDT \
  --interval 15 \
  --mode basic \
  --save
```

---

## 📁 Project Structure

```
sr_detection_system/
├── src/                           # All Python scripts
│   ├── bybit_kline_stream_ultra.py    # Kline data collection
│   ├── bybit_options_tracker.py       # Options data collection
│   ├── sr_core/                       # S/R detection core
│   └── sr_methods_technical/          # Detection methods
├── config/                        # Configuration files
├── scripts/                       # Startup/shutdown scripts
├── logs/                         # Log files
├── docs/                         # Documentation
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Docker orchestration
└── README.md                     # Full documentation
```

---

## 🎯 What's Running?

### Local Mode:
1. **Kline Stream** - Collects 1m, 5m, 15m, 60m, 240m, Daily candles
   - Logs: `logs/kline_stream.log`
   - PID: `logs/kline_stream.pid`

2. **Options Tracker** - Collects BTC, ETH, SOL options data
   - Logs: `logs/options_tracker.log`
   - PID: `logs/options_tracker.pid`

3. **Redis** - Stores all data
   - Port: 6379
   - Keys: 18+ kline keys, 1,360+ option keys, 18 S/R keys

### Docker Mode:
1. **sr-redis** - Redis container
2. **sr-kline-stream** - Kline collection container
3. **sr-options-tracker** - Options collection container
4. **sr-detector** - S/R detection container (runs every 5 min)

---

## 📊 Data in Redis

### Kline Data
```
1.BTCUSDT    → 1min candles
5.BTCUSDT    → 5min candles
15.BTCUSDT   → 15min candles
60.BTCUSDT   → 1hour candles
240.BTCUSDT  → 4hour candles
D.BTCUSDT    → Daily candles

(Same for ETHUSDT, SOLUSDT)
```

### Options Data
```
option:BTC-120000-C-25OCT24
option:BTC-115000-P-25OCT24
... (1,360+ keys)
```

### S/R Data
```
sr:technical:basic:1.BTCUSDT
sr:technical:basic:15.BTCUSDT
sr:technical:basic:60.BTCUSDT
... (18 keys total)
```

---

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not, start Redis
redis-server
```

### No Data in Redis
```bash
# Check if scripts are running
ps aux | grep bybit

# Restart scripts
./scripts/stop_all.sh
./scripts/start_all.sh
```

### Permission Denied (Scripts)
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Import Errors
```bash
# Make sure you're in project root
cd sr_detection_system

# Or use python -m
python -m src.sr_core.sr_detector_technical --all --mode basic --save
```

---

## 📖 Next Steps

1. **Read Full Documentation**: `README.md`
2. **Check System Status**: `docs/SYSTEM_STATUS.md`
3. **View Phase 1 Report**: `docs/PHASE1_COMPLETION_REPORT.md`
4. **Customize Config**: Edit `config/config.json` and `config/sr_config_technical.json`

---

## 💡 Useful Commands

```bash
# View real-time logs
tail -f logs/kline_stream.log
tail -f logs/options_tracker.log

# Check current prices
redis-cli GET "1.BTCUSDT" | jq '.c'

# Count all keys
redis-cli DBSIZE

# Monitor Redis in real-time
redis-cli MONITOR

# Clear all data (CAUTION!)
redis-cli FLUSHALL
```

---

## 🎉 Success!

If you see S/R data in Redis, you're all set! The system is:
- ✅ Collecting real-time kline data
- ✅ Tracking options data
- ✅ Detecting support and resistance levels
- ✅ Storing everything in Redis

**Happy trading!** 📈

---

## 📧 Need Help?

- Check `README.md` for full documentation
- Check `docs/` for detailed specifications
- Open an issue on GitHub

---

**Built with ❤️ for crypto traders**
