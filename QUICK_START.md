# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Start Redis

```bash
redis-server --daemonize yes
```

## 3. Start the System

```bash
./scripts/start_system.sh
```

## 4. Open Dashboard

```
http://localhost:8080/live
```

## 5. Stop the System

```bash
./scripts/stop_system.sh
```

## Troubleshooting

### Redis Not Running
```bash
redis-cli ping
# If no response:
redis-server --daemonize yes
```

### Port 8080 in Use
```bash
lsof -ti:8080 | xargs kill
```

### No Data Showing
Wait 15-30 seconds after starting for data collection to begin.

## Manual Operation

### Start Individual Services
```bash
# Kline stream
python src/data_collection/bybit_kline_stream.py

# Options tracker
python src/data_collection/bybit_options_tracker.py

# Generate S/R
python src/sr_detectors/sr_detector_technical.py --all --save
python src/sr_detectors/sr_detector_sentiment.py --all

# Web app
python src/webapp/app.py
```
