#!/usr/bin/env python3
"""
Diagnostic script to test gesture flow from AI → Navigation
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*60)
print("Gesture Flow Diagnostic")
print("="*60)

# Check 1: Can we publish robot_action messages?
print("\n1. Testing message bus publishing...")
try:
    from nevil_framework.message_bus import MessageBus
    bus = MessageBus()

    test_data = {
        "actions": ["wave:med", "nod:fast"],
        "source_text": "test",
        "mood": "neutral",
        "priority": 100,
        "timestamp": 1234567890.0
    }

    result = bus.publish("robot_action", test_data)
    print(f"   ✓ Can publish robot_action: {result}")
except Exception as e:
    print(f"   ✗ Error publishing: {e}")

# Check 2: Does navigation node have robot_action subscription?
print("\n2. Checking navigation node configuration...")
try:
    import yaml
    with open("nodes/navigation/.messages", 'r') as f:
        config = yaml.safe_load(f)

    subscribes = config.get('subscribes', [])
    has_robot_action = any(sub.get('topic') == 'robot_action' for sub in subscribes)

    if has_robot_action:
        print(f"   ✓ Navigation subscribes to robot_action")
        robot_action_sub = next(sub for sub in subscribes if sub.get('topic') == 'robot_action')
        print(f"   ✓ Callback: {robot_action_sub.get('callback')}")
    else:
        print(f"   ✗ Navigation does NOT subscribe to robot_action!")

except Exception as e:
    print(f"   ✗ Error checking config: {e}")

# Check 3: Does AI node publish robot_action?
print("\n3. Checking AI node configuration...")
try:
    with open("nodes/ai_cognition_realtime/.messages", 'r') as f:
        config = yaml.safe_load(f)

    publishes = config.get('publishes', [])
    has_robot_action = any(pub.get('topic') == 'robot_action' for pub in publishes)

    if has_robot_action:
        print(f"   ✓ AI node publishes robot_action")
    else:
        print(f"   ✗ AI node does NOT publish robot_action!")

except Exception as e:
    print(f"   ✗ Error checking config: {e}")

# Check 4: Are gesture functions defined in AI?
print("\n4. Checking AI gesture functions...")
try:
    from nodes.ai_cognition_realtime.ai_node22 import AiNode22

    # Check if perform_gesture exists in function tools
    print(f"   Checking for perform_gesture function...")
    # We can't easily check this without initializing, so just confirm import works
    print(f"   ✓ AiNode22 class imported successfully")

except Exception as e:
    print(f"   ✗ Error importing AI node: {e}")

# Check 5: Check recent logs for gestures
print("\n5. Checking recent logs for gesture activity...")
import subprocess
try:
    # Check for gesture-related log entries
    result = subprocess.run(
        ['grep', '-r', 'perform_gesture\\|robot_action\\|AI chose gesture', '/tmp/nevil*.log'],
        capture_output=True,
        text=True,
        timeout=5
    )

    if result.stdout:
        lines = result.stdout.split('\n')[:10]  # First 10 matches
        print(f"   Found {len(lines)} recent gesture log entries:")
        for line in lines:
            if line.strip():
                print(f"   {line[:100]}")
    else:
        print(f"   ⚠ No gesture activity found in recent logs")
        print(f"   This suggests GPT isn't calling perform_gesture()")

except Exception as e:
    print(f"   ⚠ Could not check logs: {e}")

# Check 6: Test gesture execution directly
print("\n6. Testing direct gesture execution...")
try:
    from nodes.navigation.picarx import Picarx
    from nodes.navigation.action_helper import actions_dict

    car = Picarx()

    # Try to execute a simple gesture
    if "wave" in actions_dict:
        print(f"   ✓ 'wave' gesture found in actions_dict")
        print(f"   Testing wave gesture...")
        actions_dict["wave"](car, speed="med")
        print(f"   ✓ Wave gesture executed successfully")
    else:
        print(f"   ✗ 'wave' gesture NOT found in actions_dict")
        print(f"   Available gestures: {list(actions_dict.keys())[:10]}")

except Exception as e:
    print(f"   ✗ Error executing gesture: {e}")

print("\n" + "="*60)
print("Diagnostic Summary")
print("="*60)
print("\nIf you see ✗ marks above, those are the issues to fix.")
print("If all ✓ but no gestures during speech, check:")
print("  1. Are GPT function calls enabled in system prompt?")
print("  2. Is GPT actually calling perform_gesture()?")
print("  3. Check AI node logs for 'AI chose gesture'")
print("="*60)
