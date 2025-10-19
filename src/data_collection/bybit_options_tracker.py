#!/usr/bin/env python3
"""
Bybit Options Data Tracker - Simplified Version
Tracks real-time options data for BTC, ETH, SOL
Stores data in Redis for analysis
"""

import asyncio
import json
import logging
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import os

import redis
import requests
from pybit.unified_trading import WebSocket
from redis.exceptions import ConnectionError, TimeoutError, RedisError


# ==================== CONFIGURATION ====================

class Config:
    """Configuration for options tracker"""

    # API Settings
    API_URL = 'https://api.bybit.com/v5/market/instruments-info'
    API_TIMEOUT = 10
    API_RETRY_COUNT = 3
    API_RETRY_DELAY = 1.0

    # Redis Settings (read from environment variables for Docker support)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = 0
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_CONNECTION_POOL_MAX = 50

    # WebSocket Settings
    WS_PING_INTERVAL = 45
    WS_PING_TIMEOUT = 15
    WS_RECONNECT_DELAY = 10
    WS_MAX_RECONNECT_ATTEMPTS = 10
    WS_SUBSCRIPTION_CHUNK_SIZE = 10
    WS_SUBSCRIPTION_DELAY = 0.5

    # Cache Settings
    CACHE_FILE = 'options_symbols_cache.json'
    CACHE_DURATION_HOURS = 24
    OPTION_ASSETS = ['BTC', 'ETH', 'SOL']

    # Performance Settings
    BATCH_SIZE = 100
    BATCH_TIMEOUT = 1.0
    WRITE_QUEUE_SIZE = 2000
    STATS_INTERVAL = 60

    # Data Settings
    CLEAR_ON_START = True  # Clear old options data on startup


# ==================== LOGGING SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# ==================== OPTIONS TRACKER ====================

class OptionsTracker:
    def __init__(self):
        self.config = Config()
        self.redis_pool = None
        self.redis_client = None
        self.ws = None
        self.running = False
        self.ping_thread = None
        self.write_queue = deque(maxlen=Config.WRITE_QUEUE_SIZE)
        self.batch_writer_task = None

        # Performance metrics
        self.metrics = {
            'messages_received': 0,
            'messages_processed': 0,
            'messages_dropped': 0,
            'redis_writes': 0,
            'redis_errors': 0,
            'ws_reconnects': 0,
            'last_message_time': None,
            'start_time': datetime.now()
        }

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received")
        self.running = False

    # ==================== REDIS ====================

    def init_redis(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_pool = redis.ConnectionPool(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                max_connections=Config.REDIS_CONNECTION_POOL_MAX,
                decode_responses=True
            )

            self.redis_client = redis.Redis(connection_pool=self.redis_pool)
            self.redis_client.ping()
            logger.info("✓ Redis connected")
            return True

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"✗ Redis connection failed: {e}")
            return False

    def clear_old_options_data(self):
        """Clear old options data from Redis"""
        if not Config.CLEAR_ON_START:
            return

        try:
            # Find all option keys
            option_keys = self.redis_client.keys("option:*")
            if option_keys:
                self.redis_client.delete(*option_keys)
                logger.info(f"Cleared {len(option_keys)} old option records")
        except RedisError as e:
            logger.error(f"Failed to clear old data: {e}")

    async def batch_writer(self):
        """Batch write options data to Redis"""
        pipeline_batch = []
        last_write = time.time()

        while self.running:
            try:
                # Collect items for batch
                while len(pipeline_batch) < Config.BATCH_SIZE:
                    if self.write_queue:
                        pipeline_batch.append(self.write_queue.popleft())
                    else:
                        break

                # Write batch if ready
                if pipeline_batch and (
                    len(pipeline_batch) >= Config.BATCH_SIZE or
                    time.time() - last_write > Config.BATCH_TIMEOUT
                ):
                    await self._write_batch(pipeline_batch)
                    pipeline_batch = []
                    last_write = time.time()

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Batch writer error: {e}")
                self.metrics['redis_errors'] += 1
                await asyncio.sleep(1)

    async def _write_batch(self, batch: List[Dict]):
        """Write batch using Redis pipeline"""
        try:
            pipe = self.redis_client.pipeline(transaction=False)

            for item in batch:
                symbol = item.get('symbol')
                if not symbol:
                    continue

                hash_key = f"option:{symbol}"

                # Store as hash
                pipe.hset(hash_key, mapping={
                    k: str(v) if v is not None else ""
                    for k, v in item.items()
                })

                # Set TTL (24 hours)
                pipe.expire(hash_key, 86400)

            # Update global stats
            pipe.hincrby("stats:options", "total_messages", len(batch))
            pipe.hset("stats:options", "last_update", str(time.time()))

            # Execute pipeline
            pipe.execute()

            self.metrics['redis_writes'] += len(batch)
            self.metrics['messages_processed'] += len(batch)

        except RedisError as e:
            logger.error(f"Redis pipeline error: {e}")
            self.metrics['redis_errors'] += 1

    # ==================== WEBSOCKET ====================

    def handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            self.metrics['messages_received'] += 1
            self.metrics['last_message_time'] = datetime.now()

            # Handle pong
            if message.get("op") == "pong":
                return

            data = message.get("data")
            if not data:
                return

            symbol = data.get('symbol')
            if not symbol:
                return

            # Prepare data record
            record = {
                'symbol': symbol,
                'timestamp': time.time(),
                'bid_iv': self._safe_float(data.get('bidIv')),
                'ask_iv': self._safe_float(data.get('askIv')),
                'last_price': self._safe_float(data.get('lastPrice')),
                'mark_price': self._safe_float(data.get('markPrice')),
                'index_price': self._safe_float(data.get('indexPrice')),
                'mark_iv': self._safe_float(data.get('markPriceIv')),
                'underlying_price': self._safe_float(data.get('underlyingPrice')),
                'open_interest': self._safe_float(data.get('openInterest')),
                'delta': self._safe_float(data.get('delta')),
                'gamma': self._safe_float(data.get('gamma')),
                'vega': self._safe_float(data.get('vega')),
                'theta': self._safe_float(data.get('theta')),
                'volume_24h': self._safe_float(data.get('volume24h')),
                'turnover_24h': self._safe_float(data.get('turnover24h')),
            }

            # Add to queue
            if len(self.write_queue) < Config.WRITE_QUEUE_SIZE:
                self.write_queue.append(record)
            else:
                self.metrics['messages_dropped'] += 1

        except Exception as e:
            logger.error(f"Message handler error: {e}")

    def _safe_float(self, value):
        """Safely convert to float"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def ping_keeper(self):
        """Keep WebSocket alive with pings"""
        while self.running:
            try:
                if self.ws and self.ws.ws and self.ws.ws.sock:
                    ping_msg = json.dumps({
                        "op": "ping",
                        "req_id": str(int(time.time() * 1000))
                    })
                    self.ws.ws.send(ping_msg)

                time.sleep(Config.WS_PING_INTERVAL)

            except Exception as e:
                logger.error(f"Ping error: {e}")
                time.sleep(Config.WS_PING_INTERVAL)

    async def subscribe_with_retry(self, symbols: List[str]):
        """Subscribe to options symbols with retry"""
        max_attempts = Config.WS_MAX_RECONNECT_ATTEMPTS
        attempt = 0

        while attempt < max_attempts and self.running:
            try:
                attempt += 1
                if attempt > 1:
                    logger.info(f"Reconnection attempt {attempt}/{max_attempts}")

                # Initialize WebSocket
                self.ws = WebSocket(
                    testnet=False,
                    channel_type="option",
                    ping_interval=Config.WS_PING_INTERVAL,
                    ping_timeout=Config.WS_PING_TIMEOUT
                )

                # Subscribe in chunks
                chunks = [symbols[i:i + Config.WS_SUBSCRIPTION_CHUNK_SIZE]
                         for i in range(0, len(symbols), Config.WS_SUBSCRIPTION_CHUNK_SIZE)]

                logger.info(f"Subscribing to {len(symbols)} symbols in {len(chunks)} batches...")

                for i, chunk in enumerate(chunks):
                    if not self.running:
                        break

                    self.ws.ticker_stream(
                        symbol=chunk,
                        callback=self.handle_message
                    )

                    if (i + 1) % 10 == 0:
                        logger.info(f"  Subscribed {i + 1}/{len(chunks)} batches")

                    await asyncio.sleep(Config.WS_SUBSCRIPTION_DELAY)

                # Start ping thread
                if not self.ping_thread or not self.ping_thread.is_alive():
                    self.ping_thread = threading.Thread(target=self.ping_keeper, daemon=True)
                    self.ping_thread.start()

                logger.info("✓ WebSocket subscriptions complete")
                return True

            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                self.metrics['ws_reconnects'] += 1

                if attempt < max_attempts:
                    delay = Config.WS_RECONNECT_DELAY * attempt
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("✗ Max reconnection attempts reached")
                    return False

    # ==================== SYMBOL MANAGEMENT ====================

    def fetch_symbols(self) -> List[str]:
        """Fetch trading symbols from Bybit API"""
        all_symbols = []

        for coin in Config.OPTION_ASSETS:
            cursor = None
            coin_symbols = []

            while True:
                try:
                    params = {
                        "category": "option",
                        "baseCoin": coin,
                        "limit": 1000
                    }
                    if cursor:
                        params["cursor"] = cursor

                    response = requests.get(
                        Config.API_URL,
                        params=params,
                        timeout=Config.API_TIMEOUT
                    )
                    response.raise_for_status()

                    data = response.json()
                    if data.get("retCode") != 0:
                        logger.error(f"API error for {coin}: {data.get('retMsg')}")
                        break

                    items = data.get("result", {}).get("list", [])
                    if not items:
                        break

                    symbols = [
                        item["symbol"]
                        for item in items
                        if item.get("status") == "Trading"
                    ]
                    coin_symbols.extend(symbols)

                    cursor = data.get("result", {}).get("nextPageCursor")
                    if not cursor:
                        break

                except Exception as e:
                    logger.error(f"Error fetching {coin} symbols: {e}")
                    break

            logger.info(f"  Fetched {len(coin_symbols)} {coin} options")
            all_symbols.extend(coin_symbols)

        return all_symbols

    def load_or_fetch_symbols(self) -> List[str]:
        """Load symbols from cache or fetch fresh"""
        cache_path = Path(Config.CACHE_FILE)

        # Try cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                expires_at = datetime.fromisoformat(cache_data['expires_at'])
                if datetime.now() < expires_at:
                    logger.info(f"✓ Loaded {len(cache_data['symbols'])} symbols from cache")
                    return cache_data['symbols']
                else:
                    logger.info("Cache expired, fetching fresh symbols...")
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

        # Fetch fresh symbols
        logger.info("Fetching symbols from Bybit API...")
        symbols = self.fetch_symbols()

        if symbols:
            # Save to cache
            cache_data = {
                'symbols': symbols,
                'count': len(symbols),
                'updated_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=Config.CACHE_DURATION_HOURS)).isoformat(),
                'by_asset': {
                    asset: len([s for s in symbols if s.startswith(f"{asset}-")])
                    for asset in Config.OPTION_ASSETS
                }
            }

            try:
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                logger.info(f"✓ Cached {len(symbols)} symbols")
            except Exception as e:
                logger.error(f"Cache write error: {e}")

        return symbols

    # ==================== MAIN EXECUTION ====================

    async def run(self):
        """Main execution loop"""
        logger.info("="*60)
        logger.info("Bybit Options Tracker Started")
        logger.info("="*60)

        # Initialize Redis
        if not self.init_redis():
            logger.error("Failed to initialize Redis. Exiting.")
            return

        # Clear old data
        self.clear_old_options_data()

        # Load symbols
        symbols = self.load_or_fetch_symbols()
        if not symbols:
            logger.error("No symbols available. Exiting.")
            return

        logger.info(f"Tracking {len(symbols)} options symbols")

        self.running = True

        # Start batch writer
        self.batch_writer_task = asyncio.create_task(self.batch_writer())

        # Subscribe to WebSocket
        success = await self.subscribe_with_retry(symbols)
        if not success:
            logger.error("Failed to establish WebSocket connection")
            self.running = False
            return

        # Main monitoring loop
        last_stats_time = time.time()

        logger.info("\n" + "="*60)
        logger.info("LIVE OPTIONS DATA STREAMING")
        logger.info("="*60)
        logger.info("Press Ctrl+C to stop\n")

        while self.running:
            try:
                await asyncio.sleep(1)

                # Print stats periodically
                if time.time() - last_stats_time > Config.STATS_INTERVAL:
                    self.print_stats()
                    last_stats_time = time.time()

                # Check WebSocket health
                if self.metrics['last_message_time']:
                    time_since_last = (datetime.now() - self.metrics['last_message_time']).seconds
                    if time_since_last > 120:
                        logger.warning(f"No data for {time_since_last} seconds, reconnecting...")
                        await self.subscribe_with_retry(symbols)

            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(5)

        # Cleanup
        await self.cleanup()

    def print_stats(self):
        """Print performance statistics"""
        uptime = datetime.now() - self.metrics['start_time']
        msg_rate = self.metrics['messages_received'] / uptime.total_seconds() if uptime.total_seconds() > 0 else 0

        logger.info("─" * 60)
        logger.info(f"📊 STATS | Uptime: {str(uptime).split('.')[0]}")
        logger.info(f"   Messages: {self.metrics['messages_received']:,} received ({msg_rate:.1f}/sec)")
        logger.info(f"   Processed: {self.metrics['messages_processed']:,}")
        logger.info(f"   Queue: {len(self.write_queue)}/{Config.WRITE_QUEUE_SIZE}")
        logger.info(f"   Errors: {self.metrics['redis_errors']} Redis, {self.metrics['messages_dropped']} dropped")
        logger.info("─" * 60)

    async def cleanup(self):
        """Graceful cleanup"""
        logger.info("\nShutting down...")

        self.running = False

        # Process remaining queue
        remaining = list(self.write_queue)
        if remaining:
            await self._write_batch(remaining)
            logger.info(f"Flushed {len(remaining)} remaining messages")

        # Cancel tasks
        if self.batch_writer_task:
            self.batch_writer_task.cancel()

        # Close WebSocket
        if self.ws:
            try:
                self.ws.exit()
            except:
                pass

        # Close Redis
        if self.redis_pool:
            self.redis_pool.disconnect()

        logger.info("✓ Shutdown complete")


# ==================== ENTRY POINT ====================

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("Bybit Options Tracker")
        print("\nUsage: python bybit_options_tracker.py")
        print("\nStores options data in Redis:")
        print("  option:{symbol} - Hash with all option metrics")
        print("  stats:options - Global statistics")
        print("\nQuery example:")
        print("  redis-cli HGETALL 'option:BTC-29DEC23-40000-C'")
        return

    try:
        tracker = OptionsTracker()
        asyncio.run(tracker.run())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
