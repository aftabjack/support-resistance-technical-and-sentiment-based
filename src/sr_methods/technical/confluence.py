"""
Confluence Detection
Combines multiple S/R detection methods to find confluent zones
"""

from typing import Dict, List
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def detect_confluence(
    sr_results: List[Dict],
    price_tolerance: float = 0.005,
    min_methods: int = 2
) -> Dict:
    """
    Detect confluent S/R zones where multiple methods agree

    Args:
        sr_results: List of S/R result dicts from different methods
        price_tolerance: Price tolerance for grouping (0.005 = 0.5%)
        min_methods: Minimum number of methods required for confluence

    Returns:
        Dict with confluent resistance and support zones
    """

    if not sr_results:
        logger.warning("No S/R results provided for confluence detection")
        return {'resistance': [], 'support': []}

    # Collect all resistance and support levels
    all_resistance = []
    all_support = []

    for result in sr_results:
        all_resistance.extend(result.get('resistance', []))
        all_support.extend(result.get('support', []))

    logger.info(f"Total levels: {len(all_resistance)} resistance, {len(all_support)} support")

    # Find confluent zones
    confluent_resistance = _find_confluent_zones(all_resistance, price_tolerance, min_methods)
    confluent_support = _find_confluent_zones(all_support, price_tolerance, min_methods)

    logger.info(f"Confluent zones: {len(confluent_resistance)} resistance, {len(confluent_support)} support")

    return {
        'resistance': confluent_resistance[:15],  # Top 15
        'support': confluent_support[:15]          # Top 15
    }


def _find_confluent_zones(
    levels: List[Dict],
    tolerance: float,
    min_methods: int
) -> List[Dict]:
    """
    Find zones where multiple levels are close together

    Args:
        levels: List of S/R level dicts
        tolerance: Price tolerance (0.005 = 0.5%)
        min_methods: Minimum number of methods required

    Returns:
        List of confluent zone dicts
    """

    if not levels:
        return []

    # Sort by price
    levels = sorted(levels, key=lambda x: x['price'])

    # Group nearby levels
    groups = []
    current_group = [levels[0]]

    for level in levels[1:]:
        # Check if this level is within tolerance of the group's average
        group_avg = sum(l['price'] for l in current_group) / len(current_group)
        distance = abs(level['price'] - group_avg) / group_avg

        if distance <= tolerance:
            # Add to current group
            current_group.append(level)
        else:
            # Finalize current group and start new one
            if len(current_group) >= min_methods:
                groups.append(current_group)
            current_group = [level]

    # Don't forget the last group
    if len(current_group) >= min_methods:
        groups.append(current_group)

    # Create confluent zones from groups
    zones = []
    for group in groups:
        zone = _create_confluent_zone(group)
        zones.append(zone)

    # Sort by confluence score (descending)
    zones = sorted(zones, key=lambda x: x['confluence_score'], reverse=True)

    return zones


def _create_confluent_zone(group: List[Dict]) -> Dict:
    """
    Create a confluent zone from a group of nearby levels

    Args:
        group: List of level dicts that are close together

    Returns:
        Confluent zone dict
    """

    # Average price (weighted by strength)
    total_strength = sum(l.get('strength', 0.5) for l in group)
    if total_strength > 0:
        weighted_price = sum(l['price'] * l.get('strength', 0.5) for l in group) / total_strength
    else:
        weighted_price = sum(l['price'] for l in group) / len(group)

    # Collect methods
    methods = []
    for level in group:
        method = level.get('method', 'unknown')
        if method not in methods:
            methods.append(method)

    # Calculate confluence score
    # Score = number of methods × average strength
    num_methods = len(methods)
    avg_strength = sum(l.get('strength', 0.5) for l in group) / len(group)
    confluence_score = num_methods * avg_strength

    # Overall strength (boosted by confluence)
    # More methods = stronger level
    confluence_bonus = min(num_methods / 10, 0.3)  # Max +0.3 boost
    final_strength = min(avg_strength + confluence_bonus, 1.0)

    return {
        'price': weighted_price,
        'strength': final_strength,
        'method': f"confluence_{num_methods}x",
        'methods': methods,
        'num_methods': num_methods,
        'confluence_score': confluence_score,
        'touches': sum(l.get('touches', 1) for l in group)
    }


def merge_all_sr_results(
    pivot_result: Dict = None,
    volume_result: Dict = None,
    vwap_result: Dict = None,
    fib_result: Dict = None,
    current_price: float = None
) -> Dict:
    """
    Merge S/R results from all methods (without confluence detection)

    Args:
        pivot_result: Result from pivot detector
        volume_result: Result from volume profile
        vwap_result: Result from VWAP
        fib_result: Result from Fibonacci
        current_price: Current price for sorting

    Returns:
        Merged dict with all resistance and support levels
    """

    all_resistance = []
    all_support = []

    # Collect all levels
    if pivot_result:
        all_resistance.extend(pivot_result.get('resistance', []))
        all_support.extend(pivot_result.get('support', []))

    if volume_result:
        all_resistance.extend(volume_result.get('resistance', []))
        all_support.extend(volume_result.get('support', []))

    if vwap_result:
        all_resistance.extend(vwap_result.get('resistance', []))
        all_support.extend(vwap_result.get('support', []))

    if fib_result:
        all_resistance.extend(fib_result.get('resistance', []))
        all_support.extend(fib_result.get('support', []))

    # Sort by price
    all_resistance = sorted(all_resistance, key=lambda x: x['price'])
    all_support = sorted(all_support, key=lambda x: x['price'], reverse=True)

    # If current_price provided, find nearest levels
    nearest_resistance = None
    nearest_support = None

    if current_price:
        # Find nearest resistance above current price
        for r in all_resistance:
            if r['price'] > current_price:
                nearest_resistance = r
                break

        # Find nearest support below current price
        for s in all_support:
            if s['price'] < current_price:
                nearest_support = s
                break

    return {
        'resistance': all_resistance[:20],  # Top 20
        'support': all_support[:20],        # Top 20
        'nearest_resistance': nearest_resistance,
        'nearest_support': nearest_support
    }
