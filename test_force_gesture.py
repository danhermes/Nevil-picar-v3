#!/usr/bin/env python3
"""
Force a gesture through the message bus to test navigation node
"""

import time
import json

print("This test requires Nevil to be RUNNING")
print("It will inject a robot_action message into the message bus")
print()
input("Press ENTER to continue...")

# Create a robot_action message file
test_message = {
    "actions": ["nod:med", "wave:med"],
    "source_text": "manual_test",
    "mood": "neutral",
    "priority": 100,
    "timestamp": time.time()
}

# Write to a file that we can inject
with open('/tmp/test_gesture.json', 'w') as f:
    json.dump(test_message, f)

print("\nTest message created at: /tmp/test_gesture.json")
print(f"Content: {test_message}")
print("\nTo inject this into Nevil's message bus, run:")
print("   python3 -c \"from nevil_framework.message_bus import MessageBus; bus = MessageBus(); bus.publish('robot_action', " + str(test_message).replace("'", '\\"') + ")\"")
print("\nOR restart Nevil and check logs for gesture activity when you talk to him")
