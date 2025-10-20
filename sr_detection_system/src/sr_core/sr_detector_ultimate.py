#!/usr/bin/env python3
"""
Ultimate S/R Detector ("Go Big")
Combines all detection methods for maximum accuracy
- Pivot Points (Day/Week/Month)
- Volume Profile (POC, HVN, LVN)
- VWAP + Standard Deviation Bands
- Fibonacci Retracements
- Confluence Detection

Target Accuracy: 90-95% at confluence zones
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
from sr_methods_technical.volume_profile import detect_volume_profile_sr
from sr_methods_technical.vwap import detect_vwap_sr
from sr_methods_technical.fibonacci import detect_fibonacci_sr
from sr_methods_technical.moving_averages import check_ema_confluence
from sr_methods_technical.confluence import detect_confluence, merge_all_sr_results


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UltimateSRDetector:
    """Ultimate S/R detector combining all methods"""

    def __init__(self, redis_helper: Optional[RedisHelper] = None):
        self.redis = redis_helper or RedisHelper()

    def detect_and_save(
        self,
        symbol: str,
        interval: str = '15',
        mode: str = 'confluence'
    ) -> Dict:
        """
        Detect S/R using all methods and save to Redis

        Args:
            symbol: Symbol (BTCUSDT, ETHUSDT, SOLUSDT)
            interval: Interval for kline data (default: 15 min)
            mode: 'confluence' (confluent zones) or 'all' (all levels)

        Returns:
            Detection result with resistance and support levels
        """

        start_time = time.time()

        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 ULTIMATE S/R DETECTION - {symbol} ({interval}min)")
        logger.info(f"{'='*70}")

        # Get current price
        current_price = self._get_current_price(symbol)
        if not current_price:
            logger.error(f"Could not get current price for {symbol}")
            return {'error': 'No current price available'}

        logger.info(f"💰 Current price: ${current_price:,.2f}")

        # Get klines for volume-based methods
        klines = self._get_klines(symbol, interval, limit=500)
        if not klines or len(klines) < 50:
            logger.error(f"Not enough kline data for {symbol}")
            return {'error': 'Not enough kline data'}

        logger.info(f"📊 Loaded {len(klines)} klines")

        # METHOD 1: Pivot Points (Day/Week/Month)
        logger.info(f"\n{'='*70}")
        logger.info("📍 METHOD 1: Pivot Points")
        logger.info(f"{'='*70}")

        prev_day = self._get_previous_period(symbol, 'day')
        prev_week = self._get_previous_period(symbol, 'week')
        prev_month = self._get_previous_period(symbol, 'month')

        pivot_result = detect_pivot_sr(
            prev_day=prev_day,
            prev_week=prev_week,
            prev_month=prev_month,
            current_price=current_price,
            include_fibonacci=True,
            include_camarilla=True
        )

        logger.info(f"✅ Found {len(pivot_result['resistance'])} resistance, {len(pivot_result['support'])} support")

        # METHOD 2: Volume Profile
        logger.info(f"\n{'='*70}")
        logger.info("📊 METHOD 2: Volume Profile (POC, HVN, LVN)")
        logger.info(f"{'='*70}")

        volume_result = detect_volume_profile_sr(
            klines=klines,
            current_price=current_price,
            num_bins=100,
            hvn_threshold=0.80,
            lvn_threshold=0.30
        )

        logger.info(f"✅ Found {len(volume_result['resistance'])} resistance, {len(volume_result['support'])} support")

        # METHOD 3: VWAP
        logger.info(f"\n{'='*70}")
        logger.info("📈 METHOD 3: VWAP + Standard Deviation Bands")
        logger.info(f"{'='*70}")

        vwap_result = detect_vwap_sr(
            klines=klines,
            current_price=current_price,
            num_std_bands=2
        )

        logger.info(f"✅ Found {len(vwap_result['resistance'])} resistance, {len(vwap_result['support'])} support")

        # METHOD 4: Fibonacci
        logger.info(f"\n{'='*70}")
        logger.info("🌀 METHOD 4: Fibonacci Retracements")
        logger.info(f"{'='*70}")

        fib_result = detect_fibonacci_sr(
            klines=klines,
            current_price=current_price,
            lookback=100
        )

        logger.info(f"✅ Found {len(fib_result['resistance'])} resistance, {len(fib_result['support'])} support")

        # Combine results
        logger.info(f"\n{'='*70}")
        logger.info("🎯 COMBINING ALL METHODS")
        logger.info(f"{'='*70}")

        if mode == 'confluence':
            # Confluence mode: Only return zones where 2+ methods agree
            result = detect_confluence(
                sr_results=[pivot_result, volume_result, vwap_result, fib_result],
                price_tolerance=0.005,  # 0.5%
                min_methods=2
            )

            # Check EMA confluence for each zone
            logger.info("🔍 Checking EMA confluence for confluent zones...")
            ema_boost_count = 0

            for level in result['resistance'] + result['support']:
                ema_conf = check_ema_confluence(level['price'], klines, tolerance=0.01)

                if ema_conf['has_confluence']:
                    # Boost strength when EMAs align (0.05 per EMA, max 0.2)
                    ema_boost = min(ema_conf['count'] * 0.05, 0.2)
                    level['strength'] = min(level['strength'] + ema_boost, 1.0)

                    # Add EMA info to methods
                    ema_methods = [f"ema_{e['period']}" for e in ema_conf['emas']]
                    level['methods'].extend(ema_methods)
                    level['num_methods'] = len(level['methods'])

                    # Store EMA confluence details
                    level['ema_confluence'] = {
                        'count': ema_conf['count'],
                        'periods': [e['period'] for e in ema_conf['emas']],
                        'boost': ema_boost
                    }

                    ema_boost_count += 1

            logger.info(f"✅ EMA confluence boosted {ema_boost_count} levels")
            logger.info(f"🔥 Confluence zones (2+ methods agree):")
        else:
            # All mode: Return all levels from all methods
            result = merge_all_sr_results(
                pivot_result=pivot_result,
                volume_result=volume_result,
                vwap_result=vwap_result,
                fib_result=fib_result,
                current_price=current_price
            )
            logger.info(f"📋 All S/R levels from all methods:")

        # Add metadata
        processing_time = (time.time() - start_time) * 1000

        result['timestamp'] = time.time()
        result['metadata'] = {
            'symbol': symbol,
            'interval': interval,
            'mode': mode,
            'current_price': current_price,
            'processing_time_ms': round(processing_time, 2),
            'klines_analyzed': len(klines),
            'methods_used': ['pivots', 'volume_profile', 'vwap', 'fibonacci', 'ema_confluence'],
            'confluence_enabled': mode == 'confluence'
        }

        # Save to Redis
        redis_key = f"sr:ultimate:{mode}:{interval}.{symbol}"
        self.redis.save_sr_result(redis_key, result, ttl=300)  # 5 minute TTL
        logger.info(f"💾 Saved result to Redis: {redis_key}")

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

    def _get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[Dict]:
        """Get kline data from Redis"""

        key = f"{interval}.{symbol}"

        try:
            # Get klines from sorted set (with scores = timestamps)
            klines_raw = self.redis.redis_client.zrevrange(key, 0, limit - 1, withscores=True)

            if not klines_raw:
                return []

            # Parse klines
            klines = []
            for kline_json, timestamp in klines_raw:
                kline = json.loads(kline_json)
                kline['timestamp'] = int(timestamp)
                klines.append(kline)

            return klines

        except Exception as e:
            logger.error(f"Error getting klines for {symbol} {interval}: {e}")
            return []

    def _get_previous_period(self, symbol: str, period: str) -> Optional[Tuple[float, float, float]]:
        """Get previous period's high, low, close from Daily klines"""

        # Use Daily klines for all calculations
        key = f"D.{symbol}"

        try:
            # Get all daily klines WITH SCORES (timestamp is the score)
            klines_raw = self.redis.redis_client.zrevrange(key, 0, -1, withscores=True)

            if not klines_raw or len(klines_raw) < 2:
                logger.warning(f"Not enough daily kline data for {symbol}")
                return None

            # Parse klines with their timestamps (score)
            klines = []
            for kline_json, timestamp in klines_raw:
                kline = json.loads(kline_json)
                kline['timestamp'] = int(timestamp)
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
                # Previous week
                target_dt = current_dt - timedelta(days=7)
                target_ts = target_dt.timestamp() * 1000

                for kline in klines:
                    if kline['timestamp'] <= target_ts:
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
                # Previous month
                target_dt = current_dt - timedelta(days=30)
                target_ts = target_dt.timestamp() * 1000

                for kline in klines:
                    if kline['timestamp'] <= target_ts:
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

        print(f"\n{'='*90}")
        print(f"🚀 ULTIMATE S/R DETECTION COMPLETE")
        print(f"{'='*90}")
        print(f"Symbol: {metadata.get('symbol')}")
        print(f"Current Price: ${metadata.get('current_price', 0):,.2f}")
        print(f"Processing Time: {metadata.get('processing_time_ms', 0):.2f}ms")
        print(f"Mode: {metadata.get('mode')} ({'Confluence zones' if metadata.get('confluence_enabled') else 'All levels'})")
        print(f"Methods: {', '.join(metadata.get('methods_used', []))}")
        print(f"{'='*90}")

        # Display resistance
        print(f"\n📈 RESISTANCE LEVELS: {len(resistance)}")
        print(f"{'='*90}")
        print(f"{'#':<4} {'Price':>14} {'Distance':>10} {'Strength':>10} {'Method':<50}")
        print(f"{'-'*90}")
        for i, level in enumerate(resistance[:15], 1):
            dist = ((level['price'] - metadata.get('current_price', 0)) / metadata.get('current_price', 1)) * 100

            # Format method (truncate if too long)
            method = level.get('method', 'unknown')
            if level.get('num_methods'):
                # Confluence level - show all methods
                methods_str = ', '.join(level.get('methods', []))[:48]
                method = f"{method} ({methods_str})"

                # Add EMA indicator if present
                if level.get('ema_confluence'):
                    ema_info = level['ema_confluence']
                    method = f"{method} +EMA({ema_info['count']})"[:48]

            method = method[:48]

            print(f"{i:<4} ${level['price']:>13,.2f} {dist:>9.2f}% {level['strength']:>9.2f} {method:<50}")

        # Display support
        print(f"\n📉 SUPPORT LEVELS: {len(support)}")
        print(f"{'='*90}")
        print(f"{'#':<4} {'Price':>14} {'Distance':>10} {'Strength':>10} {'Method':<50}")
        print(f"{'-'*90}")
        for i, level in enumerate(support[:15], 1):
            dist = ((metadata.get('current_price', 0) - level['price']) / metadata.get('current_price', 1)) * 100

            # Format method (truncate if too long)
            method = level.get('method', 'unknown')
            if level.get('num_methods'):
                # Confluence level - show all methods
                methods_str = ', '.join(level.get('methods', []))[:48]
                method = f"{method} ({methods_str})"

                # Add EMA indicator if present
                if level.get('ema_confluence'):
                    ema_info = level['ema_confluence']
                    method = f"{method} +EMA({ema_info['count']})"[:48]

            method = method[:48]

            print(f"{i:<4} ${level['price']:>13,.2f} {dist:>9.2f}% {level['strength']:>9.2f} {method:<50}")

        print(f"{'='*90}\n")


def main():
    """CLI entry point"""

    import argparse

    parser = argparse.ArgumentParser(description='Ultimate S/R Detector (Go Big)')
    parser.add_argument('--symbol', type=str, help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--all', action='store_true', help='Run for all symbols')
    parser.add_argument('--interval', type=str, default='15',
                        help='Interval for kline data (default: 15 min)')
    parser.add_argument('--mode', type=str, default='confluence',
                        choices=['confluence', 'all'],
                        help='Mode: confluence (2+ methods) or all (all levels)')
    parser.add_argument('--save', action='store_true', help='Save results to Redis (default: True)', default=True)

    args = parser.parse_args()

    # Initialize detector
    detector = UltimateSRDetector()

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
            detector.detect_and_save(
                symbol=symbol,
                interval=args.interval,
                mode=args.mode
            )
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}", exc_info=True)


if __name__ == "__main__":
    main()
