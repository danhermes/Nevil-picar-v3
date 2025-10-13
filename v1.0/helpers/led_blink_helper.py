"""
LED Blink Helper - Manages LED blink patterns for different states
"""
import time
from time import sleep


class LEDBlinkHelper:
    """
    Helper class to manage LED blink patterns for different operational states.

    States:
    - play: Double blink pattern (not listening, playing audio)
    - listen: Fast continuous blink (listening for input)
    - actions: Solid on (performing actions, GPT calls, STT, TTS)
    """

    def __init__(self, led_pin, double_blink_interval=1.2, blink_interval=0.1):
        """
        Initialize LED blink helper

        Args:
            led_pin: The Pin object for the LED
            double_blink_interval: Time between double blink sequences (seconds)
            blink_interval: Time for fast blink on/off (seconds)
        """
        self.led = led_pin
        self.DOUBLE_BLINK_INTERVAL = double_blink_interval
        self.BLINK_INTERVAL = blink_interval
        self.last_state = None
        self.last_blink_time = 0

    def handle_state(self, state):
        """
        Handle LED behavior based on current state

        Args:
            state: Current operational state ('play', 'listen', 'actions')

        Returns:
            Updated last_blink_time
        """
        # Reset timer if state changed
        if state != self.last_state:
            self.last_blink_time = 0
            self.last_state = state

        current_time = time.time()

        if state == 'play':
            return self._double_blink(current_time)
        elif state == 'listen':
            return self._fast_blink(current_time)
        elif state == 'actions':
            self._solid_on()
            return self.last_blink_time
        else:
            # Unknown state, turn off LED
            self.led.off()
            return self.last_blink_time

    def _double_blink(self, current_time):
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
            return current_time
        return self.last_blink_time

    def _fast_blink(self, current_time):
        """
        Execute fast blink pattern (listen mode - actively listening)
        Continuous fast on/off blinking
        """
        if current_time - self.last_blink_time > self.BLINK_INTERVAL:
            self.led.off()
            sleep(self.BLINK_INTERVAL)
            self.led.on()
            sleep(self.BLINK_INTERVAL)
            return current_time
        return self.last_blink_time

    def _solid_on(self):
        """
        Turn LED solid on (actions mode - performing operations)
        """
        self.led.on()

    def off(self):
        """Turn LED off"""
        self.led.off()
