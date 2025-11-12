"""
Direct Command Handler for Speech Recognition

Handles voice commands that bypass AI processing and execute directly.
Includes auto mode control, shutdown commands, and other system-level triggers.
"""

import time
import subprocess
import logging
from typing import Optional, Tuple, Callable


class DirectCommandHandler:
    """Handles direct voice commands that bypass AI processing"""

    def __init__(self, logger: logging.Logger, publish_callback: Callable):
        """
        Initialize direct command handler

        Args:
            logger: Logger instance for this handler
            publish_callback: Function to publish messages (e.g., self.publish from node)
        """
        self.logger = logger
        self.publish = publish_callback

        # Define trigger phrases for different command types
        self.auto_start_triggers = [
            'start auto', 'go play', 'seeya nevil', 'see ya nevil',
            'auto mode', 'automatic mode', 'go have fun', 'go explore',
            'entertain yourself', 'do your thing'
        ]

        self.auto_stop_triggers = [
            'stop auto', 'stop playing', 'come back', 'stop automatic',
            'manual mode', 'stop exploring'
        ]

        self.shutdown_triggers = [
            'nevil shut down', 'nevil shutdown', 'shut down nevil', 'shutdown nevil'
        ]

    def check_and_handle(self, text: str) -> bool:
        """
        Check if text contains a direct command and handle it

        Args:
            text: Recognized speech text

        Returns:
            True if a direct command was handled, False otherwise
        """
        if not text or not text.strip():
            return False

        text_lower = text.strip().lower()
        self.logger.info(f"🔍 [DIRECT CMD] Checking for direct commands in: '{text_lower}'")

        # Check shutdown triggers first (highest priority)
        if self._handle_shutdown(text, text_lower):
            return True

        # Check auto mode triggers
        if self._handle_auto_mode(text, text_lower):
            return True

        # No direct command found
        return False

    def _handle_shutdown(self, text: str, text_lower: str) -> bool:
        """Handle shutdown commands"""
        for trigger in self.shutdown_triggers:
            if trigger in text_lower:
                self.logger.info(f"🔴 [SHUTDOWN TRIGGER] Detected: '{trigger}' in '{text}'")

                # Announce shutdown via TTS
                self.publish("tts_request", {
                    "text": "Shutting down now. Goodbye!",
                    "priority": 1  # Highest priority
                })

                # Give TTS time to speak
                self.logger.info("🔴 [SHUTDOWN] Waiting for TTS to complete...")
                time.sleep(3.0)

                # Execute shutdown command
                self.logger.info("🔴 [SHUTDOWN] Executing: sudo systemctl stop nevil")
                try:
                    subprocess.run(['sudo', 'systemctl', 'stop', 'nevil'], check=True)
                    self.logger.info("🔴 [SHUTDOWN] Shutdown command executed successfully")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"🔴 [SHUTDOWN] Failed to execute shutdown: {e}")
                except Exception as e:
                    self.logger.error(f"🔴 [SHUTDOWN] Unexpected error during shutdown: {e}")

                return True

        return False

    def _handle_auto_mode(self, text: str, text_lower: str) -> bool:
        """Handle auto mode start/stop commands"""
        # Check for auto mode start triggers
        for trigger in self.auto_start_triggers:
            if trigger in text_lower:
                self.logger.info(f"🤖 [AUTO TRIGGER] Detected: '{trigger}' in '{text}'")
                # Publish direct auto command to navigation
                publish_result = self.publish("auto_mode_command", {
                    "command": "start",
                    "trigger": trigger,
                    "original_text": text.strip(),
                    "timestamp": time.time()
                })
                self.logger.info(f"📢 [PUBLISH] auto_mode_command publish result: {publish_result}")
                return True

        # Check for auto mode stop triggers
        for trigger in self.auto_stop_triggers:
            if trigger in text_lower:
                self.logger.info(f"🛑 [AUTO TRIGGER] Detected: '{trigger}' in '{text}'")
                # Publish direct auto command to navigation
                self.publish("auto_mode_command", {
                    "command": "stop",
                    "trigger": trigger,
                    "original_text": text.strip(),
                    "timestamp": time.time()
                })
                return True

        return False
