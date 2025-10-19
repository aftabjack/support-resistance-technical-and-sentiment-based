# Live Support/Resistance Dashboard 📊

Real-time crypto support and resistance level detection and visualization system using Bybit options and kline data.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)

## 🎯 Features

- **Live Data Collection**
  - Real-time kline (candlestick) data streaming from Bybit
  - Live options market data tracking (BTC, ETH, SOL)
  - WebSocket-based continuous data updates

- **Dual S/R Detection System**
  - **Technical S/R**: Swing high/low, round numbers (interval-based: 1min, 5min, 15min, 1hr, 4hr, Daily)
  - **Sentiment S/R**: Options open interest walls (interval-independent)

- **Interactive Web Dashboard**
  - Side-by-side technical and sentiment S/R visualization
  - Real-time price updates
  - Combined chart showing all S/R levels
  - Multi-symbol support (BTCUSDT, ETHUSDT, SOLUSDT)
  - Auto-refresh every 60 seconds

## 📸 Screenshots

### Live Dashboard
The dashboard displays two panels:
- **Left Panel**: Technical S/R based on selected timeframe
- **Right Panel**: Sentiment S/R from options market (OI walls)

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Live S/R Dashboard                                      │
├─────────────────────────────────────────────────────────────┤
│  Symbol: [BTCUSDT ▼]  Interval: [15 min ▼]  [🔄 Refresh]  │
├─────────────────────────────────────────────────────────────┤
│  Current Price: $111,110.00                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─── Technical S/R (15 min) ─┬─── Sentiment S/R ────┐    │
│  │  📈 Resistance              │  📈 Resistance        │    │
│  │  ├ $113,500 (+2.15%)       │  ├ $130,000 (+16.7%) │    │
│  │  │  Swing High • 5 touches │  │  OI Wall • Put OI  │    │
│  │  └ $112,000 (+0.80%)       │  └ $125,000 (+12.2%) │    │
│  │                              │                       │    │
│  │  📉 Support                  │  📉 Support          │    │
│  │  ├ $110,000 (-1.00%)       │  ├ $100,000 (-10.0%) │    │
│  │  └ $109,000 (-1.90%)       │  │  OI Wall • Call OI │    │
│  └─────────────────────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Redis server
- Internet connection (for Bybit API)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/live_sr_dashboard.git
cd live_sr_dashboard
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Start Redis
```bash
redis-server --daemonize yes
```

4. Run the system
```bash
./scripts/start_system.sh
```

5. Open your browser
```
http://localhost:8080/live
```

## 📁 Project Structure

```
live_sr_dashboard/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── src/
│   ├── data_collection/         # Live data collection
│   │   ├── bybit_kline_stream.py      # Kline data streaming
│   │   └── bybit_options_tracker.py   # Options data tracking
│   │
│   ├── sr_detectors/            # S/R detection engines
│   │   ├── sr_detector_technical.py   # Technical analysis
│   │   ├── sr_detector_sentiment.py   # Sentiment analysis
│   │   └── sr_utils.py                # Utilities & Redis helpers
│   │
│   ├── sr_methods/              # S/R detection methods
│   │   ├── technical/
│   │   │   ├── swing_high_low.py      # Swing points detection
│   │   │   └── round_numbers.py       # Psychological levels
│   │   └── sentiment/
│   │       └── oi_walls.py            # Open interest walls
│   │
│   └── webapp/                  # Web interface
│       ├── app.py                     # Flask application
│       └── templates/
│           └── live_dashboard.html    # Dashboard UI
│
├── scripts/                     # Utility scripts
│   ├── start_system.sh          # Start all services
│   └── stop_system.sh           # Stop all services
│
├── config/                      # Configuration files
│   └── config.json              # System configuration
│
└── logs/                        # Log files (auto-generated)
```

## 🔧 Configuration

### System Configuration

Edit `config/config.json` to customize:

```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "intervals": ["1", "5", "15", "60", "240", "D"],
  "redis": {
    "host": "localhost",
    "port": 6379
  },
  "webapp": {
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

## 📊 How It Works

### 1. Data Collection

**Kline Stream** (`bybit_kline_stream.py`)
- Connects to Bybit WebSocket
- Streams real-time candlestick data for all intervals
- Stores in Redis sorted sets with timestamps

**Options Tracker** (`bybit_options_tracker.py`)
- Fetches all BTC/ETH/SOL options contracts
- Subscribes to live ticker updates via WebSocket
- Tracks: price, IV, Greeks, open interest, volume
- Stores in Redis hashes

### 2. S/R Detection

**Technical S/R** (Interval-Based)
- Analyzes last 1000 candles for each interval
- Methods:
  - Swing High/Low: Identifies local extrema
  - Round Numbers: Psychological price levels
- Merges nearby levels
- Saves to Redis: `sr:technical:basic:{interval}.{symbol}`

**Sentiment S/R** (Options-Based)
- Analyzes options open interest distribution
- Detects OI walls (high concentration at strike prices)
- Separates call/put walls (support/resistance)
- Saves to Redis: `sr:sentiment:basic:{symbol}`

### 3. Web Dashboard

**Flask Backend** (`app.py`)
- API endpoints:
  - `/api/sr/{symbol}/{interval}` - Technical S/R
  - `/api/sentiment/{symbol}` - Sentiment S/R
  - `/health` - System health check

**Frontend** (`live_dashboard.html`)
- Fetches both technical and sentiment data
- Displays in two-column layout
- Combined Chart.js visualization
- Auto-refreshes every 60 seconds

## 🔌 API Endpoints

### Get Technical S/R
```http
GET /api/sr/{symbol}/{interval}
```

**Example Response:**
```json
{
  "resistance": [
    {
      "price": 113500.0,
      "strength": 0.85,
      "touches": 5,
      "method": "Swing High"
    }
  ],
  "support": [
    {
      "price": 110000.0,
      "strength": 0.92,
      "touches": 8,
      "method": "Round Number"
    }
  ],
  "metadata": {
    "symbol": "BTCUSDT",
    "interval": "15",
    "current_price": 111110.0,
    "candles_analyzed": 1000
  }
}
```

### Get Sentiment S/R
```http
GET /api/sentiment/{symbol}
```

**Example Response:**
```json
{
  "resistance": [
    {
      "price": 130000.0,
      "strength": 1.0,
      "oi": 335,
      "method": "OI Wall"
    }
  ],
  "support": [
    {
      "price": 100000.0,
      "strength": 1.0,
      "oi": 147,
      "method": "OI Wall"
    }
  ],
  "metadata": {
    "symbol": "BTCUSDT",
    "current_price": 111443.0,
    "options_analyzed": 682
  }
}
```

## 🛠️ Development

### Running Individual Components

**Start only kline stream:**
```bash
python src/data_collection/bybit_kline_stream.py
```

**Start only options tracker:**
```bash
python src/data_collection/bybit_options_tracker.py
```

**Generate S/R data manually:**
```bash
# Technical S/R
python src/sr_detectors/sr_detector_technical.py --all --mode basic --save

# Sentiment S/R
python src/sr_detectors/sr_detector_sentiment.py --all --mode basic
```

**Start only webapp:**
```bash
python src/webapp/app.py
```

### Testing Redis Data

```bash
# Check kline data
redis-cli zrevrange "15.BTCUSDT" 0 0

# Check options data
redis-cli keys "option:BTC-*" | head -5

# Check S/R data
redis-cli keys "sr:*"

# View specific S/R
redis-cli get "sr:technical:basic:15.BTCUSDT"
```

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server --daemonize yes
```

### No Data in Dashboard
```bash
# Check if data collection is running
ps aux | grep bybit

# Check Redis for data
redis-cli keys "*BTCUSDT"

# Regenerate S/R data
python src/sr_detectors/sr_detector_technical.py --all --mode basic --save
```

### Port 8080 Already in Use
```bash
# Find process using port 8080
lsof -ti:8080

# Kill the process
kill $(lsof -ti:8080)
```

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- [Bybit](https://www.bybit.com/) for providing excellent API and WebSocket services
- [Chart.js](https://www.chartjs.org/) for visualization
- [Flask](https://flask.palletsprojects.com/) for web framework
- [Redis](https://redis.io/) for data storage

---

**Built with ❤️ for crypto traders**
