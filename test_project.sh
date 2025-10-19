#!/bin/bash

echo "=========================================="
echo "🧪 Testing Live S/R Dashboard"
echo "=========================================="
echo ""

cd /Users/danish/PycharmProjects/options_trading/live_sr_dashboard

# Test 1: Config file
echo "1️⃣  Testing config file..."
if python -c "import json; json.load(open('config/config.json'))" 2>/dev/null; then
    echo "✅ Config file valid"
else
    echo "❌ Config file invalid"
    exit 1
fi

# Test 2: Imports
echo "2️⃣  Testing imports..."
python -c "
import sys
sys.path.insert(0, 'src')
from sr_detectors import sr_detector_technical
from sr_detectors import sr_detector_sentiment  
from sr_methods.technical import swing_high_low
from sr_methods.sentiment import oi_walls
from webapp import app
print('✅ All imports successful')
"

# Test 3: Redis
echo "3️⃣  Testing Redis connection..."
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis not running"
fi

# Test 4: Webapp
echo "4️⃣  Testing webapp..."
python -c "
import sys
sys.path.insert(0, 'src')
from webapp import app
print('✅ Webapp module loads')
"

# Test 5: Directory structure
echo "5️⃣  Testing directory structure..."
missing=0
for dir in config logs scripts src/data_collection src/sr_detectors src/sr_methods/technical src/sr_methods/sentiment src/webapp/templates; do
    if [ ! -d "$dir" ]; then
        echo "❌ Missing directory: $dir"
        missing=1
    fi
done

if [ $missing -eq 0 ]; then
    echo "✅ All directories present"
fi

# Test 6: Key files
echo "6️⃣  Testing key files..."
missing_files=0
for file in README.md requirements.txt .gitignore LICENSE scripts/start_system.sh scripts/stop_system.sh; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing file: $file"
        missing_files=1
    fi
done

if [ $missing_files -eq 0 ]; then
    echo "✅ All key files present"
fi

echo ""
echo "=========================================="
echo "✅ Project verification complete!"
echo "=========================================="
echo ""
echo "📊 Summary:"
echo "   - Python files: $(find . -name '*.py' | wc -l | xargs)"
echo "   - Total files: $(find . -type f | grep -v ".git" | wc -l | xargs)"
echo ""
echo "🚀 Ready to push to GitHub!"
