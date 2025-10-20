# Next Session: Support & Resistance Implementation

## Quick Resume Points

### What's Ready
✅ Data streaming working perfectly
✅ Redis storing 1000 candles per symbol/interval
✅ Real-time updates flowing
✅ Table naming: `{interval}.{symbol}` (e.g., "1.BTCUSDT")

### What's Next
🔄 Support & Resistance detection algorithm
🔄 Store S&R levels in Redis
🔄 Query interface for trading logic

---

## Questions to Answer First

Before implementing, decide:

### 1. Detection Method
- **Swing High/Low**: Find local peaks and troughs
- **Pivot Points**: Classic formula (High + Low + Close) / 3
- **Zone-based**: Areas where price bounces multiple times (RECOMMENDED)
- **Volume Profile**: Price levels with high volume
- **Fibonacci Retracements**: Based on recent swing

### 2. Sensitivity
- **Conservative**: Fewer, stronger levels (5-10 levels)
- **Moderate**: Balanced (10-20 levels) - RECOMMENDED
- **Aggressive**: More levels, may include noise (20+ levels)

### 3. Output Format
Option A - Just prices:
```python
{
  "support": [111200, 110800, 110500],
  "resistance": [111800, 112000, 112500]
}
```

Option B - With metadata (RECOMMENDED):
```python
{
  "support": [
    {"level": 111200, "strength": 0.85, "touches": 5, "zone": [111150, 111250]},
    {"level": 110800, "strength": 0.72, "touches": 3, "zone": [110750, 110850]}
  ],
  "resistance": [
    {"level": 111800, "strength": 0.90, "touches": 6, "zone": [111750, 111850]}
  ]
}
```

### 4. Update Frequency
- **Real-time**: Recalculate every candle (may be overkill)
- **Periodic**: Every 1-5 minutes (RECOMMENDED)
- **On-demand**: Only when requested by trading script

---

## Recommended Implementation Plan

### Step 1: Create S&R Detector Class
```python
class SupportResistanceDetector:
    def __init__(self, redis_client, sensitivity='moderate'):
        self.r = redis_client
        self.sensitivity = sensitivity

    def detect_levels(self, key):
        """Detect S&R from candles in Redis"""
        candles = self.get_candles(key)

        # Find swing highs/lows
        highs, lows = self.find_swings(candles)

        # Cluster into zones
        resistance_zones = self.cluster_levels(highs)
        support_zones = self.cluster_levels(lows)

        # Calculate strength
        resistance = self.calculate_strength(resistance_zones, candles)
        support = self.calculate_strength(support_zones, candles)

        return {"support": support, "resistance": resistance}
```

### Step 2: Store Results in Redis
```python
# Store S&R for each symbol/interval
redis_key = f"sr:{interval}.{symbol}"
data = json.dumps(sr_levels)
r.setex(redis_key, 300, data)  # Expire after 5 min
```

### Step 3: Query Interface
```python
def get_sr_levels(symbol, interval):
    key = f"sr:{interval}.{symbol}"
    data = r.get(key)
    return json.loads(data) if data else None
```

---

## Algorithm Pseudocode (Zone-Based)

```python
def find_support_resistance(candles, window=20, threshold=0.002):
    """
    window: lookback period for local peaks
    threshold: price similarity (0.002 = 0.2% difference groups together)
    """

    # Step 1: Find local highs and lows
    highs = []
    lows = []

    for i in range(window, len(candles) - window):
        # Check if this is a local high
        if candles[i]['h'] == max(c['h'] for c in candles[i-window:i+window]):
            highs.append(float(candles[i]['h']))

        # Check if this is a local low
        if candles[i]['l'] == min(c['l'] for c in candles[i-window:i+window]):
            lows.append(float(candles[i]['l']))

    # Step 2: Cluster nearby levels into zones
    resistance_zones = cluster_prices(highs, threshold)
    support_zones = cluster_prices(lows, threshold)

    # Step 3: Calculate strength (how many times price touched)
    for zone in resistance_zones:
        zone['touches'] = count_touches(candles, zone['level'], threshold)
        zone['strength'] = calculate_strength(zone['touches'], recency)

    return support_zones, resistance_zones
```

---

## Code Structure

```
options_trading/
├── config.json                          # Already done
├── bybit_kline_stream_optimized.py     # Already done
├── support_resistance_detector.py      # TO CREATE
├── sr_config.json                       # TO CREATE (S&R settings)
└── README.md                            # Already done
```

---

## Testing Plan

1. **Unit Test**: Test S&R detection on sample data
2. **Accuracy Test**: Compare with manual chart analysis
3. **Performance Test**: Ensure < 100ms per symbol
4. **Integration Test**: End-to-end with live data

---

## When You Return

Run these commands to resume:
```bash
# 1. Check if data stream is running
ps aux | grep bybit_kline

# 2. If not, start it
python bybit_kline_stream_optimized.py &

# 3. Verify data is flowing
redis-cli GET "1.BTCUSDT:latest"

# 4. Ready to implement S&R!
```

---

## Key Files to Reference

- **config.json**: Symbols and intervals
- **TEST_RESULTS.md**: Performance benchmarks
- **IMPROVEMENTS.md**: Optimization details
- **README.md**: Complete project overview

All saved and ready to continue!
