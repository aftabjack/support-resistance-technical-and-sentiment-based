"""
Moving Average-based S/R Detection
EMAs act as dynamic support/resistance when price is near them
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """
    Calculate Exponential Moving Average

    Args:
        prices: List of prices (chronological order, oldest first)
        period: EMA period

    Returns:
        List of EMA values (same length as prices, None for insufficient data)
    """
    if len(prices) < period:
        return [None] * len(prices)

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


def get_ema_levels(
    klines: List[Dict],
    current_price: float = None,
    periods: List[int] = [20, 50, 100, 200]
) -> Dict:
    """
    Get current EMA levels as potential S/R

    Args:
        klines: List of kline dicts with 'c' (close) key
        current_price: Current price for classification
        periods: EMA periods to calculate

    Returns:
        Dict with EMA levels and metadata
    """
    if not klines or len(klines) < max(periods):
        logger.warning(f"Not enough klines for EMA calculation (need {max(periods)}, have {len(klines)})")
        return {'levels': [], 'metadata': {}}

    # Extract close prices (chronological order)
    closes = [float(k['c']) for k in klines]

    levels = []

    for period in periods:
        if len(closes) >= period:
            ema_values = calculate_ema(closes, period)
            current_ema = ema_values[-1] if ema_values and ema_values[-1] is not None else None

            if current_ema:
                distance_pct = ((current_ema - current_price) / current_price) * 100 if current_price else 0

                # EMA strength based on period and distance
                # Closer EMAs are more reactive, longer EMAs are more significant
                if period == 20:
                    base_strength = 0.50
                elif period == 50:
                    base_strength = 0.60
                elif period == 100:
                    base_strength = 0.65
                elif period == 200:
                    base_strength = 0.70
                else:
                    base_strength = 0.50

                # Reduce strength if price is far from EMA
                if abs(distance_pct) > 5:
                    base_strength *= 0.5  # Far away, less relevant
                elif abs(distance_pct) > 2:
                    base_strength *= 0.8  # Somewhat far

                level = {
                    'price': current_ema,
                    'strength': base_strength,
                    'method': f'ema_{period}',
                    'distance_pct': distance_pct,
                    'touches': 1
                }

                levels.append(level)

    # Classify as resistance or support
    resistance = []
    support = []

    if current_price:
        for level in levels:
            if level['price'] > current_price:
                resistance.append(level)
            else:
                support.append(level)
    else:
        resistance = levels.copy()
        support = levels.copy()

    # Sort by price
    resistance = sorted(resistance, key=lambda x: x['price'])
    support = sorted(support, key=lambda x: x['price'], reverse=True)

    return {
        'resistance': resistance,
        'support': support,
        'metadata': {
            'periods_calculated': [p for p in periods if len(closes) >= p],
            'klines_used': len(klines)
        }
    }


def check_ema_confluence(price: float, klines: List[Dict], tolerance: float = 0.01) -> Dict:
    """
    Check if a price level is near any EMA (for confluence detection)

    Args:
        price: Price level to check
        klines: List of kline dicts
        tolerance: Distance tolerance (0.01 = 1%)

    Returns:
        Dict with matching EMAs
    """
    if not klines or len(klines) < 20:
        return {'has_confluence': False, 'emas': []}

    closes = [float(k['c']) for k in klines]
    periods = [20, 50, 100, 200]

    matching_emas = []

    for period in periods:
        if len(closes) >= period:
            ema_values = calculate_ema(closes, period)
            current_ema = ema_values[-1] if ema_values and ema_values[-1] is not None else None

            if current_ema:
                distance = abs(price - current_ema) / price
                if distance <= tolerance:
                    matching_emas.append({
                        'period': period,
                        'value': current_ema,
                        'distance': distance
                    })

    return {
        'has_confluence': len(matching_emas) > 0,
        'emas': matching_emas,
        'count': len(matching_emas)
    }
