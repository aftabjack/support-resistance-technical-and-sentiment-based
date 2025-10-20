# Deployment Guide - S/R Detection System

**Complete guide for deploying your S/R detection system** 🚀

---

## 📁 What You Have

Your project is now organized in a single folder: `sr_detection_system/`

### File Structure
```
sr_detection_system/
├── src/                              # All Python scripts
│   ├── bybit_kline_stream_ultra.py       # Real-time kline data collection
│   ├── bybit_options_tracker.py          # Real-time options data collection
│   ├── sr_core/
│   │   ├── __init__.py
│   │   ├── sr_utils.py                   # Redis helpers & utilities
│   │   └── sr_detector_technical.py      # Main S/R detector
│   └── sr_methods_technical/
│       ├── __init__.py
│       ├── swing_high_low.py             # Swing detection method
│       └── round_numbers.py              # Round number detection
│
├── config/
│   ├── config.json                       # Data collection config
│   └── sr_config_technical.json          # S/R detection config
│
├── scripts/
│   ├── start_all.sh                      # Start all services (local)
│   └── stop_all.sh                       # Stop all services (local)
│
├── docs/                                # Full documentation (15 files)
│   ├── COMPLETE_SR_SPECIFICATION.md
│   ├── PHASE1_COMPLETION_REPORT.md
│   ├── SYSTEM_STATUS.md
│   └── ... (and more)
│
├── logs/                                # Log files (created on first run)
│
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Docker image definition
├── docker-compose.yml                   # Docker orchestration
├── .gitignore                          # Git ignore rules
├── README.md                           # Full documentation
├── QUICKSTART.md                       # Quick start guide
└── DEPLOYMENT_GUIDE.md                 # This file
```

---

## 🎯 Deployment Options

You have **3 ways** to run this system:

### 1. **Local Development** (Recommended for testing)
- Run directly on your machine
- Easy to debug and modify
- Full control over processes

### 2. **Docker Compose** (Recommended for production)
- Containerized deployment
- Easy to scale and manage
- All services orchestrated together

### 3. **Manual Docker** (Advanced)
- Individual container management
- More control, more complex

---

## 🚀 Option 1: Local Development

### Prerequisites
```bash
# Python 3.8+
python --version

# Redis
redis-server --version

# jq (optional, for JSON parsing)
jq --version
```

### Installation
```bash
cd sr_detection_system

# Install Python dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running
```bash
# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Start everything
./scripts/start_all.sh
```

**What happens:**
1. ✅ Checks if Redis is running (starts it if needed)
2. ✅ Starts kline streaming in background
3. ✅ Starts options tracking in background
4. ✅ Waits 15 seconds for data collection
5. ✅ Generates initial S/R data
6. ✅ Shows you how to check status

### Monitoring
```bash
# View kline stream logs
tail -f logs/kline_stream.log

# View options tracker logs
tail -f logs/options_tracker.log

# Check if processes are running
ps aux | grep bybit

# Check Redis data
redis-cli KEYS "*BTCUSDT" | wc -l
redis-cli KEYS "sr:technical:basic:*"
```

### Updating S/R Data
```bash
# Update all S/R (18 combinations)
python src/sr_core/sr_detector_technical.py --all --mode basic --save

# Update specific symbol/interval
python src/sr_core/sr_detector_technical.py \
  --symbol BTCUSDT \
  --interval 15 \
  --mode basic \
  --save
```

### Stopping
```bash
./scripts/stop_all.sh
```

---

## 🐳 Option 2: Docker Compose (Recommended)

### Prerequisites
```bash
# Docker
docker --version

# Docker Compose
docker-compose --version
```

### Build and Start
```bash
cd sr_detection_system

# Build images and start all services
docker-compose up -d

# Or build explicitly first
docker-compose build
docker-compose up -d
```

**What starts:**
1. ✅ **sr-redis** - Redis container (port 6379)
2. ✅ **sr-kline-stream** - Kline data collection
3. ✅ **sr-options-tracker** - Options data tracking
4. ✅ **sr-detector** - S/R detection (runs every 5 minutes)
5. ✅ **sr-options-scheduler** - Daily options refresh (8 AM UTC)
6. ✅ **sr-web-visualizer** - Web interface (http://localhost:8080)

### Monitoring
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f kline-stream
docker-compose logs -f options-tracker
docker-compose logs -f sr-detector
docker-compose logs -f options-scheduler

# Check service status
docker-compose ps

# Check when next options refresh will happen
docker-compose logs options-scheduler | grep "Next refresh"

# Check Redis data (from host)
redis-cli -h localhost KEYS "sr:technical:basic:*"

# Or exec into Redis container
docker exec -it sr-redis redis-cli KEYS "sr:technical:basic:*"
```

### Updating
```bash
# Restart specific service
docker-compose restart sr-detector

# Restart all services
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

### Stopping
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker-compose down -v
```

---

## 📦 Option 3: Manual Docker

### Build Image
```bash
cd sr_detection_system

docker build -t sr-detection:latest .
```

### Start Redis
```bash
docker run -d \
  --name sr-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### Start Kline Stream
```bash
docker run -d \
  --name sr-kline \
  --network host \
  -e REDIS_HOST=localhost \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  sr-detection:latest \
  python src/bybit_kline_stream_ultra.py
```

### Start Options Tracker
```bash
docker run -d \
  --name sr-options \
  --network host \
  -e REDIS_HOST=localhost \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  sr-detection:latest \
  python src/bybit_options_tracker.py
```

### Run S/R Detection
```bash
docker run -it --rm \
  --network host \
  -e REDIS_HOST=localhost \
  -v $(pwd)/config:/app/config \
  sr-detection:latest \
  python src/sr_core/sr_detector_technical.py --all --mode basic --save
```

---

## 🔄 Git Deployment

### Initialize Repository
```bash
cd sr_detection_system

# Initialize git
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: S/R Detection System"
```

### Push to GitHub
```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/yourusername/sr-detection-system.git
git branch -M main
git push -u origin main
```

### Clone on Another Machine
```bash
# Clone the repository
git clone https://github.com/yourusername/sr-detection-system.git
cd sr-detection-system

# Install dependencies
pip install -r requirements.txt

# Start with Docker
docker-compose up -d

# Or start locally
./scripts/start_all.sh
```

---

## ☁️ Cloud Deployment

### AWS EC2 / DigitalOcean Droplet

```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Install Docker & Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose

# 3. Clone your repository
git clone https://github.com/yourusername/sr-detection-system.git
cd sr-detection-system

# 4. Start services
sudo docker-compose up -d

# 5. Check logs
sudo docker-compose logs -f
```

### Access from Remote
```bash
# Query Redis from remote
redis-cli -h your-server-ip GET "sr:technical:basic:15.BTCUSDT"

# Or use SSH tunnel
ssh -L 6379:localhost:6379 user@your-server-ip
redis-cli -h localhost GET "sr:technical:basic:15.BTCUSDT"
```

---

## 🔐 Production Considerations

### 1. Security

**Redis Password:**
Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --requirepass your_password
```

Update code to use password:
```python
# In sr_utils.py
self.redis_client = redis.Redis(
    host=self.host,
    port=self.port,
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)
```

### 2. Persistence

**Redis Data Persistence:**
Already configured in `docker-compose.yml`:
```yaml
volumes:
  - redis-data:/data
command: redis-server --appendonly yes
```

### 3. Monitoring

**Add Health Checks:**
```bash
# Check if services are healthy
docker-compose ps

# Check Redis health
redis-cli ping

# Check data freshness
redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.timestamp'
```

### 4. Logging

**Centralized Logging:**
```yaml
# In docker-compose.yml, add to each service:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 5. Scaling

**Add more symbols/intervals:**
Edit `config/config.json`:
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
  "intervals": ["1", "5", "15", "30", "60", "240", "D"]
}
```

---

## 📊 Verification Checklist

After deployment, verify everything is working:

- [ ] Redis is running
  ```bash
  redis-cli ping  # Should return "PONG"
  ```

- [ ] Kline data is being collected
  ```bash
  redis-cli KEYS "*BTCUSDT" | wc -l  # Should be 6-7
  ```

- [ ] Options data is being collected
  ```bash
  redis-cli KEYS "option:BTC-*" | wc -l  # Should be 600+
  ```

- [ ] S/R data is generated
  ```bash
  redis-cli KEYS "sr:technical:basic:*" | wc -l  # Should be 18
  ```

- [ ] S/R data is fresh (less than 5 minutes old)
  ```bash
  redis-cli GET "sr:technical:basic:15.BTCUSDT" | jq '.timestamp'
  # Compare with current time
  date +%s
  ```

- [ ] Logs show no errors
  ```bash
  # Local
  tail -20 logs/kline_stream.log
  tail -20 logs/options_tracker.log

  # Docker
  docker-compose logs --tail=20 kline-stream
  docker-compose logs --tail=20 options-tracker
  ```

---

## 🆘 Troubleshooting

### Services Won't Start (Local)
```bash
# Check if ports are in use
lsof -i :6379  # Redis port

# Kill existing processes
pkill -f bybit_kline
pkill -f bybit_options

# Restart
./scripts/start_all.sh
```

### Docker Containers Keep Restarting
```bash
# Check logs for errors
docker-compose logs kline-stream
docker-compose logs options-tracker

# Common issues:
# - Redis not healthy yet → Wait 30 seconds
# - Can't connect to Bybit → Check internet connection
# - Import errors → Rebuild: docker-compose up -d --build
```

### No Data in Redis
```bash
# Check if data collection scripts are running
docker-compose ps  # or ps aux | grep bybit

# Check script logs
docker-compose logs -f kline-stream

# Restart data collection
docker-compose restart kline-stream options-tracker
```

### S/R Data Not Updating
```bash
# Manually trigger update
docker-compose exec sr-detector \
  python src/sr_core/sr_detector_technical.py --all --mode basic --save

# Or restart detector
docker-compose restart sr-detector
```

---

## 📖 Additional Resources

- **Quick Start**: `QUICKSTART.md`
- **Full Documentation**: `README.md`
- **System Status**: `docs/SYSTEM_STATUS.md`
- **Phase 1 Report**: `docs/PHASE1_COMPLETION_REPORT.md`
- **All Specifications**: `docs/` folder

---

## 🎉 Success!

You now have a production-ready S/R detection system that:
- ✅ Collects real-time kline data (6 intervals × 3 symbols)
- ✅ Tracks options data (1,360+ contracts)
- ✅ Detects support & resistance (18 combinations)
- ✅ Stores everything in Redis
- ✅ Can run locally or in Docker
- ✅ Ready for Git and cloud deployment

**Happy trading!** 📈

---

**Questions?** Check `README.md` or open an issue on GitHub.
