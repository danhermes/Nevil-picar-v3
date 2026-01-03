#!/bin/bash
# Gesture Log Analysis Script
# Run this AFTER talking to Nevil to diagnose gesture issues

echo "=========================================="
echo "Gesture Activity Log Analysis"
echo "=========================================="
echo ""

# Find the most recent log files
AI_LOG=$(ls -t /tmp/nevil_ai*.log 2>/dev/null | head -1)
NAV_LOG=$(ls -t /tmp/nevil_navigation*.log 2>/dev/null | head -1)

if [ -z "$AI_LOG" ]; then
    echo "❌ No AI cognition logs found in /tmp/"
    echo "   Expected: /tmp/nevil_ai*.log"
    AI_LOG="/dev/null"
else
    echo "✓ AI Log: $AI_LOG"
fi

if [ -z "$NAV_LOG" ]; then
    echo "❌ No navigation logs found in /tmp/"
    echo "   Expected: /tmp/nevil_navigation*.log"
    NAV_LOG="/dev/null"
else
    echo "✓ Navigation Log: $NAV_LOG"
fi

echo ""
echo "=========================================="
echo "1. Checking if GPT called perform_gesture"
echo "=========================================="

GESTURE_CALLS=$(grep -i "AI chose gesture\|perform_gesture\|Function call: perform_gesture" "$AI_LOG" 2>/dev/null | tail -10)

if [ -n "$GESTURE_CALLS" ]; then
    echo "✓ FOUND: GPT is calling perform_gesture()"
    echo ""
    echo "$GESTURE_CALLS"
else
    echo "❌ NOT FOUND: GPT is NOT calling perform_gesture()"
    echo ""
    echo "This is the main issue - GPT isn't using function calls."
    echo "Possible causes:"
    echo "  - Realtime API voice mode may not support function calling"
    echo "  - Temperature too low (suppresses function calls)"
    echo "  - System prompt not being followed"
fi

echo ""
echo "=========================================="
echo "2. Checking if robot_action published"
echo "=========================================="

PUBLISH_LOGS=$(grep -i "PUBLISHING robot_action\|Publish result" "$AI_LOG" 2>/dev/null | tail -10)

if [ -n "$PUBLISH_LOGS" ]; then
    echo "✓ FOUND: AI node is publishing robot_action"
    echo ""
    echo "$PUBLISH_LOGS"
else
    echo "❌ NOT FOUND: AI node is NOT publishing robot_action"
fi

echo ""
echo "=========================================="
echo "3. Checking if navigation received actions"
echo "=========================================="

RECEIVED_LOGS=$(grep -i "RECEIVED robot action\|Extracted actions" "$NAV_LOG" 2>/dev/null | tail -10)

if [ -n "$RECEIVED_LOGS" ]; then
    echo "✓ FOUND: Navigation received robot_action messages"
    echo ""
    echo "$RECEIVED_LOGS"
else
    echo "❌ NOT FOUND: Navigation did NOT receive robot_action"
fi

echo ""
echo "=========================================="
echo "4. Checking if actions were executed"
echo "=========================================="

EXECUTION_LOGS=$(grep -i "Executing:\|STARTING ACTION SEQUENCE\|Completed.*in.*s" "$NAV_LOG" 2>/dev/null | tail -15)

if [ -n "$EXECUTION_LOGS" ]; then
    echo "✓ FOUND: Navigation is executing actions"
    echo ""
    echo "$EXECUTION_LOGS"
else
    echo "❌ NOT FOUND: Navigation is NOT executing actions"
fi

echo ""
echo "=========================================="
echo "5. Checking for errors"
echo "=========================================="

ERRORS=$(grep -i "error.*gesture\|failed.*gesture\|error.*robot_action" "$AI_LOG" "$NAV_LOG" 2>/dev/null | tail -10)

if [ -n "$ERRORS" ]; then
    echo "⚠️ FOUND ERRORS:"
    echo ""
    echo "$ERRORS"
else
    echo "✓ No errors found"
fi

echo ""
echo "=========================================="
echo "Summary & Diagnosis"
echo "=========================================="
echo ""

# Count findings
FINDINGS=0

if [ -n "$GESTURE_CALLS" ]; then
    FINDINGS=$((FINDINGS + 1))
fi
if [ -n "$PUBLISH_LOGS" ]; then
    FINDINGS=$((FINDINGS + 1))
fi
if [ -n "$RECEIVED_LOGS" ]; then
    FINDINGS=$((FINDINGS + 1))
fi
if [ -n "$EXECUTION_LOGS" ]; then
    FINDINGS=$((FINDINGS + 1))
fi

echo "Checklist:"
echo "  [$([ -n "$GESTURE_CALLS" ] && echo "✓" || echo "✗")] GPT calling perform_gesture"
echo "  [$([ -n "$PUBLISH_LOGS" ] && echo "✓" || echo "✗")] AI publishing robot_action"
echo "  [$([ -n "$RECEIVED_LOGS" ] && echo "✓" || echo "✗")] Navigation receiving messages"
echo "  [$([ -n "$EXECUTION_LOGS" ] && echo "✓" || echo "✗")] Navigation executing actions"
echo ""

if [ $FINDINGS -eq 0 ]; then
    echo "❌ DIAGNOSIS: GPT is not calling perform_gesture() at all"
    echo ""
    echo "ROOT CAUSE: Realtime API in voice mode may not reliably"
    echo "support function calling. This is a known limitation."
    echo ""
    echo "SOLUTIONS:"
    echo "  1. Switch to text-only mode (remove 'audio' from modalities)"
    echo "  2. Increase temperature to 0.8-0.9 (may help)"
    echo "  3. Use SpeechAnimationManager (keyword-based gestures)"
    echo "  4. Add explicit function call examples in system prompt"
elif [ $FINDINGS -eq 1 ]; then
    echo "⚠️ DIAGNOSIS: GPT calls gestures but they don't reach navigation"
    echo ""
    echo "Possible issues:"
    echo "  - Message bus not connected"
    echo "  - Publishing failed"
    echo "  - Navigation node not subscribed"
elif [ $FINDINGS -eq 2 ] || [ $FINDINGS -eq 3 ]; then
    echo "⚠️ DIAGNOSIS: Messages flow but execution fails"
    echo ""
    echo "Possible issues:"
    echo "  - Action queue blocked"
    echo "  - busy_state conflicts"
    echo "  - Servo/hardware problem"
elif [ $FINDINGS -eq 4 ]; then
    echo "✓ DIAGNOSIS: Everything working!"
    echo ""
    echo "Gestures should be happening. If you don't see movement:"
    echo "  - Check servo connections"
    echo "  - Check if movements are too subtle"
    echo "  - Verify car object initialized"
fi

echo ""
echo "=========================================="
echo "Recent conversation context (last 20 lines)"
echo "=========================================="
echo ""
echo "AI Log:"
tail -20 "$AI_LOG" 2>/dev/null | grep -E "User:|NEVIL|Function call|gesture|robot_action" || echo "No recent activity"

echo ""
echo "=========================================="
echo "Done! Share this output for diagnosis."
echo "=========================================="
