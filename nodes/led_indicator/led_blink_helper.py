"""
LED Blink Helper - Manages LED blink patterns for different states

This helper runs continuously in its own thread and manages LED patterns
for different operational states (play, listen, actions).
"""
import time
import threading
import logging
from time import sleep


class LEDBlinkHelper:
    """
    Helper class to manage LED blink patterns for different operational states.
    Runs continuously in its own thread.

    States:
    - play: Double blink pattern (not listening, playing audio)
    - listen: Fast continuous blink (listening for input)
    - actions: Solid on (performing actions, GPT calls, STT, TTS)
    - off: LED off
    """

    def __init__(self, led_pin, double_blink_interval=1.2, blink_interval=0.1, logger=None):
        """
        Initialize LED blink helper

        Args:
            led_pin: The Pin object for the LED
            double_blink_interval: Time between double blink sequences (seconds)
            blink_interval: Time for fast blink on/off (seconds)
            logger: Optional logger instance
        """
        self.led = led_pin
        self.DOUBLE_BLINK_INTERVAL = double_blink_interval
        self.BLINK_INTERVAL = blink_interval
        self.logger = logger or logging.getLogger(__name__)

        # Thread control
        self.running = False
        self.thread = None
        self.state_lock = threading.Lock()

        # State management
        self._current_state = "off"
        self.last_blink_time = 0

    def start(self):
        """Start the LED blink thread"""
        if self.running:
            self.logger.warning("LED blink helper already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._blink_loop, daemon=True)
        self.thread.start()
        self.logger.info("LED blink helper started")

    def stop(self):
        """Stop the LED blink thread"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.led.off()
        self.logger.info("LED blink helper stopped")

    def set_state(self, state: str):
        """
        Set the LED state

        Args:
            state: One of 'play', 'listen', 'actions', 'off'
        """
        with self.state_lock:
            if self._current_state != state:
                self.logger.debug(f"LED state change: {self._current_state} -> {state}")
                self._current_state = state
                self.last_blink_time = 0  # Reset timer on state change

    def get_state(self) -> str:
        """Get the current LED state"""
        with self.state_lock:
            return self._current_state

    def _blink_loop(self):
        """Main blink loop that runs continuously"""
        while self.running:
            try:
                with self.state_lock:
                    current_state = self._current_state
                    current_time = time.time()

                if current_state == 'play':
                    self._handle_double_blink(current_time)
                elif current_state == 'listen':
                    self._handle_fast_blink(current_time)
                elif current_state == 'actions':
                    self._handle_solid_on()
                elif current_state == 'off':
                    self.led.off()

                # Small sleep to prevent CPU spinning
                time.sleep(0.05)

            except Exception as e:
                self.logger.error(f"Error in LED blink loop: {e}")
                time.sleep(0.1)

    def _handle_double_blink(self, current_time):
        """
        Execute double blink pattern (play mode - not listening)
        Two quick blinks with pause between sequences
        """
        if current_time - self.last_blink_time > self.DOUBLE_BLINK_INTERVAL:
            self.led.off()
            self.led.on()
            sleep(0.1)
            self.led.off()
            sleep(0.1)
            self.led.on()
            sleep(0.1)
            self.led.off()

            with self.state_lock:
                self.last_blink_time = current_time

    def _handle_fast_blink(self, current_time):
        """
        Execute fast blink pattern (listen mode - actively listening)
        Continuous fast on/off blinking
        """
        if current_time - self.last_blink_time > self.BLINK_INTERVAL:
            self.led.off()
            sleep(self.BLINK_INTERVAL)
            self.led.on()
            sleep(self.BLINK_INTERVAL)

            with self.state_lock:
                self.last_blink_time = current_time

    def _handle_solid_on(self):
        """
        Turn LED solid on (actions mode - performing operations)
        """
        self.led.on()
