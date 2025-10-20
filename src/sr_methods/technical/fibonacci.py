"""
Fibonacci Retracement-based S/R Detection Methods
Calculates Fibonacci levels from recent swing highs/lows
"""

from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Standard Fibonacci levels
FIB_LEVELS = {
    0.0: 'fib_0.0',
    0.236: 'fib_23.6',
    0.382: 'fib_38.2',
    0.5: 'fib_50.0',
    0.618: 'fib_61.8',
    0.786: 'fib_78.6',
    1.0: 'fib_100.0',
    1.272: 'fib_ext_127.2',
    1.618: 'fib_ext_161.8'
}


def detect_fibonacci_sr(
    klines: List[Dict],
    current_price: float = None,
    lookback: int = 100
) -> Dict:
    """
    Detect S/R levels from Fibonacci retracements

    Args:
        klines: List of kline dicts with o, h, l, c, v keys
        current_price: Current price for filtering
        lookback: Number of klines to look back for swing high/low

    Returns:
        Dict with resistance and support levels from Fibonacci
    """

    if not klines or len(klines) < 20:
        logger.warning("Not enough klines for Fibonacci analysis")
        return {'resistance': [], 'support': []}

    # Limit lookback to available data
    lookback = min(lookback, len(klines))

    # Find swing high and swing low in the lookback period
    swing_high, swing_high_idx = _find_swing_high(klines[:lookback])
    swing_low, swing_low_idx = _find_swing_low(klines[:lookback])

    if swing_high is None or swing_low is None:
        logger.warning("Could not find swing high/low")
        return {'resistance': [], 'support': []}

    logger.info(f"Swing High: ${swing_high:,.2f} (index {swing_high_idx})")
    logger.info(f"Swing Low: ${swing_low:,.2f} (index {swing_low_idx})")

    # Determine trend direction
    # If swing high is more recent, we're in a downtrend (use retracements from high to low)
    # If swing low is more recent, we're in an uptrend (use retracements from low to high)

    resistance = []
    support = []

    if swing_high_idx < swing_low_idx:
        # Uptrend (low is more recent)
        logger.info("Detected UPTREND - Fib levels from low to high")
        fib_range = swing_high - swing_low

        for level, name in FIB_LEVELS.items():
            price = swing_low + (fib_range * level)

            # Strength based on common Fibonacci levels
            if level in [0.382, 0.5, 0.618]:
                strength = 0.80  # Strong levels
            elif level in [0.236, 0.786, 1.0]:
                strength = 0.70  # Medium levels
            else:
                strength = 0.60  # Weaker levels (extensions)

            level_dict = {
                'price': price,
                'strength': strength,
                'method': f'{name}_uptrend',
                'touches': 1
            }

            if current_price:
                if price > current_price:
                    resistance.append(level_dict)
                else:
                    support.append(level_dict)
            else:
                resistance.append(level_dict.copy())
                support.append(level_dict.copy())

    else:
        # Downtrend (high is more recent)
        logger.info("Detected DOWNTREND - Fib levels from high to low")
        fib_range = swing_high - swing_low

        for level, name in FIB_LEVELS.items():
            price = swing_high - (fib_range * level)

            # Strength based on common Fibonacci levels
            if level in [0.382, 0.5, 0.618]:
                strength = 0.80  # Strong levels
            elif level in [0.236, 0.786, 1.0]:
                strength = 0.70  # Medium levels
            else:
                strength = 0.60  # Weaker levels (extensions)

            level_dict = {
                'price': price,
                'strength': strength,
                'method': f'{name}_downtrend',
                'touches': 1
            }

            if current_price:
                if price > current_price:
                    resistance.append(level_dict)
                else:
                    support.append(level_dict)
            else:
                resistance.append(level_dict.copy())
                support.append(level_dict.copy())

    # Sort by price
    resistance = sorted(resistance, key=lambda x: x['price'])
    support = sorted(support, key=lambda x: x['price'], reverse=True)

    return {
        'resistance': resistance[:10],
        'support': support[:10]
    }


def _find_swing_high(klines: List[Dict]) -> Tuple[Optional[float], Optional[int]]:
    """Find the highest high in the klines"""
    if not klines:
        return None, None

    highs = [(float(k['h']), i) for i, k in enumerate(klines)]
    max_high, idx = max(highs, key=lambda x: x[0])
    return max_high, idx


def _find_swing_low(klines: List[Dict]) -> Tuple[Optional[float], Optional[int]]:
    """Find the lowest low in the klines"""
    if not klines:
        return None, None

    lows = [(float(k['l']), i) for i, k in enumerate(klines)]
    min_low, idx = min(lows, key=lambda x: x[0])
    return min_low, idx
