#!/usr/bin/env python3
"""
Test script to simulate asking Nevil to take a picture
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nevil_framework.messaging import MessageBus

def test_camera_request():
    """Test camera request by simulating voice command"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    logger = logging.getLogger("camera_test")

    logger.info("Testing camera request flow...")

    # Create message bus connection
    message_bus = MessageBus()

    # Simulate voice command asking for a picture
    voice_command_data = {
        "text": "Please take a picture",
        "confidence": 0.95,
        "timestamp": time.time()
    }

    logger.info(f"Publishing voice command: '{voice_command_data['text']}'")

    # Publish voice command (will be picked up by AI cognition)
    message_bus.publish("voice_command", voice_command_data)

    logger.info("Voice command published. Check LogScope for the complete flow:")
    logger.info("1. AI cognition should receive voice command")
    logger.info("2. AI should detect take_snapshot tool and publish snap_pic")
    logger.info("3. Visual node should capture stub image")
    logger.info("4. AI should analyze image and respond via speech")

    time.sleep(1)  # Give system time to process

    # Close message bus
    message_bus.cleanup()

    logger.info("Test complete. Monitor logs for results.")

if __name__ == "__main__":
    test_camera_request()