#!/usr/bin/env python3
"""
Quick viewer for EMA-enhanced S/R results
Usage: python view_ema_results.py [SYMBOL]
"""

import sys
import json
import redis

# Get symbol from command line or default to BTCUSDT
symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'BTCUSDT'

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get data
key = f"sr:ultimate:confluence:15.{symbol}"
data_json = r.get(key)

if not data_json:
    print(f"❌ No data found for {symbol}")
    print(f"   Key: {key}")
    sys.exit(1)

data = json.loads(data_json)

# Print header
print("\n" + "="*90)
print(f"          🎯 EMA-ENHANCED S/R LEVELS - {symbol}")
print("="*90 + "\n")

# Metadata
meta = data['metadata']
print("📊 METADATA")
print("─"*90)
print(f"Symbol:          {meta['symbol']}")
print(f"Current Price:   ${meta['current_price']:,.2f}")
print(f"Processing Time: {meta['processing_time_ms']}ms")
print(f"Methods:         {', '.join(meta['methods_used'])}")
print(f"Total Levels:    {len(data['resistance'])} resistance, {len(data['support'])} support")

# Get EMA-boosted levels
ema_resistance = [r for r in data['resistance'] if 'ema_confluence' in r]
ema_support = [s for s in data['support'] if 'ema_confluence' in s]

print(f"EMA Boosted:     {len(ema_resistance)} resistance, {len(ema_support)} support")

# Display EMA-boosted resistance
if ema_resistance:
    print("\n" + "="*90)
    print("📈 EMA-BOOSTED RESISTANCE LEVELS")
    print("="*90 + "\n")

    for i, level in enumerate(ema_resistance, 1):
        ema_info = level['ema_confluence']

        # Original methods (exclude EMAs)
        original_methods = [m for m in level['methods'] if not m.startswith('ema_')]
        ema_methods = [m for m in level['methods'] if m.startswith('ema_')]

        dist = ((level['price'] - meta['current_price']) / meta['current_price']) * 100

        print(f"#{i} 💰 ${level['price']:,.2f} (+{dist:.2f}% from current)")
        print(f"   Strength: {level['strength']:.2f} (boosted by +{ema_info['boost']:.2f})")
        print(f"   Total Methods: {level['num_methods']} ({len(original_methods)} original + {ema_info['count']} EMAs)")
        print(f"\n   Original Methods:")
        for method in original_methods[:5]:  # Show first 5
            print(f"     • {method}")
        if len(original_methods) > 5:
            print(f"     ... and {len(original_methods) - 5} more")

        print(f"\n   ✨ EMA Confluence ({ema_info['count']}x):")
        for period in ema_info['periods']:
            print(f"     • EMA {period}")
        print()

# Display EMA-boosted support
if ema_support:
    print("\n" + "="*90)
    print("📉 EMA-BOOSTED SUPPORT LEVELS")
    print("="*90 + "\n")

    for i, level in enumerate(ema_support, 1):
        ema_info = level['ema_confluence']

        # Original methods (exclude EMAs)
        original_methods = [m for m in level['methods'] if not m.startswith('ema_')]
        ema_methods = [m for m in level['methods'] if m.startswith('ema_')]

        dist = ((meta['current_price'] - level['price']) / meta['current_price']) * 100

        print(f"#{i} 💰 ${level['price']:,.2f} (-{dist:.2f}% from current)")
        print(f"   Strength: {level['strength']:.2f} (boosted by +{ema_info['boost']:.2f})")
        print(f"   Total Methods: {level['num_methods']} ({len(original_methods)} original + {ema_info['count']} EMAs)")
        print(f"\n   Original Methods:")
        for method in original_methods[:5]:  # Show first 5
            print(f"     • {method}")
        if len(original_methods) > 5:
            print(f"     ... and {len(original_methods) - 5} more")

        print(f"\n   ✨ EMA Confluence ({ema_info['count']}x):")
        for period in ema_info['periods']:
            print(f"     • EMA {period}")
        print()

# Summary
if not ema_resistance and not ema_support:
    print("\n" + "="*90)
    print("ℹ️  No EMA-boosted levels found")
    print("   This means none of the confluence zones aligned with EMAs (20, 50, 100, 200)")
    print("="*90)

print("\n" + "="*90)
print(f"💡 TIP: Try other symbols:")
print(f"   python view_ema_results.py ETHUSDT")
print(f"   python view_ema_results.py SOLUSDT")
print("="*90 + "\n")
