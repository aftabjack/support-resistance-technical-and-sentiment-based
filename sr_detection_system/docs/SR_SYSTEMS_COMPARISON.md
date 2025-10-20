# S/R Systems Comparison - Technical vs Sentiment
**Date:** 2025-10-16
**Purpose:** Clarify the key difference in how Technical and Sentiment S/R work

---

## 🎯 KEY INSIGHT: Interval-Specific vs Uniform

### **Technical S/R** - INTERVAL-SPECIFIC ⏱️

**Concept:** Each timeframe has its own S/R levels

**Why?**
- 1-minute candles show micro levels (scalping S/R)
- Daily candles show macro levels (swing trading S/R)
- Different intervals = Different market structure
- Each trader needs S/R for THEIR timeframe

**Example:**
```
BTCUSDT at $111,587:

1-minute S/R (micro):
  Support: $111,550, $111,520, $111,500
  Resistance: $111,600, $111,650, $111,700

60-minute S/R (swing):
  Support: $111,200, $110,800, $110,500
  Resistance: $112,000, $112,500, $113,000

Daily S/R (position):
  Support: $110,000, $108,000, $105,000
  Resistance: $115,000, $120,000, $125,000
```

**Storage in Redis:**
```
sr:technical:basic:1.BTCUSDT    → 1min S/R levels
sr:technical:basic:5.BTCUSDT    → 5min S/R levels
sr:technical:basic:15.BTCUSDT   → 15min S/R levels
sr:technical:basic:60.BTCUSDT   → 60min S/R levels
sr:technical:basic:240.BTCUSDT  → 4hour S/R levels
sr:technical:basic:D.BTCUSDT    → Daily S/R levels
```

**Total Keys:** 6 intervals × 3 symbols × 3 modes = **54 Redis keys**

---

### **Sentiment S/R** - UNIFORM 🌐

**Concept:** Same S/R levels regardless of timeframe

**Why?**
- Based on options data (not kline data)
- OI walls don't change with chart timeframe
- Max Pain is same for 1min or daily trader
- Institutional positioning is timeframe-agnostic

**Example:**
```
BTC Options (current):

OI Walls:
  Support: $110,000 (put wall)
  Resistance: $115,000 (call wall)
  Max Pain: $112,000

These levels are SAME whether you're:
  - Scalping on 1min charts
  - Swing trading on 60min charts
  - Position trading on daily charts
```

**Storage in Redis:**
```
sr:sentiment:basic:BTC    → BTC sentiment S/R (ALL intervals use this)
sr:sentiment:basic:ETH    → ETH sentiment S/R (ALL intervals use this)
sr:sentiment:basic:SOL    → SOL sentiment S/R (ALL intervals use this)
```

**Total Keys:** 3 symbols × 3 modes = **9 Redis keys**

---

## 📊 SIDE-BY-SIDE COMPARISON

| Aspect | Technical S/R | Sentiment S/R |
|--------|---------------|---------------|
| **Data Source** | Kline candles (OHLCV) | Options data (OI, Volume, Greeks) |
| **Interval Dependency** | ✅ **YES - Each interval has own levels** | ❌ **NO - Same for all intervals** |
| **Redis Keys** | 54 keys (6 intervals × 3 symbols × 3 modes) | 9 keys (3 symbols × 3 modes) |
| **Update Trigger** | New candle on that interval | Options data change (every 1-5 min) |
| **Use Case** | "What's S/R for MY timeframe?" | "Where are institutions positioned?" |
| **Trader Question** | "I trade 15min, show me 15min S/R" | "What are the option walls?" |
| **Calculation** | Per interval separately | Once per symbol, shared by all intervals |
| **Processing Time** | 200ms per interval (MEDIUM mode) | 1,150ms per symbol (MEDIUM mode) |
| **Example Key** | `sr:technical:medium:15.BTCUSDT` | `sr:sentiment:medium:BTC` |

---

## 🔧 UPDATED ARCHITECTURE

### Technical S/R Processing Flow

```
For each symbol (BTC, ETH, SOL):
  For each interval (1, 5, 15, 60, 240, D):

    1. Fetch candles from Redis: {interval}.{symbol}
       Example: "15.BTCUSDT" → 1,000 candles

    2. Calculate S/R for THAT interval:
       - Swing High/Low (on 15min candles)
       - Volume Profile (on 15min candles)
       - Round Numbers (current price)

    3. Store result: sr:technical:{mode}:{interval}.{symbol}
       Example: "sr:technical:medium:15.BTCUSDT"

    4. Result applies ONLY to 15min traders
```

**Total Calculations:** 6 intervals × 3 symbols = **18 separate calculations**

**Parallel Processing:**
All 18 can run in parallel → Fast!

---

### Sentiment S/R Processing Flow

```
For each symbol (BTC, ETH, SOL):

    1. Fetch ALL options for symbol: option:BTC-*
       Example: 698 BTC options (all strikes, all expirations)

    2. Calculate S/R (interval-agnostic):
       - OI Walls (from all options)
       - Volume Hotspots (from all options)
       - Max Pain (from all options)

    3. Store result: sr:sentiment:{mode}:{symbol}
       Example: "sr:sentiment:medium:BTC"

    4. Result applies to ALL intervals (1m, 5m, 15m, 60m, etc.)
```

**Total Calculations:** 3 symbols = **3 calculations**

**Usage:**
- 1min trader queries: `sr:sentiment:medium:BTC`
- Daily trader queries: `sr:sentiment:medium:BTC` (SAME result!)

---

## 📋 REDIS SCHEMA UPDATED

### Technical S/R Keys

```
Pattern: sr:technical:{mode}:{interval}.{symbol}

Examples:
  sr:technical:basic:1.BTCUSDT       → BTC 1min S/R (basic mode)
  sr:technical:medium:5.BTCUSDT      → BTC 5min S/R (medium mode)
  sr:technical:medium:15.ETHUSDT     → ETH 15min S/R (medium mode)
  sr:technical:high:60.SOLUSDT       → SOL 60min S/R (high mode)
  sr:technical:medium:D.BTCUSDT      → BTC Daily S/R (medium mode)

Total: 6 intervals × 3 symbols × 3 modes = 54 keys
```

### Sentiment S/R Keys

```
Pattern: sr:sentiment:{mode}:{symbol}

Examples:
  sr:sentiment:basic:BTC       → BTC sentiment S/R (basic mode)
  sr:sentiment:medium:ETH      → ETH sentiment S/R (medium mode)
  sr:sentiment:high:SOL        → SOL sentiment S/R (high mode)

Total: 3 symbols × 3 modes = 9 keys
```

---

## 🎯 USAGE EXAMPLES

### Example 1: Scalper Trading BTC on 1min

**Query:**
```python
# Get 1min technical S/R
technical_sr = redis.get("sr:technical:medium:1.BTCUSDT")

# Get sentiment S/R (same for all intervals)
sentiment_sr = redis.get("sr:sentiment:medium:BTC")

# Combine both
combined = merge_sr(technical_sr, sentiment_sr)
```

**Result:**
```json
{
  "technical_1min": {
    "support": [111550, 111500],
    "resistance": [111600, 111650]
  },
  "sentiment": {
    "support": [110000],
    "resistance": [115000],
    "max_pain": 112000
  },
  "high_confidence": [
    // None - different timeframes
  ]
}
```

---

### Example 2: Swing Trader on 60min

**Query:**
```python
# Get 60min technical S/R
technical_sr = redis.get("sr:technical:medium:60.BTCUSDT")

# Get sentiment S/R (SAME as scalper!)
sentiment_sr = redis.get("sr:sentiment:medium:BTC")

# Combine
combined = merge_sr(technical_sr, sentiment_sr)
```

**Result:**
```json
{
  "technical_60min": {
    "support": [111200, 110800],
    "resistance": [112000, 112500]
  },
  "sentiment": {
    "support": [110000],
    "resistance": [115000],
    "max_pain": 112000
  },
  "high_confidence": [
    {
      "price": 112000,
      "reason": "60min resistance + Max Pain",
      "confidence": 0.95
    }
  ]
}
```

---

### Example 3: Multi-Timeframe Analysis

**Query all technical timeframes:**
```python
intervals = ["1", "5", "15", "60", "240", "D"]

for interval in intervals:
    key = f"sr:technical:medium:{interval}.BTCUSDT"
    print(f"{interval}: {redis.get(key)}")

# Sentiment (once)
print(f"Sentiment: {redis.get('sr:sentiment:medium:BTC')}")
```

**Result:**
```
1min:   Support [111550, 111500], Resistance [111600, 111650]
5min:   Support [111450, 111350], Resistance [111700, 111800]
15min:  Support [111200, 111000], Resistance [111900, 112100]
60min:  Support [110800, 110500], Resistance [112000, 112500]
240min: Support [110000, 109500], Resistance [113000, 114000]
Daily:  Support [108000, 105000], Resistance [115000, 120000]

Sentiment: Support [110000], Resistance [115000], Max Pain 112000
```

**Analysis:**
- Micro levels (1m, 5m) for scalping
- Intermediate levels (15m, 60m) for day trading
- Macro levels (240m, D) for swing trading
- Sentiment levels (uniform) for institutional context

---

## 📊 PROCESSING TIME BREAKDOWN

### Technical S/R (MEDIUM mode)

| Scenario | Time |
|----------|------|
| **Single Interval** (e.g., just 60min) | 200ms |
| **All 6 Intervals** (sequential) | 1,200ms (1.2s) |
| **All 6 Intervals** (parallel) | 200ms ⭐ |
| **All 18 Combinations** (3 symbols × 6 intervals, parallel) | 200ms ⭐ |

---

### Sentiment S/R (MEDIUM mode)

| Scenario | Time |
|----------|------|
| **Single Symbol** (e.g., BTC) | 1,150ms (1.15s) |
| **All 3 Symbols** (sequential) | 3,450ms (3.5s) |
| **All 3 Symbols** (parallel) | 1,150ms (1.15s) ⭐ |

---

### Combined Update (Both Systems)

| Scenario | Sequential | Parallel |
|----------|-----------|----------|
| **Tech (18) + Sentiment (3)** | 4.65s | **1.35s** ⭐ |

**With parallel processing: 1.35 seconds to update everything!**

---

## 🔄 UPDATE STRATEGY

### Strategy 1: Interval-Triggered (Smart)

```python
# Technical: Update only the interval that got new candle
def on_new_candle(symbol, interval):
    # Only recalculate THIS interval
    update_technical_sr(symbol, interval)
    # Example: 1.BTCUSDT got new candle
    # → Recalculate sr:technical:medium:1.BTCUSDT
    # → Don't touch 5.BTCUSDT, 15.BTCUSDT, etc.

# Sentiment: Update when options data changes
def on_options_update(symbol):
    update_sentiment_sr(symbol)
    # Example: BTC options updated
    # → Recalculate sr:sentiment:medium:BTC
```

**Efficiency:** Only recalculate what changed!

---

### Strategy 2: Time-Triggered (Simple)

```python
# Technical: Update all intervals every 5 minutes
schedule.every(5).minutes.do(update_all_technical_sr)

# Sentiment: Update all symbols every 5 minutes
schedule.every(5).minutes.do(update_all_sentiment_sr)
```

**Simpler but less efficient**

---

### Strategy 3: On-Demand (Lazy)

```python
# Calculate only when requested
def get_sr(symbol, interval, type="technical"):
    key = f"sr:{type}:{mode}:{interval}.{symbol}"

    # Check if exists and not stale
    result = redis.get(key)
    if result and not is_stale(result):
        return result

    # Calculate fresh
    if type == "technical":
        result = calculate_technical_sr(symbol, interval)
    else:
        result = calculate_sentiment_sr(symbol)

    redis.setex(key, 300, result)  # Cache 5 min
    return result
```

**Most efficient, but adds latency**

---

## 🎯 RECOMMENDED APPROACH

### For Technical S/R:
**Interval-triggered updates**

```
When new candle arrives on 15.BTCUSDT:
  → Update sr:technical:medium:15.BTCUSDT (200ms)
  → Don't touch other intervals (they didn't change)

Benefit: Minimal computation, always fresh
```

---

### For Sentiment S/R:
**Time-triggered updates (every 5 minutes)**

```
Every 5 minutes:
  → Update sr:sentiment:medium:BTC (1.15s)
  → Update sr:sentiment:medium:ETH (1.15s)
  → Update sr:sentiment:medium:SOL (1.15s)
  → Total: 3.5s (or 1.15s in parallel)

Benefit: Options data doesn't change every second
```

---

## 📋 CONFIGURATION UPDATED

### sr_config_technical.json

```json
{
  "mode": "medium",

  "intervals": {
    "enabled": ["1", "5", "15", "60", "240", "D"],
    "update_strategy": "interval_triggered",
    "fallback_update_seconds": 300
  },

  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],

  "redis": {
    "output_key_pattern": "sr:technical:{mode}:{interval}.{symbol}",
    "ttl_seconds": 300
  }
}
```

### sr_config_sentiment.json

```json
{
  "mode": "medium",

  "symbols": ["BTC", "ETH", "SOL"],

  "update_strategy": "time_triggered",
  "update_frequency_seconds": 300,

  "redis": {
    "output_key_pattern": "sr:sentiment:{mode}:{symbol}",
    "ttl_seconds": 300
  }
}
```

---

## 🎯 QUERY API DESIGN

### Get S/R for Specific Trading Setup

```python
def get_sr_for_trading(symbol, interval, include_sentiment=True):
    """
    Get S/R levels for a specific trading setup

    Args:
        symbol: "BTCUSDT", "ETHUSDT", "SOLUSDT"
        interval: "1", "5", "15", "60", "240", "D"
        include_sentiment: Whether to include sentiment S/R

    Returns:
        Combined S/R levels
    """
    # Get technical S/R for THIS interval
    tech_key = f"sr:technical:medium:{interval}.{symbol}"
    technical = redis.get(tech_key)

    result = {
        "symbol": symbol,
        "interval": interval,
        "technical_sr": technical
    }

    if include_sentiment:
        # Extract base symbol (BTC from BTCUSDT)
        base = symbol.replace("USDT", "")
        sent_key = f"sr:sentiment:medium:{base}"
        sentiment = redis.get(sent_key)

        result["sentiment_sr"] = sentiment
        result["combined"] = merge_sr(technical, sentiment)

    return result
```

**Usage:**
```python
# Scalper on 1min
scalper_sr = get_sr_for_trading("BTCUSDT", "1")

# Swing trader on Daily
swing_sr = get_sr_for_trading("BTCUSDT", "D")

# Different intervals, different technical S/R, SAME sentiment S/R!
```

---

## ✅ SUMMARY

### ✅ **Technical S/R:**
- **Interval-Specific** - Each timeframe has own levels
- **18 calculations** (6 intervals × 3 symbols)
- **54 Redis keys** (× 3 modes)
- **Update:** When new candle on that interval
- **Query:** `sr:technical:medium:15.BTCUSDT`

### ✅ **Sentiment S/R:**
- **Uniform** - Same levels for all intervals
- **3 calculations** (3 symbols)
- **9 Redis keys** (× 3 modes)
- **Update:** Every 5 minutes (time-triggered)
- **Query:** `sr:sentiment:medium:BTC`

### ✅ **Combined:**
- High confidence when both agree
- Different timeframes show different alignments
- Complete market view (price action + institution positioning)

---

**This design is perfect! Technical adapts to timeframe, Sentiment provides universal context.**

**Ready to finalize the complete specification?**
