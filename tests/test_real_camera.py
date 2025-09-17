#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nevil_framework.message_bus import MessageBus, create_message
import time

print("Testing real camera capture...")

# Create message bus
bus = MessageBus()

# Create snap_pic message
snap_pic_data = {
    "requested_by": "real_camera_test",
    "timestamp": time.time()
}

# Create and publish message
message = create_message("snap_pic", snap_pic_data, "real_camera_test")
print(f"Publishing snap_pic message to test real camera...")

bus.publish("snap_pic", message)

print("Message published. Check logs and images directory for real camera capture.")
time.sleep(3)
bus.cleanup()

