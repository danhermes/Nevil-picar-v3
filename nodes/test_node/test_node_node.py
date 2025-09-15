"""
Test Node for Nevil v3.0 Framework Validation

Simple test node that demonstrates declarative messaging and basic node functionality.
"""

import time
from nevil_framework.base_node import NevilNode


class TestNodeNode(NevilNode):
    """
    Simple test node for validating the Nevil v3.0 framework.

    Features:
    - Publishes test messages periodically
    - Responds to test input commands
    - Demonstrates declarative messaging setup
    - Validates framework components
    """

    def __init__(self):
        super().__init__("test_node")
        self.message_counter = 0
        self.last_message_time = 0

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.test_interval = config.get('test_interval', 5.0)
        self.max_messages = config.get('max_messages', 0)  # 0 = unlimited

    def initialize(self):
        """Initialize test node components"""
        self.logger.info("Test node initializing...")

        # Log our messaging configuration
        self.logger.info(f"Published topics: {list(self.published_topics)}")
        self.logger.info(f"Subscribed topics: {list(self.subscribed_topics)}")
        self.logger.info(f"Test interval: {self.test_interval}s")
        self.logger.info(f"Max messages: {self.max_messages}")

        self.logger.info("Test node initialization complete")

    def main_loop(self):
        """Main processing loop - sends test messages periodically"""
        current_time = time.time()

        # Send test message if interval has elapsed
        if current_time - self.last_message_time >= self.test_interval:
            self._send_test_message()
            self.last_message_time = current_time

        # Brief pause to prevent busy waiting
        time.sleep(0.1)

    def _send_test_message(self):
        """Send a test message"""
        if self.max_messages > 0 and self.message_counter >= self.max_messages:
            self.logger.info(f"Reached maximum message count ({self.max_messages})")
            return

        self.message_counter += 1

        test_data = {
            "message": f"Test message #{self.message_counter} from {self.node_name}",
            "counter": self.message_counter,
            "timestamp": time.time()
        }

        # Publish test message (topic must be declared in .messages file)
        self.logger.debug(f"Message bus available: {self.message_bus is not None}")
        if self.publish("test_output", test_data):
            self.logger.info(f"Published test message #{self.message_counter}")
        else:
            self.logger.error(f"Failed to publish test message #{self.message_counter} - message bus: {self.message_bus is not None}")

    def on_test_input(self, message):
        """
        Handle test input messages.

        This callback is automatically configured via the .messages file.
        """
        try:
            command = message.data.get("command", "")
            self.logger.info(f"Received test input command: '{command}' from {message.source_node}")

            # Respond to specific commands
            if command == "ping":
                response_data = {
                    "message": f"Pong from {self.node_name}",
                    "counter": self.message_counter,
                    "timestamp": time.time()
                }
                self.publish("test_output", response_data)
                self.logger.info("Responded to ping command")

            elif command == "status":
                status_data = {
                    "message": f"Test node status: counter={self.message_counter}, uptime={time.time() - self.last_heartbeat:.1f}s",
                    "counter": self.message_counter,
                    "timestamp": time.time()
                }
                self.publish("test_output", status_data)
                self.logger.info("Responded to status command")

            elif command == "reset":
                self.message_counter = 0
                reset_data = {
                    "message": f"Test node counter reset",
                    "counter": self.message_counter,
                    "timestamp": time.time()
                }
                self.publish("test_output", reset_data)
                self.logger.info("Reset message counter")

            else:
                self.logger.warning(f"Unknown test command: '{command}'")

        except Exception as e:
            self.logger.error(f"Error handling test input: {e}")

    def cleanup(self):
        """Cleanup test node resources"""
        self.logger.info(f"Test node shutting down after {self.message_counter} messages")

    def get_test_stats(self):
        """Get test-specific statistics"""
        return {
            "message_counter": self.message_counter,
            "test_interval": self.test_interval,
            "max_messages": self.max_messages,
            "last_message_time": self.last_message_time
        }