# Support & Resistance Implementation Plan
**Date:** 2025-10-16
**Project:** Options Trading - Dual S/R Detection System

---

## 🎯 Overview

**Goal:** Implement a comprehensive Support & Resistance detection system using two complementary approaches:

1. **Technical S/R** - Price action based (from kline data)
2. **Market Sentiment S/R** - Options positioning based (from OI/Volume data)

---

## 📊 Part 1: Technical S/R (Kline-Based)

### Concept
Uses historical price data to identify levels where price has repeatedly bounced or reversed.

### Data Source
```
Redis Keys: {interval}.{symbol}
Format: Sorted set with 1,000 candles
Fields: open, high, low, close, volume
```

### Detection Methods

#### Method 1: **Swing High/Low Detection** ⭐ RECOMMENDED
**How it works:**
1. Scan through candles with a rolling window (e.g., 20 candles)
2. Identify local highs where `high[i] > all(high[i-20:i+20])`
3. Identify local lows where `low[i] < all(low[i-20:i+20])`
4. Cluster nearby levels (within 0.2% of each other)
5. Count how many times price "touched" each cluster
6. Calculate strength based on touches + recency

**Pseudocode:**
```python
def find_swing_highs(candles, window=20):
    highs = []
    for i in range(window, len(candles) - window):
        current_high = candles[i]['h']

        # Check if local maximum
        if current_high == max(c['h'] for c in candles[i-window:i+window]):
            highs.append((current_high, i))

    return highs

def cluster_levels(levels, threshold=0.002):
    # Group levels within 0.2% of each other
    clusters = []
    sorted_levels = sorted(levels)

    current_cluster = [sorted_levels[0]]
    for level in sorted_levels[1:]:
        if abs(level - current_cluster[-1]) / current_cluster[-1] <= threshold:
            current_cluster.append(level)
        else:
            clusters.append(current_cluster)
            current_cluster = [level]

    return clusters
```

**Advantages:**
- ✅ Simple and proven methodology
- ✅ Works on any timeframe
- ✅ Easy to visualize
- ✅ Clear entry/exit points
- ✅ Fast computation (< 100ms)

**Disadvantages:**
- ❌ Lagging indicator (backward-looking)
- ❌ Doesn't account for future expectations
- ❌ May create false levels in choppy markets
- ❌ Requires parameter tuning (window size, threshold)

---

#### Method 2: **Pivot Points**
**How it works:**
```python
pivot = (high + low + close) / 3
resistance_1 = 2 * pivot - low
support_1 = 2 * pivot - high
resistance_2 = pivot + (high - low)
support_2 = pivot - (high - low)
```

**Advantages:**
- ✅ Mathematical certainty
- ✅ Widely used by traders
- ✅ No parameter tuning needed

**Disadvantages:**
- ❌ Only works for daily timeframe
- ❌ Static (doesn't adapt to price action)
- ❌ May not reflect actual market structure

---

#### Method 3: **Volume Profile**
**How it works:**
1. Divide price range into bins (e.g., $100 increments)
2. Sum volume traded at each price level
3. Identify high-volume nodes (support) and low-volume nodes (resistance)

**Advantages:**
- ✅ Accounts for volume (liquidity)
- ✅ Shows where most trading occurred
- ✅ Can identify value areas

**Disadvantages:**
- ❌ Computationally expensive
- ❌ Requires tick data (we only have OHLCV)
- ❌ Less clear for options traders

---

#### Method 4: **Fibonacci Retracement**
**How it works:**
1. Identify recent swing high and swing low
2. Calculate Fibonacci levels: 23.6%, 38.2%, 50%, 61.8%, 78.6%
3. Use as potential S/R levels

**Advantages:**
- ✅ Popular with traders (self-fulfilling)
- ✅ Provides multiple levels
- ✅ Works across timeframes

**Disadvantages:**
- ❌ Subjective (which swing to use?)
- ❌ Not based on actual price behavior
- ❌ Can create too many levels

---

### **Recommended Approach: Swing High/Low with Clustering**

**Why:**
1. Based on actual price action (empirical)
2. Accounts for level strength (touches)
3. Adaptable to any timeframe
4. Computationally efficient
5. Combines well with options data

**Parameters:**
```python
{
  "window": 20,              # Lookback for local extrema
  "threshold": 0.002,        # Price similarity (0.2%)
  "min_touches": 2,          # Minimum touches to be valid level
  "max_levels": 15,          # Maximum S/R levels to return
  "recency_weight": 0.3      # How much to weight recent touches
}
```

**Output Format:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "timestamp": 1760611859,
  "current_price": 111587.70,
  "support": [
    {
      "level": 111200.50,
      "strength": 0.85,
      "touches": 5,
      "zone": [111150, 111250],
      "last_touch_index": 890
    },
    {
      "level": 110800.25,
      "strength": 0.72,
      "touches": 3,
      "zone": [110750, 110850],
      "last_touch_index": 650
    }
  ],
  "resistance": [
    {
      "level": 112000.75,
      "strength": 0.90,
      "touches": 6,
      "zone": [111950, 112050],
      "last_touch_index": 920
    }
  ]
}
```

---

## 📊 Part 2: Market Sentiment S/R (Options-Based)

### Concept
Uses options positioning data to identify where institutions/traders expect price to move or stall. High open interest at a strike indicates a potential "wall" that price may struggle to cross.

### Data Source
```
Redis Keys: option:{symbol}
Fields needed:
  - strike_price (from symbol name)
  - open_interest
  - volume_24h
  - underlying_price
  - delta (for calls vs puts)
```

### Detection Methods

#### Method 1: **Max Pain Theory** ⭐ RECOMMENDED
**Concept:** Price tends to gravitate toward the strike price where the maximum number of options expire worthless (maximum pain for option buyers).

**How it works:**
1. For each strike price, calculate total value of all options that would expire ITM
2. The strike with minimum total value = Max Pain level
3. This becomes a strong S/R level

**Formula:**
```python
def calculate_max_pain(options_chain):
    strikes = get_all_strikes()

    for strike in strikes:
        call_pain = sum(
            max(0, strike - call.strike) * call.open_interest
            for call in calls if call.strike < strike
        )
        put_pain = sum(
            max(0, put.strike - strike) * put.open_interest
            for put in puts if put.strike > strike
        )
        total_pain[strike] = call_pain + put_pain

    max_pain_strike = min(total_pain, key=total_pain.get)
    return max_pain_strike
```

**Advantages:**
- ✅ Shows where market makers want price to go
- ✅ Self-fulfilling prophecy (dealers hedge toward it)
- ✅ Works well near expiration
- ✅ Accounts for real money positioning

**Disadvantages:**
- ❌ Only relevant near expiration (< 7 days)
- ❌ Assumes dealers are delta-neutral hedging
- ❌ Requires complete options chain
- ❌ Can change quickly with new trades

---

#### Method 2: **Open Interest Walls**
**How it works:**
1. Group options by strike price
2. Sum total OI for calls and puts at each strike
3. Identify strikes with exceptionally high OI (> 2 std deviations)
4. Calls with high OI = Resistance (dealers sell spot as price rises)
5. Puts with high OI = Support (dealers buy spot as price falls)

**Formula:**
```python
def find_oi_walls(options):
    oi_by_strike = {}

    for option in options:
        strike = extract_strike(option['symbol'])
        oi_by_strike[strike] = oi_by_strike.get(strike, 0) + option['open_interest']

    mean_oi = statistics.mean(oi_by_strike.values())
    std_oi = statistics.stdev(oi_by_strike.values())
    threshold = mean_oi + 2 * std_oi

    walls = [
        strike for strike, oi in oi_by_strike.items()
        if oi > threshold
    ]

    return walls
```

**Advantages:**
- ✅ Shows actual positioning (real liquidity)
- ✅ Market makers must hedge these positions
- ✅ Works for any expiration
- ✅ Clear resistance/support zones

**Disadvantages:**
- ❌ OI can be old positions (not current sentiment)
- ❌ Doesn't account for position direction (long vs short)
- ❌ Can be manipulated by large players
- ❌ Requires real-time OI data

---

#### Method 3: **Gamma Exposure (GEX)**
**How it works:**
1. Calculate total gamma exposure at each strike
2. Positive GEX (dealers long gamma) = Support (stabilizing)
3. Negative GEX (dealers short gamma) = Resistance (destabilizing)
4. Zero GEX = Potential inflection point

**Formula:**
```python
def calculate_gamma_exposure(options, underlying_price):
    gex_by_strike = {}

    for option in options:
        strike = extract_strike(option['symbol'])
        gamma = option['gamma']
        oi = option['open_interest']

        # Dealers are opposite side
        if is_call(option):
            dealer_position = -oi  # Short calls
        else:
            dealer_position = -oi  # Short puts

        gex = gamma * dealer_position * underlying_price * 0.01
        gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex

    return gex_by_strike
```

**Advantages:**
- ✅ Extremely powerful for intraday moves
- ✅ Shows how dealers will hedge (directional pressure)
- ✅ Accounts for dealer positioning
- ✅ Can predict volatility zones

**Disadvantages:**
- ❌ Complex calculation
- ❌ Requires accurate gamma data
- ❌ Changes rapidly with price
- ❌ More relevant for SPX/SPY, less for crypto

---

#### Method 4: **Volume-Weighted Strike Levels**
**How it works:**
1. Weight each strike by 24h volume (recent interest)
2. Identify strikes with unusual volume spikes
3. High volume = Active level = Potential S/R

**Formula:**
```python
def find_volume_strikes(options):
    volume_by_strike = {}

    for option in options:
        strike = extract_strike(option['symbol'])
        volume = option['volume_24h']
        volume_by_strike[strike] = volume_by_strike.get(strike, 0) + volume

    # Find strikes with volume > 2x average
    avg_volume = statistics.mean(volume_by_strike.values())

    hot_strikes = [
        strike for strike, vol in volume_by_strike.items()
        if vol > 2 * avg_volume
    ]

    return hot_strikes
```

**Advantages:**
- ✅ Shows current market interest (forward-looking)
- ✅ Reflects recent positioning changes
- ✅ Complements OI data
- ✅ Simple to calculate

**Disadvantages:**
- ❌ Volume can be one-sided (close vs open)
- ❌ Short-term signal (24h only)
- ❌ Can have false signals from hedging activity
- ❌ Doesn't show direction (buy vs sell)

---

### **Recommended Approach: Hybrid OI + Volume**

**Why:**
1. OI shows established positioning (structural levels)
2. Volume shows current interest (active levels)
3. Together they give both past and present sentiment
4. Computationally efficient
5. Clear actionable levels

**Parameters:**
```python
{
  "oi_threshold_std": 2.0,        # OI must be > 2 std dev
  "volume_threshold_multiplier": 2.0,  # Volume > 2x average
  "min_oi_absolute": 10.0,        # Minimum OI to consider (filter noise)
  "strike_clustering": 500,       # Group strikes within $500
  "expiration_filter": 30,        # Only use options expiring within 30 days
  "call_put_ratio_threshold": 0.5 # C/P ratio for directional bias
}
```

**Output Format:**
```json
{
  "symbol": "BTC-USDT",
  "timestamp": 1760611859,
  "current_price": 111587.70,
  "support_strikes": [
    {
      "strike": 110000,
      "total_oi": 1250.5,
      "put_oi": 850.2,
      "call_oi": 400.3,
      "volume_24h": 450.8,
      "strength": 0.88,
      "type": "put_wall",
      "expiration_date": "2025-10-24",
      "days_to_expiry": 8
    }
  ],
  "resistance_strikes": [
    {
      "strike": 115000,
      "total_oi": 2100.8,
      "call_oi": 1800.5,
      "put_oi": 300.3,
      "volume_24h": 680.2,
      "strength": 0.95,
      "type": "call_wall",
      "expiration_date": "2025-10-24",
      "days_to_expiry": 8
    }
  ],
  "max_pain": 112000,
  "gamma_flip_level": 111500
}
```

---

## 🔄 Comparison: Technical vs Market Sentiment

| Aspect | Technical S/R | Market Sentiment S/R |
|--------|---------------|----------------------|
| **Data Source** | Price history (OHLCV) | Options positioning (OI/Volume) |
| **Timeframe** | Past price action | Current + future expectations |
| **Accuracy** | High (proven levels) | Medium-High (probabilistic) |
| **Speed** | Fast (< 100ms) | Medium (< 500ms with 1,928 options) |
| **Stability** | Stable (changes slowly) | Dynamic (changes with new trades) |
| **Predictive** | Low (backward-looking) | High (forward-looking) |
| **Manipulation** | Hard to manipulate | Can be manipulated (fake walls) |
| **Best For** | Swing trading, clear levels | Institutional positioning, hedging |
| **Drawback** | Lagging | Can change suddenly |
| **Reliability** | Very reliable | Reliable near expiration |

---

## ⚖️ Advantages & Disadvantages

### Technical S/R (Kline-Based)

#### ✅ Advantages:
1. **Proven Methodology** - Used for decades across all markets
2. **Simple to Understand** - Clear visual representation
3. **Fast Computation** - Works on large datasets quickly
4. **Stable Levels** - Don't change rapidly
5. **Works Offline** - Only needs price data
6. **Good for All Timeframes** - Scalable from 1m to daily
7. **No External Dependencies** - Self-contained algorithm

#### ❌ Disadvantages:
1. **Lagging Indicator** - Based on past price action
2. **No Future Insight** - Doesn't show where institutions are positioned
3. **Subjective Parameters** - Window size, threshold need tuning
4. **False Breakouts** - Can give wrong signals in trending markets
5. **Doesn't Account for Volume** - All candles weighted equally (can fix with volume weighting)
6. **Overfitting Risk** - Too many parameters can optimize for past, not future

---

### Market Sentiment S/R (Options-Based)

#### ✅ Advantages:
1. **Forward-Looking** - Shows where traders expect price to go
2. **Real Money Positions** - Reflects actual institutional positioning
3. **Market Maker Hedging** - Dealers must hedge, creating real support/resistance
4. **Psychological Levels** - Round numbers with high OI become self-fulfilling
5. **Detects Manipulation** - Can see when walls appear/disappear
6. **Complements Technical** - Different dimension of analysis
7. **Accounts for Derivatives** - Crypto options market is growing in influence

#### ❌ Disadvantages:
1. **Requires Options Data** - Not available for all assets/timeframes
2. **More Complex** - Harder to understand and explain
3. **Can Change Rapidly** - Large trades can move OI quickly
4. **Expiration Dependent** - Less relevant far from expiration
5. **Slower Computation** - Need to process 1,928+ options
6. **Data Quality** - Requires accurate, real-time OI/volume
7. **Market Size** - Less reliable in illiquid options markets

---

## 🎯 Recommended Strategy: Hybrid Approach

### Why Combine Both?

**Technical S/R provides:**
- Historical context (where price has bounced before)
- Clear visual levels for charts
- Stable baseline for trading decisions

**Market Sentiment S/R provides:**
- Current institutional positioning
- Future price expectations
- Dynamic levels that adapt quickly

**Together they create:**
- High-confidence levels (when both agree)
- Early warning signals (when sentiment shifts before price)
- Comprehensive market view (past behavior + future expectations)

---

### Implementation Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   S/R DETECTION SYSTEM                  │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│   TECHNICAL DETECTOR  │       │  SENTIMENT DETECTOR   │
│   (Kline-based)       │       │  (Options-based)      │
└───────────────────────┘       └───────────────────────┘
            │                               │
            │ Input: 1,000 candles          │ Input: 1,928 options
            │ Method: Swing high/low        │ Method: OI walls + Volume
            │ Speed: <100ms                 │ Speed: <500ms
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│  TECHNICAL S/R LEVELS │       │  SENTIMENT S/R LEVELS │
│  - Support: 5-8       │       │  - Support strikes: 3-5│
│  - Resistance: 5-8    │       │  - Resistance strikes: 3-5│
│  - Strength scores    │       │  - OI/Volume data     │
└───────────────────────┘       └───────────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
                ┌───────────────────────┐
                │   LEVEL AGGREGATOR    │
                │   - Merge nearby      │
                │   - Assign confidence │
                │   - Rank by strength  │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   UNIFIED S/R OUTPUT  │
                │   - Combined levels   │
                │   - Type (tech/sent)  │
                │   - Confidence score  │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   REDIS STORAGE       │
                │   Key: sr:{interval}. │
                │        {symbol}       │
                │   TTL: 5 minutes      │
                └───────────────────────┘
```

---

## 📋 Implementation Roadmap

### Phase 1: Technical S/R ⭐ START HERE
**Time Estimate:** 2-3 hours

**Files to Create:**
1. `sr_detector_technical.py` - Core detection logic
2. `sr_config_technical.json` - Parameters
3. `test_technical_sr.py` - Unit tests

**Steps:**
1. Implement swing high/low detection
2. Implement level clustering
3. Calculate strength scores
4. Test with live kline data
5. Store results in Redis

**Output:**
- Working technical S/R detector
- Verified against manual chart analysis
- Performance benchmarks

---

### Phase 2: Market Sentiment S/R
**Time Estimate:** 3-4 hours

**Files to Create:**
1. `sr_detector_sentiment.py` - OI/Volume analysis
2. `sr_config_sentiment.json` - Parameters
3. `test_sentiment_sr.py` - Unit tests

**Steps:**
1. Parse strike prices from option symbols
2. Calculate OI walls (calls vs puts)
3. Identify volume hotspots
4. Calculate max pain (optional)
5. Test with live options data
6. Store results in Redis

**Output:**
- Working sentiment S/R detector
- Strike-level analysis
- Performance benchmarks

---

### Phase 3: Hybrid System
**Time Estimate:** 2-3 hours

**Files to Create:**
1. `sr_detector_hybrid.py` - Combines both approaches
2. `sr_config_hybrid.json` - Combined parameters
3. `test_hybrid_sr.py` - Integration tests

**Steps:**
1. Merge technical + sentiment levels
2. Assign confidence scores based on agreement
3. Implement level ranking algorithm
4. Create unified output format
5. Add visualization helpers
6. Test end-to-end

**Output:**
- Complete S/R system
- High-confidence levels
- Trading signals

---

### Phase 4: Automation & Monitoring
**Time Estimate:** 1-2 hours

**Files to Create:**
1. `sr_scheduler.py` - Auto-update every N minutes
2. `sr_dashboard.py` - Simple monitoring script

**Steps:**
1. Set up periodic detection (every 5 min)
2. Add logging and metrics
3. Create simple query interface
4. Add alerting for level breaks
5. Performance monitoring

---

## 🔧 Technical Specifications

### Redis Storage Schema

#### Technical S/R:
```
Key: sr:technical:{interval}.{symbol}
TTL: 300 seconds (5 minutes)
Format: JSON string
```

#### Sentiment S/R:
```
Key: sr:sentiment:{symbol}
TTL: 300 seconds
Format: JSON string
```

#### Hybrid S/R:
```
Key: sr:hybrid:{interval}.{symbol}
TTL: 300 seconds
Format: JSON string
```

### Update Frequency

| Type | Update Interval | Reason |
|------|----------------|--------|
| Technical | Every 1-5 minutes | New candles confirm |
| Sentiment | Every 1 minute | OI/Volume changes frequently |
| Hybrid | Every 1-5 minutes | Combines both |

### Performance Requirements

| Metric | Target | Max Acceptable |
|--------|--------|----------------|
| Technical Detection | < 100ms | < 200ms |
| Sentiment Detection | < 500ms | < 1000ms |
| Hybrid Merge | < 50ms | < 100ms |
| Total End-to-End | < 650ms | < 1300ms |

---

## 📊 Expected Output Examples

### Technical S/R for BTCUSDT (1m):
```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "timestamp": 1760611859,
  "current_price": 111587.70,
  "support": [
    {"level": 111200, "strength": 0.85, "touches": 5},
    {"level": 110800, "strength": 0.72, "touches": 3}
  ],
  "resistance": [
    {"level": 112000, "strength": 0.90, "touches": 6}
  ]
}
```

### Sentiment S/R for BTC:
```json
{
  "symbol": "BTC",
  "timestamp": 1760611859,
  "current_price": 111587.70,
  "support_strikes": [
    {"strike": 110000, "total_oi": 1250.5, "type": "put_wall", "strength": 0.88}
  ],
  "resistance_strikes": [
    {"strike": 115000, "total_oi": 2100.8, "type": "call_wall", "strength": 0.95}
  ],
  "max_pain": 112000
}
```

### Hybrid S/R:
```json
{
  "symbol": "BTCUSDT",
  "interval": "1m",
  "timestamp": 1760611859,
  "current_price": 111587.70,
  "levels": [
    {
      "price": 112000,
      "type": "resistance",
      "confidence": 0.95,
      "sources": ["technical", "sentiment_max_pain"],
      "details": {
        "technical_strength": 0.90,
        "technical_touches": 6,
        "sentiment_type": "max_pain"
      }
    },
    {
      "price": 111200,
      "type": "support",
      "confidence": 0.85,
      "sources": ["technical"],
      "details": {
        "technical_strength": 0.85,
        "technical_touches": 5
      }
    },
    {
      "price": 110000,
      "type": "support",
      "confidence": 0.88,
      "sources": ["sentiment"],
      "details": {
        "sentiment_strike": 110000,
        "sentiment_oi": 1250.5,
        "sentiment_type": "put_wall"
      }
    }
  ]
}
```

---

## 🎯 Success Metrics

### For Technical S/R:
- ✅ Correctly identifies 80%+ of visual S/R levels on chart
- ✅ Processes 1,000 candles in < 100ms
- ✅ Produces 10-15 meaningful levels per symbol
- ✅ Strength scores correlate with actual bounces

### For Sentiment S/R:
- ✅ Identifies major OI walls visible on options flow
- ✅ Max pain within 5% of actual expiration price
- ✅ Processes 1,928 options in < 500ms
- ✅ Detects 5-10 significant strike levels

### For Hybrid System:
- ✅ High-confidence levels (both agree) have 90%+ accuracy
- ✅ End-to-end latency < 1 second
- ✅ False positive rate < 10%
- ✅ Useful for both scalping (1m) and swing trading (60m, daily)

---

## 🚨 Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Overfitting to historical data** | High | Validate on out-of-sample data, use simple algorithms |
| **Options data incomplete** | Medium | Filter by minimum OI, use multiple expirations |
| **Computation too slow** | Low | Profile code, optimize hot paths, cache results |
| **False signals in choppy markets** | Medium | Add volatility filter, require multiple confirmations |
| **Level clustering issues** | Low | Tune threshold parameter, use dynamic clustering |
| **Redis memory usage** | Low | Set proper TTLs, limit stored levels |

---

## ✅ Next Steps - DECISION REQUIRED

### Option A: Sequential Implementation (RECOMMENDED)
1. Build Technical S/R first (simpler, faster)
2. Test and validate thoroughly
3. Then add Sentiment S/R
4. Finally combine into hybrid

**Pros:** Lower risk, easier debugging, faster initial results
**Cons:** Longer total time, sentiment detection comes later

### Option B: Parallel Implementation
1. Build both detectors simultaneously
2. Test independently
3. Merge at the end

**Pros:** Faster overall completion
**Cons:** Higher complexity, harder to debug

### Option C: Hybrid First
1. Build basic versions of both
2. Combine immediately
3. Iterate on accuracy

**Pros:** See final vision quickly
**Cons:** Hard to isolate issues, may build on shaky foundation

---

## 🎯 RECOMMENDED: Option A - Sequential

**Start with Phase 1:**
- Create `sr_detector_technical.py`
- Create `sr_config_technical.json`
- Test with 1.BTCUSDT data
- Validate accuracy
- Then move to sentiment

**This document is ready for implementation!**

---

**END OF PLAN**
**Status:** 📋 Planning Complete
**Next:** Choose implementation approach and begin coding
