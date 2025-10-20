from pybit.unified_trading import WebSocket, HTTP
from time import sleep
import redis
import json
from datetime import datetime

ws = WebSocket(testnet=False, channel_type="linear")
session = HTTP(testnet=False)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
intervals = [1, 5, 15, 60, 240, 'D']
limit = 1000


def store_confirmed_candle(key, timestamp, ohlcv):
    """Store confirmed candle in sorted set and maintain limit"""
    data = json.dumps({'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
    r.zadd(key, {data: timestamp})

    count = r.zcard(key)
    if count > limit:
        r.zremrangebyrank(key, 0, count - limit - 1)


def store_unconfirmed_candle(key, timestamp, ohlcv):
    """Store unconfirmed candle in temporary key"""
    data = json.dumps({'ts': timestamp, 'o': ohlcv[0], 'h': ohlcv[1], 'l': ohlcv[2], 'c': ohlcv[3], 'v': ohlcv[4]})
    r.set(f"{key}:latest", data)


def historical_data():
    """Fetch and store historical kline data"""
    for symbol in symbols:
        for interval in intervals:
            now = int(datetime.now().timestamp() * 1000)

            if interval == 'D':
                ms_per_candle = 24 * 60 * 60 * 1000
            else:
                ms_per_candle = int(interval) * 60 * 1000

            start_time = now - (limit * ms_per_candle)

            data = session.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                start=start_time,
                end=now,
                limit=limit
            )

            result = data.get('result')
            sym = f"{interval}.{result.get('symbol')}"
            candles = result.get('list')

            for candle in candles:
                timestamp = int(candle[0])
                ohlcv = [candle[1], candle[2], candle[3], candle[4], candle[5]]
                store_confirmed_candle(sym, timestamp, ohlcv)


def handle_message(message):
    """Handle live kline updates from WebSocket"""
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


historical_data()

for symbol in symbols:
    for interval in intervals:
        ws.kline_stream(interval=interval, symbol=symbol, callback=handle_message)


while True:
    sleep(1)
