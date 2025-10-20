"""
Swing High/Low Detection
Identifies significant swing points that can act as support and resistance
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def detect_swing_highs_lows(
    candles: List[Dict],
    lookback: int = 5,
    min_touches: int = 2,
    touch_threshold: float = 0.002
) -> Dict:
    """
    Detect swing highs and lows from candle data

    Args:
        candles: List of candle dictionaries (OHLCV)
        lookback: Number of candles to look back/forward for swing detection
        min_touches: Minimum touches required to qualify as S/R
        touch_threshold: Price tolerance for touch detection (0.002 = 0.2%)

    Returns:
        Dictionary with 'resistance' and 'support' lists

    Algorithm:
        1. Find local highs/lows using lookback window
        2. Group nearby swing points
        3. Count touches for each level
        4. Filter by minimum touches
        5. Calculate strength scores
    """
    if not candles or len(candles) < lookback * 2:
        logger.warning(f"Not enough candles for swing detection: {len(candles)}")
        return {'resistance': [], 'support': []}

    # Step 1: Find swing highs and lows
    swing_highs = find_swing_highs(candles, lookback)
    swing_lows = find_swing_lows(candles, lookback)

    logger.info(f"Found {len(swing_highs)} swing highs and {len(swing_lows)} swing lows")

    # Step 2 & 3: Group and count touches
    resistance_levels = process_swing_points(
        swing_highs,
        candles,
        min_touches,
        touch_threshold,
        level_type='resistance'
    )

    support_levels = process_swing_points(
        swing_lows,
        candles,
        min_touches,
        touch_threshold,
        level_type='support'
    )

    logger.info(f"Detected {len(resistance_levels)} resistance and {len(support_levels)} support levels")

    return {
        'resistance': resistance_levels,
        'support': support_levels
    }


def find_swing_highs(candles: List[Dict], lookback: int = 5) -> List[Dict]:
    """
    Find swing high points

    A swing high is a candle whose high is higher than N candles before and after it

    Args:
        candles: List of candle dictionaries
        lookback: Number of candles to check before/after

    Returns:
        List of swing high dictionaries with 'price' and 'index'
    """
    swing_highs = []

    for i in range(lookback, len(candles) - lookback):
        current_high = candles[i]['high']
        is_swing_high = True

        # Check candles before
        for j in range(i - lookback, i):
            if candles[j]['high'] >= current_high:
                is_swing_high = False
                break

        # Check candles after
        if is_swing_high:
            for j in range(i + 1, i + lookback + 1):
                if candles[j]['high'] >= current_high:
                    is_swing_high = False
                    break

        if is_swing_high:
            swing_highs.append({
                'price': current_high,
                'index': i,
                'candle': candles[i]
            })

    return swing_highs


def find_swing_lows(candles: List[Dict], lookback: int = 5) -> List[Dict]:
    """
    Find swing low points

    A swing low is a candle whose low is lower than N candles before and after it

    Args:
        candles: List of candle dictionaries
        lookback: Number of candles to check before/after

    Returns:
        List of swing low dictionaries with 'price' and 'index'
    """
    swing_lows = []

    for i in range(lookback, len(candles) - lookback):
        current_low = candles[i]['low']
        is_swing_low = True

        # Check candles before
        for j in range(i - lookback, i):
            if candles[j]['low'] <= current_low:
                is_swing_low = False
                break

        # Check candles after
        if is_swing_low:
            for j in range(i + 1, i + lookback + 1):
                if candles[j]['low'] <= current_low:
                    is_swing_low = False
                    break

        if is_swing_low:
            swing_lows.append({
                'price': current_low,
                'index': i,
                'candle': candles[i]
            })

    return swing_lows


def process_swing_points(
    swing_points: List[Dict],
    candles: List[Dict],
    min_touches: int,
    touch_threshold: float,
    level_type: str
) -> List[Dict]:
    """
    Process swing points into S/R levels

    Args:
        swing_points: List of swing point dictionaries
        candles: Full candle data
        min_touches: Minimum touches required
        touch_threshold: Touch detection threshold
        level_type: 'resistance' or 'support'

    Returns:
        List of S/R level dictionaries
    """
    if not swing_points:
        return []

    # Group nearby swing points
    grouped_levels = group_swing_points(swing_points, threshold=touch_threshold)

    # Count touches for each level
    levels_with_touches = []
    for level in grouped_levels:
        touches = count_touches(level['price'], candles, touch_threshold, level_type)

        if touches >= min_touches:
            # Calculate strength
            strength = calculate_swing_strength(touches, len(swing_points))

            levels_with_touches.append({
                'price': round(level['price'], 2),
                'strength': strength,
                'touches': touches,
                'method': f'swing_{level_type[0:4]}',  # swing_resi or swing_supp
                'last_touch': level.get('index', 0)
            })

    # Sort by strength
    levels_with_touches.sort(key=lambda x: x['strength'], reverse=True)

    return levels_with_touches


def group_swing_points(swing_points: List[Dict], threshold: float = 0.002) -> List[Dict]:
    """
    Group swing points that are close together

    Args:
        swing_points: List of swing point dictionaries
        threshold: Distance threshold as percentage

    Returns:
        List of grouped swing point dictionaries
    """
    if not swing_points:
        return []

    # Sort by price
    sorted_points = sorted(swing_points, key=lambda x: x['price'])

    grouped = []
    current_group = [sorted_points[0]]

    for point in sorted_points[1:]:
        # Check if close to current group average
        avg_price = sum(p['price'] for p in current_group) / len(current_group)
        distance = abs(point['price'] - avg_price) / avg_price

        if distance < threshold:
            # Add to current group
            current_group.append(point)
        else:
            # Finish current group and start new one
            grouped.append(merge_group(current_group))
            current_group = [point]

    # Add last group
    grouped.append(merge_group(current_group))

    return grouped


def merge_group(group: List[Dict]) -> Dict:
    """
    Merge a group of swing points into one level

    Args:
        group: List of swing point dictionaries

    Returns:
        Merged level dictionary
    """
    if len(group) == 1:
        return group[0]

    # Calculate average price
    avg_price = sum(p['price'] for p in group) / len(group)

    # Use most recent index
    max_index = max(p['index'] for p in group)

    return {
        'price': avg_price,
        'index': max_index,
        'count': len(group)
    }


def count_touches(
    level_price: float,
    candles: List[Dict],
    threshold: float,
    level_type: str
) -> int:
    """
    Count how many times price touched this level

    Args:
        level_price: The S/R level price
        candles: Full candle data
        threshold: Touch detection threshold
        level_type: 'resistance' or 'support'

    Returns:
        Number of touches
    """
    touches = 0

    for candle in candles:
        if level_type == 'resistance':
            # For resistance, check if high touched the level
            if abs(candle['high'] - level_price) / level_price < threshold:
                touches += 1
        else:
            # For support, check if low touched the level
            if abs(candle['low'] - level_price) / level_price < threshold:
                touches += 1

    return touches


def calculate_swing_strength(touches: int, total_swings: int) -> float:
    """
    Calculate strength score for swing level

    Args:
        touches: Number of touches
        total_swings: Total number of swing points found

    Returns:
        Strength score between 0 and 1
    """
    # Base strength from touches (normalized to 0-1)
    touch_strength = min(touches / 10, 1.0)  # Max at 10 touches

    # Boost if significant proportion of total swings
    if total_swings > 0:
        proportion = touches / total_swings
        proportion_boost = min(proportion * 0.3, 0.2)  # Max 20% boost
    else:
        proportion_boost = 0

    strength = min(touch_strength + proportion_boost, 1.0)

    return round(strength, 2)


# Testing function
def test_swing_detection():
    """Test swing detection with sample data"""
    # Create sample candles (simulating price action)
    sample_candles = []

    # Generate uptrend with swing points
    base_price = 111000
    for i in range(100):
        if i % 10 == 5:
            # Swing low
            candle = {
                'open': base_price - 200,
                'high': base_price - 100,
                'low': base_price - 300,
                'close': base_price - 150,
                'volume': 100
            }
        elif i % 10 == 0:
            # Swing high
            candle = {
                'open': base_price + 150,
                'high': base_price + 300,
                'low': base_price + 100,
                'close': base_price + 200,
                'volume': 100
            }
        else:
            # Regular candle
            candle = {
                'open': base_price,
                'high': base_price + 50,
                'low': base_price - 50,
                'close': base_price + 25,
                'volume': 100
            }

        sample_candles.append(candle)
        base_price += 10  # Slight uptrend

    # Run detection
    result = detect_swing_highs_lows(sample_candles, lookback=3, min_touches=2)

    print("Swing High/Low Detection Test:")
    print(f"Resistance levels: {len(result['resistance'])}")
    for level in result['resistance'][:5]:
        print(f"  ${level['price']:.2f} - Touches: {level['touches']}, Strength: {level['strength']}")

    print(f"\nSupport levels: {len(result['support'])}")
    for level in result['support'][:5]:
        print(f"  ${level['price']:.2f} - Touches: {level['touches']}, Strength: {level['strength']}")


if __name__ == "__main__":
    test_swing_detection()
