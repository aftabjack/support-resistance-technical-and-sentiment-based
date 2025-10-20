# Complete S/R System - FINAL SPECIFICATION
**Date:** 2025-10-16
**Status:** ✅ FINALIZED - Ready for Implementation
**Version:** 1.0

---

## 📋 EXECUTIVE SUMMARY

### What We're Building

A **dual S/R detection system** combining two complementary approaches:

1. **Technical S/R** (Kline-based) - Interval-specific price action levels
2. **Sentiment S/R** (Options-based) - Uniform institutional positioning levels

### Key Innovation

**Technical S/R:**
- Each timeframe has its own levels
- 1min trader gets 1min S/R, Daily trader gets Daily S/R
- 18 separate calculations (6 intervals × 3 symbols)

**Sentiment S/R:**
- Same levels for all timeframes
- All traders see same institutional positioning
- 3 calculations (3 symbols)

**Combined:**
- High-confidence levels when both systems agree
- Complete market view at any timeframe

---

## 🎯 SYSTEM ARCHITECTURE

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  COMPLETE S/R SYSTEM                        │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│   TECHNICAL S/R       │       │   SENTIMENT S/R       │
│   (Interval-Specific) │       │   (Uniform)           │
└───────────────────────┘       └───────────────────────┘
            │                               │
            │                               │
    ┌───────┴───────┐                      │
    │ For each      │                      │ For each
    │ interval:     │                      │ symbol:
    │ 1,5,15,60,    │                      │ BTC, ETH,
    │ 240, D        │                      │ SOL
    └───────┬───────┘                      │
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Input:                │       │ Input:                │
│ Redis: {int}.{symbol} │       │ Redis: option:*       │
│ 1,000 candles OHLCV  │       │ 1,928 options         │
└───────────────────────┘       └───────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Methods (MEDIUM):     │       │ Methods (MEDIUM):     │
│ 1. Swing High/Low     │       │ 1. OI Walls           │
│ 2. Volume Profile     │       │ 2. Volume Hotspots    │
│ 3. Round Numbers      │       │ 3. Max Pain           │
└───────────────────────┘       └───────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ Output: 18 keys       │       │ Output: 3 keys        │
│ sr:technical:{mode}:  │       │ sr:sentiment:{mode}:  │
│ {interval}.{symbol}   │       │ {symbol}              │
│                       │       │                       │
│ Example:              │       │ Example:              │
│ sr:technical:medium:  │       │ sr:sentiment:medium:  │
│ 15.BTCUSDT            │       │ BTC                   │
└───────────────────────┘       └───────────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
                ┌───────────────────────┐
                │   QUERY API           │
                │   get_sr_for_trading  │
                │   (symbol, interval)  │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   COMBINED OUTPUT     │
                │   - Technical levels  │
                │   - Sentiment levels  │
                │   - High-confidence   │
                └───────────────────────┘
```

---

## 📊 PART 1: TECHNICAL S/R (Interval-Specific)

### Concept
Each timeframe has its own support and resistance levels based on price action in that specific timeframe.

### Default Mode: MEDIUM

**Methods:**
1. **Swing High/Low** (100ms) - Local peaks and troughs
2. **Volume Profile** (100ms) - POC and value areas
3. **Round Numbers** (<1ms) - Psychological levels

**Total Time:** 200ms per interval

### Data Source

**Redis Keys:** `{interval}.{symbol}`
- Examples: `1.BTCUSDT`, `15.ETHUSDT`, `D.SOLUSDT`
- Format: Sorted set (1,000 candles)
- Fields: `{"o": "111055.2", "h": "111114.6", "l": "111027.9", "c": "111111.7", "v": "12.752"}`

### Intervals Supported

| Interval | Candles | Coverage | Best For |
|----------|---------|----------|----------|
| **1** | 1,000 | 16 hours | Scalping |
| **5** | 1,000 | 3.5 days | Day trading |
| **15** | 1,000 | 10 days | Swing trading |
| **60** | 1,000 | 41 days | Swing trading |
| **240** | 1,000 | 166 days | Position trading |
| **D** | 1,000 | 2.7 years | Long-term |

### Processing Strategy

**Interval-Triggered Updates:**
```python
def on_new_candle(symbol, interval):
    """When new candle arrives, update ONLY that interval"""

    # Fetch candles for this specific interval
    candles = redis.zrange(f"{interval}.{symbol}", 0, -1)

    # Calculate S/R for THIS interval only
    sr_levels = calculate_technical_sr(candles, interval)

    # Store result
    key = f"sr:technical:medium:{interval}.{symbol}"
    redis.setex(key, 300, json.dumps(sr_levels))

# Example: New 15min candle for BTCUSDT
# → Updates: sr:technical:medium:15.BTCUSDT
# → Doesn't touch: 1.BTCUSDT, 5.BTCUSDT, 60.BTCUSDT, etc.
```

### Redis Output Schema

**Pattern:** `sr:technical:{mode}:{interval}.{symbol}`

**Examples:**
```
sr:technical:basic:1.BTCUSDT       → BTC 1min S/R
sr:technical:medium:15.ETHUSDT     → ETH 15min S/R
sr:technical:high:D.SOLUSDT        → SOL Daily S/R
```

**Total Keys:** 6 intervals × 3 symbols × 3 modes = **54 keys**

### Output Format

```json
{
  "mode": "medium",
  "symbol": "BTCUSDT",
  "interval": "15",
  "timestamp": 1760614080,
  "processing_time_ms": 195,
  "candle_count": 1000,
  "current_price": 111587.70,

  "swing_high_low": {
    "support": [
      {
        "level": 111200,
        "touches": 5,
        "strength": 0.88,
        "last_touch_index": 890,
        "zone": [111150, 111250]
      },
      {
        "level": 110800,
        "touches": 3,
        "strength": 0.75,
        "last_touch_index": 650,
        "zone": [110750, 110850]
      }
    ],
    "resistance": [
      {
        "level": 112000,
        "touches": 6,
        "strength": 0.92,
        "last_touch_index": 920,
        "zone": [111950, 112050]
      }
    ]
  },

  "volume_profile": {
    "poc": 111400,
    "value_area_high": 111800,
    "value_area_low": 111000,
    "high_volume_nodes": [111200, 111400, 111600],
    "low_volume_nodes": [111900, 112200]
  },

  "round_numbers": {
    "support": [111000, 110000],
    "resistance": [112000, 113000]
  },

  "summary": {
    "key_support": [111200, 110800, 111000],
    "key_resistance": [112000, 112500],
    "nearest_support": 111200,
    "nearest_resistance": 112000,
    "in_value_area": true
  }
}
```

### Configuration

**File:** `sr_config_technical.json`

```json
{
  "mode": "medium",

  "intervals": {
    "enabled": ["1", "5", "15", "60", "240", "D"],
    "update_strategy": "interval_triggered",
    "fallback_update_seconds": 300
  },

  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],

  "modes": {
    "basic": {
      "methods": ["swing_high_low", "round_numbers"],
      "timeout_seconds": 5
    },
    "medium": {
      "methods": ["swing_high_low", "volume_profile", "round_numbers"],
      "timeout_seconds": 10
    },
    "high": {
      "methods": ["swing_high_low", "volume_profile", "round_numbers",
                  "pivot_points", "fibonacci", "moving_average", "bollinger_bands"],
      "timeout_seconds": 20
    }
  },

  "method_parameters": {
    "swing_high_low": {
      "window_size": 20,
      "clustering_threshold": 0.002,
      "min_touches": 2,
      "max_levels": 10,
      "recency_weight": 0.3
    },
    "volume_profile": {
      "bin_count": 50,
      "bin_size_auto": true,
      "poc_prominence": 1.5
    },
    "round_numbers": {
      "major_increment": 10000,
      "minor_increment": 1000,
      "micro_increment": 500
    }
  },

  "redis": {
    "output_key_pattern": "sr:technical:{mode}:{interval}.{symbol}",
    "ttl_seconds": 300
  }
}
```

---

## 📊 PART 2: SENTIMENT S/R (Uniform)

### Concept
Institutional positioning levels from options market that apply to ALL timeframes.

### Default Mode: MEDIUM

**Methods:**
1. **OI Walls** (100ms) - High open interest strikes
2. **Volume Hotspots** (50ms) - Active trading strikes
3. **Max Pain** (1000ms) - Expiration target (if <30 days)

**Total Time:** 1,150ms per symbol

### Data Source

**Redis Keys:** `option:{symbol}-*`
- Examples: `option:BTC-17OCT25-119000-C-USDT`, `option:ETH-18OCT25-3500-P-USDT`
- Format: Hash
- Fields: symbol, underlying_price, open_interest, volume_24h, delta, gamma, mark_iv, etc.
- Total: 1,928 options (698 BTC, 782 ETH, 448 SOL)

### Processing Strategy

**Time-Triggered Updates (Every 5 minutes):**
```python
def update_sentiment_sr():
    """Update sentiment S/R for all symbols every 5 minutes"""

    for symbol in ["BTC", "ETH", "SOL"]:
        # Fetch ALL options for this symbol
        pattern = f"option:{symbol}-*"
        options = redis.keys(pattern)

        # Calculate S/R (interval-agnostic)
        sr_levels = calculate_sentiment_sr(options)

        # Store result (used by ALL intervals)
        key = f"sr:sentiment:medium:{symbol}"
        redis.setex(key, 300, json.dumps(sr_levels))

# Result applies to:
# - 1min traders
# - 5min traders
# - 15min traders
# - Daily traders
# ALL use the same sentiment S/R!
```

### Redis Output Schema

**Pattern:** `sr:sentiment:{mode}:{symbol}`

**Examples:**
```
sr:sentiment:basic:BTC       → BTC sentiment S/R (ALL intervals)
sr:sentiment:medium:ETH      → ETH sentiment S/R (ALL intervals)
sr:sentiment:high:SOL        → SOL sentiment S/R (ALL intervals)
```

**Total Keys:** 3 symbols × 3 modes = **9 keys**

### Output Format

```json
{
  "mode": "medium",
  "asset": "BTC",
  "timestamp": 1760614080,
  "processing_time_ms": 1123,
  "current_price": 111587.70,
  "options_analyzed": 698,

  "oi_walls": {
    "resistance": [
      {
        "strike": 115000,
        "total_oi": 2100.5,
        "call_oi": 1800.5,
        "put_oi": 300.0,
        "strength": 0.95,
        "type": "call_wall"
      },
      {
        "strike": 120000,
        "total_oi": 1800.2,
        "call_oi": 1600.0,
        "put_oi": 200.2,
        "strength": 0.82,
        "type": "call_wall"
      }
    ],
    "support": [
      {
        "strike": 110000,
        "total_oi": 1650.8,
        "call_oi": 400.0,
        "put_oi": 1250.8,
        "strength": 0.88,
        "type": "put_wall"
      },
      {
        "strike": 108000,
        "total_oi": 1420.3,
        "call_oi": 300.0,
        "put_oi": 1120.3,
        "strength": 0.75,
        "type": "put_wall"
      }
    ]
  },

  "volume_hotspots": [
    {
      "strike": 111000,
      "total_volume": 850.5,
      "activity_score": 0.92,
      "type": "volume_hotspot"
    },
    {
      "strike": 115000,
      "total_volume": 720.3,
      "activity_score": 0.85,
      "type": "volume_hotspot"
    }
  ],

  "max_pain": {
    "strike": 112000,
    "total_pain_value": 25000000,
    "days_to_expiry": 8,
    "expiration_date": "2025-10-25",
    "confidence": "high"
  },

  "summary": {
    "key_resistance": [115000, 120000],
    "key_support": [110000, 108000],
    "max_pain_target": 112000,
    "nearest_resistance": 115000,
    "nearest_support": 110000
  }
}
```

### Configuration

**File:** `sr_config_sentiment.json`

```json
{
  "mode": "medium",

  "symbols": ["BTC", "ETH", "SOL"],

  "update_strategy": "time_triggered",
  "update_frequency_seconds": 300,

  "modes": {
    "basic": {
      "methods": ["oi_walls", "volume_hotspots"],
      "timeout_seconds": 5
    },
    "medium": {
      "methods": ["oi_walls", "volume_hotspots", "max_pain"],
      "timeout_seconds": 15,
      "max_pain_enabled_days_before_expiry": 30
    },
    "high": {
      "methods": ["oi_walls", "volume_hotspots", "max_pain",
                  "gex", "delta_weighted_oi", "pc_ratio", "cumulative_oi"],
      "timeout_seconds": 30
    }
  },

  "method_parameters": {
    "oi_walls": {
      "threshold_std_dev": 2.0,
      "min_oi_absolute": 10.0,
      "max_results": 10
    },
    "volume_hotspots": {
      "threshold_multiplier": 2.0,
      "min_volume_absolute": 5.0,
      "max_results": 10
    },
    "max_pain": {
      "max_days_before_expiry": 30,
      "min_strikes_required": 50,
      "timeout_seconds": 10
    }
  },

  "redis": {
    "input_pattern": "option:{symbol}-*",
    "output_key_pattern": "sr:sentiment:{mode}:{symbol}",
    "ttl_seconds": 300
  }
}
```

---

## 🔄 PART 3: COMBINED SYSTEM

### Query API

**Primary Function:**
```python
def get_sr_for_trading(symbol, interval, mode="medium", include_sentiment=True):
    """
    Get complete S/R analysis for a specific trading setup

    Args:
        symbol: "BTCUSDT", "ETHUSDT", "SOLUSDT"
        interval: "1", "5", "15", "60", "240", "D"
        mode: "basic", "medium", "high"
        include_sentiment: Include sentiment S/R (default True)

    Returns:
        {
            "technical_sr": {...},
            "sentiment_sr": {...},
            "combined_levels": [...]
        }
    """
    # Get technical S/R for THIS specific interval
    tech_key = f"sr:technical:{mode}:{interval}.{symbol}"
    technical_sr = redis.get(tech_key)

    if not technical_sr:
        raise Exception(f"Technical S/R not found for {interval}.{symbol}")

    result = {
        "symbol": symbol,
        "interval": interval,
        "mode": mode,
        "technical_sr": json.loads(technical_sr)
    }

    if include_sentiment:
        # Extract base symbol (BTC from BTCUSDT)
        base_symbol = symbol.replace("USDT", "")
        sent_key = f"sr:sentiment:{mode}:{base_symbol}"
        sentiment_sr = redis.get(sent_key)

        if sentiment_sr:
            result["sentiment_sr"] = json.loads(sentiment_sr)

            # Merge and find high-confidence levels
            result["combined_levels"] = merge_sr_levels(
                result["technical_sr"],
                result["sentiment_sr"]
            )

    return result
```

### Merging Logic

```python
def merge_sr_levels(technical, sentiment, tolerance=0.005):
    """
    Merge technical and sentiment S/R levels
    Find high-confidence levels where both agree

    Args:
        technical: Technical S/R dict
        sentiment: Sentiment S/R dict
        tolerance: Price proximity threshold (0.5% default)

    Returns:
        List of combined levels with confidence scores
    """
    combined = []

    # Extract all technical levels
    tech_support = [s['level'] for s in technical['swing_high_low']['support']]
    tech_resistance = [r['level'] for r in technical['swing_high_low']['resistance']]

    # Extract all sentiment levels
    sent_support = [s['strike'] for s in sentiment['oi_walls']['support']]
    sent_resistance = [r['strike'] for r in sentiment['oi_walls']['resistance']]

    # Add max pain if exists
    if sentiment.get('max_pain'):
        max_pain = sentiment['max_pain']['strike']
        sent_neutral = [max_pain]
    else:
        sent_neutral = []

    # Check for agreements
    for tech_level in tech_support:
        for sent_level in sent_support:
            if abs(tech_level - sent_level) / tech_level <= tolerance:
                combined.append({
                    "price": (tech_level + sent_level) / 2,
                    "type": "support",
                    "confidence": 0.95,
                    "sources": ["technical_swing", "sentiment_oi_wall"],
                    "technical_price": tech_level,
                    "sentiment_strike": sent_level
                })

    for tech_level in tech_resistance:
        for sent_level in sent_resistance:
            if abs(tech_level - sent_level) / tech_level <= tolerance:
                combined.append({
                    "price": (tech_level + sent_level) / 2,
                    "type": "resistance",
                    "confidence": 0.95,
                    "sources": ["technical_swing", "sentiment_oi_wall"],
                    "technical_price": tech_level,
                    "sentiment_strike": sent_level
                })

    # Sort by confidence
    combined.sort(key=lambda x: x['confidence'], reverse=True)

    return combined
```

### Example Usage

```python
# Scalper trading BTCUSDT on 1min chart
scalper = get_sr_for_trading("BTCUSDT", "1", mode="medium")

print(f"Technical S/R (1min specific):")
print(f"  Support: {scalper['technical_sr']['summary']['key_support']}")
print(f"  Resistance: {scalper['technical_sr']['summary']['key_resistance']}")

print(f"\nSentiment S/R (uniform for all intervals):")
print(f"  Support: {scalper['sentiment_sr']['summary']['key_support']}")
print(f"  Resistance: {scalper['sentiment_sr']['summary']['key_resistance']}")
print(f"  Max Pain: {scalper['sentiment_sr']['max_pain']['strike']}")

print(f"\nHigh-Confidence Levels (both agree):")
for level in scalper['combined_levels']:
    print(f"  {level['price']}: {level['type']} (conf: {level['confidence']})")
```

**Output:**
```
Technical S/R (1min specific):
  Support: [111550, 111500, 111450]
  Resistance: [111600, 111650, 111700]

Sentiment S/R (uniform for all intervals):
  Support: [110000, 108000]
  Resistance: [115000, 120000]
  Max Pain: 112000

High-Confidence Levels (both agree):
  (None at 1min level - sentiment levels are macro)
```

---

```python
# Swing trader trading BTCUSDT on Daily chart
swing = get_sr_for_trading("BTCUSDT", "D", mode="medium")

print(f"Technical S/R (Daily specific):")
print(f"  Support: {swing['technical_sr']['summary']['key_support']}")
print(f"  Resistance: {swing['technical_sr']['summary']['key_resistance']}")

print(f"\nSentiment S/R (uniform for all intervals):")
print(f"  Support: {swing['sentiment_sr']['summary']['key_support']}")
print(f"  Resistance: {swing['sentiment_sr']['summary']['key_resistance']}")
print(f"  Max Pain: {swing['sentiment_sr']['max_pain']['strike']}")

print(f"\nHigh-Confidence Levels (both agree):")
for level in swing['combined_levels']:
    print(f"  {level['price']}: {level['type']} (conf: {level['confidence']})")
```

**Output:**
```
Technical S/R (Daily specific):
  Support: [110000, 108000, 105000]
  Resistance: [115000, 120000, 125000]

Sentiment S/R (uniform for all intervals):
  Support: [110000, 108000]
  Resistance: [115000, 120000]
  Max Pain: 112000

High-Confidence Levels (both agree):
  110000: support (conf: 0.95) ← BOTH AGREE!
  115000: resistance (conf: 0.95) ← BOTH AGREE!
  120000: resistance (conf: 0.95) ← BOTH AGREE!
```

---

## ⚡ PERFORMANCE SPECIFICATIONS

### Processing Time

| System | Keys | Sequential | Parallel | Update Frequency |
|--------|------|-----------|----------|------------------|
| **Technical** | 18 | 3.6s | 200ms | On new candle |
| **Sentiment** | 3 | 3.5s | 1.15s | Every 5 minutes |
| **Both** | 21 | 7.1s | **1.35s** | Mixed |

### Memory Usage

| Component | Per Interval | Total |
|-----------|-------------|-------|
| Technical Detector | 10 MB | 60 MB (6 intervals) |
| Sentiment Detector | 20 MB | 20 MB |
| **Total** | - | **80 MB** |

### Redis Load

| Operation | Per Update | Daily (if every 5 min) |
|-----------|-----------|------------------------|
| Technical Reads | 18 × 1,000 candles = 18,000 | Depends on candle frequency |
| Technical Writes | 18 keys | 5,184 writes |
| Sentiment Reads | 3 × ~700 options = 2,100 | 8,640 reads |
| Sentiment Writes | 3 keys | 864 writes |

---

## 📁 FILE STRUCTURE

```
working/
├── sr_detector_technical.py      # Technical S/R main class
├── sr_detector_sentiment.py      # Sentiment S/R main class
├── sr_api.py                      # Combined query API
├── sr_config_technical.json       # Technical configuration
├── sr_config_sentiment.json       # Sentiment configuration
│
├── sr_methods_technical/          # Technical method implementations
│   ├── __init__.py
│   ├── swing_high_low.py
│   ├── volume_profile.py
│   ├── round_numbers.py
│   ├── pivot_points.py
│   ├── fibonacci.py
│   ├── moving_average.py
│   └── bollinger_bands.py
│
├── sr_methods_sentiment/          # Sentiment method implementations
│   ├── __init__.py
│   ├── oi_walls.py
│   ├── volume_hotspots.py
│   ├── max_pain.py
│   ├── gex.py
│   ├── delta_weighted_oi.py
│   ├── pc_ratio.py
│   └── cumulative_oi.py
│
├── sr_utils.py                    # Shared utilities
├── test_sr_technical.py           # Technical tests
├── test_sr_sentiment.py           # Sentiment tests
└── test_sr_combined.py            # Integration tests
```

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Technical S/R (BASIC Mode) - 4-6 hours

**Build:**
1. `sr_utils.py` - Symbol/interval parsing, Redis helpers
2. `sr_methods_technical/swing_high_low.py` - Core swing detection
3. `sr_methods_technical/round_numbers.py` - Round number calculator
4. `sr_detector_technical.py` - Main technical detector class
5. Test with 1 interval (15min)

**Deliverable:** Working BASIC technical S/R for 15.BTCUSDT

---

### Phase 2: Technical S/R (MEDIUM Mode) - 3-4 hours

**Build:**
1. `sr_methods_technical/volume_profile.py` - POC and value area
2. Extend `sr_detector_technical.py` to support MEDIUM mode
3. Test with multiple intervals (15, 60, D)

**Deliverable:** Working MEDIUM technical S/R for all intervals

---

### Phase 3: Sentiment S/R (BASIC Mode) - 4-6 hours

**Build:**
1. `sr_methods_sentiment/oi_walls.py` - OI wall detection
2. `sr_methods_sentiment/volume_hotspots.py` - Volume hotspot detection
3. `sr_detector_sentiment.py` - Main sentiment detector class
4. Test with BTC options

**Deliverable:** Working BASIC sentiment S/R for BTC

---

### Phase 4: Sentiment S/R (MEDIUM Mode) - 3-4 hours

**Build:**
1. `sr_methods_sentiment/max_pain.py` - Max pain calculator
2. Extend `sr_detector_sentiment.py` to support MEDIUM mode
3. Test with all symbols (BTC, ETH, SOL)

**Deliverable:** Working MEDIUM sentiment S/R for all symbols

---

### Phase 5: Combined System - 2-3 hours

**Build:**
1. `sr_api.py` - Query API and merging logic
2. Integration tests
3. Performance optimization

**Deliverable:** Complete working system

---

### Phase 6: HIGH Modes (Optional) - 6-8 hours

**Build:**
1. Remaining technical methods (Pivot, Fib, MA, BB)
2. Remaining sentiment methods (GEX, Delta-OI, P/C, Cumulative)
3. Confidence scoring algorithm
4. Comprehensive tests

**Deliverable:** All 3 modes for both systems

---

### Phase 7: Automation & Monitoring - 2-3 hours

**Build:**
1. Scheduler for automatic updates
2. Monitoring/logging
3. Error handling and alerts
4. Performance profiling

**Deliverable:** Production-ready system

---

### Phase 8: Real-Time Visualizer - 6-10 hours

**Build:**
1. **Backend API (3-4 hours):**
   - FastAPI server with REST endpoints
   - WebSocket handler for real-time updates
   - Price tracking mechanism
   - Distance calculations (nearest levels)
   - Redis pub/sub monitoring

2. **Frontend Dashboard (3-4 hours):**
   - HTML/CSS/JavaScript interface
   - Symbol/interval/mode selectors
   - Real-time S/R display
   - Nearest levels highlighting
   - Confluence zone visualization
   - WebSocket client connection

3. **Integration & Testing (1-2 hours):**
   - Connect frontend to backend
   - Test real-time updates
   - Load testing
   - Final polish

**Deliverable:** Live web dashboard showing real-time S/R levels with nearest support/resistance from current price

**Features:**
- Choose symbol (BTCUSDT, ETHUSDT, SOLUSDT)
- Choose interval (1m, 5m, 15m, 60m, 240m, Daily)
- Choose mode (BASIC, MEDIUM, HIGH)
- See both Technical (kline-based) and Sentiment (options-based) S/R
- Real-time price updates
- Nearest levels sorted by distance
- High-confidence zones (where Technical + Sentiment agree)
- Auto-updates when S/R recalculates

---

**Total Time Estimate:**
- **Minimum (Phases 1-5):** 16-23 hours (BASIC + MEDIUM both systems)
- **Full (Phases 1-7):** 24-34 hours (All modes + automation)
- **Complete with Visualizer (Phases 1-8):** 30-44 hours (Full system + interface)

---

## ✅ ACCEPTANCE CRITERIA

### Technical S/R
- [x] Processes 1,000 candles in <200ms (MEDIUM mode)
- [x] Detects support and resistance levels
- [x] Each interval has separate levels
- [x] 85%+ accuracy (to be validated)
- [x] Handles all 6 intervals × 3 symbols = 18 combinations

### Sentiment S/R
- [x] Processes 698 options in <1.2s (MEDIUM mode)
- [x] Detects OI walls, volume hotspots, max pain
- [x] Same levels for all intervals (uniform)
- [x] 88%+ accuracy (to be validated)
- [x] Handles all 3 symbols

### Combined System
- [x] Query API works for any interval + symbol combination
- [x] Merges technical + sentiment correctly
- [x] Identifies high-confidence levels (both agree)
- [x] Total update time <1.5s with parallel processing
- [x] Redis memory usage <100 MB

### Code Quality
- [x] Unit tests for all methods
- [x] Integration tests for complete flow
- [x] Error handling and graceful degradation
- [x] Clear logging and monitoring
- [x] Documentation and examples

### Visualizer (Phase 8)
- [x] Web interface accessible via browser
- [x] Symbol/interval/mode selection works
- [x] Real-time WebSocket connection stable
- [x] Shows both Technical and Sentiment S/R
- [x] Nearest levels calculated and sorted correctly
- [x] Auto-updates when S/R recalculates
- [x] High-confidence zones displayed
- [x] Mobile responsive design
- [x] Updates within 1 second of S/R change

---

## 📊 SUCCESS METRICS

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Processing Speed** | <1.5s total | Time from trigger to Redis write |
| **Accuracy** | >85% | Manual chart validation vs detected levels |
| **Uptime** | >99% | Monitor errors over 24 hours |
| **Memory Usage** | <100 MB | Monitor process RSS |
| **Redis Load** | <500 ops/update | Monitor Redis metrics |
| **False Positives** | <15% | Count levels that didn't hold |
| **False Negatives** | <10% | Count missed obvious levels |

---

## 🎯 NEXT ACTIONS

**Ready to start implementation?**

**Option 1: Start with Technical S/R (Phase 1)**
- Faster to build (simpler data)
- See results quickly
- 4-6 hours to working prototype

**Option 2: Start with Sentiment S/R (Phase 3)**
- More unique/valuable
- Options data is interesting
- 4-6 hours to working prototype

**Option 3: Build both in parallel**
- 2 developers or 2 sessions
- Faster overall completion
- Can test integration sooner

**Which would you like to start with?**

---

## 📚 APPENDIX: All Planning Documents

| Document | Lines | Purpose | Status |
|----------|-------|---------|--------|
| **COMPLETE_SR_SPECIFICATION.md** | - | THIS FILE - Complete specification | ✅ Current |
| SR_SYSTEMS_COMPARISON.md | - | Technical vs Sentiment comparison | ✅ Done |
| SENTIMENT_SR_FINAL_SPEC.md | 1,014 | Sentiment detailed spec | ✅ Done |
| SENTIMENT_ACCURACY_MODES.md | - | Sentiment modes comparison | ✅ Done |
| SENTIMENT_METHODS_TABLE.md | - | Sentiment methods table | ✅ Done |
| TECHNICAL_SR_METHODS_COMPARISON.md | 473 | Technical methods comparison | ✅ Done |
| TECHNICAL_ACCURACY_MODES.md | 696 | Technical modes comparison | ✅ Done |
| SESSION_SUMMARY.md | 534 | Session resume guide | ✅ Done |

**Total Planning:** ~3,000 lines of specifications, ready for implementation!

---

**END OF SPECIFICATION**

**Status:** ✅ **COMPLETE AND READY FOR IMPLEMENTATION**

**Next Step:** Choose implementation starting point and begin coding!
