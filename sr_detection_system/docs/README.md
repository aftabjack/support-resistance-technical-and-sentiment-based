# Working Folder - Active Development

**Created:** 2025-10-16
**Purpose:** Active development folder for data collection and S&R detection

---

## 📁 Current Files

### 1. **bybit_kline_stream_ultra.py** (199 lines)
- **Purpose:** Real-time kline/candlestick data streaming
- **Features:**
  - ✅ PID file protection (prevents duplicate runs)
  - ✅ Redis connection retry logic
  - ✅ Health checks
  - ✅ Graceful shutdown
  - ✅ Historical data loading (1000 candles per symbol)
- **Data:** BTCUSDT, ETHUSDT, SOLUSDT
- **Intervals:** 1m, 5m, 15m, 60m, 240m, Daily
- **Storage:** Redis sorted sets

### 2. **bybit_options_tracker.py** (583 lines)
- **Purpose:** Real-time options data streaming
- **Features:**
  - ✅ Batch processing (100 records/batch)
  - ✅ Auto-reconnect on disconnect
  - ✅ Symbol caching (24 hours)
  - ✅ Performance metrics
- **Coverage:** ~1,928 options (BTC/ETH/SOL)
- **Metrics:** IV, Greeks, prices, volume
- **Storage:** Redis hashes

### 3. **config.json**
- Configuration for kline streaming
- Symbols, intervals, Redis settings

---

## 🚀 Usage

### Start Kline Streaming:
```bash
cd working
python bybit_kline_stream_ultra.py &
```

### Start Options Tracking:
```bash
cd working
python bybit_options_tracker.py &
```

### Stop Kline Streaming:
```bash
# PID file prevents duplicates
rm /tmp/bybit_stream.pid
pkill -f bybit_kline_stream_ultra.py
```

---

## 📊 Next Steps

- [ ] Create `support_resistance_detector.py`
- [ ] Create `sr_config.json`
- [ ] Test S&R detection with live data
- [ ] Integrate options data analysis

---

## 🔄 Backup

If anything breaks, restore from:
```bash
cp ../data_processing/* .
```

The `data_processing/` folder contains tested, working backups.
