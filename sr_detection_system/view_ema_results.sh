#!/bin/bash
# Quick viewer for EMA-enhanced S/R results

SYMBOL="${1:-BTCUSDT}"

echo ""
echo "=========================================================================="
echo "          🎯 EMA-ENHANCED S/R LEVELS - $SYMBOL"
echo "=========================================================================="
echo ""

# Get data from API
curl -s "http://localhost:8080/api/ultimate/$SYMBOL/15" | jq -r '

# Metadata
"📊 METADATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Symbol:          \(.metadata.symbol)
Current Price:   $\(.metadata.current_price | tonumber | floor | tostring | split("") | reverse | join("") | gsub("(.{3})"; "\\1,") | split("") | reverse | join("") | sub("^,"; ""))
Processing Time: \(.metadata.processing_time_ms)ms
Methods:         \(.metadata.methods_used | join(", "))
Total Levels:    \(.resistance | length) resistance, \(.support | length) support
",

# EMA-boosted levels
"
📈 EMA-BOOSTED RESISTANCE LEVELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",

(.resistance[] | select(.ema_confluence) |
"
💰 Price: $\(.price | floor)
   Distance: +\(((.price - .price) / .price * 100) | tonumber)% from current
   Strength: \(.strength) (boosted by +\(.ema_confluence.boost))

   Original Methods (\(.num_methods - .ema_confluence.count)):
   \(.methods | map(select(startswith("ema_") | not)) | map("   • " + .) | join("\n"))

   ✨ EMA Confluence (\(.ema_confluence.count)x):
   \(.ema_confluence.periods | map("   • EMA " + tostring) | join("\n"))
"),

"
📉 EMA-BOOSTED SUPPORT LEVELS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",

(.support[] | select(.ema_confluence) |
"
💰 Price: $\(.price | floor)
   Distance: -\(((.price - .price) / .price * 100) | tonumber)% from current
   Strength: \(.strength) (boosted by +\(.ema_confluence.boost))

   Original Methods (\(.num_methods - .ema_confluence.count)):
   \(.methods | map(select(startswith("ema_") | not)) | map("   • " + .) | join("\n"))

   ✨ EMA Confluence (\(.ema_confluence.count)x):
   \(.ema_confluence.periods | map("   • EMA " + tostring) | join("\n"))
"),

"
=========================================================================="
'

echo ""
echo "💡 TIP: Run with different symbol:"
echo "   ./view_ema_results.sh ETHUSDT"
echo "   ./view_ema_results.sh SOLUSDT"
echo ""
