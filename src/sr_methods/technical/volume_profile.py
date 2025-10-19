"""
Volume Profile-based S/R Detection Methods
Calculates Point of Control (POC) and High/Low Volume Nodes (HVN/LVN)
"""

from typing import Dict, List, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def detect_volume_profile_sr(
    klines: List[Dict],
    current_price: float = None,
    num_bins: int = 100,
    hvn_threshold: float = 0.8,
    lvn_threshold: float = 0.3
) -> Dict:
    """
    Detect S/R levels from Volume Profile (Volume-at-Price)

    Args:
        klines: List of kline dicts with o, h, l, c, v keys
        current_price: Current price for filtering
        num_bins: Number of price bins to use (default: 100)
        hvn_threshold: HVN threshold as percentile (0.8 = top 20% volume)
        lvn_threshold: LVN threshold as percentile (0.3 = bottom 30% volume)

    Returns:
        Dict with resistance and support levels including POC
    """

    if not klines or len(klines) < 10:
        logger.warning("Not enough klines for volume profile analysis")
        return {'resistance': [], 'support': []}

    # Extract price range
    all_highs = [float(k['h']) for k in klines]
    all_lows = [float(k['l']) for k in klines]
    price_min = min(all_lows)
    price_max = max(all_highs)

    # Create price bins
    bin_size = (price_max - price_min) / num_bins
    if bin_size == 0:
        logger.warning("Price range is zero, cannot create volume profile")
        return {'resistance': [], 'support': []}

    # Volume profile: bin_index -> total_volume
    volume_profile = defaultdict(float)

    # Distribute volume across bins for each kline
    for kline in klines:
        high = float(kline['h'])
        low = float(kline['l'])
        volume = float(kline['v'])

        # Calculate which bins this kline's price range covers
        low_bin = int((low - price_min) / bin_size)
        high_bin = int((high - price_min) / bin_size)

        # Clamp to valid range
        low_bin = max(0, min(low_bin, num_bins - 1))
        high_bin = max(0, min(high_bin, num_bins - 1))

        # Distribute volume evenly across bins
        bins_covered = high_bin - low_bin + 1
        volume_per_bin = volume / bins_covered

        for bin_idx in range(low_bin, high_bin + 1):
            volume_profile[bin_idx] += volume_per_bin

    # Find POC (Point of Control) - bin with highest volume
    if not volume_profile:
        logger.warning("Volume profile is empty")
        return {'resistance': [], 'support': []}

    poc_bin = max(volume_profile.items(), key=lambda x: x[1])[0]
    poc_price = price_min + (poc_bin * bin_size) + (bin_size / 2)
    poc_volume = volume_profile[poc_bin]

    logger.info(f"POC: ${poc_price:,.2f} (bin {poc_bin}, volume: {poc_volume:,.0f})")

    # Calculate volume percentiles for HVN/LVN detection
    volumes = list(volume_profile.values())
    volumes_sorted = sorted(volumes)
    hvn_cutoff = volumes_sorted[int(len(volumes_sorted) * hvn_threshold)]
    lvn_cutoff = volumes_sorted[int(len(volumes_sorted) * lvn_threshold)]

    # Collect HVN (High Volume Nodes) and LVN (Low Volume Nodes)
    hvn_bins = []
    lvn_bins = []

    for bin_idx, vol in volume_profile.items():
        if vol >= hvn_cutoff:
            hvn_bins.append(bin_idx)
        elif vol <= lvn_cutoff:
            lvn_bins.append(bin_idx)

    logger.info(f"Found {len(hvn_bins)} HVN bins and {len(lvn_bins)} LVN bins")

    # Merge adjacent bins into levels
    hvn_levels = _merge_adjacent_bins(hvn_bins, bin_size, price_min, volume_profile)
    lvn_levels = _merge_adjacent_bins(lvn_bins, bin_size, price_min, volume_profile)

    # Build S/R levels
    resistance = []
    support = []

    # POC is always a strong level (can act as both S and R)
    poc_level = {
        'price': poc_price,
        'strength': 1.0,
        'method': 'volume_poc',
        'volume': poc_volume,
        'touches': 1
    }

    if current_price:
        if poc_price > current_price:
            resistance.append(poc_level)
        else:
            support.append(poc_level)
    else:
        # Add to both if no current price
        resistance.append(poc_level.copy())
        support.append(poc_level.copy())

    # HVN levels (high volume = strong S/R)
    for level in hvn_levels:
        level['method'] = 'volume_hvn'
        level['strength'] = 0.85  # HVN is strong
        if current_price:
            if level['price'] > current_price:
                resistance.append(level)
            else:
                support.append(level)
        else:
            resistance.append(level.copy())
            support.append(level.copy())

    # LVN levels (low volume = weak S/R, but can act as magnets)
    for level in lvn_levels:
        level['method'] = 'volume_lvn'
        level['strength'] = 0.60  # LVN is weaker
        if current_price:
            if level['price'] > current_price:
                resistance.append(level)
            else:
                support.append(level)
        else:
            resistance.append(level.copy())
            support.append(level.copy())

    # Sort by price
    resistance = sorted(resistance, key=lambda x: x['price'])
    support = sorted(support, key=lambda x: x['price'], reverse=True)

    return {
        'resistance': resistance[:10],  # Top 10
        'support': support[:10]          # Top 10
    }


def _merge_adjacent_bins(
    bins: List[int],
    bin_size: float,
    price_min: float,
    volume_profile: Dict[int, float]
) -> List[Dict]:
    """
    Merge adjacent bins into single levels

    Returns:
        List of level dicts with price, volume
    """
    if not bins:
        return []

    bins = sorted(bins)
    levels = []
    current_group = [bins[0]]

    for bin_idx in bins[1:]:
        # Check if adjacent to current group
        if bin_idx == current_group[-1] + 1:
            current_group.append(bin_idx)
        else:
            # Finalize current group
            levels.append(_create_level_from_group(current_group, bin_size, price_min, volume_profile))
            current_group = [bin_idx]

    # Don't forget last group
    if current_group:
        levels.append(_create_level_from_group(current_group, bin_size, price_min, volume_profile))

    return levels


def _create_level_from_group(
    group: List[int],
    bin_size: float,
    price_min: float,
    volume_profile: Dict[int, float]
) -> Dict:
    """Create a level from a group of adjacent bins"""

    # Average price of the group
    avg_bin = sum(group) / len(group)
    price = price_min + (avg_bin * bin_size) + (bin_size / 2)

    # Total volume
    total_volume = sum(volume_profile[bin_idx] for bin_idx in group)

    return {
        'price': price,
        'volume': total_volume,
        'touches': len(group)  # Number of bins merged
    }
