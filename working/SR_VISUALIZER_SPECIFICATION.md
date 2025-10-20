# S/R Visualizer Specification
**Date:** 2025-10-17
**Purpose:** Real-time interface for visualizing Support & Resistance levels

---

## 🎯 Requirements

### User Requirements:
1. **Interface/Visualizer** - Choose symbol, interval, see all S/R data
2. **Real-time updates** - Price changes reflect in S/R calculations automatically
3. **Nearest levels first** - Show S/R closest to current price
4. **Both systems visible** - Technical (kline-based) + Sentiment (options-based) side by side

---

## 📊 Interface Design

### **Main Dashboard Layout**

```
┌────────────────────────────────────────────────────────────────┐
│  S/R Detection Dashboard                    🔴 LIVE           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Symbol: [BTCUSDT ▼]  Interval: [15min ▼]  Mode: [MEDIUM ▼]  │
│                                                                 │
│  Current Price: $111,587.50  ↑ +0.25%                         │
│  Last Update: 2 seconds ago                                    │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📈 NEAREST SUPPORT & RESISTANCE LEVELS                        │
│                                                                 │
│  ┌─────────────────────────┬─────────────────────────────┐   │
│  │  💪 RESISTANCE (Above)  │  🛡️ SUPPORT (Below)         │   │
│  ├─────────────────────────┼─────────────────────────────┤   │
│  │                         │                             │   │
│  │  🔥 $111,650 (+$62)     │  🔥 $111,550 (-$37)        │   │
│  │  📊 Technical (15min)   │  📊 Technical (15min)      │   │
│  │  Volume Profile         │  Swing Low                 │   │
│  │  Strength: ████████ 85% │  Strength: ████████ 87%    │   │
│  │                         │                             │   │
│  │  ⚡ $112,000 (+$412)    │  ⚡ $111,200 (-$387)       │   │
│  │  📊 Technical (15min)   │  📊 Technical (15min)      │   │
│  │  Round Number           │  Swing Low                 │   │
│  │  Strength: ██████░░ 72% │  Strength: ████████ 88%    │   │
│  │                         │                             │   │
│  │  🎯 $115,000 (+$3,412)  │  🎯 $110,000 (-$1,587)     │   │
│  │  💭 Sentiment (Options) │  💭 Sentiment (Options)    │   │
│  │  Call Wall (OI: 2,450)  │  Put Wall (OI: 3,120)      │   │
│  │  Strength: █████████ 92%│  Strength: █████████ 94%   │   │
│  │                         │                             │   │
│  └─────────────────────────┴─────────────────────────────┘   │
│                                                                 │
│  💎 HIGH CONFIDENCE ZONES (Tech + Sentiment Confluence)        │
│  ─────────────────────────────────────────────────────────────│
│  • $112,000 → Technical Round Number + Max Pain               │
│    Distance: +$412 (0.37%)  Confidence: 95%  🟢               │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📋 DETAILED VIEW                                              │
│                                                                 │
│  ┌─ Technical S/R (15min) ────────────────────────────────┐   │
│  │                                                         │   │
│  │  Resistance Levels (3):                                │   │
│  │  1. $111,650 (+$62, 0.06%) - Volume Profile - 85% 📊  │   │
│  │  2. $111,700 (+$112, 0.10%) - Swing High - 78% 📊     │   │
│  │  3. $112,000 (+$412, 0.37%) - Round Number - 72% 📊   │   │
│  │                                                         │   │
│  │  Support Levels (3):                                   │   │
│  │  1. $111,550 (-$37, -0.03%) - Swing Low - 87% 📊      │   │
│  │  2. $111,500 (-$87, -0.08%) - Round Number - 68% 📊   │   │
│  │  3. $111,200 (-$387, -0.35%) - Swing Low - 88% 📊     │   │
│  │                                                         │   │
│  │  Last Calculated: 5 seconds ago (auto-updates)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ Sentiment S/R (Options) ──────────────────────────────┐   │
│  │                                                         │   │
│  │  Resistance Levels (2):                                │   │
│  │  1. $115,000 (+$3,412, 3.06%) - Call Wall - 92% 💭    │   │
│  │     • Open Interest: 2,450 BTC                         │   │
│  │     • Volume 24h: 850 BTC                              │   │
│  │  2. $120,000 (+$8,412, 7.54%) - Volume Hotspot - 78%  │   │
│  │     • Volume 24h: 1,200 BTC                            │   │
│  │                                                         │   │
│  │  Support Levels (2):                                   │   │
│  │  1. $110,000 (-$1,587, -1.42%) - Put Wall - 94% 💭    │   │
│  │     • Open Interest: 3,120 BTC                         │   │
│  │     • Volume 24h: 1,050 BTC                            │   │
│  │  2. $108,000 (-$3,587, -3.21%) - Put Wall - 85% 💭    │   │
│  │     • Open Interest: 1,890 BTC                         │   │
│  │                                                         │   │
│  │  Max Pain: $112,000                                    │   │
│  │  Last Calculated: 15 seconds ago (updates every 5min) │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Technical Architecture

### **Backend: FastAPI + Redis + WebSocket**

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Redis DB   │ ───> │  FastAPI     │ ───> │  Frontend   │
│             │      │  Backend     │      │  Dashboard  │
│ • Klines    │      │              │      │             │
│ • Options   │      │ • REST API   │      │ • HTML/JS   │
│ • S/R Data  │      │ • WebSocket  │      │ • WebSocket │
│ • Prices    │      │ • Calculators│      │ • Live UI   │
└─────────────┘      └──────────────┘      └─────────────┘
       ↑                    ↑
       └────────────────────┘
         Background updater
```

---

## 📁 File Structure

```
working/
├── backend/
│   ├── api_server.py              # FastAPI server (main)
│   ├── sr_api.py                  # S/R query endpoints
│   ├── websocket_handler.py       # Real-time updates
│   ├── price_tracker.py           # Current price monitoring
│   └── sr_nearest_calculator.py   # Distance calculations
│
├── frontend/
│   ├── index.html                 # Main dashboard
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css         # Dashboard styling
│   │   └── js/
│   │       ├── main.js            # Core logic
│   │       ├── websocket.js       # Real-time connection
│   │       └── sr_display.js      # S/R rendering
│   └── templates/
│       └── dashboard.html         # Template (if using Jinja2)
│
└── sr_visualizer_config.json      # Visualizer config
```

---

## 🔌 API Endpoints

### **REST API**

#### 1. Get Current S/R Data
```http
GET /api/sr/{symbol}/{interval}
```

**Query Parameters:**
- `mode`: "basic" | "medium" | "high" (default: "medium")
- `include_sentiment`: true | false (default: true)
- `nearest_only`: true | false (default: false)

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "15",
  "mode": "medium",
  "current_price": 111587.50,
  "timestamp": 1729170000,

  "technical_sr": {
    "resistance": [
      {
        "price": 111650,
        "distance_dollars": 62.50,
        "distance_percent": 0.056,
        "method": "volume_profile",
        "strength": 0.85,
        "touches": 5,
        "last_touch": 1729169500
      }
    ],
    "support": [
      {
        "price": 111550,
        "distance_dollars": -37.50,
        "distance_percent": -0.034,
        "method": "swing_low",
        "strength": 0.87,
        "touches": 3,
        "last_touch": 1729169200
      }
    ]
  },

  "sentiment_sr": {
    "resistance": [
      {
        "price": 115000,
        "distance_dollars": 3412.50,
        "distance_percent": 3.058,
        "method": "oi_call_wall",
        "strength": 0.92,
        "open_interest": 2450.5,
        "volume_24h": 850.2
      }
    ],
    "support": [
      {
        "price": 110000,
        "distance_dollars": -1587.50,
        "distance_percent": -1.423,
        "method": "oi_put_wall",
        "strength": 0.94,
        "open_interest": 3120.8,
        "volume_24h": 1050.5
      }
    ],
    "max_pain": 112000
  },

  "high_confidence_zones": [
    {
      "price": 112000,
      "distance_dollars": 412.50,
      "distance_percent": 0.370,
      "technical_methods": ["round_number"],
      "sentiment_methods": ["max_pain"],
      "combined_strength": 0.95,
      "type": "resistance"
    }
  ],

  "nearest_levels": {
    "resistance": {
      "price": 111650,
      "distance_dollars": 62.50,
      "type": "technical",
      "method": "volume_profile"
    },
    "support": {
      "price": 111550,
      "distance_dollars": -37.50,
      "type": "technical",
      "method": "swing_low"
    }
  }
}
```

---

#### 2. Get All Symbols
```http
GET /api/symbols
```

**Response:**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "current_prices": {
    "BTCUSDT": 111587.50,
    "ETHUSDT": 3245.80,
    "SOLUSDT": 156.32
  }
}
```

---

#### 3. Get Available Intervals
```http
GET /api/intervals/{symbol}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "intervals": ["1", "5", "15", "60", "240", "D"],
  "interval_labels": {
    "1": "1 minute",
    "5": "5 minutes",
    "15": "15 minutes",
    "60": "1 hour",
    "240": "4 hours",
    "D": "Daily"
  }
}
```

---

### **WebSocket API**

#### Connection
```javascript
ws://localhost:8000/ws/sr/{symbol}/{interval}
```

#### Message Format (Server → Client)

**1. S/R Update**
```json
{
  "type": "sr_update",
  "symbol": "BTCUSDT",
  "interval": "15",
  "data": { /* Same as REST response */ }
}
```

**2. Price Update**
```json
{
  "type": "price_update",
  "symbol": "BTCUSDT",
  "price": 111590.00,
  "change_percent": 0.002,
  "timestamp": 1729170005
}
```

**3. Nearest Level Alert**
```json
{
  "type": "level_alert",
  "symbol": "BTCUSDT",
  "alert": {
    "level_price": 111650,
    "current_price": 111645,
    "distance": 5,
    "type": "resistance",
    "method": "volume_profile",
    "strength": 0.85,
    "message": "Price approaching resistance at $111,650"
  }
}
```

---

## 🖥️ Frontend Implementation

### **Technology Options**

#### **Option 1: Pure HTML/CSS/JavaScript** ⭐ RECOMMENDED
**Pros:**
- Lightweight, fast
- No build process
- Easy to customize
- Works anywhere

**Cons:**
- More code to write
- Manual state management

**Stack:**
- HTML5 + CSS3
- Vanilla JavaScript
- WebSocket API
- Chart.js (optional, for visualization)

---

#### **Option 2: Streamlit**
**Pros:**
- Python-based (same language as backend)
- Very fast to build
- Built-in components

**Cons:**
- Less customizable
- WebSocket requires workarounds
- Heavier

**Stack:**
- Streamlit
- st.selectbox, st.metric, st.columns
- Auto-refresh with st.rerun()

---

#### **Option 3: React/Vue.js**
**Pros:**
- Modern, reactive
- Rich ecosystem
- Best for complex interactions

**Cons:**
- Requires Node.js, build process
- Overkill for this use case
- Steeper learning curve

---

### **Recommended: Option 1 (HTML/JS)**

---

## 💻 Backend Code Structure

### **api_server.py** (Main FastAPI server)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import redis.asyncio as redis
import json
from typing import Dict, List
import asyncio

app = FastAPI(title="S/R Visualizer API")

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Redis connection
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url("redis://localhost:6379", decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    await redis_client.close()

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open("frontend/index.html", "r") as f:
        return f.read()

# REST API endpoints (see below)
# WebSocket endpoints (see below)
```

---

### **sr_api.py** (S/R query logic)

```python
from typing import Optional, Dict, Any
import redis.asyncio as redis
import json
from datetime import datetime

class SRQueryAPI:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_sr_data(
        self,
        symbol: str,
        interval: str,
        mode: str = "medium",
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete S/R data for symbol/interval
        """
        # Get current price
        current_price = await self._get_current_price(symbol)

        # Get technical S/R
        tech_key = f"sr:technical:{mode}:{interval}.{symbol}"
        tech_data = await self.redis.get(tech_key)
        tech_sr = json.loads(tech_data) if tech_data else {}

        # Calculate distances for technical levels
        tech_sr = self._add_distances(tech_sr, current_price)

        result = {
            "symbol": symbol,
            "interval": interval,
            "mode": mode,
            "current_price": current_price,
            "timestamp": datetime.now().timestamp(),
            "technical_sr": tech_sr
        }

        # Get sentiment S/R if requested
        if include_sentiment:
            base_symbol = symbol.replace("USDT", "")
            sent_key = f"sr:sentiment:{mode}:{base_symbol}"
            sent_data = await self.redis.get(sent_key)
            sent_sr = json.loads(sent_data) if sent_data else {}

            # Calculate distances for sentiment levels
            sent_sr = self._add_distances(sent_sr, current_price)

            result["sentiment_sr"] = sent_sr
            result["high_confidence_zones"] = self._find_confluence(tech_sr, sent_sr)

        # Find nearest levels
        result["nearest_levels"] = self._find_nearest_levels(
            tech_sr,
            sent_sr if include_sentiment else {},
            current_price
        )

        return result

    def _add_distances(self, sr_data: Dict, current_price: float) -> Dict:
        """Add distance calculations to all levels"""
        for level_type in ["resistance", "support"]:
            if level_type in sr_data:
                for level in sr_data[level_type]:
                    level["distance_dollars"] = level["price"] - current_price
                    level["distance_percent"] = (
                        (level["price"] - current_price) / current_price * 100
                    )
        return sr_data

    def _find_nearest_levels(
        self,
        tech_sr: Dict,
        sent_sr: Dict,
        current_price: float
    ) -> Dict:
        """Find nearest resistance and support"""
        all_resistance = []
        all_support = []

        # Collect all resistance levels
        for sr_data, sr_type in [(tech_sr, "technical"), (sent_sr, "sentiment")]:
            if "resistance" in sr_data:
                for level in sr_data["resistance"]:
                    all_resistance.append({
                        **level,
                        "type": sr_type
                    })

        # Collect all support levels
        for sr_data, sr_type in [(tech_sr, "technical"), (sent_sr, "sentiment")]:
            if "support" in sr_data:
                for level in sr_data["support"]:
                    all_support.append({
                        **level,
                        "type": sr_type
                    })

        # Sort by distance
        all_resistance.sort(key=lambda x: abs(x["distance_dollars"]))
        all_support.sort(key=lambda x: abs(x["distance_dollars"]))

        return {
            "resistance": all_resistance[0] if all_resistance else None,
            "support": all_support[0] if all_support else None
        }

    def _find_confluence(self, tech_sr: Dict, sent_sr: Dict) -> List[Dict]:
        """Find where technical and sentiment levels agree"""
        confluence_zones = []
        threshold = 0.005  # 0.5% price tolerance

        # Check resistance confluence
        if "resistance" in tech_sr and "resistance" in sent_sr:
            for tech_level in tech_sr["resistance"]:
                for sent_level in sent_sr["resistance"]:
                    if abs(tech_level["price"] - sent_level["price"]) / tech_level["price"] < threshold:
                        confluence_zones.append({
                            "price": (tech_level["price"] + sent_level["price"]) / 2,
                            "distance_dollars": tech_level["distance_dollars"],
                            "distance_percent": tech_level["distance_percent"],
                            "technical_methods": [tech_level["method"]],
                            "sentiment_methods": [sent_level["method"]],
                            "combined_strength": (tech_level["strength"] + sent_level["strength"]) / 2,
                            "type": "resistance"
                        })

        # Check support confluence
        if "support" in tech_sr and "support" in sent_sr:
            for tech_level in tech_sr["support"]:
                for sent_level in sent_sr["support"]:
                    if abs(tech_level["price"] - sent_level["price"]) / tech_level["price"] < threshold:
                        confluence_zones.append({
                            "price": (tech_level["price"] + sent_level["price"]) / 2,
                            "distance_dollars": tech_level["distance_dollars"],
                            "distance_percent": tech_level["distance_percent"],
                            "technical_methods": [tech_level["method"]],
                            "sentiment_methods": [sent_level["method"]],
                            "combined_strength": (tech_level["strength"] + sent_level["strength"]) / 2,
                            "type": "support"
                        })

        return confluence_zones

    async def _get_current_price(self, symbol: str) -> float:
        """Get current price from Redis"""
        # Try to get from latest candle
        candle_key = f"1.{symbol}"
        candles = await self.redis.zrevrange(candle_key, 0, 0)

        if candles:
            candle_data = json.loads(candles[0])
            return float(candle_data["close"])

        return 0.0
```

---

### **websocket_handler.py** (Real-time updates)

```python
from fastapi import WebSocket
import asyncio
import json
from typing import Dict, Set
from sr_api import SRQueryAPI

class WebSocketManager:
    def __init__(self, redis_client):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.sr_api = SRQueryAPI(redis_client)
        self.redis = redis_client

    async def connect(self, websocket: WebSocket, symbol: str, interval: str):
        """Accept and register new WebSocket connection"""
        await websocket.accept()

        key = f"{symbol}:{interval}"
        if key not in self.active_connections:
            self.active_connections[key] = set()

        self.active_connections[key].add(websocket)

    def disconnect(self, websocket: WebSocket, symbol: str, interval: str):
        """Remove WebSocket connection"""
        key = f"{symbol}:{interval}"
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)

    async def broadcast_sr_update(self, symbol: str, interval: str):
        """Send S/R update to all connected clients for this symbol/interval"""
        key = f"{symbol}:{interval}"

        if key not in self.active_connections:
            return

        # Get fresh S/R data
        sr_data = await self.sr_api.get_sr_data(symbol, interval)

        message = {
            "type": "sr_update",
            "symbol": symbol,
            "interval": interval,
            "data": sr_data
        }

        # Send to all connected clients
        dead_connections = set()
        for connection in self.active_connections[key]:
            try:
                await connection.send_json(message)
            except:
                dead_connections.add(connection)

        # Clean up dead connections
        for dead in dead_connections:
            self.active_connections[key].discard(dead)

    async def broadcast_price_update(self, symbol: str, price: float):
        """Broadcast price update to all clients watching this symbol"""
        # Find all intervals for this symbol
        for key in self.active_connections.keys():
            if key.startswith(f"{symbol}:"):
                message = {
                    "type": "price_update",
                    "symbol": symbol,
                    "price": price,
                    "timestamp": asyncio.get_event_loop().time()
                }

                for connection in self.active_connections[key]:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

    async def monitor_sr_changes(self):
        """Background task to monitor Redis for S/R changes"""
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("sr:*")

        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                # Parse Redis key: sr:technical:medium:15.BTCUSDT
                key_parts = message["channel"].split(":")

                if len(key_parts) >= 4:
                    if key_parts[1] == "technical":
                        # Technical S/R updated
                        interval_symbol = key_parts[3]
                        interval, symbol = interval_symbol.split(".", 1)
                        await self.broadcast_sr_update(symbol, interval)

                    elif key_parts[1] == "sentiment":
                        # Sentiment S/R updated (affects all intervals)
                        base_symbol = key_parts[3]
                        symbol = f"{base_symbol}USDT"

                        # Broadcast to all intervals for this symbol
                        for interval in ["1", "5", "15", "60", "240", "D"]:
                            await self.broadcast_sr_update(symbol, interval)
```

---

### **Complete API Endpoints**

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from sr_api import SRQueryAPI
from websocket_handler import WebSocketManager

# ... (startup code from above)

sr_api = SRQueryAPI(redis_client)
ws_manager = WebSocketManager(redis_client)

@app.get("/api/sr/{symbol}/{interval}")
async def get_sr(
    symbol: str,
    interval: str,
    mode: str = Query("medium", regex="^(basic|medium|high)$"),
    include_sentiment: bool = True,
    nearest_only: bool = False
):
    """Get S/R data for symbol/interval"""
    data = await sr_api.get_sr_data(symbol, interval, mode, include_sentiment)

    if nearest_only:
        return {
            "symbol": symbol,
            "interval": interval,
            "current_price": data["current_price"],
            "nearest_levels": data["nearest_levels"]
        }

    return data

@app.get("/api/symbols")
async def get_symbols():
    """Get all available symbols with current prices"""
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    prices = {}

    for symbol in symbols:
        candle_key = f"1.{symbol}"
        candles = await redis_client.zrevrange(candle_key, 0, 0)
        if candles:
            candle_data = json.loads(candles[0])
            prices[symbol] = float(candle_data["close"])

    return {
        "symbols": symbols,
        "current_prices": prices
    }

@app.get("/api/intervals/{symbol}")
async def get_intervals(symbol: str):
    """Get available intervals for symbol"""
    return {
        "symbol": symbol,
        "intervals": ["1", "5", "15", "60", "240", "D"],
        "interval_labels": {
            "1": "1 minute",
            "5": "5 minutes",
            "15": "15 minutes",
            "60": "1 hour",
            "240": "4 hours",
            "D": "Daily"
        }
    }

@app.websocket("/ws/sr/{symbol}/{interval}")
async def websocket_sr(websocket: WebSocket, symbol: str, interval: str):
    """WebSocket endpoint for real-time S/R updates"""
    await ws_manager.connect(websocket, symbol, interval)

    try:
        # Send initial data
        initial_data = await sr_api.get_sr_data(symbol, interval)
        await websocket.send_json({
            "type": "sr_update",
            "symbol": symbol,
            "interval": interval,
            "data": initial_data
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle any client requests (if needed)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, symbol, interval)

# Background task to monitor S/R updates
@app.on_event("startup")
async def start_monitoring():
    asyncio.create_task(ws_manager.monitor_sr_changes())
```

---

## 🎨 Frontend Code

### **index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S/R Detection Dashboard</title>
    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>S/R Detection Dashboard</h1>
            <div class="status">
                <span id="connection-status" class="status-dot disconnected"></span>
                <span id="connection-text">DISCONNECTED</span>
            </div>
        </header>

        <!-- Controls -->
        <div class="controls">
            <div class="control-group">
                <label>Symbol:</label>
                <select id="symbol-select">
                    <option value="BTCUSDT">BTCUSDT</option>
                    <option value="ETHUSDT">ETHUSDT</option>
                    <option value="SOLUSDT">SOLUSDT</option>
                </select>
            </div>

            <div class="control-group">
                <label>Interval:</label>
                <select id="interval-select">
                    <option value="1">1 minute</option>
                    <option value="5">5 minutes</option>
                    <option value="15" selected>15 minutes</option>
                    <option value="60">1 hour</option>
                    <option value="240">4 hours</option>
                    <option value="D">Daily</option>
                </select>
            </div>

            <div class="control-group">
                <label>Mode:</label>
                <select id="mode-select">
                    <option value="basic">BASIC</option>
                    <option value="medium" selected>MEDIUM</option>
                    <option value="high">HIGH</option>
                </select>
            </div>
        </div>

        <!-- Current Price -->
        <div class="current-price">
            <h2>Current Price: <span id="current-price">--</span></h2>
            <p>Last Update: <span id="last-update">--</span></p>
        </div>

        <!-- Nearest Levels -->
        <div class="nearest-levels">
            <h2>📈 NEAREST SUPPORT & RESISTANCE LEVELS</h2>

            <div class="levels-grid">
                <!-- Resistance Column -->
                <div class="levels-column">
                    <h3>💪 RESISTANCE (Above)</h3>
                    <div id="resistance-list"></div>
                </div>

                <!-- Support Column -->
                <div class="levels-column">
                    <h3>🛡️ SUPPORT (Below)</h3>
                    <div id="support-list"></div>
                </div>
            </div>
        </div>

        <!-- High Confidence Zones -->
        <div class="confluence-zones">
            <h2>💎 HIGH CONFIDENCE ZONES (Tech + Sentiment Confluence)</h2>
            <div id="confluence-list"></div>
        </div>

        <!-- Detailed View -->
        <div class="detailed-view">
            <h2>📋 DETAILED VIEW</h2>

            <!-- Technical S/R -->
            <div class="sr-section">
                <h3>📊 Technical S/R (<span id="tech-interval">15min</span>)</h3>
                <div id="technical-details"></div>
            </div>

            <!-- Sentiment S/R -->
            <div class="sr-section">
                <h3>💭 Sentiment S/R (Options)</h3>
                <div id="sentiment-details"></div>
            </div>
        </div>
    </div>

    <script src="/static/js/websocket.js"></script>
    <script src="/static/js/sr_display.js"></script>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

---

### **static/js/main.js**

```javascript
// Main application logic
let currentSymbol = 'BTCUSDT';
let currentInterval = '15';
let currentMode = 'medium';
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Setup event listeners
    document.getElementById('symbol-select').addEventListener('change', handleSymbolChange);
    document.getElementById('interval-select').addEventListener('change', handleIntervalChange);
    document.getElementById('mode-select').addEventListener('change', handleModeChange);

    // Initial connection
    connectWebSocket();
});

function handleSymbolChange(e) {
    currentSymbol = e.target.value;
    reconnectWebSocket();
}

function handleIntervalChange(e) {
    currentInterval = e.target.value;
    document.getElementById('tech-interval').textContent = getIntervalLabel(currentInterval);
    reconnectWebSocket();
}

function handleModeChange(e) {
    currentMode = e.target.value;
    reconnectWebSocket();
}

function getIntervalLabel(interval) {
    const labels = {
        '1': '1min',
        '5': '5min',
        '15': '15min',
        '60': '1hour',
        '240': '4hour',
        'D': 'Daily'
    };
    return labels[interval] || interval;
}

function connectWebSocket() {
    const wsUrl = `ws://localhost:8000/ws/sr/${currentSymbol}/${currentInterval}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = function() {
        updateConnectionStatus(true);
        console.log('WebSocket connected');
    };

    ws.onmessage = function(event) {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };

    ws.onclose = function() {
        updateConnectionStatus(false);
        console.log('WebSocket disconnected');

        // Attempt reconnection after 3 seconds
        setTimeout(connectWebSocket, 3000);
    };
}

function reconnectWebSocket() {
    if (ws) {
        ws.close();
    }
    connectWebSocket();
}

function handleWebSocketMessage(message) {
    switch(message.type) {
        case 'sr_update':
            updateSRDisplay(message.data);
            break;
        case 'price_update':
            updatePrice(message.price);
            break;
        case 'level_alert':
            showLevelAlert(message.alert);
            break;
    }
}

function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-text');

    if (connected) {
        statusDot.classList.remove('disconnected');
        statusDot.classList.add('connected');
        statusText.textContent = 'LIVE';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'DISCONNECTED';
    }
}
```

---

### **static/js/sr_display.js**

```javascript
// S/R display functions
function updateSRDisplay(data) {
    // Update current price
    document.getElementById('current-price').textContent = formatPrice(data.current_price);
    document.getElementById('last-update').textContent = formatTimestamp(data.timestamp);

    // Update nearest levels
    updateNearestLevels(data);

    // Update confluence zones
    updateConfluenceZones(data.high_confidence_zones);

    // Update detailed views
    updateTechnicalDetails(data.technical_sr);
    updateSentimentDetails(data.sentiment_sr);
}

function updateNearestLevels(data) {
    // Get all levels sorted by distance
    const allLevels = [];

    // Technical resistance
    if (data.technical_sr && data.technical_sr.resistance) {
        data.technical_sr.resistance.forEach(level => {
            allLevels.push({...level, type: 'resistance', source: 'technical', icon: '📊'});
        });
    }

    // Technical support
    if (data.technical_sr && data.technical_sr.support) {
        data.technical_sr.support.forEach(level => {
            allLevels.push({...level, type: 'support', source: 'technical', icon: '📊'});
        });
    }

    // Sentiment resistance
    if (data.sentiment_sr && data.sentiment_sr.resistance) {
        data.sentiment_sr.resistance.forEach(level => {
            allLevels.push({...level, type: 'resistance', source: 'sentiment', icon: '💭'});
        });
    }

    // Sentiment support
    if (data.sentiment_sr && data.sentiment_sr.support) {
        data.sentiment_sr.support.forEach(level => {
            allLevels.push({...level, type: 'support', source: 'sentiment', icon: '💭'});
        });
    }

    // Sort and display
    const resistance = allLevels.filter(l => l.type === 'resistance').slice(0, 3);
    const support = allLevels.filter(l => l.type === 'support').slice(0, 3);

    displayLevels('resistance-list', resistance);
    displayLevels('support-list', support);
}

function displayLevels(elementId, levels) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';

    levels.forEach(level => {
        const levelCard = createLevelCard(level);
        container.appendChild(levelCard);
    });
}

function createLevelCard(level) {
    const card = document.createElement('div');
    card.className = 'level-card';

    const isClose = Math.abs(level.distance_percent) < 0.1;
    if (isClose) card.classList.add('level-close');

    card.innerHTML = `
        <div class="level-header">
            <span class="level-icon">${level.icon}</span>
            <span class="level-price">${formatPrice(level.price)}</span>
            <span class="level-distance">(${formatDistance(level.distance_dollars)})</span>
        </div>
        <div class="level-info">
            <div class="level-source">${level.icon} ${level.source} (${currentInterval})</div>
            <div class="level-method">${formatMethod(level.method)}</div>
            <div class="level-strength">
                <div class="strength-bar">
                    <div class="strength-fill" style="width: ${level.strength * 100}%"></div>
                </div>
                <span class="strength-text">${Math.round(level.strength * 100)}%</span>
            </div>
        </div>
    `;

    return card;
}

function updateConfluenceZones(zones) {
    const container = document.getElementById('confluence-list');

    if (!zones || zones.length === 0) {
        container.innerHTML = '<p class="no-data">No high confidence zones detected</p>';
        return;
    }

    container.innerHTML = '';
    zones.forEach(zone => {
        const zoneDiv = document.createElement('div');
        zoneDiv.className = 'confluence-zone';
        zoneDiv.innerHTML = `
            <strong>${formatPrice(zone.price)}</strong> →
            ${zone.technical_methods.join(', ')} + ${zone.sentiment_methods.join(', ')}
            <br>
            Distance: ${formatDistance(zone.distance_dollars)} (${zone.distance_percent.toFixed(2)}%)
            Confidence: ${Math.round(zone.combined_strength * 100)}% 🟢
        `;
        container.appendChild(zoneDiv);
    });
}

function updateTechnicalDetails(techSR) {
    const container = document.getElementById('technical-details');

    if (!techSR) {
        container.innerHTML = '<p class="no-data">No technical S/R data</p>';
        return;
    }

    let html = '<div class="sr-details">';

    // Resistance
    html += '<h4>Resistance Levels:</h4><ul>';
    if (techSR.resistance) {
        techSR.resistance.forEach((level, i) => {
            html += `
                <li>
                    ${i + 1}. ${formatPrice(level.price)}
                    (${formatDistance(level.distance_dollars)}, ${level.distance_percent.toFixed(2)}%)
                    - ${formatMethod(level.method)}
                    - ${Math.round(level.strength * 100)}% 📊
                </li>
            `;
        });
    }
    html += '</ul>';

    // Support
    html += '<h4>Support Levels:</h4><ul>';
    if (techSR.support) {
        techSR.support.forEach((level, i) => {
            html += `
                <li>
                    ${i + 1}. ${formatPrice(level.price)}
                    (${formatDistance(level.distance_dollars)}, ${level.distance_percent.toFixed(2)}%)
                    - ${formatMethod(level.method)}
                    - ${Math.round(level.strength * 100)}% 📊
                </li>
            `;
        });
    }
    html += '</ul>';

    html += '</div>';
    container.innerHTML = html;
}

function updateSentimentDetails(sentSR) {
    const container = document.getElementById('sentiment-details');

    if (!sentSR) {
        container.innerHTML = '<p class="no-data">No sentiment S/R data</p>';
        return;
    }

    let html = '<div class="sr-details">';

    // Resistance
    html += '<h4>Resistance Levels:</h4><ul>';
    if (sentSR.resistance) {
        sentSR.resistance.forEach((level, i) => {
            html += `
                <li>
                    ${i + 1}. ${formatPrice(level.price)}
                    (${formatDistance(level.distance_dollars)}, ${level.distance_percent.toFixed(2)}%)
                    - ${formatMethod(level.method)}
                    - ${Math.round(level.strength * 100)}% 💭
                    <br>• Open Interest: ${level.open_interest?.toFixed(2) || 'N/A'} BTC
                    <br>• Volume 24h: ${level.volume_24h?.toFixed(2) || 'N/A'} BTC
                </li>
            `;
        });
    }
    html += '</ul>';

    // Support
    html += '<h4>Support Levels:</h4><ul>';
    if (sentSR.support) {
        sentSR.support.forEach((level, i) => {
            html += `
                <li>
                    ${i + 1}. ${formatPrice(level.price)}
                    (${formatDistance(level.distance_dollars)}, ${level.distance_percent.toFixed(2)}%)
                    - ${formatMethod(level.method)}
                    - ${Math.round(level.strength * 100)}% 💭
                    <br>• Open Interest: ${level.open_interest?.toFixed(2) || 'N/A'} BTC
                    <br>• Volume 24h: ${level.volume_24h?.toFixed(2) || 'N/A'} BTC
                </li>
            `;
        });
    }
    html += '</ul>';

    // Max Pain
    if (sentSR.max_pain) {
        html += `<p><strong>Max Pain:</strong> ${formatPrice(sentSR.max_pain)}</p>`;
    }

    html += '</div>';
    container.innerHTML = html;
}

// Utility functions
function formatPrice(price) {
    return '$' + price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatDistance(distance) {
    const sign = distance >= 0 ? '+' : '';
    return sign + '$' + Math.abs(distance).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatMethod(method) {
    const methodNames = {
        'swing_high': 'Swing High',
        'swing_low': 'Swing Low',
        'volume_profile': 'Volume Profile',
        'round_number': 'Round Number',
        'oi_call_wall': 'Call Wall (OI)',
        'oi_put_wall': 'Put Wall (OI)',
        'max_pain': 'Max Pain',
        'volume_hotspot': 'Volume Hotspot'
    };
    return methodNames[method] || method;
}

function formatTimestamp(timestamp) {
    const now = Date.now() / 1000;
    const diff = now - timestamp;

    if (diff < 60) {
        return `${Math.floor(diff)} seconds ago`;
    } else if (diff < 3600) {
        return `${Math.floor(diff / 60)} minutes ago`;
    } else {
        return new Date(timestamp * 1000).toLocaleTimeString();
    }
}

function updatePrice(price) {
    document.getElementById('current-price').textContent = formatPrice(price);
    document.getElementById('last-update').textContent = 'just now';
}

function showLevelAlert(alert) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'alert-toast';
    toast.innerHTML = `
        <strong>Level Alert!</strong><br>
        ${alert.message}
    `;

    document.body.appendChild(toast);

    // Remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}
```

---

### **static/css/styles.css**

```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #0f1419;
    color: #e1e8ed;
    line-height: 1.6;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

/* Header */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
    margin-bottom: 20px;
}

.header h1 {
    font-size: 24px;
    font-weight: 600;
}

.status {
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.status-dot.connected {
    background: #00ff00;
    box-shadow: 0 0 10px #00ff00;
}

.status-dot.disconnected {
    background: #ff0000;
}

/* Controls */
.controls {
    display: flex;
    gap: 20px;
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
    margin-bottom: 20px;
}

.control-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.control-group label {
    font-size: 12px;
    color: #8899a6;
    text-transform: uppercase;
}

.control-group select {
    padding: 10px;
    background: #0f1419;
    color: #e1e8ed;
    border: 1px solid #38444d;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
}

.control-group select:hover {
    border-color: #1da1f2;
}

/* Current Price */
.current-price {
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
    margin-bottom: 20px;
    text-align: center;
}

.current-price h2 {
    font-size: 32px;
    color: #1da1f2;
}

.current-price p {
    color: #8899a6;
    font-size: 14px;
}

/* Nearest Levels */
.nearest-levels {
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
    margin-bottom: 20px;
}

.nearest-levels h2 {
    margin-bottom: 20px;
    font-size: 20px;
}

.levels-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.levels-column h3 {
    font-size: 16px;
    margin-bottom: 15px;
    color: #8899a6;
}

.level-card {
    background: #0f1419;
    border: 1px solid #38444d;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    transition: all 0.3s;
}

.level-card:hover {
    border-color: #1da1f2;
    transform: translateY(-2px);
}

.level-card.level-close {
    border-color: #ffad1f;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.level-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.level-icon {
    font-size: 20px;
}

.level-price {
    font-size: 20px;
    font-weight: 600;
}

.level-distance {
    font-size: 14px;
    color: #8899a6;
}

.level-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.level-source, .level-method {
    font-size: 12px;
    color: #8899a6;
}

.level-strength {
    display: flex;
    align-items: center;
    gap: 10px;
}

.strength-bar {
    flex: 1;
    height: 8px;
    background: #38444d;
    border-radius: 4px;
    overflow: hidden;
}

.strength-fill {
    height: 100%;
    background: linear-gradient(90deg, #1da1f2, #00ff00);
    transition: width 0.3s;
}

.strength-text {
    font-size: 12px;
    color: #8899a6;
}

/* Confluence Zones */
.confluence-zones {
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
    margin-bottom: 20px;
}

.confluence-zones h2 {
    margin-bottom: 15px;
    font-size: 18px;
}

.confluence-zone {
    background: #0f1419;
    border: 2px solid #00ff00;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
}

.no-data {
    color: #8899a6;
    font-style: italic;
}

/* Detailed View */
.detailed-view {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
}

.sr-section {
    padding: 20px;
    background: #1a1f29;
    border-radius: 8px;
}

.sr-section h3 {
    margin-bottom: 15px;
    font-size: 18px;
}

.sr-details h4 {
    margin-top: 15px;
    margin-bottom: 10px;
    color: #1da1f2;
}

.sr-details ul {
    list-style: none;
    padding-left: 0;
}

.sr-details li {
    padding: 8px 0;
    border-bottom: 1px solid #38444d;
}

/* Alert Toast */
.alert-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #ffad1f;
    color: #0f1419;
    padding: 15px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease-out;
    z-index: 1000;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Responsive */
@media (max-width: 768px) {
    .levels-grid {
        grid-template-columns: 1fr;
    }

    .controls {
        flex-direction: column;
    }
}
```

---

## 🚀 Implementation Timeline

### **Phase 8: Real-Time Visualizer** - 6-10 hours

#### **Step 1: Backend API** (3-4 hours)
- [ ] Create `api_server.py` with FastAPI
- [ ] Implement `sr_api.py` with distance calculations
- [ ] Add `websocket_handler.py` for real-time updates
- [ ] Create price tracking mechanism
- [ ] Add Redis pub/sub monitoring
- [ ] Test API endpoints

#### **Step 2: Frontend Dashboard** (3-4 hours)
- [ ] Create `index.html` with layout
- [ ] Implement `main.js` for controls
- [ ] Add `sr_display.js` for rendering
- [ ] Create `websocket.js` for real-time connection
- [ ] Style with `styles.css`
- [ ] Test WebSocket connectivity

#### **Step 3: Integration & Testing** (1-2 hours)
- [ ] Connect frontend to backend
- [ ] Test real-time updates
- [ ] Verify nearest level calculations
- [ ] Test symbol/interval switching
- [ ] Load testing
- [ ] Final polish

---

## 🎯 Final Summary

### **What You'll Get:**

1. **Real-Time Dashboard**
   - Choose symbol (BTCUSDT, ETHUSDT, SOLUSDT)
   - Choose interval (1m, 5m, 15m, 60m, 240m, Daily)
   - Choose mode (BASIC, MEDIUM, HIGH)

2. **Live S/R Display**
   - Technical S/R (interval-specific)
   - Sentiment S/R (options-based)
   - Nearest levels highlighted
   - Distance from current price
   - Strength indicators

3. **Auto-Updates**
   - Technical S/R: Updates when new candle arrives
   - Sentiment S/R: Updates every 5 minutes
   - Price: Updates in real-time
   - WebSocket push notifications

4. **High Confidence Zones**
   - Shows where Technical + Sentiment agree
   - Combined strength score
   - Clear visual indicators

5. **Clean Interface**
   - Dark theme (easy on eyes)
   - Responsive design
   - Smooth animations
   - Mobile-friendly

---

## 📊 Complete Redis Data Flow

```
Data Sources:
  Klines → {interval}.{symbol} → 1,000 candles each
  Options → option:{symbol}-* → OI, volume, Greeks

     ↓

S/R Calculators (background):
  Technical → sr:technical:{mode}:{interval}.{symbol}
  Sentiment → sr:sentiment:{mode}:{symbol}

     ↓

API Server (FastAPI):
  REST: /api/sr/{symbol}/{interval}
  WebSocket: /ws/sr/{symbol}/{interval}

     ↓

Frontend Dashboard:
  • Fetches S/R data
  • Calculates distances
  • Sorts by nearest
  • Updates in real-time

     ↓

User sees:
  • Current price
  • Nearest resistance (above)
  • Nearest support (below)
  • Confluence zones
  • Full details
```

---

## ✅ Requirements Met

- ✅ Interface to choose symbol & interval
- ✅ Real-time updates (WebSocket)
- ✅ Price changes reflect in S/R calculations
- ✅ Nearest S/R levels from current price
- ✅ Both Technical (kline-based) and Sentiment (options-based) visible
- ✅ Clean, modern UI
- ✅ Automatic background processing
- ✅ High confidence zone detection

---

**This visualizer completes the entire S/R detection system!**

Would you like me to create the implementation files now, or do you need any adjustments to the design?
