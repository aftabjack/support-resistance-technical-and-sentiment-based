#!/usr/bin/env python3
"""
Pivot Point-based S/R Detector
Detects support and resistance from previous period high/low/close using pivot points
"""

import sys
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sr_core.sr_utils import RedisHelper
from sr_methods_technical.pivot_points import detect_pivot_sr


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PivotSRDetector:
    """Detect S/R levels from pivot points"""

    def __init__(self, redis_helper: Optional[RedisHelper] = None):
        self.redis = redis_helper or RedisHelper()

    def detect_and_save(
        self,
        symbol: str,
        mode: str = 'basic'
    ) -> Dict:
        """
        Detect pivot-based S/R levels and save to Redis

        Args:
            symbol: Symbol (BTCUSDT, ETHUSDT, SOLUSDT)
            mode: Detection mode ('basic' or 'advanced')

        Returns:
            Detection result with resistance and support levels
        """

        start_time = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"Detecting Pivot S/R for {symbol} (mode: {mode})")
        logger.info(f"{'='*60}")

        # Get current price
        current_price = self._get_current_price(symbol)
        if not current_price:
            logger.error(f"Could not get current price for {symbol}")
            return {'error': 'No current price available'}

        logger.info(f"Current price: ${current_price:,.2f}")

        # Get previous period data
        prev_day = self._get_previous_period(symbol, 'day')
        prev_week = self._get_previous_period(symbol, 'week')
        prev_month = self._get_previous_period(symbol, 'month')

        if not prev_day:
            logger.error(f"Could not get previous day data for {symbol}")
            return {'error': 'No previous day data available'}

        logger.info(f"Previous Day:   H: ${prev_day[0]:,.2f}  L: ${prev_day[1]:,.2f}  C: ${prev_day[2]:,.2f}")
        if prev_week:
            logger.info(f"Previous Week:  H: ${prev_week[0]:,.2f}  L: ${prev_week[1]:,.2f}  C: ${prev_week[2]:,.2f}")
        if prev_month:
            logger.info(f"Previous Month: H: ${prev_month[0]:,.2f}  L: ${prev_month[1]:,.2f}  C: ${prev_month[2]:,.2f}")

        # Detect pivots
        if mode == 'basic':
            # Basic mode: Previous day pivots only, standard + fibonacci
            result = detect_pivot_sr(
                prev_day=prev_day,
                prev_week=None,
                prev_month=None,
                current_price=current_price,
                include_fibonacci=True,
                include_camarilla=False
            )
        elif mode == 'advanced':
            # Advanced mode: All periods, all pivot types
            result = detect_pivot_sr(
                prev_day=prev_day,
                prev_week=prev_week,
                prev_month=prev_month,
                current_price=current_price,
                include_fibonacci=True,
                include_camarilla=True
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
            'current_price': current_price,
            'processing_time_ms': round(processing_time, 2),
            'periods_used': {
                'day': prev_day is not None,
                'week': prev_week is not None,
                'month': prev_month is not None
            }
        }

        # Save to Redis
        redis_key = f"sr:pivots:{mode}:{symbol}"
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

    def _get_previous_period(self, symbol: str, period: str) -> Optional[Tuple[float, float, float]]:
        """
        Get previous period's high, low, close from Daily klines

        Args:
            symbol: Trading symbol
            period: 'day', 'week', or 'month'

        Returns:
            (high, low, close) tuple or None
        """

        # Use Daily klines for all calculations
        key = f"D.{symbol}"

        try:
            # Get all daily klines WITH SCORES (timestamp is the score)
            klines_raw = self.redis.redis_client.zrevrange(key, 0, -1, withscores=True)

            if not klines_raw or len(klines_raw) < 2:
                logger.warning(f"Not enough daily kline data for {symbol}")
                return None

            # Parse klines with their timestamps (score)
            # zrevrange with withscores=True returns list of tuples: [(data, score), ...]
            klines = []
            for kline_json, timestamp in klines_raw:
                kline = json.loads(kline_json)
                kline['timestamp'] = int(timestamp)  # Store timestamp in the kline dict
                klines.append(kline)

            # Current (most recent) kline
            current_kline = klines[0]
            current_ts = current_kline['timestamp'] / 1000  # Convert to seconds
            current_dt = datetime.fromtimestamp(current_ts)

            if period == 'day':
                # Previous day = second kline in the list
                if len(klines) >= 2:
                    prev_kline = klines[1]
                    return (
                        float(prev_kline['h']),
                        float(prev_kline['l']),
                        float(prev_kline['c'])
                    )

            elif period == 'week':
                # Previous week = kline from 7 days ago
                target_dt = current_dt - timedelta(days=7)
                target_ts = target_dt.timestamp() * 1000

                # Find kline closest to 7 days ago
                for kline in klines:
                    if kline['timestamp'] <= target_ts:
                        # Found a kline at or before target time
                        # Aggregate all klines in that week
                        week_start = target_dt - timedelta(days=target_dt.weekday())
                        week_end = week_start + timedelta(days=7)
                        week_start_ts = week_start.timestamp() * 1000
                        week_end_ts = week_end.timestamp() * 1000

                        week_klines = [k for k in klines if week_start_ts <= k['timestamp'] < week_end_ts]

                        if week_klines:
                            high = max(float(k['h']) for k in week_klines)
                            low = min(float(k['l']) for k in week_klines)
                            close = float(week_klines[-1]['c'])
                            return (high, low, close)

            elif period == 'month':
                # Previous month = kline from 30 days ago
                target_dt = current_dt - timedelta(days=30)
                target_ts = target_dt.timestamp() * 1000

                # Find kline closest to 30 days ago
                for kline in klines:
                    if kline['timestamp'] <= target_ts:
                        # Found a kline at or before target time
                        # Aggregate all klines in that month
                        month_start = target_dt.replace(day=1)
                        if target_dt.month == 12:
                            month_end = month_start.replace(year=month_start.year + 1, month=1)
                        else:
                            month_end = month_start.replace(month=month_start.month + 1)

                        month_start_ts = month_start.timestamp() * 1000
                        month_end_ts = month_end.timestamp() * 1000

                        month_klines = [k for k in klines if month_start_ts <= k['timestamp'] < month_end_ts]

                        if month_klines:
                            high = max(float(k['h']) for k in month_klines)
                            low = min(float(k['l']) for k in month_klines)
                            close = float(month_klines[-1]['c'])
                            return (high, low, close)

        except Exception as e:
            logger.error(f"Error getting previous {period} data for {symbol}: {e}")

        return None

    def _display_results(self, result: Dict):
        """Display detection results"""

        metadata = result.get('metadata', {})
        resistance = result.get('resistance', [])
        support = result.get('support', [])

        print(f"\n{'='*80}")
        print(f"Pivot S/R Detection Complete")
        print(f"{'='*80}")
        print(f"Symbol: {metadata.get('symbol')}")
        print(f"Current Price: ${metadata.get('current_price', 0):,.2f}")
        print(f"Processing Time: {metadata.get('processing_time_ms', 0):.2f}ms")
        print(f"Mode: {metadata.get('mode')}")
        print(f"{'='*80}")

        print(f"\n📈 Resistance Levels (Pivots): {len(resistance)}")
        print(f"{'='*80}")
        print(f"{'#':<4} {'Price':>12} {'Distance':>10} {'Strength':>10} {'Method':<40}")
        print(f"{'-'*80}")
        for i, level in enumerate(resistance[:10], 1):
            dist = ((level['price'] - metadata.get('current_price', 0)) / metadata.get('current_price', 1)) * 100
            method = level['method'][:38]  # Truncate if too long
            print(f"{i:<4} ${level['price']:>11,.2f} {dist:>9.2f}% {level['strength']:>9.2f} {method:<40}")

        print(f"\n📉 Support Levels (Pivots): {len(support)}")
        print(f"{'='*80}")
        print(f"{'#':<4} {'Price':>12} {'Distance':>10} {'Strength':>10} {'Method':<40}")
        print(f"{'-'*80}")
        for i, level in enumerate(support[:10], 1):
            dist = ((metadata.get('current_price', 0) - level['price']) / metadata.get('current_price', 1)) * 100
            method = level['method'][:38]  # Truncate if too long
            print(f"{i:<4} ${level['price']:>11,.2f} {dist:>9.2f}% {level['strength']:>9.2f} {method:<40}")

        print(f"{'='*80}\n")


def main():
    """CLI entry point"""

    import argparse

    parser = argparse.ArgumentParser(description='Pivot Point-based S/R Detector')
    parser.add_argument('--symbol', type=str, help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--all', action='store_true', help='Run for all symbols')
    parser.add_argument('--mode', type=str, default='basic',
                        choices=['basic', 'advanced'],
                        help='Detection mode (basic=day only, advanced=day+week+month)')
    parser.add_argument('--save', action='store_true', help='Save results to Redis (default: True)', default=True)

    args = parser.parse_args()

    # Initialize detector
    detector = PivotSRDetector()

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
