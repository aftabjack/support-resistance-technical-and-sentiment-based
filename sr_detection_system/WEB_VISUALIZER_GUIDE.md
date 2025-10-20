# Web Visualizer Guide

**Real-time S/R visualization in your browser** 🌐

---

## 🚀 Quick Access

### URL
```
http://localhost:8080
```

**Just open this in your browser!** The web interface is already running.

---

## ✨ Features

### 📊 Interactive Chart
- Real-time price chart with S/R levels overlaid
- Resistance levels shown in **red**
- Support levels shown in **green**
- Current price highlighted in **blue**

### 📈 Info Cards
- **Current Price** - Live price with last update time
- **Nearest Resistance** - Closest resistance above current price
- **Nearest Support** - Closest support below current price
- **Processing Time** - How fast S/R was calculated

### 📋 Level Lists
- **All Resistance Levels** - Sorted by distance from current price
- **All Support Levels** - Sorted by distance from current price
- Each level shows:
  - Price
  - Distance from current price (%)
  - Detection method (swing/round number)
  - Strength score
  - Number of touches

### 🎨 Visual Indicators
- **Strong** levels (strength ≥ 0.8) - Green badge
- **Moderate** levels (strength 0.5-0.8) - Yellow badge
- **Weak** levels (strength < 0.5) - Red badge

---

## 🎯 How to Use

### 1. Select Symbol
Choose from:
- BTCUSDT
- ETHUSDT
- SOLUSDT

### 2. Select Timeframe
Choose from:
- 1 min
- 5 min
- 15 min
- 1 hour
- 4 hour
- Daily

### 3. Click "Load Data"
The chart and levels will update automatically.

### 4. Auto-Refresh
The page auto-refreshes every 60 seconds to show latest data.

---

## 📊 Example View

When you load BTCUSDT 15min, you'll see:

**Chart:**
```
Current Price: $105,593.60
Nearest Resistance: $106,104.67 (+0.48%)
Nearest Support: $100,962.16 (-4.39%)
Processing Time: 17.30ms
```

**Resistance Levels:**
```
$106,104.67  +0.48%   round_number   Strength: 0.88   120 touches
$107,149.47  +1.47%   round_number   Strength: 0.79   100 touches
$108,306.78  +2.57%   swing_resi     Strength: 1.00   528 touches
...
```

**Support Levels:**
```
$105,401.57  -0.18%   round_number   Strength: 0.87   51 touches
$104,784.14  -0.77%   round_number   Strength: 0.89   120 touches
$103,908.57  -1.60%   round_number   Strength: 0.81   43 touches
...
```

---

## 🔧 Docker Setup

The web visualizer runs as part of your Docker Compose stack:

### Check Status
```bash
docker-compose ps web-visualizer
```

### View Logs
```bash
docker-compose logs -f web-visualizer
```

### Restart
```bash
docker-compose restart web-visualizer
```

### Access from Remote
If deploying to a server, access via:
```
http://YOUR_SERVER_IP:8080
```

---

## 🌐 API Endpoints

The web visualizer also provides REST API endpoints:

### Get S/R Data
```bash
# Get S/R for BTCUSDT 15min
curl http://localhost:8080/api/sr/BTCUSDT/15 | jq .

# Get S/R for ETHUSDT 60min
curl http://localhost:8080/api/sr/ETHUSDT/60 | jq .
```

**Response:**
```json
{
  "resistance": [...],
  "support": [...],
  "timestamp": 1760705024.92,
  "timestamp_readable": "2025-10-17 18:13:44",
  "age_seconds": 45,
  "metadata": {
    "symbol": "BTCUSDT",
    "interval": "15",
    "current_price": 105593.6,
    "processing_time_ms": 17.3
  }
}
```

### List Available Data
```bash
curl http://localhost:8080/api/list | jq .
```

**Response:**
```json
{
  "BTCUSDT": ["1", "5", "15", "60", "240", "D"],
  "ETHUSDT": ["1", "5", "15", "60", "240", "D"],
  "SOLUSDT": ["1", "5", "15", "60", "240", "D"]
}
```

### Health Check
```bash
curl http://localhost:8080/health | jq .
```

**Response:**
```json
{
  "status": "healthy",
  "redis": "connected",
  "timestamp": "2025-10-17T18:15:30.123456"
}
```

---

## 🎨 UI Features

### Responsive Design
- Works on desktop, tablet, and mobile
- Adapts to screen size automatically

### Color Coding
- **Resistance** - Red background, red text
- **Support** - Green background, green text
- **Current Price** - Blue

### Hover Effects
- Level items highlight on hover
- Shows more details interactively

### Real-time Updates
- Auto-refreshes every 60 seconds
- Shows "Last Updated" timestamp
- Displays data age in seconds

---

## 🔒 Security Considerations

### Production Deployment

If deploying to production, consider:

1. **Reverse Proxy (Nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

2. **HTTPS/SSL**
Use Let's Encrypt for free SSL certificates

3. **Authentication**
Add basic auth or OAuth if needed

4. **Firewall**
Only expose port 8080 to trusted IPs

---

## 🚀 Advanced Usage

### Embed in Your App
```html
<iframe src="http://localhost:8080" width="100%" height="800px"></iframe>
```

### Query from JavaScript
```javascript
fetch('http://localhost:8080/api/sr/BTCUSDT/15')
  .then(response => response.json())
  .then(data => {
    console.log('Current price:', data.metadata.current_price);
    console.log('Nearest resistance:', data.resistance[0]);
    console.log('Nearest support:', data.support[0]);
  });
```

### Query from Python
```python
import requests

response = requests.get('http://localhost:8080/api/sr/BTCUSDT/15')
data = response.json()

print(f"Current Price: ${data['metadata']['current_price']:,.2f}")
print(f"Nearest Resistance: ${data['resistance'][0]['price']:,.2f}")
print(f"Nearest Support: ${data['support'][0]['price']:,.2f}")
```

---

## 🆘 Troubleshooting

### Cannot Access Web Interface

**Check if container is running:**
```bash
docker-compose ps web-visualizer
```

**Check logs:**
```bash
docker-compose logs web-visualizer
```

**Restart:**
```bash
docker-compose restart web-visualizer
```

### No Data Displayed

**Check Redis connection:**
```bash
redis-cli ping
```

**Check if S/R data exists:**
```bash
redis-cli KEYS "sr:technical:basic:*"
```

**Check API endpoint:**
```bash
curl http://localhost:8080/api/sr/BTCUSDT/15
```

### Port Already in Use

If port 8080 is already in use, change it in `docker-compose.yml`:

```yaml
ports:
  - "8081:8080"  # Change 8081 to any available port
```

Then access at: `http://localhost:8081`

---

## 📊 Performance

- **Chart rendering**: ~100ms
- **Data loading**: 10-50ms
- **Auto-refresh**: Every 60 seconds
- **Concurrent users**: 100+ (depending on server)

---

## 🎯 Next Steps

### Phase 8 Enhancements (Planned)
- Real-time WebSocket updates (no page refresh needed)
- Historical S/R tracking
- Alert system for price near S/R levels
- Export S/R data to CSV/JSON
- Multiple symbol comparison
- Custom indicator overlays

---

## 💡 Tips

1. **Use 15min or 60min** for day trading
2. **Check multiple timeframes** - confluence of S/R levels is powerful
3. **Strong levels (0.8+)** are more reliable
4. **High touches (100+)** indicate significant levels
5. **Nearest levels** matter most for immediate price action

---

## 📖 Related Documentation

- `HOW_TO_VIEW_SR.md` - Other ways to access S/R data
- `DEPLOYMENT_GUIDE.md` - Full Docker deployment guide
- `START_HERE.md` - Project overview

---

**Your web visualizer is live at http://localhost:8080** 🚀

Enjoy real-time S/R visualization!
