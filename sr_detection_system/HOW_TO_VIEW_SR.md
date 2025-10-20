# How to View Support & Resistance Levels

Your S/R levels are stored in **Redis database** and updated every 5 minutes. Here are all the ways to view them:

---

## 🚀 Quick View (Recommended)

### **Method 1: Use the View Script (Best for humans)**

```bash
# View specific symbol and interval
python scripts/view_sr.py BTCUSDT 15

# List all available data
python scripts/view_sr.py

# Other examples
python scripts/view_sr.py ETHUSDT 60
python scripts/view_sr.py SOLUSDT D
```

**Output:**
```
======================================================================
📊 SUPPORT & RESISTANCE - BTCUSDT (15min)
======================================================================
💰 Current Price: $105,593.60
⏱️  Generated: 2025-10-17 18:13:44
⚡ Processing Time: 17.30ms
📈 Resistance Levels: 10
📉 Support Levels: 10
======================================================================

🎯 NEAREST LEVELS:
----------------------------------------------------------------------
📈 Nearest Resistance: $106,104.67 (+0.48%)
   Method: round_number
   Strength: 0.88
   Touches: 120

📉 Nearest Support: $100,962.16 (-4.39%)
   Method: round_number
   Strength: 0.24
   Touches: 6
```

---

## 📊 Other Methods

### **Method 2: Redis CLI (Raw JSON)**

```bash
# Get S/R for BTCUSDT 15min
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .

# Get S/R for ETHUSDT 60min
redis-cli GET "sr:technical:basic:60.ETHUSDT" | jq .

# Get S/R for SOLUSDT Daily
redis-cli GET "sr:technical:basic:D.SOLUSDT" | jq .
```

**Output:**
```json
{
  "resistance": [
    {
      "price": 106104.67,
      "strength": 0.88,
      "touches": 120,
      "method": "round_number",
      "merged_count": 12
    }
  ],
  "support": [...],
  "metadata": {
    "symbol": "BTCUSDT",
    "current_price": 105593.6,
    "processing_time_ms": 17.3
  }
}
```

### **Method 3: List All Available Keys**

```bash
# See all S/R combinations
redis-cli KEYS "sr:technical:basic:*"
```

**Output:**
```
sr:technical:basic:1.BTCUSDT
sr:technical:basic:5.BTCUSDT
sr:technical:basic:15.BTCUSDT
sr:technical:basic:60.BTCUSDT
sr:technical:basic:240.BTCUSDT
sr:technical:basic:D.BTCUSDT
... (18 total)
```

### **Method 4: Get Top 3 Levels Only**

```bash
# Top 3 resistance
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[:3]'

# Top 3 support
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.support[:3]'

# Nearest resistance (first above current price)
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[0]'
```

---

## 🔑 S/R Key Format

**Pattern:** `sr:technical:basic:{INTERVAL}.{SYMBOL}`

**Examples:**
```
sr:technical:basic:1.BTCUSDT      → BTC 1-minute
sr:technical:basic:5.BTCUSDT      → BTC 5-minute
sr:technical:basic:15.BTCUSDT     → BTC 15-minute
sr:technical:basic:60.BTCUSDT     → BTC 60-minute (1 hour)
sr:technical:basic:240.BTCUSDT    → BTC 240-minute (4 hour)
sr:technical:basic:D.BTCUSDT      → BTC Daily

sr:technical:basic:15.ETHUSDT     → ETH 15-minute
sr:technical:basic:60.SOLUSDT     → SOL 60-minute
```

---

## 📖 Data Structure

Each S/R key contains:

```json
{
  "resistance": [
    {
      "price": 106104.67,         // Price level
      "strength": 0.88,            // Strength (0-1, higher = stronger)
      "touches": 120,              // Number of times price touched this level
      "method": "round_number",    // Detection method (swing_resi/round_number)
      "merged_count": 12          // How many nearby levels were merged
    }
  ],
  "support": [
    {
      "price": 105401.57,
      "strength": 0.87,
      "touches": 51,
      "method": "round_number",
      "merged_count": 3
    }
  ],
  "timestamp": 1760705024.92,     // When this was generated
  "metadata": {
    "symbol": "BTCUSDT",
    "interval": "15",
    "mode": "basic",
    "candles_analyzed": 1000,
    "processing_time_ms": 17.3,
    "current_price": 105593.6
  }
}
```

---

## 📝 Understanding the Data

### **Resistance Levels**
- Levels **above** current price
- Price may have difficulty breaking through
- Sorted by distance from current price (nearest first)
- Strength 1.0 = strongest resistance

### **Support Levels**
- Levels **below** current price
- Price may have difficulty falling through
- Sorted by distance from current price (nearest first)
- Strength 1.0 = strongest support

### **Detection Methods**
- **`swing_resi`/`swing_supp`** - Detected from swing highs/lows in price action
- **`round_number`** - Psychological levels (100K, 50K, etc.)

### **Strength**
- **1.0** = Very strong (many touches, recent activity)
- **0.5-0.9** = Moderate strength
- **<0.5** = Weaker level

### **Touches**
- How many times price has touched this level
- More touches = more reliable level

---

## ⚡ Real-Time Updates

S/R data is automatically updated **every 5 minutes** by the `sr-detector` Docker container.

**Check when data was last updated:**
```bash
# Get timestamp of last update
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.timestamp'

# Convert to human-readable
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.metadata'
```

---

## 🐳 Docker vs Local

### **Docker (Current Setup)**
```bash
# View S/R
docker exec -it sr-redis redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .

# Or from host (if Redis port is exposed)
redis-cli -h localhost GET "sr:technical:basic:15.BTCUSDT" | jq .

# Or use the script
python scripts/view_sr.py BTCUSDT 15
```

### **Local**
```bash
# Directly access Redis
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .

# Use the script
python scripts/view_sr.py BTCUSDT 15
```

---

## 📊 All Available Combinations

You have **18 S/R combinations**:

| Symbol | Intervals |
|--------|-----------|
| BTCUSDT | 1min, 5min, 15min, 60min, 240min, Daily |
| ETHUSDT | 1min, 5min, 15min, 60min, 240min, Daily |
| SOLUSDT | 1min, 5min, 15min, 60min, 240min, Daily |

---

## 🔧 Use Cases

### **For Day Trading (1-5min)**
```bash
python scripts/view_sr.py BTCUSDT 1
python scripts/view_sr.py BTCUSDT 5
```

### **For Swing Trading (15-60min)**
```bash
python scripts/view_sr.py BTCUSDT 15
python scripts/view_sr.py BTCUSDT 60
```

### **For Position Trading (4h-Daily)**
```bash
python scripts/view_sr.py BTCUSDT 240
python scripts/view_sr.py BTCUSDT D
```

### **Find Nearest Levels**
```bash
# The view_sr.py script automatically shows nearest levels
python scripts/view_sr.py BTCUSDT 15

# Or extract with jq
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[0], .support[0]'
```

---

## 🛠️ Integration Examples

### **Python**
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get S/R data
data = r.get("sr:technical:basic:15.BTCUSDT")
sr = json.loads(data)

# Access levels
current_price = sr['metadata']['current_price']
resistance = sr['resistance']
support = sr['support']

# Find nearest resistance
nearest_r = next((r for r in resistance if r['price'] > current_price), None)
print(f"Nearest resistance: ${nearest_r['price']}")
```

### **Node.js**
```javascript
const redis = require('redis');
const client = redis.createClient();

client.get('sr:technical:basic:15.BTCUSDT', (err, data) => {
  const sr = JSON.parse(data);
  console.log('Current price:', sr.metadata.current_price);
  console.log('Nearest resistance:', sr.resistance[0]);
});
```

### **cURL (HTTP/REST)**
```bash
# If you have a REST API wrapper
curl http://localhost:8000/api/sr/BTCUSDT/15
```

---

## 💡 Tips

1. **Always check timestamp** - Make sure data is recent (< 5 minutes old)
2. **Compare multiple timeframes** - Look at 15min, 60min, and Daily together
3. **Focus on high strength levels** - Strength > 0.8 are more reliable
4. **More touches = stronger level** - 100+ touches is very significant
5. **Nearest levels matter most** - Levels far from current price are less relevant

---

## 🆘 Troubleshooting

### **No Data Found**
```bash
# Check if Redis is running
redis-cli ping

# Check if Docker containers are up
docker-compose ps

# Check if S/R detector is running
docker-compose logs sr-detector

# Verify keys exist
redis-cli KEYS "sr:technical:basic:*"
```

### **Old Data (> 5 minutes)**
```bash
# Check if detector is running
docker-compose logs --tail=20 sr-detector

# Manually trigger S/R detection
docker exec -it sr-detector python src/sr_core/sr_detector_technical.py --all --mode basic --save
```

### **Empty Levels**
- System just started (wait 1-2 minutes for data collection)
- Not enough historical data yet
- Check logs for errors

---

## 📚 Next Steps

- **Phase 2**: Volume Profile S/R (coming soon)
- **Phase 3**: Sentiment S/R from options data (OI walls, max pain)
- **Phase 8**: Web visualizer to view S/R graphically

---

**Your S/R data is live and updating every 5 minutes! 🚀**

Use `python scripts/view_sr.py` to start exploring.
