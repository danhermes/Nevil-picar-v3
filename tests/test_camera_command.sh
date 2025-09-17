#!/bin/bash

# Simple test to trigger camera functionality
# This simulates saying "Hey Nevil, take a picture" to the system

echo "Testing camera functionality..."
echo "System should be listening now."
echo ""
echo "The expected flow:"
echo "1. Say 'Take a picture' clearly near the microphone"
echo "2. Speech recognition should pick it up"
echo "3. AI should detect take_snapshot request"
echo "4. Visual node should capture stub image"
echo "5. AI should analyze the image with OpenAI"
echo "6. Speech synthesis should speak the response"
echo ""
echo "Monitor logs in real-time with: ./logscope"
echo "Or check specific messages with: "
echo "  tail -f logs/* | grep -E '(snap_pic|visual_data|take_snapshot|📷|📸)'"
echo ""
echo "Press Ctrl+C to exit when done testing"

# Monitor for camera-related activity
tail -f logs/* 2>/dev/null | grep -E "(snap_pic|visual_data|take_snapshot|📷|📸|Detected.*snapshot)" --line-buffered