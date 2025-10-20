# S/R Detection System

Real-time Support & Resistance detection system for cryptocurrency trading using kline and options data.

## 🎯 Features

- **Technical S/R Detection** - Interval-specific levels from kline data
  - Swing High/Low detection
  - Round Number detection
  - Volume Profile (Phase 2)

- **Sentiment S/R Detection** - Uniform levels from options data (Coming Soon)
  - OI Walls
  - Volume Hotspots
  - Max Pain calculation

- **Real-time Data Collection**
  - Kline/candlestick streaming (1m, 5m, 15m, 60m, 240m, Daily)
  - Options data tracking (BTC, ETH, SOL)

- **Redis Storage** - Fast in-memory caching
- **CLI Interface** - Easy command-line usage
- **Docker Support** - Containerized deployment

---

## 📋 Quick Start

### Prerequisites

- Python 3.8+
- Redis server
- Bybit API access (no authentication required for public data)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd sr_detection_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start Redis**
```bash
# macOS (with Homebrew)
brew services start redis

# Linux
sudo systemctl start redis

# Or run manually
redis-server
```

4. **Configure symbols and intervals**
Edit `config/config.json` to set your trading pairs and timeframes.

---

## 🚀 Running the System

### Option 1: Manual Start (Development)

**Step 1: Start data collection**
```bash
# Terminal 1 - Kline streaming
python src/bybit_kline_stream_ultra.py

# Terminal 2 - Options tracking
python src/bybit_options_tracker.py
```

**Step 2: Generate S/R data**
```bash
# Generate S/R for all symbols and intervals
python src/sr_core/sr_detector_technical.py --all --mode basic --save

# Or for specific symbol/interval
python src/sr_core/sr_detector_technical.py --symbol BTCUSDT --interval 15 --mode basic --save
```

---

### Option 2: Docker Compose (Production)

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

---

## 📊 Usage Examples

### Query S/R Data from Redis

```bash
# List all S/R keys
redis-cli KEYS "sr:technical:basic:*"

# Get BTCUSDT 15min S/R
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq .

# Get top 3 resistance levels
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.resistance[:3]'

# Get top 3 support levels
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.support[:3]'

# Get metadata (processing time, current price, etc.)
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.metadata'
```

### Python API Usage

```python
from src.sr_core.sr_utils import RedisHelper

# Initialize Redis helper
redis_helper = RedisHelper()

# Get S/R result
result = redis_helper.get_sr_result("sr:technical:basic:15.BTCUSDT")

print(f"Current Price: ${result['metadata']['current_price']:,.2f}")
print(f"\nTop Resistance:")
for level in result['resistance'][:3]:
    print(f"  ${level['price']:,.2f} - {level['method']} - Strength: {level['strength']}")

print(f"\nTop Support:")
for level in result['support'][:3]:
    print(f"  ${level['price']:,.2f} - {level['method']} - Strength: {level['strength']}")
```

---

## 🗂️ Project Structure

```
sr_detection_system/
├── src/
│   ├── bybit_kline_stream_ultra.py    # Kline data collection
│   ├── bybit_options_tracker.py       # Options data collection
│   ├── sr_core/
│   │   ├── __init__.py
│   │   ├── sr_utils.py                # Redis helpers & utilities
│   │   └── sr_detector_technical.py   # Technical S/R detector
│   └── sr_methods_technical/
│       ├── __init__.py
│       ├── swing_high_low.py          # Swing detection
│       └── round_numbers.py           # Round number detection
│
├── config/
│   ├── config.json                    # Data collection config
│   └── sr_config_technical.json       # S/R detection config
│
├── scripts/
│   ├── start_all.sh                   # Start all services
│   └── stop_all.sh                    # Stop all services
│
├── docs/
│   ├── PHASE1_COMPLETION_REPORT.md    # Phase 1 details
│   ├── SYSTEM_STATUS.md               # Current status
│   └── *.md                           # Other documentation
│
├── logs/                              # Log files
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker image
├── docker-compose.yml                 # Docker orchestration
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

---

## 📈 Redis Schema

### Kline Data
```
Pattern: {interval}.{symbol}
Example: 15.BTCUSDT (15-minute candles for BTCUSDT)

Data: Sorted set of JSON candles
  {"o": "111500", "h": "111600", "l": "111400", "c": "111550", "v": "125.5"}

Count: 18 keys (6 intervals × 3 symbols)
Limit: 1,000 candles per key
```

### Options Data
```
Pattern: option:{symbol}-{strike}-{type}-{expiry}
Example: option:BTC-120000-C-25OCT24

Data: Hash with OI, volume, Greeks
  {
    "symbol": "BTC-120000-C-25OCT24",
    "strike_price": "120000",
    "option_type": "Call",
    "open_interest": "2450.5",
    "volume_24h": "850.2",
    "delta": "0.65",
    "gamma": "0.0001",
    ...
  }

Count: 1,360+ keys (varies by market)
```

### S/R Results
```
Pattern: sr:technical:{mode}:{interval}.{symbol}
Example: sr:technical:basic:15.BTCUSDT

Data: JSON with resistance, support, metadata
  {
    "resistance": [
      {
        "price": 111702.47,
        "strength": 1.0,
        "touches": 2161,
        "method": "swing_resi"
      },
      ...
    ],
    "support": [...],
    "metadata": {
      "symbol": "BTCUSDT",
      "interval": "15",
      "processing_time_ms": 42.86,
      "current_price": 111110.0
    }
  }

Count: 18 keys (6 intervals × 3 symbols) for BASIC mode
TTL: 300 seconds (5 minutes)
```

---

## ⚙️ Configuration

### Data Collection (`config/config.json`)

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "intervals": ["1", "5", "15", "60", "240", "D"]
}
```

### S/R Detection (`config/sr_config_technical.json`)

```json
{
  "mode": "basic",
  "intervals": ["1", "5", "15", "60", "240", "D"],
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "candles_limit": 1000,

  "methods": {
    "basic": {
      "swing_high_low": {
        "enabled": true,
        "lookback": 5,
        "min_touches": 2
      },
      "round_numbers": {
        "enabled": true,
        "max_distance_pct": 0.05
      }
    }
  },

  "output": {
    "merge_threshold": 0.005,
    "max_resistance": 10,
    "max_support": 10,
    "ttl_seconds": 300
  }
}
```

---

## 🔧 CLI Commands

### S/R Detection

```bash
# Detect S/R for specific symbol/interval
python src/sr_core/sr_detector_technical.py \
  --symbol BTCUSDT \
  --interval 15 \
  --mode basic \
  --save

# Process all symbols and intervals
python src/sr_core/sr_detector_technical.py \
  --all \
  --mode basic \
  --save

# Use custom config
python src/sr_core/sr_detector_technical.py \
  --all \
  --config config/sr_config_technical.json \
  --save

# View output without saving
python src/sr_core/sr_detector_technical.py \
  --symbol BTCUSDT \
  --interval 15 \
  --mode basic
```

### Test Utilities

```bash
# Test Redis connection and data
python src/sr_core/sr_utils.py

# Test swing detection
python -m src.sr_methods_technical.swing_high_low

# Test round numbers
python -m src.sr_methods_technical.round_numbers
```

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t sr-detection-system .

# Run container
docker run -d \
  --name sr-system \
  --network host \
  sr-detection-system

# View logs
docker logs -f sr-system

# Stop container
docker stop sr-system
```

### Docker Compose (Recommended)

```bash
# Start all services (Redis + Data Collection + S/R Detection)
docker-compose up -d

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart kline-stream

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 📊 Performance

### Current Performance (Phase 1 - BASIC Mode)

| Symbol | Avg Processing Time | Target | Status |
|--------|---------------------|--------|--------|
| BTCUSDT | 47ms | <100ms | ✅ 2x faster |
| ETHUSDT | 28ms | <100ms | ✅ 3.5x faster |
| SOLUSDT | 22ms | <100ms | ✅ 4.5x faster |
| **Overall** | **33ms** | **<100ms** | ✅ **3x faster** |

**Total for all 18 combinations:** ~600ms sequential, ~60ms parallel (estimated)

---

## 🛣️ Roadmap

### ✅ Phase 1: Technical S/R (BASIC) - COMPLETED
- Swing High/Low detection
- Round Number detection
- All 18 combinations (6 intervals × 3 symbols)
- Average 33ms processing time

### 🔄 Phase 2: Technical S/R (MEDIUM) - In Progress
- Volume Profile detection
- Point of Control (POC)
- Value Area High/Low
- Target: <200ms

### 📅 Phase 3: Sentiment S/R (BASIC) - Planned
- OI Walls detection
- Volume Hotspots
- Based on options data
- Target: <150ms per symbol

### 📅 Phase 4: Sentiment S/R (MEDIUM) - Planned
- Max Pain calculation
- Target: <1,150ms per symbol

### 📅 Phase 5: Combined System - Planned
- Merge Technical + Sentiment
- High-confidence zones
- Query API

### 📅 Phase 6: HIGH Modes - Optional
- All 7 technical methods
- All 7 sentiment methods

### 📅 Phase 7: Automation - Planned
- Automatic updates
- Interval-triggered (technical)
- Time-triggered (sentiment)

### 📅 Phase 8: Real-Time Visualizer - Planned
- FastAPI backend
- WebSocket real-time updates
- Web dashboard
- Nearest levels display

---

## 🧪 Testing

```bash
# Test Redis connection
python src/sr_core/sr_utils.py

# Test individual methods
python -m src.sr_methods_technical.swing_high_low
python -m src.sr_methods_technical.round_numbers

# Test full detection
python src/sr_core/sr_detector_technical.py --symbol BTCUSDT --interval 15 --mode basic
```

---

## 🐛 Troubleshooting

### Redis Connection Failed
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
redis-server
```

### No Kline Data
```bash
# Check if kline stream is running
ps aux | grep bybit_kline

# Check Redis keys
redis-cli KEYS "*BTCUSDT"

# Restart kline stream
python src/bybit_kline_stream_ultra.py
```

### No Options Data
```bash
# Check options tracker
ps aux | grep bybit_options

# Check Redis
redis-cli KEYS "option:BTC-*" | wc -l

# Restart options tracker
python src/bybit_options_tracker.py
```

### Import Errors
```bash
# Run from project root
cd sr_detection_system

# Use python -m for modules
python -m src.sr_core.sr_detector_technical --all --mode basic --save
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

## 🙏 Acknowledgments

- Bybit API for real-time data
- Redis for high-performance caching
- Python community for excellent libraries

---

**Built with ❤️ for crypto traders**
