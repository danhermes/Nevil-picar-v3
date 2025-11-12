#!/bin/bash
# Validate Nevil 2.2 environment setup

echo "🔍 Validating Nevil 2.2 Environment"
echo "===================================="
echo ""

ERRORS=0

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found"
    exit 1
fi

# Check Python packages
echo "Checking Python packages..."
$PYTHON_CMD -c "import websockets" 2>/dev/null || { echo "❌ websockets not installed"; ERRORS=$((ERRORS+1)); }
$PYTHON_CMD -c "import aiohttp" 2>/dev/null || { echo "❌ aiohttp not installed"; ERRORS=$((ERRORS+1)); }
$PYTHON_CMD -c "import numpy" 2>/dev/null || { echo "❌ numpy not installed"; ERRORS=$((ERRORS+1)); }
$PYTHON_CMD -c "import openai" 2>/dev/null || { echo "❌ openai not installed"; ERRORS=$((ERRORS+1)); }

# Check API key
echo "Checking API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    ERRORS=$((ERRORS+1))
else
    echo "✅ OPENAI_API_KEY configured"
fi

# Check directory structure
echo "Checking directory structure..."
[ -d "nevil_framework/realtime" ] || { echo "❌ Missing nevil_framework/realtime"; ERRORS=$((ERRORS+1)); }
[ -d "nodes/speech_recognition_realtime" ] || { echo "❌ Missing nodes/speech_recognition_realtime"; ERRORS=$((ERRORS+1)); }
[ -d "nodes/ai_cognition_realtime" ] || { echo "❌ Missing nodes/ai_cognition_realtime"; ERRORS=$((ERRORS+1)); }
[ -d "nodes/speech_synthesis_realtime" ] || { echo "❌ Missing nodes/speech_synthesis_realtime"; ERRORS=$((ERRORS+1)); }

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ Environment validation passed!"
    exit 0
else
    echo "❌ Environment validation failed ($ERRORS errors)"
    exit 1
fi
