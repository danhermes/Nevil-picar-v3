#!/usr/bin/env python3
"""
Direct test of visual node by triggering snap_pic
"""

import os
import sys
import time
import json
from threading import Event

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nevil_framework.message_bus import MessageBus, create_message

def test_visual_node():
    """Direct test of visual node snap_pic functionality"""
    print("Testing visual node snap_pic functionality...")

    # Create message bus
    bus = MessageBus()

    # Create snap_pic message
    snap_pic_data = {
        "requested_by": "test_script",
        "timestamp": time.time()
    }

    # Create message
    message = create_message("snap_pic", snap_pic_data, "test_script")

    print(f"Publishing snap_pic message: {snap_pic_data}")

    # Publish message
    bus.publish("snap_pic", message)

    print("Message published. Check logs for visual node response.")
    print("Expected flow:")
    print("1. Visual node receives snap_pic message")
    print("2. Visual node captures stub image")
    print("3. Visual node publishes visual_data message")
    print("4. AI cognition receives visual_data and analyzes image")

    # Wait a moment then cleanup
    time.sleep(2)
    bus.cleanup()

if __name__ == "__main__":
    test_visual_node()