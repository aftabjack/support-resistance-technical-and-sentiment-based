# Options Trading - Bybit Data Processing

## Project Status: Data Processing ✅ Complete | S&R Detection 🔄 Next

---

## What Was Completed

### 1. **Data Streaming Script** ✅
- Real-time WebSocket streaming from Bybit
- Historical data fetch (1000 candles per symbol/interval)
- Redis storage with optimized pipeline batching
- Config-driven settings

### 2. **Files Created**

| File | Purpose |
|------|---------|
| `config.json` | Configuration (edit symbols, intervals, Redis settings) |
| `bybit_kline_stream+historical_data.py` | Original working version with Redis |
| `bybit_kline_stream_optimized.py` | **Recommended** - 6-7× faster with pipeline batching |
| `bybit_kline_stream_ultra.py` | PID file protection + health checks |
| `IMPROVEMENTS.md` | Detailed optimization explanations |
| `TEST_RESULTS.md` | Complete test results and performance metrics |

### 3. **Redis Structure**

**Confirmed Candles** (Sorted Sets):
```
Key: "1.BTCUSDT", "5.ETHUSDT", "D.SOLUSDT", etc.
Format: {interval}.{symbol}
Data: JSON {"o": "111500", "h": "111600", "l": "111400", "c": "111550", "v": "234.5"}
Score: timestamp (milliseconds)
Limit: 1000 candles per key
```

**Unconfirmed Candles** (Strings):
```
Key: "1.BTCUSDT:latest"
Data: JSON {"ts": 1760536079999, "o": "...", "h": "...", "l": "...", "c": "...", "v": "..."}
```

---

## How to Use

### Start the Data Stream
```bash
# Recommended version
python bybit_kline_stream_optimized.py

# With PID protection
python bybit_kline_stream_ultra.py

# Stop with Ctrl+C
```

### Query Data from Redis
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Get all confirmed candles for 1-min BTCUSDT
candles = r.zrange("1.BTCUSDT", 0, -1, withscores=True)

# Get latest unconfirmed candle
latest = json.loads(r.get("1.BTCUSDT:latest"))

# Get specific time range
start_ts = 1760530000000
end_ts = 1760535000000
range_candles = r.zrangebyscore("1.BTCUSDT", start_ts, end_ts)
```

### Edit Configuration
Edit `config.json`:
```json
{
  "trading": {
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],  // Add/remove
    "intervals": [1, 5, 15, 60, 240, "D"],          // Customize timeframes
    "candle_limit": 1000                            // History size
  }
}
```

---

## Performance Metrics

- **Startup**: 3-5 seconds (loads 18,000 candles)
- **Memory**: 4.37 MB (Redis) + 39 MB (Python)
- **CPU**: 0% idle
- **Live Updates**: 2-5 updates/second per symbol
- **Redis Calls**: 36 (vs 36,000 without optimization)

---

## Next: Support & Resistance Detection

### Approach to Implement
- **Method**: Zone-based S&R (more realistic than exact prices)
- **Sensitivity**: Moderate (filter noise, catch important levels)
- **Output**: Levels + strength + touch count
- **Update**: Periodic (every 1-5 min)

### Questions to Answer Before Implementation
1. Which method? (Swing High/Low, Pivot Points, Zone-based, or All)
2. Sensitivity level? (Conservative/Moderate/Aggressive)
3. Output format? (Just prices, or with metadata)
4. Update frequency? (Real-time, periodic, on-demand)

### Recommended Next Steps
```bash
# 1. Create S&R detection script
# - Read candles from Redis
# - Calculate support/resistance zones
# - Store results back in Redis or separate structure

# 2. Integrate with trading logic
# - Query S&R levels
# - Use for entry/exit signals
```

---

## Troubleshooting

### Redis not running
```bash
redis-server --daemonize yes
redis-cli ping  # Should return PONG
```

### Multiple instances running
```bash
# Kill all instances
pkill -9 -f bybit_kline

# Remove PID file (ultra version only)
rm -f /tmp/bybit_stream.pid
```

### Check data
```bash
# How many keys
redis-cli DBSIZE

# Check candle count
redis-cli ZCARD "1.BTCUSDT"

# View latest candle
redis-cli GET "1.BTCUSDT:latest"
```

---

## Database Recommendation

**Redis** ✅ Chosen for:
- Ultra-fast in-memory access (microseconds)
- Sorted Sets perfect for time-series data
- Simple CRUD operations
- Easy size management (auto-remove oldest)

**Why not others:**
- PostgreSQL/TimescaleDB: Overkill for 1000-candle window
- SQLite: Slower, single-threaded writes
- MongoDB: More complex, slower than Redis

---

## Contact & Notes

**Status**: Production-ready
**Performance Rating**: 9/10
**Last Updated**: 2025-10-15

All files saved in: `/Users/danish/PycharmProjects/options_trading/`
