#!/usr/bin/env python3
"""
Test navigation node gesture execution by publishing robot_action directly
"""

import time
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from nevil_framework.message_bus import MessageBus

print("=" * 60)
print("Testing Navigation Gesture Execution")
print("=" * 60)
print("\n⚠️  Make sure Nevil is RUNNING for this test to work!\n")

# Initialize message bus
bus = MessageBus.get_instance()

# Create test gesture message
test_data = {
    "actions": ["wave_hands:med", "nod:med"],
    "source_text": "manual_test_from_script",
    "mood": "neutral",
    "priority": 100,
    "timestamp": time.time()
}

print("Publishing robot_action message:")
print(f"  Actions: {test_data['actions']}")
print(f"  Source: {test_data['source_text']}")
print()

# Publish to robot_action topic
bus.publish(
    topic="robot_action",
    data=test_data
)

print("✓ Message published!")
print("\nWatch Nevil - he should wave and nod within a few seconds.")
print("If he doesn't move, check:")
print("  1. Is Nevil running?")
print("  2. Are there errors in the navigation node logs?")
print("  3. Is the message bus working?")
print()
