"""
S/R Visualizer Web App
Real-time Support & Resistance visualization
"""

from flask import Flask, render_template, jsonify, request
import redis
import json
import os
from datetime import datetime

app = Flask(__name__)

# Redis connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Available symbols and intervals
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
INTERVALS = [
    {'value': '1', 'label': '1 min'},
    {'value': '5', 'label': '5 min'},
    {'value': '15', 'label': '15 min'},
    {'value': '60', 'label': '1 hour'},
    {'value': '240', 'label': '4 hour'},
    {'value': 'D', 'label': 'Daily'}
]


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', symbols=SYMBOLS, intervals=INTERVALS)


@app.route('/live')
def live_dashboard():
    """Live S/R Dashboard - Technical + Sentiment"""
    return render_template('live_dashboard.html')


@app.route('/ema')
def ema_viewer():
    """EMA-Enhanced S/R Viewer"""
    return render_template('ema_viewer.html')


@app.route('/api/sr/<symbol>/<interval>')
def get_sr(symbol, interval):
    """Get S/R data for symbol and interval"""

    symbol = symbol.upper()
    key = f"sr:technical:basic:{interval}.{symbol}"

    # Get data from Redis
    data = r.get(key)

    if not data:
        return jsonify({
            'error': f'No data found for {symbol} {interval}',
            'key': key
        }), 404

    sr_data = json.loads(data)

    # Add human-readable timestamp
    dt = datetime.fromtimestamp(sr_data['timestamp'])
    sr_data['timestamp_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate age in seconds
    age = datetime.now().timestamp() - sr_data['timestamp']
    sr_data['age_seconds'] = int(age)

    return jsonify(sr_data)


@app.route('/api/list')
def list_sr():
    """List all available S/R data"""

    keys = r.keys("sr:technical:basic:*")

    result = {}
    for key in keys:
        # Parse key: sr:technical:basic:15.BTCUSDT
        parts = key.split(':')[-1].split('.')
        interval = parts[0]
        symbol = parts[1]

        if symbol not in result:
            result[symbol] = []
        result[symbol].append(interval)

    # Sort intervals
    for symbol in result:
        result[symbol] = sorted(result[symbol], key=lambda x: float(x) if x.isdigit() else 9999)

    return jsonify(result)


@app.route('/api/current_price/<symbol>')
def get_current_price(symbol):
    """Get current price from latest kline data"""

    symbol = symbol.upper()

    # Try to get from 1-minute kline (stored as sorted set)
    for interval in ['1', '5', '15']:
        key = f"{interval}.{symbol}"

        try:
            # Try zset first (with score = timestamp)
            latest = r.zrevrange(key, 0, 0, withscores=True)
            if latest:
                kline_json, timestamp = latest[0]
                kline = json.loads(kline_json)
                return jsonify({
                    'symbol': symbol,
                    'price': float(kline['c']),
                    'timestamp': int(timestamp),
                    'interval': interval
                })
        except Exception as e:
            # Try string
            try:
                data = r.get(key)
                if data:
                    kline = json.loads(data)
                    return jsonify({
                        'symbol': symbol,
                        'price': float(kline['c']),
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'interval': interval
                    })
            except:
                continue

    return jsonify({'error': 'No price data available'}), 404


@app.route('/api/sentiment/<symbol>')
def get_sentiment_sr(symbol):
    """Get sentiment S/R data for symbol"""

    symbol = symbol.upper()
    key = f"sr:sentiment:basic:{symbol}"

    # Get data from Redis
    data = r.get(key)

    if not data:
        return jsonify({
            'error': f'No sentiment S/R data found for {symbol}',
            'key': key
        }), 404

    sr_data = json.loads(data)

    # Add human-readable timestamp
    dt = datetime.fromtimestamp(sr_data['timestamp'])
    sr_data['timestamp_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate age in seconds
    age = datetime.now().timestamp() - sr_data['timestamp']
    sr_data['age_seconds'] = int(age)

    return jsonify(sr_data)


@app.route('/api/pivots/<symbol>')
def get_pivots_sr(symbol):
    """Get pivot-based S/R data for symbol"""

    symbol = symbol.upper()
    key = f"sr:pivots:basic:{symbol}"

    # Get data from Redis
    data = r.get(key)

    if not data:
        return jsonify({
            'error': f'No pivot S/R data found for {symbol}',
            'key': key
        }), 404

    sr_data = json.loads(data)

    # Add human-readable timestamp
    dt = datetime.fromtimestamp(sr_data['timestamp'])
    sr_data['timestamp_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate age in seconds
    age = datetime.now().timestamp() - sr_data['timestamp']
    sr_data['age_seconds'] = int(age)

    return jsonify(sr_data)


@app.route('/api/ultimate/<symbol>/<interval>')
def get_ultimate_sr(symbol, interval):
    """Get ultimate S/R data for symbol and interval (confluence mode)"""

    symbol = symbol.upper()
    key = f"sr:ultimate:confluence:{interval}.{symbol}"

    # Get data from Redis
    data = r.get(key)

    if not data:
        return jsonify({
            'error': f'No ultimate S/R data found for {symbol} {interval}',
            'key': key
        }), 404

    sr_data = json.loads(data)

    # Add human-readable timestamp
    dt = datetime.fromtimestamp(sr_data['timestamp'])
    sr_data['timestamp_readable'] = dt.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate age in seconds
    age = datetime.now().timestamp() - sr_data['timestamp']
    sr_data['age_seconds'] = int(age)

    return jsonify(sr_data)


@app.route('/health')
def health():
    """Health check endpoint with data freshness validation"""
    try:
        r.ping()

        # Check data freshness
        now = int(datetime.now().timestamp())
        max_age_seconds = 1800  # 30 minutes
        warnings = []

        # Check kline data freshness for BTCUSDT
        latest = r.zrevrange('15.BTCUSDT', 0, 0, withscores=True)
        if latest:
            timestamp_ms = int(latest[0][1])
            timestamp_s = timestamp_ms // 1000
            age = now - timestamp_s

            if age > max_age_seconds:
                warnings.append(f'Kline data is stale ({age}s old)')
        else:
            warnings.append('No kline data found')

        # Check S/R data freshness
        sr_data = r.get('sr:technical:basic:15.BTCUSDT')
        if sr_data:
            sr_json = json.loads(sr_data)
            sr_age = now - sr_json.get('timestamp', now)
            if sr_age > 600:  # 10 minutes
                warnings.append(f'S/R data is stale ({sr_age}s old)')
        else:
            warnings.append('No S/R data found')

        response = {
            'status': 'healthy' if not warnings else 'degraded',
            'redis': 'connected',
            'timestamp': datetime.now().isoformat(),
            'data_age_seconds': age if latest else None
        }

        if warnings:
            response['warnings'] = warnings

        return jsonify(response), 200 if not warnings else 200

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'redis': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
