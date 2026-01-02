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
        # Listed in priority order - UNAMBIGUOUS commands first
        # NOTE: Avoid phrases that sound like interactive play invitations
        self.auto_start_triggers = [
            # MOST RELIABLE - Technical/explicit commands
            'start automatic mode',
            'enter automatic mode',
            'start automatic',
            'automatic mode',
            'start auto mode',
            'auto mode',
            'start auto',

            # GOOD - Action-oriented but clear
            'go explore',
            'go roam',
            'go wander',
            'explore mode',

            # PARTING PHRASES - Clear intention to leave Nevil alone
            'seeya nevil',
            'see ya nevil',
            'see you nevil',
            'bye nevil go play',
            'go do your thing',
            'go be autonomous',

            # LESS RELIABLE - Can be ambiguous
            # Removed: 'go play', 'nevil go play', 'go have fun'
            # These sound like "let's play together" invitations to the AI
        ]

        self.auto_stop_triggers = [
            'stop auto', 'stop playing', 'come back', 'stop automatic',
            'manual mode', 'stop exploring', 'nevil come back'
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
        self.logger.info(f"🔍 [DIRECT CMD] ===== CHECKING FOR DIRECT COMMANDS =====")
        self.logger.info(f"🔍 [DIRECT CMD] Raw text: '{text}'")
        self.logger.info(f"🔍 [DIRECT CMD] Lowercase: '{text_lower}'")

        # Check shutdown triggers first (highest priority)
        if self._handle_shutdown(text, text_lower):
            self.logger.info(f"✅ [DIRECT CMD] SHUTDOWN command handled - SKIPPING AI")
            return True

        # Check auto mode triggers
        if self._handle_auto_mode(text, text_lower):
            self.logger.info(f"✅ [DIRECT CMD] AUTO MODE command handled - SKIPPING AI")
            return True

        # No direct command found
        self.logger.info(f"❌ [DIRECT CMD] No direct command found - SENDING TO AI")
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
        """
        Handle auto mode start/stop commands

        Uses exact matching and word boundary checking to catch commands
        before they reach the AI.
        """
        import re

        self.logger.info(f"🔎 [AUTO MODE CHECK] Checking {len(self.auto_start_triggers)} start triggers...")

        # Check for auto mode start triggers
        for i, trigger in enumerate(self.auto_start_triggers, 1):
            self.logger.debug(f"🔎 [AUTO MODE CHECK] [{i}] Testing trigger: '{trigger}'")

            # Method 1: Exact match (case-insensitive)
            if text_lower == trigger:
                self.logger.info(f"🎯 [AUTO TRIGGER] EXACT MATCH: '{trigger}'")
                return self._start_auto_mode(trigger, text)

            # Method 2: Word boundary match
            pattern = r'\b' + re.escape(trigger) + r'\b'
            if re.search(pattern, text_lower):
                self.logger.info(f"🎯 [AUTO TRIGGER] WORD BOUNDARY MATCH: '{trigger}' in '{text_lower}'")

                # Special handling for ambiguous "go play"
                if trigger == 'go play' and len(text_lower) > len('go play'):
                    # Check if followed by music-related words
                    after_match = re.search(r'go play\s+(\w+)', text_lower)
                    if after_match:
                        next_word = after_match.group(1)
                        music_words = ['music', 'song', 'audio', 'sound', 'radio', 'spotify', 'tune', 'track']
                        if next_word in music_words:
                            self.logger.info(f"🚫 [AUTO TRIGGER] Skipping 'go play' - music command detected: '{next_word}'")
                            continue

                return self._start_auto_mode(trigger, text)

        self.logger.info(f"🔎 [AUTO MODE CHECK] Checking {len(self.auto_stop_triggers)} stop triggers...")

        # Check for auto mode stop triggers
        for i, trigger in enumerate(self.auto_stop_triggers, 1):
            self.logger.debug(f"🔎 [AUTO MODE CHECK] [{i}] Testing trigger: '{trigger}'")

            # Method 1: Exact match
            if text_lower == trigger:
                self.logger.info(f"🎯 [AUTO TRIGGER] EXACT MATCH: '{trigger}'")
                return self._stop_auto_mode(trigger, text)

            # Method 2: Word boundary match
            pattern = r'\b' + re.escape(trigger) + r'\b'
            if re.search(pattern, text_lower):
                self.logger.info(f"🎯 [AUTO TRIGGER] WORD BOUNDARY MATCH: '{trigger}' in '{text_lower}'")
                return self._stop_auto_mode(trigger, text)

        return False

    def _start_auto_mode(self, trigger: str, original_text: str) -> bool:
        """Execute auto mode start command"""
        self.logger.info(f"🚀 [AUTO START] Trigger: '{trigger}', Text: '{original_text}'")
        publish_result = self.publish("auto_mode_command", {
            "command": "start",
            "trigger": trigger,
            "original_text": original_text.strip(),
            "timestamp": time.time()
        })
        self.logger.info(f"📢 [PUBLISH] auto_mode_command (start) → {publish_result}")
        return True

    def _stop_auto_mode(self, trigger: str, original_text: str) -> bool:
        """Execute auto mode stop command"""
        self.logger.info(f"🛑 [AUTO STOP] Trigger: '{trigger}', Text: '{original_text}'")
        publish_result = self.publish("auto_mode_command", {
            "command": "stop",
            "trigger": trigger,
            "original_text": original_text.strip(),
            "timestamp": time.time()
        })
        self.logger.info(f"📢 [PUBLISH] auto_mode_command (stop) → {publish_result}")
        return True
