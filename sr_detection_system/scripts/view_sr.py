#!/usr/bin/env python3
"""
View Support & Resistance Levels
Simple script to view S/R data from Redis in a clean format
"""

import redis
import json
import sys
from datetime import datetime

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def view_sr(symbol, interval):
    """View S/R levels for a specific symbol and interval"""

    key = f"sr:technical:basic:{interval}.{symbol}"

    # Get data from Redis
    data = r.get(key)

    if not data:
        print(f"❌ No S/R data found for {symbol} {interval}min")
        print(f"   Key: {key}")
        print("\nAvailable keys:")
        for k in r.keys("sr:technical:basic:*"):
            print(f"   - {k}")
        return

    sr_data = json.loads(data)

    # Extract data
    current_price = sr_data['metadata']['current_price']
    resistance = sr_data['resistance']
    support = sr_data['support']
    timestamp = sr_data['timestamp']
    processing_time = sr_data['metadata']['processing_time_ms']

    # Convert timestamp
    dt = datetime.fromtimestamp(timestamp)
    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')

    print("\n" + "="*70)
    print(f"📊 SUPPORT & RESISTANCE - {symbol} ({interval}min)")
    print("="*70)
    print(f"💰 Current Price: ${current_price:,.2f}")
    print(f"⏱️  Generated: {time_str}")
    print(f"⚡ Processing Time: {processing_time:.2f}ms")
    print(f"📈 Resistance Levels: {len(resistance)}")
    print(f"📉 Support Levels: {len(support)}")
    print("="*70)

    # Find nearest levels
    nearest_resistance = None
    nearest_support = None

    for r_level in resistance:
        if r_level['price'] > current_price:
            nearest_resistance = r_level
            break

    for s_level in reversed(support):
        if s_level['price'] < current_price:
            nearest_support = s_level
            break

    # Display nearest levels
    print("\n🎯 NEAREST LEVELS:")
    print("-" * 70)

    if nearest_resistance:
        dist = ((nearest_resistance['price'] - current_price) / current_price) * 100
        print(f"📈 Nearest Resistance: ${nearest_resistance['price']:,.2f} (+{dist:.2f}%)")
        print(f"   Method: {nearest_resistance['method']}")
        print(f"   Strength: {nearest_resistance['strength']:.2f}")
        print(f"   Touches: {nearest_resistance['touches']}")
    else:
        print("📈 No resistance above current price")

    print()

    if nearest_support:
        dist = ((current_price - nearest_support['price']) / current_price) * 100
        print(f"📉 Nearest Support: ${nearest_support['price']:,.2f} (-{dist:.2f}%)")
        print(f"   Method: {nearest_support['method']}")
        print(f"   Strength: {nearest_support['strength']:.2f}")
        print(f"   Touches: {nearest_support['touches']}")
    else:
        print("📉 No support below current price")

    # Display all resistance levels
    print("\n" + "="*70)
    print("📈 ALL RESISTANCE LEVELS (Above Current Price)")
    print("="*70)
    print(f"{'Price':<15} {'Distance':<12} {'Method':<15} {'Strength':<10} {'Touches'}")
    print("-" * 70)

    for r_level in resistance[:10]:
        if r_level['price'] > current_price:
            dist = ((r_level['price'] - current_price) / current_price) * 100
            print(f"${r_level['price']:>13,.2f} {f'+{dist:.2f}%':<12} {r_level['method']:<15} {r_level['strength']:<10.2f} {r_level['touches']}")

    # Display all support levels
    print("\n" + "="*70)
    print("📉 ALL SUPPORT LEVELS (Below Current Price)")
    print("="*70)
    print(f"{'Price':<15} {'Distance':<12} {'Method':<15} {'Strength':<10} {'Touches'}")
    print("-" * 70)

    for s_level in support[:10]:
        if s_level['price'] < current_price:
            dist = ((current_price - s_level['price']) / current_price) * 100
            print(f"${s_level['price']:>13,.2f} {f'-{dist:.2f}%':<12} {s_level['method']:<15} {s_level['strength']:<10.2f} {s_level['touches']}")

    print("\n" + "="*70)
    print()


def list_available():
    """List all available S/R data"""
    print("\n" + "="*70)
    print("📋 AVAILABLE S/R DATA")
    print("="*70)

    keys = sorted(r.keys("sr:technical:basic:*"))

    if not keys:
        print("❌ No S/R data found in Redis")
        return

    print(f"\nTotal: {len(keys)} S/R combinations\n")

    # Group by symbol
    symbols = {}
    for key in keys:
        parts = key.split(':')[-1].split('.')
        interval = parts[0]
        symbol = parts[1]

        if symbol not in symbols:
            symbols[symbol] = []
        symbols[symbol].append(interval)

    for symbol in sorted(symbols.keys()):
        intervals = sorted(symbols[symbol], key=lambda x: float(x) if x.isdigit() else 9999)
        print(f"  {symbol}: {', '.join([f'{i}min' if i != 'D' else 'Daily' for i in intervals])}")

    print("\n" + "="*70)
    print()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - list available
        list_available()
        print("\n📖 Usage:")
        print(f"   python {sys.argv[0]} <SYMBOL> <INTERVAL>")
        print("\nExamples:")
        print(f"   python {sys.argv[0]} BTCUSDT 15")
        print(f"   python {sys.argv[0]} ETHUSDT 60")
        print(f"   python {sys.argv[0]} SOLUSDT D")
        print()

    elif len(sys.argv) == 3:
        symbol = sys.argv[1].upper()
        interval = sys.argv[2]
        view_sr(symbol, interval)

    else:
        print("❌ Invalid arguments")
        print(f"\nUsage: python {sys.argv[0]} <SYMBOL> <INTERVAL>")
        print("\nExamples:")
        print(f"   python {sys.argv[0]} BTCUSDT 15")
        print(f"   python {sys.argv[0]} ETHUSDT 60")
        sys.exit(1)
