"""
OI Walls Detection - Sentiment-based S/R
Detects support and resistance levels based on Open Interest concentration
"""

import logging
from typing import Dict, List, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


def detect_oi_walls(
    options_data: List[Dict],
    current_price: float,
    oi_threshold_percentile: float = 0.75,
    merge_distance: float = 0.005,
    min_oi: float = 100
) -> Dict:
    """
    Detect OI walls from options data

    Args:
        options_data: List of option contracts with OI data
        current_price: Current underlying price
        oi_threshold_percentile: OI percentile threshold (0.75 = top 25%)
        merge_distance: Distance to merge nearby strikes (0.005 = 0.5%)
        min_oi: Minimum OI to consider

    Returns:
        Dict with resistance and support levels
    """

    if not options_data:
        logger.warning("No options data provided")
        return {'resistance': [], 'support': []}

    # Separate calls and puts
    calls = [opt for opt in options_data if opt.get('optionType') == 'Call']
    puts = [opt for opt in options_data if opt.get('optionType') == 'Put']

    logger.info(f"Analyzing {len(calls)} calls and {len(puts)} puts")

    # Detect resistance from call OI (high call OI = resistance)
    resistance = detect_resistance_from_calls(calls, current_price, oi_threshold_percentile, merge_distance, min_oi)

    # Detect support from put OI (high put OI = support)
    support = detect_support_from_puts(puts, current_price, oi_threshold_percentile, merge_distance, min_oi)

    logger.info(f"Detected {len(resistance)} resistance and {len(support)} support OI walls")

    return {
        'resistance': resistance[:10],  # Top 10
        'support': support[:10]  # Top 10
    }


def detect_resistance_from_calls(
    calls: List[Dict],
    current_price: float,
    oi_threshold_percentile: float,
    merge_distance: float,
    min_oi: float
) -> List[Dict]:
    """Detect resistance levels from call OI concentration"""

    if not calls:
        return []

    # Filter calls above current price with significant OI
    relevant_calls = [
        c for c in calls
        if c.get('strike', 0) > current_price and c.get('openInterest', 0) >= min_oi
    ]

    if not relevant_calls:
        return []

    # Calculate OI threshold
    all_oi = [c['openInterest'] for c in relevant_calls]
    all_oi.sort()
    threshold_idx = int(len(all_oi) * oi_threshold_percentile)
    oi_threshold = all_oi[threshold_idx] if threshold_idx < len(all_oi) else min_oi

    # Group by strike and sum OI
    strike_oi = defaultdict(lambda: {'oi': 0, 'volume': 0, 'contracts': 0})

    for call in relevant_calls:
        if call['openInterest'] >= oi_threshold:
            strike = call['strike']
            strike_oi[strike]['oi'] += call.get('openInterest', 0)
            strike_oi[strike]['volume'] += call.get('volume24h', 0)
            strike_oi[strike]['contracts'] += 1

    # Convert to list
    levels = []
    for strike, data in strike_oi.items():
        levels.append({
            'price': strike,
            'oi': data['oi'],
            'volume': data['volume'],
            'contracts': data['contracts']
        })

    # Merge nearby strikes
    levels = merge_nearby_levels(levels, current_price, merge_distance)

    # Calculate strength (normalized OI)
    if levels:
        max_oi = max(l['oi'] for l in levels)
        for level in levels:
            level['strength'] = min(1.0, level['oi'] / max_oi)
            level['method'] = 'oi_wall_call'

    # Sort by OI (highest first)
    levels.sort(key=lambda x: x['oi'], reverse=True)

    return levels


def detect_support_from_puts(
    puts: List[Dict],
    current_price: float,
    oi_threshold_percentile: float,
    merge_distance: float,
    min_oi: float
) -> List[Dict]:
    """Detect support levels from put OI concentration"""

    if not puts:
        return []

    # Filter puts below current price with significant OI
    relevant_puts = [
        p for p in puts
        if p.get('strike', 0) < current_price and p.get('openInterest', 0) >= min_oi
    ]

    if not relevant_puts:
        return []

    # Calculate OI threshold
    all_oi = [p['openInterest'] for p in relevant_puts]
    all_oi.sort()
    threshold_idx = int(len(all_oi) * oi_threshold_percentile)
    oi_threshold = all_oi[threshold_idx] if threshold_idx < len(all_oi) else min_oi

    # Group by strike and sum OI
    strike_oi = defaultdict(lambda: {'oi': 0, 'volume': 0, 'contracts': 0})

    for put in relevant_puts:
        if put['openInterest'] >= oi_threshold:
            strike = put['strike']
            strike_oi[strike]['oi'] += put.get('openInterest', 0)
            strike_oi[strike]['volume'] += put.get('volume24h', 0)
            strike_oi[strike]['contracts'] += 1

    # Convert to list
    levels = []
    for strike, data in strike_oi.items():
        levels.append({
            'price': strike,
            'oi': data['oi'],
            'volume': data['volume'],
            'contracts': data['contracts']
        })

    # Merge nearby strikes
    levels = merge_nearby_levels(levels, current_price, merge_distance)

    # Calculate strength (normalized OI)
    if levels:
        max_oi = max(l['oi'] for l in levels)
        for level in levels:
            level['strength'] = min(1.0, level['oi'] / max_oi)
            level['method'] = 'oi_wall_put'

    # Sort by OI (highest first)
    levels.sort(key=lambda x: x['oi'], reverse=True)

    return levels


def merge_nearby_levels(
    levels: List[Dict],
    current_price: float,
    merge_distance: float
) -> List[Dict]:
    """Merge levels that are very close to each other"""

    if not levels:
        return []

    # Sort by price
    levels.sort(key=lambda x: x['price'])

    merged = []
    current_group = [levels[0]]

    for level in levels[1:]:
        # Check if within merge distance
        base_price = current_group[0]['price']
        distance = abs(level['price'] - base_price) / current_price

        if distance <= merge_distance:
            # Add to current group
            current_group.append(level)
        else:
            # Merge current group and start new one
            merged.append(merge_group(current_group))
            current_group = [level]

    # Merge last group
    if current_group:
        merged.append(merge_group(current_group))

    return merged


def merge_group(group: List[Dict]) -> Dict:
    """Merge a group of levels into one"""

    # Weighted average price by OI
    total_oi = sum(l['oi'] for l in group)
    avg_price = sum(l['price'] * l['oi'] for l in group) / total_oi if total_oi > 0 else group[0]['price']

    return {
        'price': avg_price,
        'oi': total_oi,
        'volume': sum(l['volume'] for l in group),
        'contracts': sum(l['contracts'] for l in group),
        'merged_count': len(group)
    }
