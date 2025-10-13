"""
LED Indicator Node for Nevil v3.0

Provides visual feedback about system state through LED blink patterns:
- Listen mode: Fast continuous blink (listening for input)
- Play mode: Double blink pattern (playing audio, not listening)
- Actions mode: Solid on (performing actions, GPT calls, STT, TTS)
"""

import time
import os
import sys
from pathlib import Path
from nevil_framework.base_node import NevilNode

# Add current directory to path for importing led_blink_helper
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
from led_blink_helper import LEDBlinkHelper


class LedIndicatorNode(NevilNode):
    """
    LED Indicator Node - Provides visual status feedback.

    Features:
    - Three distinct LED patterns for different states
    - Responds to system mode changes
    - Runs continuously in background thread
    - Declarative messaging via .messages configuration
    """

    def __init__(self):
        super().__init__("led_indicator")

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.hardware_config = config.get('hardware', {})
        self.timing_config = config.get('timing', {})
        self.mode_mappings = config.get('mode_mappings', {})

        # LED hardware
        self.led = None
        self.led_helper = None

        # State tracking
        self.current_state = "off"
        self.is_speaking = False
        self.is_listening = False

    def initialize(self):
        """Initialize LED hardware and blink helper"""
        self.logger.info("Initializing LED Indicator Node...")

        try:
            # Initialize LED pin using robot_hat
            from robot_hat import Pin
            led_pin_name = self.hardware_config.get('led_pin', 'LED')
            self.led = Pin(led_pin_name)
            self.logger.info(f"LED pin initialized: {led_pin_name}")

            # Initialize blink helper with timing from config
            double_blink_interval = self.timing_config.get('double_blink_interval', 1.2)
            blink_interval = self.timing_config.get('blink_interval', 0.1)

            self.led_helper = LEDBlinkHelper(
                led_pin=self.led,
                double_blink_interval=double_blink_interval,
                blink_interval=blink_interval,
                logger=self.logger
            )

            # Start the blink helper thread
            self.led_helper.start()

            # Set initial state to solid on (default idle state)
            self._update_led_state("actions")

            self.logger.info("LED Indicator Configuration:")
            self.logger.info(f"  LED Pin: {led_pin_name}")
            self.logger.info(f"  Double blink interval: {double_blink_interval}s")
            self.logger.info(f"  Fast blink interval: {blink_interval}s")
            self.logger.info("LED Indicator Node initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize LED indicator: {e}")
            raise

    def main_loop(self):
        """Main processing loop - LED runs in background thread"""
        try:
            # LED blink helper runs in its own thread
            # Main loop just needs to stay alive and handle messages
            time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in LED indicator main loop: {e}")
            time.sleep(0.5)

    def cleanup(self):
        """Cleanup LED resources"""
        self.logger.info("Cleaning up LED indicator...")

        try:
            # Stop blink helper thread
            if self.led_helper:
                self.led_helper.stop()

            # Turn off LED
            if self.led:
                self.led.off()

            self.logger.info("LED indicator cleanup complete")

        except Exception as e:
            self.logger.error(f"Error during LED cleanup: {e}")

    # ========================================================================
    # Message Callbacks (automatically registered via .messages file)
    # ========================================================================

    def on_system_mode_change(self, message):
        """
        Handle system mode changes.
        Maps system modes to LED states based on mode_mappings config.
        """
        try:
            mode = message.data.get('mode', 'idle')
            self.logger.debug(f"System mode changed to: {mode}")

            # Map system mode to LED state
            led_state = self.mode_mappings.get(mode, 'play')

            # Special handling for listening mode
            if mode == 'listening':
                self.is_listening = True
            else:
                self.is_listening = False

            # Update LED state
            self._update_led_state(led_state)

        except Exception as e:
            self.logger.error(f"Error handling system mode change: {e}")

    def on_speaking_status(self, message):
        """
        Handle speaking status changes.
        Speaking/TTS stays in 'actions' mode (solid on) - no LED change needed.
        """
        try:
            speaking = message.data.get('speaking', False)
            self.is_speaking = speaking
            # Speaking doesn't change LED - stays solid on (actions mode)
            # Only listen mode (fast blink) and autonomous play mode (double blink) change LED

        except Exception as e:
            self.logger.error(f"Error handling speaking status: {e}")

    def on_listening_status(self, message):
        """
        Handle listening status changes from speech recognition.
        Fast blink when listening, solid on otherwise.
        """
        try:
            listening = message.data.get('listening', False)
            self.is_listening = listening

            if listening:
                # Actively listening -> fast blink
                self._update_led_state('listen')
                self.logger.debug("LED: Started listening (fast blink)")
            else:
                # Stopped listening -> back to solid on (actions mode for idle/processing/speaking)
                self._update_led_state('actions')
                self.logger.debug("LED: Stopped listening, back to solid on")

        except Exception as e:
            self.logger.error(f"Error handling listening status: {e}")

    def on_auto_mode_status(self, message):
        """
        Handle autonomous play mode status changes.
        Double blink when in play mode, solid on when not.
        """
        try:
            active = message.data.get('active', False)

            if active:
                # Auto mode active -> double blink (play mode)
                self._update_led_state('play')
                self.logger.debug("LED: Auto mode active (double blink)")
            else:
                # Auto mode inactive -> back to solid on (unless listening)
                if self.is_listening:
                    self._update_led_state('listen')
                else:
                    self._update_led_state('actions')
                self.logger.debug("LED: Auto mode inactive, back to solid on")

        except Exception as e:
            self.logger.error(f"Error handling auto mode status: {e}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _update_led_state(self, new_state: str):
        """
        Update LED state and publish status change.

        Args:
            new_state: One of 'play', 'listen', 'actions', 'off'
        """
        if self.current_state != new_state:
            self.logger.debug(f"LED state transition: {self.current_state} -> {new_state}")
            self.current_state = new_state

            # Update hardware
            if self.led_helper:
                self.led_helper.set_state(new_state)

            # Publish status change
            self._publish_led_status()

    def _publish_led_status(self):
        """Publish current LED status"""
        try:
            self.publish("led_status", {
                "state": self.current_state,
                "timestamp": time.time()
            })
        except Exception as e:
            self.logger.error(f"Error publishing LED status: {e}")


# Node factory function (optional, for dynamic loading)
def create_node():
    """Factory function to create LED indicator node"""
    return LedIndicatorNode()
