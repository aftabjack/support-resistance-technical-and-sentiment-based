"""
S/R Utilities Module
Shared utilities for Technical and Sentiment S/R detection
"""

import redis
import json
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedisHelper:
    """Helper class for Redis operations"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Initialize Redis connection

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.host = host
        self.port = port
        self.db = db
        self.redis_client = None
        self.connect()

    def connect(self):
        """Establish Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def get_klines(self, symbol: str, interval: str, limit: int = 1000) -> List[Dict]:
        """
        Get kline data from Redis

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Interval (e.g., "15")
            limit: Number of candles to fetch

        Returns:
            List of candle dictionaries (OHLCV)
        """
        key = f"{interval}.{symbol}"

        try:
            # Get latest 'limit' candles from sorted set
            candles_json = self.redis_client.zrevrange(key, 0, limit - 1)

            if not candles_json:
                logger.warning(f"No candles found for {key}")
                return []

            # Parse JSON candles
            candles = []
            for i, candle_str in enumerate(reversed(candles_json)):  # Reverse to get chronological order
                candle = json.loads(candle_str)
                # Handle both short and long key formats
                candles.append({
                    'timestamp': i,  # Use index as timestamp since not stored
                    'open': float(candle.get('o', candle.get('open', 0))),
                    'high': float(candle.get('h', candle.get('high', 0))),
                    'low': float(candle.get('l', candle.get('low', 0))),
                    'close': float(candle.get('c', candle.get('close', 0))),
                    'volume': float(candle.get('v', candle.get('volume', 0)))
                })

            logger.info(f"Fetched {len(candles)} candles for {key}")
            return candles

        except Exception as e:
            logger.error(f"Error fetching klines for {key}: {e}")
            return []

    def get_options(self, base_symbol: str) -> List[Dict]:
        """
        Get options data from Redis

        Args:
            base_symbol: Base symbol (e.g., "BTC", "ETH", "SOL")

        Returns:
            List of option dictionaries
        """
        pattern = f"option:{base_symbol}-*"

        try:
            # Get all option keys
            keys = self.redis_client.keys(pattern)

            if not keys:
                logger.warning(f"No options found for {base_symbol}")
                return []

            # Fetch all options
            options = []
            for key in keys:
                option_data = self.redis_client.hgetall(key)

                if option_data:
                    # Parse option data
                    options.append({
                        'symbol': option_data.get('symbol', ''),
                        'strike': float(option_data.get('strike_price', 0)),
                        'option_type': option_data.get('option_type', ''),
                        'expiry': option_data.get('expiry_date', ''),
                        'open_interest': float(option_data.get('open_interest', 0)),
                        'volume_24h': float(option_data.get('volume_24h', 0)),
                        'delta': float(option_data.get('delta', 0)),
                        'gamma': float(option_data.get('gamma', 0)),
                        'iv': float(option_data.get('iv', 0)),
                        'timestamp': float(option_data.get('timestamp', 0))
                    })

            logger.info(f"Fetched {len(options)} options for {base_symbol}")
            return options

        except Exception as e:
            logger.error(f"Error fetching options for {base_symbol}: {e}")
            return []

    def save_sr_result(self, key: str, data: Dict, ttl: int = 300):
        """
        Save S/R result to Redis

        Args:
            key: Redis key (e.g., "sr:technical:medium:15.BTCUSDT")
            data: S/R data dictionary
            ttl: Time to live in seconds (default 5 minutes)
        """
        try:
            # Add timestamp
            data['timestamp'] = datetime.now().timestamp()

            # Save to Redis
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(data, indent=2)
            )

            logger.info(f"Saved S/R result to {key}")

        except Exception as e:
            logger.error(f"Error saving S/R result to {key}: {e}")

    def get_sr_result(self, key: str) -> Optional[Dict]:
        """
        Get S/R result from Redis

        Args:
            key: Redis key

        Returns:
            S/R data dictionary or None
        """
        try:
            data = self.redis_client.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Error getting S/R result from {key}: {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """
        Get current price from latest 1-minute candle

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")

        Returns:
            Current close price
        """
        try:
            candles = self.get_klines(symbol, "1", limit=1)

            if candles:
                return candles[-1]['close']

            return 0.0

        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0


def parse_interval_symbol(key: str) -> Tuple[str, str]:
    """
    Parse interval and symbol from key

    Args:
        key: Key in format "{interval}.{symbol}" (e.g., "15.BTCUSDT")

    Returns:
        Tuple of (interval, symbol)

    Example:
        >>> parse_interval_symbol("15.BTCUSDT")
        ("15", "BTCUSDT")
    """
    parts = key.split(".", 1)

    if len(parts) == 2:
        return parts[0], parts[1]

    raise ValueError(f"Invalid key format: {key}. Expected format: {{interval}}.{{symbol}}")


def get_base_symbol(symbol: str) -> str:
    """
    Extract base symbol from trading pair

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")

    Returns:
        Base symbol (e.g., "BTC")

    Example:
        >>> get_base_symbol("BTCUSDT")
        "BTC"
        >>> get_base_symbol("ETHUSDT")
        "ETH"
    """
    # Remove common quote currencies
    for quote in ["USDT", "USD", "BUSD", "USDC"]:
        if symbol.endswith(quote):
            return symbol[:-len(quote)]

    return symbol


def calculate_strength(touches: int, volume: float = 0, max_touches: int = 10) -> float:
    """
    Calculate strength score for S/R level

    Args:
        touches: Number of times price touched this level
        volume: Volume at this level (optional)
        max_touches: Maximum touches to consider for normalization

    Returns:
        Strength score between 0 and 1

    Example:
        >>> calculate_strength(5, volume=1000000)
        0.75
    """
    # Base strength from touches (0.0 to 1.0)
    touch_strength = min(touches / max_touches, 1.0)

    # Boost from volume (optional)
    volume_boost = 0.0
    if volume > 0:
        # Normalize volume (example: significant volume = 1M+)
        volume_boost = min(volume / 10000000, 0.2)  # Max 20% boost

    # Combined strength (capped at 1.0)
    strength = min(touch_strength + volume_boost, 1.0)

    return round(strength, 2)


def round_to_significant(price: float, sig_figs: int = 5) -> float:
    """
    Round price to significant figures

    Args:
        price: Price value
        sig_figs: Number of significant figures

    Returns:
        Rounded price

    Example:
        >>> round_to_significant(111587.5, 5)
        111590.0
    """
    if price == 0:
        return 0

    from math import log10, floor

    # Find order of magnitude
    magnitude = floor(log10(abs(price)))

    # Round to significant figures
    factor = 10 ** (magnitude - sig_figs + 1)
    rounded = round(price / factor) * factor

    return rounded


def is_round_number(price: float, tolerance: float = 0.001) -> bool:
    """
    Check if price is a round number

    Args:
        price: Price value
        tolerance: Tolerance as percentage (0.001 = 0.1%)

    Returns:
        True if price is close to round number

    Example:
        >>> is_round_number(111000)
        True
        >>> is_round_number(111587.5)
        False
    """
    # Check for different levels of round numbers
    for factor in [100000, 50000, 10000, 5000, 1000, 500, 100, 50]:
        if abs(price % factor) / price < tolerance:
            return True

    return False


def merge_nearby_levels(
    levels: List[Dict],
    threshold: float = 0.005,
    key: str = 'price'
) -> List[Dict]:
    """
    Merge S/R levels that are very close together

    Args:
        levels: List of level dictionaries
        threshold: Distance threshold as percentage (0.005 = 0.5%)
        key: Dictionary key for price value

    Returns:
        Merged list of levels

    Example:
        >>> levels = [{'price': 111500, 'strength': 0.8}, {'price': 111550, 'strength': 0.7}]
        >>> merge_nearby_levels(levels, threshold=0.005)
        [{'price': 111525, 'strength': 0.85}]
    """
    if not levels:
        return []

    # Sort by price
    sorted_levels = sorted(levels, key=lambda x: x[key])

    merged = []
    current_group = [sorted_levels[0]]

    for level in sorted_levels[1:]:
        # Check if close to current group
        avg_price = sum(l[key] for l in current_group) / len(current_group)
        distance = abs(level[key] - avg_price) / avg_price

        if distance < threshold:
            # Add to current group
            current_group.append(level)
        else:
            # Start new group
            merged.append(merge_level_group(current_group, key))
            current_group = [level]

    # Add last group
    merged.append(merge_level_group(current_group, key))

    return merged


def merge_level_group(group: List[Dict], key: str = 'price') -> Dict:
    """
    Merge a group of nearby levels into one

    Args:
        group: List of level dictionaries
        key: Dictionary key for price value

    Returns:
        Merged level dictionary
    """
    if len(group) == 1:
        return group[0]

    # Calculate weighted average price (by strength)
    total_strength = sum(l.get('strength', 1.0) for l in group)
    avg_price = sum(l[key] * l.get('strength', 1.0) for l in group) / total_strength

    # Combine strengths (max)
    max_strength = max(l.get('strength', 0) for l in group)

    # Combine touches (sum)
    total_touches = sum(l.get('touches', 0) for l in group)

    # Use method from strongest level
    strongest = max(group, key=lambda x: x.get('strength', 0))

    return {
        key: round(avg_price, 2),
        'strength': round(max_strength, 2),
        'touches': total_touches,
        'method': strongest.get('method', 'merged'),
        'merged_count': len(group)
    }


def filter_by_distance(
    levels: List[Dict],
    current_price: float,
    max_distance_pct: float = 0.05,
    key: str = 'price'
) -> List[Dict]:
    """
    Filter levels by maximum distance from current price

    Args:
        levels: List of level dictionaries
        current_price: Current market price
        max_distance_pct: Maximum distance as percentage (0.05 = 5%)
        key: Dictionary key for price value

    Returns:
        Filtered list of levels

    Example:
        >>> levels = [{'price': 111500}, {'price': 115000}, {'price': 120000}]
        >>> filter_by_distance(levels, 111000, max_distance_pct=0.05)
        [{'price': 111500}]
    """
    filtered = []

    for level in levels:
        distance = abs(level[key] - current_price) / current_price

        if distance <= max_distance_pct:
            filtered.append(level)

    return filtered


def format_sr_output(
    resistance: List[Dict],
    support: List[Dict],
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Format S/R detection output

    Args:
        resistance: List of resistance levels
        support: List of support levels
        metadata: Optional metadata dictionary

    Returns:
        Formatted S/R output dictionary
    """
    output = {
        'resistance': sorted(resistance, key=lambda x: x['price']),
        'support': sorted(support, key=lambda x: x['price'], reverse=True),
        'timestamp': datetime.now().timestamp()
    }

    if metadata:
        output['metadata'] = metadata

    return output


# Convenience function for testing
def test_redis_connection():
    """Test Redis connection and data availability"""
    redis_helper = RedisHelper()

    print("Testing Redis Connection...")
    print(f"Connected: {redis_helper.redis_client.ping()}")
    print()

    # Test klines
    print("Testing Kline Data:")
    for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        for interval in ["1", "15", "60"]:
            candles = redis_helper.get_klines(symbol, interval, limit=10)
            print(f"  {interval}.{symbol}: {len(candles)} candles")
    print()

    # Test options
    print("Testing Options Data:")
    for base_symbol in ["BTC", "ETH", "SOL"]:
        options = redis_helper.get_options(base_symbol)
        print(f"  {base_symbol}: {len(options)} options")
    print()

    # Test current prices
    print("Current Prices:")
    for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        price = redis_helper.get_current_price(symbol)
        print(f"  {symbol}: ${price:,.2f}")


if __name__ == "__main__":
    # Run tests
    test_redis_connection()
