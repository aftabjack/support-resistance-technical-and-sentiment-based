# View All S/R Data - Technical + Sentiment

**Complete guide to viewing both types of Support & Resistance levels** 📊

---

## 🎯 You Now Have TWO Types of S/R!

### 1. **Technical S/R** (from kline data)
- Based on price action (swing highs/lows, round numbers)
- **Interval-specific** (different for 1min, 5min, 15min, etc.)
- Updates every 5 minutes
- Keys: `sr:technical:basic:{interval}.{symbol}`

### 2. **Sentiment S/R** (from options data) ✨ NEW!
- Based on Open Interest walls (OI concentration)
- **Uniform across all intervals** (same for all timeframes)
- Updates every 5 minutes
- Keys: `sr:sentiment:basic:{symbol}`

---

## 🌐 **Web Visualizer (API Access)**

### Base URL
```
http://localhost:8080
```

### Technical S/R API
```bash
# Get technical S/R for BTCUSDT 15min
curl http://localhost:8080/api/sr/BTCUSDT/15 | jq .

# Get technical S/R for ETHUSDT 60min
curl http://localhost:8080/api/sr/ETHUSDT/60 | jq .
```

### Sentiment S/R API ✨ NEW!
```bash
# Get sentiment S/R for BTCUSDT (applies to all intervals)
curl http://localhost:8080/api/sentiment/BTCUSDT | jq .

# Get sentiment S/R for ETHUSDT
curl http://localhost:8080/api/sentiment/ETHUSDT | jq .

# Get sentiment S/R for SOLUSDT
curl http://localhost:8080/api/sentiment/SOLUSDT | jq .
```

### Current Price API (Real-time) ✨ NEW!
```bash
# Get current price for BTCUSDT
curl http://localhost:8080/api/current_price/BTCUSDT | jq .

# Response:
{
  "symbol": "BTCUSDT",
  "price": 105300.80,
  "timestamp": 1760769600000,
  "interval": "1"
}
```

---

## 📊 Example: Complete S/R View for BTCUSDT

### Step 1: Get Current Price
```bash
curl -s http://localhost:8080/api/current_price/BTCUSDT | jq .
```

**Output:**
```json
{
  "symbol": "BTCUSDT",
  "price": 105300.80,
  "timestamp": 1760769600000
}
```

### Step 2: Get Technical S/R (15min timeframe)
```bash
curl -s http://localhost:8080/api/sr/BTCUSDT/15 | jq '.resistance[:3], .support[:3]'
```

**Output:**
```json
[
  {
    "price": 106104.67,
    "strength": 0.88,
    "touches": 125,
    "method": "round_number"
  },
  {
    "price": 107149.20,
    "strength": 0.79,
    "touches": 100,
    "method": "round_number"
  },
  {
    "price": 108306.78,
    "strength": 1.0,
    "touches": 528,
    "method": "swing_resi"
  }
]
```

### Step 3: Get Sentiment S/R (OI Walls)
```bash
curl -s http://localhost:8080/api/sentiment/BTCUSDT | jq '.resistance[:3], .support[:3]'
```

**Output:**
```json
[
  {
    "price": 130000.00,
    "oi": 336.22,
    "strength": 1.0,
    "method": "oi_wall_call",
    "contracts": 1
  },
  {
    "price": 150000.00,
    "oi": 229.16,
    "strength": 0.68,
    "method": "oi_wall_call",
    "contracts": 1
  },
  {
    "price": 125000.00,
    "oi": 202.49,
    "strength": 0.60,
    "method": "oi_wall_call",
    "contracts": 1
  }
]
```

---

## 📝 **Command Line View**

### Technical S/R
```bash
# View technical S/R (pretty formatted)
python scripts/view_sr.py BTCUSDT 15

# Or directly from Redis
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .
```

### Sentiment S/R
```bash
# Run detector manually
python src/sr_core/sr_detector_sentiment.py --symbol BTCUSDT --mode basic

# Or directly from Redis
redis-cli GET "sr:sentiment:basic:BTCUSDT" | jq .
```

### Current Price
```bash
# Get latest kline data
redis-cli ZREVRANGE "1.BTCUSDT" 0 0 | tail -1 | jq '.c'
```

---

## 🔍 **Redis Keys**

### List All S/R Keys
```bash
# Technical S/R (18 keys: 6 intervals × 3 symbols)
redis-cli KEYS "sr:technical:basic:*"

# Sentiment S/R (3 keys: 3 symbols)
redis-cli KEYS "sr:sentiment:basic:*"
```

**Example Output:**
```
Technical:
sr:technical:basic:1.BTCUSDT
sr:technical:basic:5.BTCUSDT
sr:technical:basic:15.BTCUSDT
sr:technical:basic:60.BTCUSDT
sr:technical:basic:240.BTCUSDT
sr:technical:basic:D.BTCUSDT
... (12 more for ETH and SOL)

Sentiment:
sr:sentiment:basic:BTCUSDT
sr:sentiment:basic:ETHUSDT
sr:sentiment:basic:SOLUSDT
```

---

## 📊 **Comparison: Technical vs Sentiment**

### Technical S/R
- **Source**: Price action (klines)
- **Method**: Swing highs/lows, round numbers
- **Timeframe**: Interval-specific (15min data differs from 60min)
- **Updates**: Every 5 minutes
- **Best For**: Intraday trading, specific timeframe analysis
- **Example**:
  - Resistance at $106,104 (round number, 125 touches)
  - Support at $105,401 (round number, 51 touches)

### Sentiment S/R
- **Source**: Options data (Open Interest)
- **Method**: OI concentration (walls)
- **Timeframe**: Uniform (same for all intervals)
- **Updates**: Every 5 minutes
- **Best For**: Understanding market sentiment, major support/resistance zones
- **Example**:
  - Resistance at $130,000 (OI wall: 336 contracts)
  - Support at $100,000 (OI wall: 147 contracts)

---

## 🎯 **Trading Strategy: Combine Both!**

### Example for BTCUSDT at $105,300

**Current Price:** $105,300

**Technical Resistance (15min):**
- $106,104 (+0.76%) - Round number, 125 touches
- $107,149 (+1.76%) - Round number, 100 touches
- $108,306 (+2.85%) - Swing high, 528 touches ⭐ STRONG

**Sentiment Resistance (OI Walls):**
- $125,000 (+18.71%) - OI: 202 contracts
- $130,000 (+23.46%) - OI: 336 contracts ⭐ STRONGEST
- $150,000 (+42.45%) - OI: 229 contracts

**Analysis:**
- Near-term resistance: $106k-$108k (technical)
- Major resistance zone: $125k-$130k (sentiment - heavy OI)
- Price likely to struggle at $108k first (strong technical level)
- If breaks $108k, next major stop is $125k-$130k (OI walls)

---

## 🔄 **Real-Time Monitoring**

### Check if Data is Fresh
```bash
# Technical S/R age
curl -s http://localhost:8080/api/sr/BTCUSDT/15 | jq '.age_seconds'

# Sentiment S/R age
curl -s http://localhost:8080/api/sentiment/BTCUSDT | jq '.age_seconds'

# Should be < 300 seconds (5 minutes)
```

### Monitor Current Price
```bash
# Get price every second
while true; do
  curl -s http://localhost:8080/api/current_price/BTCUSDT | jq '.price'
  sleep 1
done
```

### Watch S/R Updates
```bash
# Monitor Redis for changes
redis-cli MONITOR | grep "sr:"
```

---

## 📈 **Python Integration**

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8080"

# Get current price
def get_current_price(symbol):
    r = requests.get(f"{BASE_URL}/api/current_price/{symbol}")
    return r.json()['price']

# Get technical S/R
def get_technical_sr(symbol, interval):
    r = requests.get(f"{BASE_URL}/api/sr/{symbol}/{interval}")
    return r.json()

# Get sentiment S/R
def get_sentiment_sr(symbol):
    r = requests.get(f"{BASE_URL}/api/sentiment/{symbol}")
    return r.json()

# Example usage
symbol = "BTCUSDT"
current_price = get_current_price(symbol)
technical = get_technical_sr(symbol, "15")
sentiment = get_sentiment_sr(symbol)

print(f"Current Price: ${current_price:,.2f}")
print(f"\nTechnical Resistance: ${technical['resistance'][0]['price']:,.2f}")
print(f"Sentiment Resistance: ${sentiment['resistance'][0]['price']:,.2f}")
```

---

## ✅ **Verification Checklist**

- [ ] Current price updates in real-time
- [ ] Technical S/R available for all 18 combinations (6 intervals × 3 symbols)
- [ ] Sentiment S/R available for all 3 symbols
- [ ] Data age < 5 minutes
- [ ] Both detectors running in Docker

```bash
# Verify all
docker-compose ps | grep sr-detector  # Should be Up
redis-cli KEYS "sr:*" | wc -l          # Should show 21 keys (18 technical + 3 sentiment)
curl http://localhost:8080/health      # Should return healthy
```

---

## 🚀 **What's Running**

All S/R detection is **automatic** in Docker:

```bash
docker-compose ps
```

**Services:**
1. **sr-redis** - Database
2. **sr-kline-stream** - Kline data collection
3. **sr-options-tracker** - Options data tracking
4. **sr-detector** - **Runs BOTH technical AND sentiment S/R every 5 min** ⭐
5. **sr-options-scheduler** - Daily refresh at 8 AM UTC
6. **sr-web-visualizer** - Web API (port 8080)

---

## 📖 **Documentation**

- `HOW_TO_VIEW_SR.md` - Technical S/R only
- `WEB_VISUALIZER_GUIDE.md` - Web interface guide
- `VIEW_ALL_SR_DATA.md` - This file (both types)

---

## 💡 **Pro Tips**

1. **Combine both types** - Technical for entry/exit, Sentiment for major zones
2. **Check current price first** - Know where you are before looking at S/R
3. **Use appropriate timeframe** - Day trading = 5-15min, Swing = 60min-Daily
4. **Monitor OI changes** - Sentiment S/R can shift as new options are added
5. **Strong confluence** - When technical and sentiment align, level is very strong

---

**All your S/R data is live and updating automatically!** 🎉

- Technical S/R: Every interval, every 5 minutes
- Sentiment S/R: Market-wide, every 5 minutes
- Current Price: Real-time from 1-minute klines

**Access everything at: http://localhost:8080/api/** 📊
