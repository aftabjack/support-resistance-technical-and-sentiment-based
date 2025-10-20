"""
Round Number Detection
Identifies psychologically significant round numbers as potential S/R levels
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def detect_round_numbers(
    candles: List[Dict],
    max_distance_pct: float = 0.05,
    touch_threshold: float = 0.003
) -> Dict:
    """
    Detect round number S/R levels based on current price

    Args:
        candles: List of candle dictionaries (OHLCV)
        max_distance_pct: Maximum distance from current price (0.05 = 5%)
        touch_threshold: Price tolerance for touch detection (0.003 = 0.3%)

    Returns:
        Dictionary with 'resistance' and 'support' lists

    Algorithm:
        1. Get current price from latest candle
        2. Generate round numbers within range
        3. Count historical touches for each level
        4. Calculate strength based on touches and proximity
        5. Separate into resistance (above) and support (below)
    """
    if not candles:
        logger.warning("No candles provided for round number detection")
        return {'resistance': [], 'support': []}

    # Get current price
    current_price = candles[-1]['close']

    logger.info(f"Detecting round numbers near ${current_price:,.2f}")

    # Generate round numbers within range
    round_levels = generate_round_numbers(current_price, max_distance_pct)

    # Count touches and calculate strength
    levels_with_data = []
    for level_price in round_levels:
        touches = count_touches(level_price, candles, touch_threshold)

        # Calculate strength
        distance = abs(level_price - current_price) / current_price
        strength = calculate_round_number_strength(
            touches,
            distance,
            get_round_factor(level_price)
        )

        levels_with_data.append({
            'price': level_price,
            'strength': strength,
            'touches': touches,
            'method': 'round_number',
            'round_factor': get_round_factor(level_price)
        })

    # Separate into resistance and support
    resistance = [l for l in levels_with_data if l['price'] > current_price]
    support = [l for l in levels_with_data if l['price'] < current_price]

    # Sort by strength
    resistance.sort(key=lambda x: x['strength'], reverse=True)
    support.sort(key=lambda x: x['strength'], reverse=True)

    logger.info(f"Detected {len(resistance)} round number resistance and {len(support)} support levels")

    return {
        'resistance': resistance,
        'support': support
    }


def generate_round_numbers(current_price: float, max_distance_pct: float) -> List[float]:
    """
    Generate round numbers within range of current price

    Args:
        current_price: Current market price
        max_distance_pct: Maximum distance as percentage

    Returns:
        List of round number prices

    Round number factors (importance):
        - 100000 (e.g., 100000, 200000) - Highest
        - 50000 (e.g., 50000, 150000) - Very High
        - 10000 (e.g., 110000, 120000) - High
        - 5000 (e.g., 105000, 115000) - Medium-High
        - 1000 (e.g., 111000, 112000) - Medium
        - 500 (e.g., 111500, 112000) - Medium-Low
        - 100 (e.g., 111100, 111200) - Low
    """
    round_numbers = set()

    # Define round factors based on price magnitude
    if current_price >= 10000:
        factors = [100000, 50000, 10000, 5000, 1000, 500, 100]
    elif current_price >= 1000:
        factors = [10000, 5000, 1000, 500, 100, 50, 10]
    elif current_price >= 100:
        factors = [1000, 500, 100, 50, 10, 5, 1]
    else:
        factors = [100, 50, 10, 5, 1, 0.5, 0.1]

    # Calculate price range
    max_distance = current_price * max_distance_pct
    min_price = current_price - max_distance
    max_price = current_price + max_distance

    # Generate round numbers for each factor
    for factor in factors:
        # Find nearest round number below min_price
        start = int(min_price / factor) * factor

        # Generate up to max_price
        current = start
        while current <= max_price:
            if current > 0 and min_price <= current <= max_price:
                round_numbers.add(float(current))
            current += factor

    # Convert to sorted list
    return sorted(list(round_numbers))


def get_round_factor(price: float) -> int:
    """
    Get the round factor for a given price

    Args:
        price: The price to check

    Returns:
        Round factor (e.g., 1000, 5000, 10000)

    Example:
        >>> get_round_factor(111000)
        1000
        >>> get_round_factor(110000)
        10000
    """
    factors = [100000, 50000, 10000, 5000, 1000, 500, 100, 50, 10, 5, 1]

    for factor in factors:
        if price % factor == 0:
            return factor

    return 1


def count_touches(level_price: float, candles: List[Dict], threshold: float) -> int:
    """
    Count how many times price touched this round number

    Args:
        level_price: The round number level
        candles: Full candle data
        threshold: Touch detection threshold

    Returns:
        Number of touches
    """
    touches = 0

    for candle in candles:
        # Check if candle touched the level (high or low)
        if abs(candle['high'] - level_price) / level_price < threshold:
            touches += 1
        elif abs(candle['low'] - level_price) / level_price < threshold:
            touches += 1
        # Also check if level is within candle range
        elif candle['low'] <= level_price <= candle['high']:
            touches += 1

    return touches


def calculate_round_number_strength(
    touches: int,
    distance_pct: float,
    round_factor: int
) -> float:
    """
    Calculate strength score for round number level

    Args:
        touches: Number of historical touches
        distance_pct: Distance from current price as percentage
        round_factor: Round number factor (1000, 5000, 10000, etc.)

    Returns:
        Strength score between 0 and 1

    Strength components:
        - Touch strength (0-0.5): More touches = stronger
        - Proximity strength (0-0.3): Closer to price = stronger
        - Factor strength (0-0.2): Bigger round number = stronger
    """
    # Touch strength (max 0.5)
    touch_strength = min(touches / 10, 0.5)

    # Proximity strength (max 0.3)
    # Closer levels are stronger
    proximity_strength = max(0.3 * (1 - distance_pct / 0.05), 0)

    # Factor strength (max 0.2)
    # Bigger round numbers are stronger
    factor_weights = {
        100000: 0.20,
        50000: 0.18,
        10000: 0.15,
        5000: 0.12,
        1000: 0.10,
        500: 0.08,
        100: 0.05,
        50: 0.03,
        10: 0.02
    }
    factor_strength = factor_weights.get(round_factor, 0.01)

    # Combined strength
    strength = touch_strength + proximity_strength + factor_strength

    return round(min(strength, 1.0), 2)


def filter_top_round_numbers(levels: List[Dict], max_levels: int = 5) -> List[Dict]:
    """
    Filter to keep only the strongest round number levels

    Args:
        levels: List of round number level dictionaries
        max_levels: Maximum number to keep

    Returns:
        Filtered list of levels
    """
    # Already sorted by strength, just take top N
    return levels[:max_levels]


# Testing function
def test_round_numbers():
    """Test round number detection with sample data"""
    from sr_core.sr_utils import RedisHelper

    # Get real data
    redis_helper = RedisHelper()

    # Test with BTCUSDT 15min
    candles = redis_helper.get_klines("BTCUSDT", "15", limit=1000)

    if not candles:
        print("No candles available for testing")
        return

    # Run detection
    result = detect_round_numbers(candles, max_distance_pct=0.05)

    current_price = candles[-1]['close']

    print(f"Round Number Detection Test (Current: ${current_price:,.2f}):")
    print(f"\nResistance levels: {len(result['resistance'])}")
    for level in result['resistance'][:10]:
        distance = ((level['price'] - current_price) / current_price) * 100
        print(f"  ${level['price']:,.0f} (+{distance:.2f}%) - Factor: {level['round_factor']}, "
              f"Touches: {level['touches']}, Strength: {level['strength']}")

    print(f"\nSupport levels: {len(result['support'])}")
    for level in result['support'][:10]:
        distance = ((current_price - level['price']) / current_price) * 100
        print(f"  ${level['price']:,.0f} (-{distance:.2f}%) - Factor: {level['round_factor']}, "
              f"Touches: {level['touches']}, Strength: {level['strength']}")


if __name__ == "__main__":
    test_round_numbers()
