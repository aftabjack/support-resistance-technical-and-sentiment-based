from pybit.unified_trading import WebSocket, HTTP
from time import sleep
import redis
import json
from datetime import datetime
import signal
import sys
import os

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Redis connection pool (more efficient than single connection)
redis_pool = redis.ConnectionPool(
    host=config['redis']['host'],
    port=config['redis']['port'],
    db=config['redis']['db'],
    decode_responses=True,
    max_connections=10
)
r = redis.Redis(connection_pool=redis_pool)

ws = WebSocket(
    testnet=config['bybit']['testnet'],
    channel_type=config['bybit']['channel_type']
)
session = HTTP(testnet=config['bybit']['testnet'])

symbols = config['trading']['symbols']
intervals = config['trading']['intervals']
limit = config['trading']['candle_limit']

running = True
PID_FILE = '/tmp/bybit_stream.pid'


def signal_handler(sig, frame):
    """Graceful shutdown on Ctrl+C"""
    global running
    running = False
    # Clean up PID file
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    ws.exit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Check for already running instance
if os.path.exists(PID_FILE):
    with open(PID_FILE, 'r') as f:
        old_pid = f.read().strip()
    print(f"ERROR: Instance already running (PID: {old_pid})")
    print("If this is incorrect, delete /tmp/bybit_stream.pid and retry")
    sys.exit(1)

# Create PID file
with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))

# Redis connection health check
try:
    r.ping()
except redis.ConnectionError:
    print("ERROR: Redis not running! Please start Redis server.")
    sys.exit(1)

# Clear Redis DB on startup for fresh data (if enabled)
if config['redis'].get('clear_on_startup', True):
    r.flushdb()


def redis_retry(func, *args, max_retries=3, **kwargs):
    """Retry Redis operations on connection errors"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except redis.ConnectionError:
            if attempt == max_retries - 1:
                print(f"ERROR: Redis connection lost after {max_retries} retries")
                raise
            sleep(1)


def store_confirmed_candle(key, timestamp, ohlcv):
    """Store confirmed candle and maintain limit using pipeline"""
    def _store():
        # Check if timestamp already exists to avoid duplicates (from historical overlap)
        existing = r.zrangebyscore(key, timestamp, timestamp)
        if existing:
            return  # Skip duplicate

        pipe = r.pipeline()
        data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})

        pipe.zadd(key, {data: timestamp})
        pipe.zcard(key)

        # Add ZREMRANGEBYRANK to pipeline to reduce roundtrips
        pipe.zremrangebyrank(key, 0, -(limit + 1))
        pipe.execute()

    redis_retry(_store)


def store_unconfirmed_candle(key, timestamp, ohlcv):
    """Store unconfirmed candle in temporary key"""
    def _store():
        data = json.dumps({'ts': timestamp, 'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
        r.set(f"{key}:latest", data)

    redis_retry(_store)


def batch_store_candles(key, candles_data):
    """Store multiple candles at once using pipeline (massive speedup)"""
    if not candles_data:
        return

    def _store():
        pipe = r.pipeline()

        for timestamp, ohlcv in candles_data:
            data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
            pipe.zadd(key, {data: timestamp})

        # Add ZREMRANGEBYRANK to pipeline to reduce roundtrips
        pipe.zremrangebyrank(key, 0, -(limit + 1))
        pipe.execute()

    redis_retry(_store)


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
