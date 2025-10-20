#!/usr/bin/env python3
"""
Sentiment-based S/R Detector
Detects support and resistance levels from options data
"""

import sys
import json
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sr_detectors.sr_utils import RedisHelper
from sr_methods.sentiment.oi_walls import detect_oi_walls


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentSRDetector:
    """Detect S/R levels from options data (sentiment-based)"""

    def __init__(self, redis_helper: Optional[RedisHelper] = None):
        self.redis = redis_helper or RedisHelper()

    def detect_and_save(
        self,
        symbol: str,
        mode: str = 'basic'
    ) -> Dict:
        """
        Detect sentiment S/R levels and save to Redis

        Args:
            symbol: Symbol (BTCUSDT, ETHUSDT, SOLUSDT)
            mode: Detection mode ('basic' = OI walls only)

        Returns:
            Detection result with resistance and support levels
        """

        start_time = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"Detecting Sentiment S/R for {symbol} (mode: {mode})")
        logger.info(f"{'='*60}")

        # Get current price from latest kline
        current_price = self._get_current_price(symbol)
        if not current_price:
            logger.error(f"Could not get current price for {symbol}")
            return {'error': 'No current price available'}

        logger.info(f"Current price: ${current_price:,.2f}")

        # Get options data from Redis
        options_data = self._get_options_data(symbol)
        if not options_data:
            logger.error(f"No options data found for {symbol}")
            return {'error': 'No options data available'}

        logger.info(f"Loaded {len(options_data)} option contracts")

        # Detect based on mode
        if mode == 'basic':
            result = detect_oi_walls(
                options_data=options_data,
                current_price=current_price,
                oi_threshold_percentile=0.75,
                merge_distance=0.005,
                min_oi=100
            )
        else:
            logger.error(f"Unknown mode: {mode}")
            return {'error': f'Unknown mode: {mode}'}

        # Add metadata
        processing_time = (time.time() - start_time) * 1000

        result['timestamp'] = time.time()
        result['metadata'] = {
            'symbol': symbol,
            'mode': mode,
            'options_analyzed': len(options_data),
            'processing_time_ms': round(processing_time, 2),
            'current_price': current_price
        }

        # Save to Redis
        redis_key = f"sr:sentiment:{mode}:{symbol}"
        self.redis.save_sr_result(redis_key, result, ttl=300)  # 5 minute TTL
        logger.info(f"Saved result to Redis: {redis_key}")

        # Display results
        self._display_results(result)

        return result

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from latest kline data"""

        for interval in ['1', '5', '15']:
            key = f"{interval}.{symbol}"

            try:
                # Try sorted set (zset) - kline stream stores as zset
                latest = self.redis.redis_client.zrevrange(key, 0, 0, withscores=False)
                if latest:
                    kline = json.loads(latest[0])
                    return float(kline['c'])
            except:
                # Try string (simple get)
                try:
                    kline_data = self.redis.redis_client.get(key)
                    if kline_data:
                        kline = json.loads(kline_data)
                        return float(kline['c'])
                except:
                    continue

        return None

    def _get_options_data(self, symbol: str) -> List[Dict]:
        """Get options data from Redis"""

        # Get base coin (BTC, ETH, SOL)
        base_coin = symbol.replace('USDT', '')

        # Get all option keys for this coin
        pattern = f"option:{base_coin}-*"
        keys = list(self.redis.redis_client.scan_iter(match=pattern, count=1000))

        logger.info(f"Found {len(keys)} option contracts for {base_coin}")

        options = []
        for key in keys:
            try:
                # Options are stored as Redis hashes
                data = self.redis.redis_client.hgetall(key)
                if data:
                    # Parse the key to extract strike and type
                    # Format: option:BTC-26DEC25-60000-C or option:BTC-28NOV25-138000-P-USDT
                    parts = key.split(':')[1].replace('-USDT', '').split('-')

                    # Get strike price and option type
                    strike = None
                    opt_type = None

                    # Try to find numeric strike and C/P indicator
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            strike = float(part)
                        if part in ['C', 'P'] and i < len(parts):
                            opt_type = 'Call' if part == 'C' else 'Put'

                    if strike and opt_type:
                        opt = {
                            'strike': strike,
                            'optionType': opt_type,
                            'openInterest': float(data.get(b'open_interest', data.get('open_interest', 0))),
                            'volume24h': float(data.get(b'volume_24h', data.get('volume_24h', 0))),
                            'symbol': key
                        }
                        options.append(opt)
            except Exception as e:
                logger.debug(f"Error parsing option {key}: {e}")
                continue

        logger.info(f"Successfully parsed {len(options)} option contracts")
        return options

    def _display_results(self, result: Dict):
        """Display detection results"""

        metadata = result.get('metadata', {})
        resistance = result.get('resistance', [])
        support = result.get('support', [])

        print(f"\n{'='*60}")
        print(f"Sentiment S/R Detection Complete")
        print(f"{'='*60}")
        print(f"Symbol: {metadata.get('symbol')}")
        print(f"Current Price: ${metadata.get('current_price', 0):,.2f}")
        print(f"Processing Time: {metadata.get('processing_time_ms', 0):.2f}ms")
        print(f"Options Analyzed: {metadata.get('options_analyzed', 0)}")
        print(f"{'='*60}")

        print(f"\n📈 Resistance Levels (OI Walls): {len(resistance)}")
        print(f"{'='*60}")
        for i, level in enumerate(resistance[:5], 1):
            dist = ((level['price'] - metadata.get('current_price', 0)) / metadata.get('current_price', 1)) * 100
            print(f"{i}. ${level['price']:>10,.2f}  |  +{dist:>6.2f}%  |  OI: {level['oi']:>8,.0f}  |  Strength: {level['strength']:.2f}")

        print(f"\n📉 Support Levels (OI Walls): {len(support)}")
        print(f"{'='*60}")
        for i, level in enumerate(support[:5], 1):
            dist = ((metadata.get('current_price', 0) - level['price']) / metadata.get('current_price', 1)) * 100
            print(f"{i}. ${level['price']:>10,.2f}  |  -{dist:>6.2f}%  |  OI: {level['oi']:>8,.0f}  |  Strength: {level['strength']:.2f}")

        print(f"{'='*60}\n")


def main():
    """CLI entry point"""

    import argparse

    parser = argparse.ArgumentParser(description='Sentiment-based S/R Detector')
    parser.add_argument('--symbol', type=str, help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--all', action='store_true', help='Run for all symbols')
    parser.add_argument('--mode', type=str, default='basic', help='Detection mode (basic)')
    parser.add_argument('--save', action='store_true', help='Save results to Redis (default: True)', default=True)

    args = parser.parse_args()

    # Initialize detector
    detector = SentimentSRDetector()

    # Symbols to process
    if args.all:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    elif args.symbol:
        symbols = [args.symbol.upper()]
    else:
        print("Error: Specify --symbol or --all")
        sys.exit(1)

    # Process each symbol
    for symbol in symbols:
        try:
            detector.detect_and_save(symbol=symbol, mode=args.mode)
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)


if __name__ == "__main__":
    main()
