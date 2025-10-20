"""
Technical S/R Detector
Main detector class for interval-specific technical S/R analysis
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sr_core.sr_utils import RedisHelper, merge_nearby_levels, format_sr_output
from sr_methods_technical.swing_high_low import detect_swing_highs_lows
from sr_methods_technical.round_numbers import detect_round_numbers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TechnicalSRDetector:
    """
    Technical S/R Detector

    Detects support and resistance levels from kline data
    Interval-specific: Each timeframe has its own S/R levels
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Technical S/R Detector

        Args:
            config_path: Path to configuration JSON file (optional)
        """
        self.redis_helper = RedisHelper()
        self.config = self.load_config(config_path) if config_path else self.default_config()
        logger.info(f"Initialized TechnicalSRDetector with mode: {self.config['mode']}")

    def default_config(self) -> Dict:
        """Default configuration"""
        return {
            "mode": "basic",
            "intervals": ["1", "5", "15", "60", "240", "D"],
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "candles_limit": 1000,
            "methods": {
                "basic": {
                    "swing_high_low": {
                        "enabled": True,
                        "lookback": 5,
                        "min_touches": 2,
                        "touch_threshold": 0.002
                    },
                    "round_numbers": {
                        "enabled": True,
                        "max_distance_pct": 0.05,
                        "touch_threshold": 0.003
                    }
                }
            },
            "output": {
                "merge_threshold": 0.005,
                "max_resistance": 10,
                "max_support": 10,
                "ttl_seconds": 300
            }
        }

    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}, using default")
            return self.default_config()

    def detect(
        self,
        symbol: str,
        interval: str,
        mode: Optional[str] = None
    ) -> Dict:
        """
        Detect S/R levels for specific symbol and interval

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "15", "60", "D")
            mode: Detection mode ("basic", "medium", "high") - overrides config

        Returns:
            Dictionary with resistance and support levels
        """
        start_time = datetime.now()

        mode = mode or self.config['mode']
        logger.info(f"Detecting S/R for {symbol} {interval} ({mode} mode)")

        # Get candle data
        candles = self.redis_helper.get_klines(
            symbol,
            interval,
            limit=self.config['candles_limit']
        )

        if not candles:
            logger.error(f"No candles found for {symbol} {interval}")
            return format_sr_output([], [], {'error': 'No candle data'})

        logger.info(f"Fetched {len(candles)} candles for {symbol} {interval}")

        # Detect using configured methods
        if mode == "basic":
            result = self.detect_basic(candles)
        elif mode == "medium":
            result = self.detect_medium(candles)
        elif mode == "high":
            result = self.detect_high(candles)
        else:
            logger.error(f"Unknown mode: {mode}")
            return format_sr_output([], [], {'error': f'Unknown mode: {mode}'})

        # Post-processing
        result = self.post_process(result, candles[-1]['close'])

        # Add metadata
        elapsed = (datetime.now() - start_time).total_seconds()
        result['metadata'] = {
            'symbol': symbol,
            'interval': interval,
            'mode': mode,
            'candles_analyzed': len(candles),
            'processing_time_ms': round(elapsed * 1000, 2),
            'current_price': candles[-1]['close']
        }

        logger.info(f"Detection complete in {elapsed*1000:.2f}ms: "
                   f"{len(result['resistance'])} resistance, {len(result['support'])} support")

        return result

    def detect_basic(self, candles: List[Dict]) -> Dict:
        """
        BASIC mode detection
        Uses: Swing High/Low + Round Numbers

        Args:
            candles: List of candle dictionaries

        Returns:
            Dictionary with resistance and support levels
        """
        all_resistance = []
        all_support = []

        # Method 1: Swing High/Low
        if self.config['methods']['basic']['swing_high_low']['enabled']:
            swing_config = self.config['methods']['basic']['swing_high_low']
            swing_result = detect_swing_highs_lows(
                candles,
                lookback=swing_config['lookback'],
                min_touches=swing_config['min_touches'],
                touch_threshold=swing_config['touch_threshold']
            )
            all_resistance.extend(swing_result['resistance'])
            all_support.extend(swing_result['support'])
            logger.info(f"Swing: {len(swing_result['resistance'])} R, {len(swing_result['support'])} S")

        # Method 2: Round Numbers
        if self.config['methods']['basic']['round_numbers']['enabled']:
            round_config = self.config['methods']['basic']['round_numbers']
            round_result = detect_round_numbers(
                candles,
                max_distance_pct=round_config['max_distance_pct'],
                touch_threshold=round_config['touch_threshold']
            )
            all_resistance.extend(round_result['resistance'])
            all_support.extend(round_result['support'])
            logger.info(f"Round: {len(round_result['resistance'])} R, {len(round_result['support'])} S")

        return format_sr_output(all_resistance, all_support)

    def detect_medium(self, candles: List[Dict]) -> Dict:
        """
        MEDIUM mode detection
        Uses: BASIC + Volume Profile

        Args:
            candles: List of candle dictionaries

        Returns:
            Dictionary with resistance and support levels
        """
        # Start with BASIC
        result = self.detect_basic(candles)

        # TODO: Add Volume Profile in Phase 2
        logger.info("MEDIUM mode: Volume Profile not yet implemented, using BASIC")

        return result

    def detect_high(self, candles: List[Dict]) -> Dict:
        """
        HIGH mode detection
        Uses: MEDIUM + Pivot Points + Fibonacci + Moving Average + Bollinger Bands

        Args:
            candles: List of candle dictionaries

        Returns:
            Dictionary with resistance and support levels
        """
        # Start with MEDIUM
        result = self.detect_medium(candles)

        # TODO: Add remaining methods in Phase 6
        logger.info("HIGH mode: Additional methods not yet implemented, using MEDIUM")

        return result

    def post_process(self, result: Dict, current_price: float) -> Dict:
        """
        Post-process detected levels

        Args:
            result: Raw detection result
            current_price: Current market price

        Returns:
            Processed result
        """
        output_config = self.config['output']

        # Merge nearby levels
        if result['resistance']:
            result['resistance'] = merge_nearby_levels(
                result['resistance'],
                threshold=output_config['merge_threshold']
            )

        if result['support']:
            result['support'] = merge_nearby_levels(
                result['support'],
                threshold=output_config['merge_threshold']
            )

        # Limit number of levels
        result['resistance'] = result['resistance'][:output_config['max_resistance']]
        result['support'] = result['support'][:output_config['max_support']]

        # Sort resistance ascending (closest first)
        result['resistance'] = sorted(result['resistance'], key=lambda x: x['price'])

        # Sort support descending (closest first)
        result['support'] = sorted(result['support'], key=lambda x: x['price'], reverse=True)

        return result

    def save_to_redis(self, symbol: str, interval: str, result: Dict, mode: Optional[str] = None):
        """
        Save detection result to Redis

        Args:
            symbol: Trading symbol
            interval: Time interval
            result: Detection result
            mode: Detection mode (optional, uses config if not provided)
        """
        mode = mode or self.config['mode']
        key = f"sr:technical:{mode}:{interval}.{symbol}"
        ttl = self.config['output']['ttl_seconds']

        self.redis_helper.save_sr_result(key, result, ttl)
        logger.info(f"Saved result to Redis: {key}")

    def detect_and_save(
        self,
        symbol: str,
        interval: str,
        mode: Optional[str] = None
    ) -> Dict:
        """
        Detect S/R levels and save to Redis

        Args:
            symbol: Trading symbol
            interval: Time interval
            mode: Detection mode

        Returns:
            Detection result
        """
        result = self.detect(symbol, interval, mode)
        self.save_to_redis(symbol, interval, result, mode)
        return result


def main():
    """Main function for testing and CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Technical S/R Detection')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--interval', type=str, default='15', help='Time interval')
    parser.add_argument('--mode', type=str, default='basic', choices=['basic', 'medium', 'high'],
                       help='Detection mode')
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--save', action='store_true', help='Save to Redis')
    parser.add_argument('--all', action='store_true', help='Process all symbols and intervals')

    args = parser.parse_args()

    # Initialize detector
    detector = TechnicalSRDetector(config_path=args.config)

    if args.all:
        # Process all configured symbols and intervals
        print(f"\nProcessing all symbols and intervals ({args.mode} mode)...\n")

        for symbol in detector.config['symbols']:
            for interval in detector.config['intervals']:
                print(f"{'='*60}")
                print(f"Symbol: {symbol}, Interval: {interval}")
                print(f"{'='*60}")

                if args.save:
                    result = detector.detect_and_save(symbol, interval, args.mode)
                else:
                    result = detector.detect(symbol, interval, args.mode)

                # Display summary
                print(f"\nCurrent Price: ${result['metadata']['current_price']:,.2f}")
                print(f"Processing Time: {result['metadata']['processing_time_ms']}ms")

                print(f"\nResistance ({len(result['resistance'])}):")
                for level in result['resistance'][:5]:
                    dist = ((level['price'] - result['metadata']['current_price']) /
                           result['metadata']['current_price'] * 100)
                    print(f"  ${level['price']:,.2f} (+{dist:.2f}%) - {level['method']} - "
                          f"Strength: {level['strength']}, Touches: {level['touches']}")

                print(f"\nSupport ({len(result['support'])}):")
                for level in result['support'][:5]:
                    dist = ((result['metadata']['current_price'] - level['price']) /
                           result['metadata']['current_price'] * 100)
                    print(f"  ${level['price']:,.2f} (-{dist:.2f}%) - {level['method']} - "
                          f"Strength: {level['strength']}, Touches: {level['touches']}")

                print()
    else:
        # Process single symbol/interval
        print(f"\nDetecting S/R for {args.symbol} {args.interval} ({args.mode} mode)...\n")

        if args.save:
            result = detector.detect_and_save(args.symbol, args.interval, args.mode)
        else:
            result = detector.detect(args.symbol, args.interval, args.mode)

        # Display result
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
