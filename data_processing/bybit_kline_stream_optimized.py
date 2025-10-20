from pybit.unified_trading import WebSocket, HTTP
from time import sleep
import redis
import json
from datetime import datetime
import signal
import sys

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


def signal_handler(sig, frame):
    """Graceful shutdown on Ctrl+C"""
    global running
    running = False
    ws.exit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Clear Redis DB on startup for fresh data (if enabled)
if config['redis'].get('clear_on_startup', True):
    r.flushdb()


def store_confirmed_candle(key, timestamp, ohlcv):
    """Store confirmed candle and maintain limit using pipeline"""
    pipe = r.pipeline()
    data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})

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
    """Store multiple candles at once using pipeline (massive speedup)"""
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
        r.zremrangebyrank(key, 0, count - limit - 1)


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
