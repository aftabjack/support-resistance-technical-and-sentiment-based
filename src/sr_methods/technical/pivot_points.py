"""
Pivot Point-based S/R Detection Methods
Calculates support and resistance from previous period high/low/close
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


def calculate_standard_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Standard Pivot Points (Floor Pivots)

    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close

    Returns:
        Dict with PP, R1-R3, S1-S3
    """
    pp = (high + low + close) / 3

    r1 = (2 * pp) - low
    s1 = (2 * pp) - high

    r2 = pp + (high - low)
    s2 = pp - (high - low)

    r3 = high + 2 * (pp - low)
    s3 = low - 2 * (high - pp)

    return {
        'PP': pp,
        'R1': r1, 'R2': r2, 'R3': r3,
        'S1': s1, 'S2': s2, 'S3': s3
    }


def calculate_fibonacci_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Fibonacci Pivot Points

    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close

    Returns:
        Dict with PP, R1-R3, S1-S3 (Fibonacci levels)
    """
    pp = (high + low + close) / 3
    range_hl = high - low

    r1 = pp + 0.382 * range_hl
    r2 = pp + 0.618 * range_hl
    r3 = pp + 1.000 * range_hl

    s1 = pp - 0.382 * range_hl
    s2 = pp - 0.618 * range_hl
    s3 = pp - 1.000 * range_hl

    return {
        'PP': pp,
        'R1': r1, 'R2': r2, 'R3': r3,
        'S1': s1, 'S2': s2, 'S3': s3
    }


def calculate_camarilla_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Camarilla Pivot Points

    Args:
        high: Previous period high
        low: Previous period low
        close: Previous period close

    Returns:
        Dict with PP, R1-R4, S1-S4
    """
    pp = (high + low + close) / 3
    range_hl = high - low

    r4 = close + (range_hl * 1.1 / 2)
    r3 = close + (range_hl * 1.1 / 4)
    r2 = close + (range_hl * 1.1 / 6)
    r1 = close + (range_hl * 1.1 / 12)

    s1 = close - (range_hl * 1.1 / 12)
    s2 = close - (range_hl * 1.1 / 6)
    s3 = close - (range_hl * 1.1 / 4)
    s4 = close - (range_hl * 1.1 / 2)

    return {
        'PP': pp,
        'R1': r1, 'R2': r2, 'R3': r3, 'R4': r4,
        'S1': s1, 'S2': s2, 'S3': s3, 'S4': s4
    }


def detect_pivot_sr(
    prev_day: Tuple[float, float, float],
    prev_week: Tuple[float, float, float] = None,
    prev_month: Tuple[float, float, float] = None,
    current_price: float = None,
    include_fibonacci: bool = True,
    include_camarilla: bool = True
) -> Dict:
    """
    Detect S/R levels from pivot points

    Args:
        prev_day: (high, low, close) of previous day
        prev_week: (high, low, close) of previous week (optional)
        prev_month: (high, low, close) of previous month (optional)
        current_price: Current price for filtering
        include_fibonacci: Include Fibonacci pivots
        include_camarilla: Include Camarilla pivots

    Returns:
        Dict with resistance and support levels
    """
    resistance = []
    support = []

    # Previous Day Levels
    if prev_day:
        high, low, close = prev_day

        # Add previous high/low/close as direct S/R
        if current_price:
            if high > current_price:
                resistance.append({
                    'price': high,
                    'strength': 0.9,
                    'method': 'prev_day_high',
                    'touches': 1
                })
            if low < current_price:
                support.append({
                    'price': low,
                    'strength': 0.9,
                    'method': 'prev_day_low',
                    'touches': 1
                })

        # Standard Pivots (Daily)
        std_pivots = calculate_standard_pivots(high, low, close)
        for level, price in std_pivots.items():
            if level.startswith('R') and (not current_price or price > current_price):
                resistance.append({
                    'price': price,
                    'strength': 0.85 if level == 'R1' else (0.75 if level == 'R2' else 0.65),
                    'method': f'standard_pivot_day_{level}',
                    'touches': 1
                })
            elif level.startswith('S') and (not current_price or price < current_price):
                support.append({
                    'price': price,
                    'strength': 0.85 if level == 'S1' else (0.75 if level == 'S2' else 0.65),
                    'method': f'standard_pivot_day_{level}',
                    'touches': 1
                })
            elif level == 'PP':
                # Pivot point can act as both support and resistance
                if not current_price or price > current_price:
                    resistance.append({
                        'price': price,
                        'strength': 0.80,
                        'method': 'standard_pivot_day_PP',
                        'touches': 1
                    })
                if not current_price or price < current_price:
                    support.append({
                        'price': price,
                        'strength': 0.80,
                        'method': 'standard_pivot_day_PP',
                        'touches': 1
                    })

        # Fibonacci Pivots (Daily)
        if include_fibonacci:
            fib_pivots = calculate_fibonacci_pivots(high, low, close)
            for level, price in fib_pivots.items():
                if level.startswith('R') and (not current_price or price > current_price):
                    resistance.append({
                        'price': price,
                        'strength': 0.80 if level == 'R1' else (0.70 if level == 'R2' else 0.60),
                        'method': f'fibonacci_pivot_day_{level}',
                        'touches': 1
                    })
                elif level.startswith('S') and (not current_price or price < current_price):
                    support.append({
                        'price': price,
                        'strength': 0.80 if level == 'S1' else (0.70 if level == 'S2' else 0.60),
                        'method': f'fibonacci_pivot_day_{level}',
                        'touches': 1
                    })

        # Camarilla Pivots (Daily)
        if include_camarilla:
            cam_pivots = calculate_camarilla_pivots(high, low, close)
            for level, price in cam_pivots.items():
                if level.startswith('R') and (not current_price or price > current_price):
                    # R3 and R4 are breakout levels (stronger)
                    strength = 0.85 if level in ['R3', 'R4'] else 0.70
                    resistance.append({
                        'price': price,
                        'strength': strength,
                        'method': f'camarilla_pivot_day_{level}',
                        'touches': 1
                    })
                elif level.startswith('S') and (not current_price or price < current_price):
                    # S3 and S4 are breakout levels (stronger)
                    strength = 0.85 if level in ['S3', 'S4'] else 0.70
                    support.append({
                        'price': price,
                        'strength': strength,
                        'method': f'camarilla_pivot_day_{level}',
                        'touches': 1
                    })

    # Previous Week Levels
    if prev_week:
        high, low, close = prev_week

        if current_price:
            if high > current_price:
                resistance.append({
                    'price': high,
                    'strength': 0.95,
                    'method': 'prev_week_high',
                    'touches': 1
                })
            if low < current_price:
                support.append({
                    'price': low,
                    'strength': 0.95,
                    'method': 'prev_week_low',
                    'touches': 1
                })

        # Standard Pivots (Weekly)
        std_pivots = calculate_standard_pivots(high, low, close)
        for level, price in std_pivots.items():
            if level.startswith('R') and (not current_price or price > current_price):
                resistance.append({
                    'price': price,
                    'strength': 0.90 if level == 'R1' else (0.80 if level == 'R2' else 0.70),
                    'method': f'standard_pivot_week_{level}',
                    'touches': 1
                })
            elif level.startswith('S') and (not current_price or price < current_price):
                support.append({
                    'price': price,
                    'strength': 0.90 if level == 'S1' else (0.80 if level == 'S2' else 0.70),
                    'method': f'standard_pivot_week_{level}',
                    'touches': 1
                })

    # Previous Month Levels
    if prev_month:
        high, low, close = prev_month

        if current_price:
            if high > current_price:
                resistance.append({
                    'price': high,
                    'strength': 1.0,
                    'method': 'prev_month_high',
                    'touches': 1
                })
            if low < current_price:
                support.append({
                    'price': low,
                    'strength': 1.0,
                    'method': 'prev_month_low',
                    'touches': 1
                })

        # Standard Pivots (Monthly)
        std_pivots = calculate_standard_pivots(high, low, close)
        for level, price in std_pivots.items():
            if level.startswith('R') and (not current_price or price > current_price):
                resistance.append({
                    'price': price,
                    'strength': 0.95 if level == 'R1' else (0.85 if level == 'R2' else 0.75),
                    'method': f'standard_pivot_month_{level}',
                    'touches': 1
                })
            elif level.startswith('S') and (not current_price or price < current_price):
                support.append({
                    'price': price,
                    'strength': 0.95 if level == 'S1' else (0.85 if level == 'S2' else 0.75),
                    'method': f'standard_pivot_month_{level}',
                    'touches': 1
                })

    # Sort and deduplicate
    resistance = sorted(resistance, key=lambda x: x['price'])
    support = sorted(support, key=lambda x: x['price'], reverse=True)

    # Merge levels that are very close (within 0.2%)
    resistance = _merge_close_levels(resistance, threshold=0.002)
    support = _merge_close_levels(support, threshold=0.002)

    return {
        'resistance': resistance[:15],  # Top 15 resistance levels
        'support': support[:15]          # Top 15 support levels
    }


def _merge_close_levels(levels: List[Dict], threshold: float = 0.002) -> List[Dict]:
    """
    Merge S/R levels that are very close together

    Args:
        levels: List of S/R level dicts
        threshold: Distance threshold (0.002 = 0.2%)

    Returns:
        Merged list
    """
    if not levels:
        return []

    merged = []
    current_group = [levels[0]]

    for level in levels[1:]:
        # Check if this level is close to the current group
        avg_price = sum(l['price'] for l in current_group) / len(current_group)
        distance = abs(level['price'] - avg_price) / avg_price

        if distance < threshold:
            # Add to current group
            current_group.append(level)
        else:
            # Finalize current group and start new one
            merged.append(_merge_level_group(current_group))
            current_group = [level]

    # Don't forget the last group
    if current_group:
        merged.append(_merge_level_group(current_group))

    return merged


def _merge_level_group(group: List[Dict]) -> Dict:
    """Merge a group of close levels into one"""
    if len(group) == 1:
        return group[0]

    # Average price
    avg_price = sum(l['price'] for l in group) / len(group)

    # Max strength
    max_strength = max(l['strength'] for l in group)

    # Combine methods
    methods = ', '.join(set(l['method'] for l in group))

    # Sum touches
    total_touches = sum(l.get('touches', 1) for l in group)

    return {
        'price': avg_price,
        'strength': max_strength,
        'method': methods,
        'touches': total_touches
    }
