from pybit.unified_trading import WebSocket, HTTP
from time import sleep
import redis
import json
from datetime import datetime
import signal
import sys
import os

# PID file to prevent multiple instances (use /app/logs for Docker)
PID_FILE = 'logs/kline_stream.pid' if os.path.exists('logs') else '/tmp/bybit_stream.pid'

# Skip PID check in Docker (we are PID 1 in the container)
IN_DOCKER = os.getpid() == 1 or os.path.exists('/.dockerenv')

if not IN_DOCKER and os.path.exists(PID_FILE):
    with open(PID_FILE, 'r') as f:
        old_pid = f.read().strip()
    # Check if process is actually running
    try:
        os.kill(int(old_pid), 0)
        print(f"Already running (PID: {old_pid}). Stop existing instance first.")
        sys.exit(1)
    except (OSError, ValueError):
        # Process doesn't exist, remove stale PID file
        os.remove(PID_FILE)

with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))

# Load config (support both local and Docker paths)
config_paths = ['config.json', 'config/config.json', '/app/config/config.json']
config_file = next((p for p in config_paths if os.path.exists(p)), None)
if not config_file:
    print("ERROR: config.json not found in any expected location")
    sys.exit(1)

with open(config_file, 'r') as f:
    config = json.load(f)

# Redis connection pool (support environment variables for Docker)
redis_pool = redis.ConnectionPool(
    host=os.getenv('REDIS_HOST', config['redis']['host']),
    port=int(os.getenv('REDIS_PORT', config['redis']['port'])),
    db=config['redis']['db'],
    decode_responses=True,
    max_connections=10
)
r = redis.Redis(connection_pool=redis_pool)

# Test Redis connection
try:
    r.ping()
except redis.ConnectionError:
    print("ERROR: Cannot connect to Redis. Is it running?")
    os.remove(PID_FILE)
    sys.exit(1)

ws = WebSocket(
    testnet=config['bybit']['testnet'],
    channel_type=config['bybit']['channel_type']
)
session = HTTP(testnet=config['bybit']['testnet'])

symbols = config['trading']['symbols']
intervals = config['trading']['intervals']
limit = config['trading']['candle_limit']

running = True


def cleanup():
    """Cleanup on exit"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def signal_handler(sig, frame):
    """Graceful shutdown on Ctrl+C"""
    global running
    running = False
    ws.exit()
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Clear Redis DB on startup (if enabled)
if config['redis'].get('clear_on_startup', True):
    r.flushdb()


def store_confirmed_candle(key, timestamp, ohlcv):
    """Store confirmed candle and maintain limit using pipeline"""
    pipe = r.pipeline()
    data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})

    # Check if already exists (avoid duplicates from historical + live overlap)
    if r.zscore(key, data) is None:
        pipe.zadd(key, {data: timestamp})
        pipe.zcard(key)
        results = pipe.execute()

        count = results[1]
        if count > limit:
            r.zremrangebyrank(key, 0, count - limit - 1)


def store_unconfirmed_candle(key, timestamp, ohlcv):
    """Store unconfirmed candle in temporary key"""
    data = json.dumps({'ts': timestamp, 'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
    r.set(f"{key}:latest", data)


def batch_store_candles(key, candles_data):
    """Store multiple candles at once using pipeline"""
    if not candles_data:
        return

    pipe = r.pipeline()

    for timestamp, ohlcv in candles_data:
        data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
        pipe.zadd(key, {data: timestamp})

    pipe.zcard(key)
    results = pipe.execute()

    count = results[-1]
    if count > limit:
        # Put this in pipeline for one less roundtrip
        pipe = r.pipeline()
        pipe.zremrangebyrank(key, 0, count - limit - 1)
        pipe.execute()


def historical_data():
    """Fetch and store historical kline data with batching"""
    for symbol in symbols:
        for interval in intervals:
            try:
                now = int(datetime.now().timestamp() * 1000)

                if interval == 'D':
                    ms_per_candle = 24 * 60 * 60 * 1000
                else:
                    ms_per_candle = int(interval) * 60 * 1000

                start_time = now - (limit * ms_per_candle)

                data = session.get_kline(
                    category=config['bybit']['category'],
                    symbol=symbol,
                    interval=interval,
                    start=start_time,
                    end=now,
                    limit=limit
                )

                if data.get('retCode') != 0:
                    continue

                result = data.get('result')
                sym = f"{interval}.{result.get('symbol')}"
                candles = result.get('list', [])

                candles_data = [
                    (int(candle[0]), [candle[1], candle[2], candle[3], candle[4], candle[5]])
                    for candle in candles
                ]

                batch_store_candles(sym, candles_data)

            except Exception:
                continue


def handle_message(message):
    """Handle live kline updates from WebSocket"""
    try:
        sym = message.get('topic', '').replace('kline.', '')
        data = message.get('data', [{}])[0]

        timestamp = data.get('end')
        ohlcv = [
            data.get('open'),
            data.get('high'),
            data.get('low'),
            data.get('close'),
            data.get('volume')
        ]
        confirm = data.get('confirm', False)

        if confirm:
            store_confirmed_candle(sym, timestamp, ohlcv)
        else:
            store_unconfirmed_candle(sym, timestamp, ohlcv)

    except Exception:
        pass


historical_data()

for symbol in symbols:
    for interval in intervals:
        ws.kline_stream(interval=interval, symbol=symbol, callback=handle_message)


while running:
    sleep(1)

cleanup()
