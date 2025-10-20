#!/usr/bin/env python3
"""
Research Script - Test Technical Indicators with 1000 Klines
Tests Moving Averages, Bollinger Bands, ATR, etc. for S/R accuracy
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sr_core.sr_utils import RedisHelper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndicatorResearcher:
    """Research and test technical indicators for S/R detection"""

    def __init__(self):
        self.redis = RedisHelper()

    def get_klines(self, symbol: str, interval: str, limit: int = 1000) -> List[Dict]:
        """Get kline data from Redis"""
        key = f"{interval}.{symbol}"

        try:
            klines_raw = self.redis.redis_client.zrevrange(key, 0, limit - 1, withscores=True)

            if not klines_raw:
                return []

            klines = []
            for kline_json, timestamp in klines_raw:
                kline = json.loads(kline_json)
                kline['timestamp'] = int(timestamp)
                kline['close'] = float(kline['c'])
                kline['high'] = float(kline['h'])
                kline['low'] = float(kline['l'])
                kline['volume'] = float(kline['v'])
                klines.append(kline)

            # Reverse to chronological order (oldest first)
            return list(reversed(klines))

        except Exception as e:
            logger.error(f"Error getting klines: {e}")
            return []

    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return []

        ema = []
        multiplier = 2 / (period + 1)

        # Start with SMA for first value
        sma = sum(prices[:period]) / period
        ema.append(sma)

        # Calculate EMA for remaining values
        for price in prices[period:]:
            ema_value = (price - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)

        # Pad with None for first period-1 values
        return [None] * (period - 1) + ema

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """Calculate Bollinger Bands (Middle, Upper, Lower)"""
        if len(prices) < period:
            return [], [], []

        middle = []
        upper = []
        lower = []

        for i in range(len(prices)):
            if i < period - 1:
                middle.append(None)
                upper.append(None)
                lower.append(None)
            else:
                window = prices[i - period + 1:i + 1]
                sma = sum(window) / period
                variance = sum((x - sma) ** 2 for x in window) / period
                std = variance ** 0.5

                middle.append(sma)
                upper.append(sma + (std_dev * std))
                lower.append(sma - (std_dev * std))

        return middle, upper, lower

    def calculate_atr(self, klines: List[Dict], period: int = 14) -> List[float]:
        """Calculate Average True Range"""
        if len(klines) < period:
            return []

        true_ranges = []

        for i in range(1, len(klines)):
            high = klines[i]['high']
            low = klines[i]['low']
            prev_close = klines[i-1]['close']

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # Calculate ATR
        atr = []
        atr_value = sum(true_ranges[:period]) / period
        atr.append(atr_value)

        for tr in true_ranges[period:]:
            atr_value = ((atr[-1] * (period - 1)) + tr) / period
            atr.append(atr_value)

        # Pad with None for first values
        return [None] + [None] * (period - 1) + atr

    def test_ma_as_sr(self, klines: List[Dict], ma_values: List[float], ma_name: str) -> Dict:
        """Test how well MA acts as Support/Resistance"""
        if not ma_values or not klines:
            return {'touches': 0, 'bounces': 0, 'accuracy': 0}

        touches = 0
        bounces = 0

        for i in range(len(klines)):
            if ma_values[i] is None:
                continue

            price = klines[i]['close']
            ma = ma_values[i]

            # Check if price touched MA (within 0.5%)
            distance = abs(price - ma) / ma
            if distance < 0.005:  # Within 0.5%
                touches += 1

                # Check if it bounced (next few candles moved away)
                if i < len(klines) - 3:
                    # Check if price bounced in next 3 candles
                    future_prices = [klines[i+j]['close'] for j in range(1, 4) if i+j < len(klines)]
                    if future_prices:
                        avg_future = sum(future_prices) / len(future_prices)
                        future_distance = abs(avg_future - ma) / ma

                        if future_distance > distance * 1.5:  # Moved away
                            bounces += 1

        accuracy = (bounces / touches * 100) if touches > 0 else 0

        return {
            'touches': touches,
            'bounces': bounces,
            'accuracy': accuracy
        }

    def test_bollinger_as_sr(self, klines: List[Dict], upper: List[float], lower: List[float]) -> Dict:
        """Test how well Bollinger Bands act as S/R"""
        if not upper or not lower or not klines:
            return {'upper_bounces': 0, 'lower_bounces': 0, 'accuracy': 0}

        upper_touches = 0
        upper_bounces = 0
        lower_touches = 0
        lower_bounces = 0

        for i in range(len(klines)):
            if upper[i] is None or lower[i] is None:
                continue

            high = klines[i]['high']
            low = klines[i]['low']
            close = klines[i]['close']

            # Check upper band touch
            if high >= upper[i] * 0.995:  # Within 0.5%
                upper_touches += 1

                # Check bounce
                if i < len(klines) - 3:
                    future_closes = [klines[i+j]['close'] for j in range(1, 4) if i+j < len(klines)]
                    if future_closes and all(c < upper[i] * 0.99 for c in future_closes):
                        upper_bounces += 1

            # Check lower band touch
            if low <= lower[i] * 1.005:  # Within 0.5%
                lower_touches += 1

                # Check bounce
                if i < len(klines) - 3:
                    future_closes = [klines[i+j]['close'] for j in range(1, 4) if i+j < len(klines)]
                    if future_closes and all(c > lower[i] * 1.01 for c in future_closes):
                        lower_bounces += 1

        total_touches = upper_touches + lower_touches
        total_bounces = upper_bounces + lower_bounces
        accuracy = (total_bounces / total_touches * 100) if total_touches > 0 else 0

        return {
            'upper_touches': upper_touches,
            'upper_bounces': upper_bounces,
            'lower_touches': lower_touches,
            'lower_bounces': lower_bounces,
            'total_touches': total_touches,
            'total_bounces': total_bounces,
            'accuracy': accuracy
        }

    def run_research(self, symbol: str = 'BTCUSDT', interval: str = '15'):
        """Run complete research on all indicators"""

        print(f"\n{'='*80}")
        print(f"🔬 INDICATOR RESEARCH - {symbol} ({interval}min)")
        print(f"{'='*80}\n")

        # Get klines
        logger.info(f"Fetching klines for {symbol} {interval}...")
        klines = self.get_klines(symbol, interval, limit=1000)

        if not klines:
            print("❌ No kline data available")
            return

        print(f"✅ Loaded {len(klines)} klines")
        print(f"📊 Data range: {len(klines)} candles (~{len(klines) * int(interval) / 60:.1f} hours)")

        current_price = klines[-1]['close']
        print(f"💰 Current price: ${current_price:,.2f}\n")

        closes = [k['close'] for k in klines]

        # ======================================================================
        # TEST 1: MOVING AVERAGES
        # ======================================================================
        print(f"{'='*80}")
        print("📈 TEST 1: EXPONENTIAL MOVING AVERAGES (EMA)")
        print(f"{'='*80}\n")

        ma_periods = [20, 50, 100, 200]
        ma_results = {}

        for period in ma_periods:
            if len(closes) >= period:
                ema = self.calculate_ema(closes, period)
                current_ema = ema[-1] if ema and ema[-1] is not None else None

                if current_ema:
                    distance = ((current_price - current_ema) / current_ema) * 100

                    # Test as S/R
                    test_result = self.test_ma_as_sr(klines, ema, f'EMA{period}')

                    ma_results[period] = {
                        'current_value': current_ema,
                        'distance_pct': distance,
                        'test_result': test_result
                    }

                    print(f"EMA {period}:")
                    print(f"  Current Value: ${current_ema:,.2f}")
                    print(f"  Distance: {distance:+.2f}%")
                    print(f"  Touches: {test_result['touches']}")
                    print(f"  Bounces: {test_result['bounces']}")
                    print(f"  Accuracy: {test_result['accuracy']:.1f}%")
                    print()

        # ======================================================================
        # TEST 2: BOLLINGER BANDS
        # ======================================================================
        print(f"{'='*80}")
        print("📊 TEST 2: BOLLINGER BANDS (20, 2σ)")
        print(f"{'='*80}\n")

        middle, upper, lower = self.calculate_bollinger_bands(closes, period=20, std_dev=2.0)

        if middle and middle[-1] is not None:
            current_middle = middle[-1]
            current_upper = upper[-1]
            current_lower = lower[-1]
            bandwidth = ((current_upper - current_lower) / current_middle) * 100

            bb_result = self.test_bollinger_as_sr(klines, upper, lower)

            print(f"Bollinger Bands (20, 2σ):")
            print(f"  Upper Band: ${current_upper:,.2f} (+{((current_upper - current_price) / current_price) * 100:.2f}%)")
            print(f"  Middle:     ${current_middle:,.2f}")
            print(f"  Lower Band: ${current_lower:,.2f} ({((current_lower - current_price) / current_price) * 100:.2f}%)")
            print(f"  Bandwidth:  {bandwidth:.2f}%")
            print(f"\n  Upper Touches: {bb_result['upper_touches']} | Bounces: {bb_result['upper_bounces']}")
            print(f"  Lower Touches: {bb_result['lower_touches']} | Bounces: {bb_result['lower_bounces']}")
            print(f"  Overall Accuracy: {bb_result['accuracy']:.1f}%")
            print()

        # ======================================================================
        # TEST 3: ATR LEVELS
        # ======================================================================
        print(f"{'='*80}")
        print("📉 TEST 3: ATR-BASED LEVELS (14)")
        print(f"{'='*80}\n")

        atr_values = self.calculate_atr(klines, period=14)

        if atr_values and atr_values[-1] is not None:
            current_atr = atr_values[-1]
            atr_pct = (current_atr / current_price) * 100

            # ATR-based S/R levels
            atr_levels = {
                'R2': current_price + (2 * current_atr),
                'R1': current_price + current_atr,
                'S1': current_price - current_atr,
                'S2': current_price - (2 * current_atr)
            }

            print(f"ATR (14): ${current_atr:,.2f} ({atr_pct:.2f}% of price)")
            print(f"\nATR-Based Levels:")
            print(f"  R2: ${atr_levels['R2']:,.2f} (+{((atr_levels['R2'] - current_price) / current_price) * 100:.2f}%)")
            print(f"  R1: ${atr_levels['R1']:,.2f} (+{((atr_levels['R1'] - current_price) / current_price) * 100:.2f}%)")
            print(f"  Current: ${current_price:,.2f}")
            print(f"  S1: ${atr_levels['S1']:,.2f} ({((atr_levels['S1'] - current_price) / current_price) * 100:.2f}%)")
            print(f"  S2: ${atr_levels['S2']:,.2f} ({((atr_levels['S2'] - current_price) / current_price) * 100:.2f}%)")
            print()

        # ======================================================================
        # SUMMARY
        # ======================================================================
        print(f"{'='*80}")
        print("📋 SUMMARY & RECOMMENDATIONS")
        print(f"{'='*80}\n")

        print("Accuracy Results:")
        for period, data in ma_results.items():
            acc = data['test_result']['accuracy']
            touches = data['test_result']['touches']
            print(f"  EMA {period}: {acc:.1f}% accuracy ({touches} touches)")

        if middle and middle[-1]:
            print(f"  Bollinger Bands: {bb_result['accuracy']:.1f}% accuracy ({bb_result['total_touches']} touches)")

        print("\nData Sufficiency:")
        print(f"  Klines available: {len(klines)}")
        print(f"  EMA 200 needs: 200 ✅" if len(klines) >= 200 else "  EMA 200 needs: 200 ❌")
        print(f"  Bollinger needs: 20 ✅")
        print(f"  ATR needs: 14 ✅")

        print("\n💡 Recommendations:")

        # Find best performing EMA
        if ma_results:
            best_ema = max(ma_results.items(), key=lambda x: x[1]['test_result']['accuracy'])
            print(f"  - Best EMA: {best_ema[0]} ({best_ema[1]['test_result']['accuracy']:.1f}% accuracy)")

        if middle and bb_result['accuracy'] > 70:
            print(f"  - Bollinger Bands: Good ({bb_result['accuracy']:.1f}% accuracy)")

        print("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Research Technical Indicators')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Symbol to analyze')
    parser.add_argument('--interval', type=str, default='15', help='Interval (1, 5, 15, 60, etc.)')

    args = parser.parse_args()

    researcher = IndicatorResearcher()
    researcher.run_research(symbol=args.symbol, interval=args.interval)


if __name__ == '__main__':
    main()
