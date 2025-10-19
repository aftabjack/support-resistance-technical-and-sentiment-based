"""
VWAP-based S/R Detection Methods
Calculates VWAP and standard deviation bands
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def detect_vwap_sr(
    klines: List[Dict],
    current_price: float = None,
    num_std_bands: int = 2
) -> Dict:
    """
    Detect S/R levels from VWAP and standard deviation bands

    Args:
        klines: List of kline dicts with o, h, l, c, v keys
        current_price: Current price for filtering
        num_std_bands: Number of standard deviation bands (1, 2, or 3)

    Returns:
        Dict with resistance and support levels from VWAP bands
    """

    if not klines or len(klines) < 10:
        logger.warning("Not enough klines for VWAP analysis")
        return {'resistance': [], 'support': []}

    # Calculate VWAP
    cumulative_tpv = 0  # Typical Price × Volume
    cumulative_volume = 0

    for kline in klines:
        high = float(kline['h'])
        low = float(kline['l'])
        close = float(kline['c'])
        volume = float(kline['v'])

        typical_price = (high + low + close) / 3
        cumulative_tpv += typical_price * volume
        cumulative_volume += volume

    if cumulative_volume == 0:
        logger.warning("Total volume is zero, cannot calculate VWAP")
        return {'resistance': [], 'support': []}

    vwap = cumulative_tpv / cumulative_volume

    logger.info(f"VWAP: ${vwap:,.2f}")

    # Calculate standard deviation
    variance_sum = 0
    for kline in klines:
        high = float(kline['h'])
        low = float(kline['l'])
        close = float(kline['c'])
        volume = float(kline['v'])

        typical_price = (high + low + close) / 3
        variance_sum += ((typical_price - vwap) ** 2) * volume

    variance = variance_sum / cumulative_volume
    std_dev = variance ** 0.5

    logger.info(f"Standard Deviation: ${std_dev:,.2f}")

    # Build S/R levels
    resistance = []
    support = []

    # VWAP itself is a level
    vwap_level = {
        'price': vwap,
        'strength': 0.80,
        'method': 'vwap',
        'touches': 1
    }

    if current_price:
        if vwap > current_price:
            resistance.append(vwap_level)
        else:
            support.append(vwap_level)
    else:
        resistance.append(vwap_level.copy())
        support.append(vwap_level.copy())

    # Add standard deviation bands
    for i in range(1, num_std_bands + 1):
        upper_band = vwap + (i * std_dev)
        lower_band = vwap - (i * std_dev)

        # Strength decreases with distance from VWAP
        strength = 0.75 if i == 1 else (0.65 if i == 2 else 0.55)

        upper_level = {
            'price': upper_band,
            'strength': strength,
            'method': f'vwap_+{i}std',
            'touches': 1
        }

        lower_level = {
            'price': lower_band,
            'strength': strength,
            'method': f'vwap_-{i}std',
            'touches': 1
        }

        if current_price:
            if upper_band > current_price:
                resistance.append(upper_level)
            if lower_band < current_price:
                support.append(lower_level)
        else:
            resistance.append(upper_level)
            support.append(lower_level)

    # Sort by price
    resistance = sorted(resistance, key=lambda x: x['price'])
    support = sorted(support, key=lambda x: x['price'], reverse=True)

    return {
        'resistance': resistance,
        'support': support
    }
