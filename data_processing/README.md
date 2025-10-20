# Data Processing Scripts - Backup Copy

**Created:** 2025-10-16
**Purpose:** Clean backup of working data collection scripts before implementing S&R detection

---

## 📁 Files in This Folder

### 1. **bybit_kline_stream_optimized.py**
- **Purpose:** Streams real-time kline (candlestick) data from Bybit
- **Data:** BTCUSDT, ETHUSDT, SOLUSDT (1m, 3m, 5m intervals)
- **Storage:** Redis sorted sets (`{interval}.{symbol}`)
- **Status:** ✅ Tested and working
- **Performance:**
  - Loads 18,000 historical candles in 3-5 seconds
  - Stores 1000 candles per symbol/interval
  - 0% CPU idle, ~39MB RAM

### 2. **bybit_options_tracker.py**
- **Purpose:** Streams real-time options data from Bybit
- **Data:** BTC, ETH, SOL options (all strikes/expirations)
- **Metrics:** IV, Greeks (delta, gamma, vega, theta), prices, volume
- **Storage:** Redis hashes (`option:{symbol}`)
- **Status:** ✅ Tested and working
- **Coverage:** ~1,928 options symbols
  - BTC: 698 options
  - ETH: 782 options
  - SOL: 448 options

### 3. **config.json**
- **Purpose:** Configuration for kline streaming
- **Contains:**
  - Symbols to track
  - Intervals (1m, 3m, 5m)
  - Candle limits per symbol (1000)

---

## 🚀 How to Use

### Start Kline Data Collection:
```bash
cd data_processing
python bybit_kline_stream_optimized.py &
```

### Start Options Data Collection:
```bash
cd data_processing
python bybit_options_tracker.py &
```

### Verify Data in Redis:
```bash
# Check kline data
redis-cli ZCARD "1.BTCUSDT"  # Should return 1000
redis-cli GET "1.BTCUSDT:latest"  # Latest unconfirmed candle

# Check options data
redis-cli HGETALL "option:BTC-29DEC23-40000-C"
redis-cli HGET "stats:options" "total_messages"
```

---

## 📦 Redis Storage Schema

### Kline Data:
```
{interval}.{symbol}          → Sorted set (1000 candles)
{interval}.{symbol}:latest   → String (latest unconfirmed candle)
```

### Options Data:
```
option:{symbol}              → Hash (all metrics)
stats:options                → Hash (global stats)
```

---

## 🔄 Restore Instructions

If you need to revert to this working version:

```bash
# From project root
cp data_processing/bybit_kline_stream_optimized.py .
cp data_processing/bybit_options_tracker.py .
cp data_processing/config.json .
```

---

## ⚠️ Important Notes

1. **Redis Must Be Running:** Both scripts require Redis on localhost:6379
2. **Dependencies:** Install with `pip install redis requests pybit`
3. **Cleanup:** Kline script runs `flushdb()` on startup to clear old data
4. **Caching:** Options tracker caches symbols for 24 hours in `options_symbols_cache.json`
5. **Auto-Reconnect:** Both scripts handle WebSocket disconnects automatically

---

## 📊 What's Next

These scripts will be used as the data source for:
- Support & Resistance detection (from kline data)
- Options Greeks analysis
- Volatility tracking
- Trading signals

**DO NOT MODIFY** these backup files. Work on the copies in the parent directory.
