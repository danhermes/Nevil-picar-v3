"""
Nevil v3.0 Base Node Class

Provides the foundation for all Nevil nodes with declarative messaging,
threading, logging, and lifecycle management.
"""

import threading
import queue
import time
import logging
import signal
import os
import yaml
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional, Set
from enum import Enum

from .message_bus import Message, MessageBus, create_message, MessagePriority


class NodeStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class NevilNode(ABC):
    """
    Base class for all Nevil v3.0 nodes.

    Provides:
    - Declarative message setup via .messages files
    - Thread-safe message handling
    - Logging infrastructure
    - Configuration management
    - Graceful shutdown handling
    - Health monitoring

    Key Feature: init_messages() automatically sets up all publishers and subscribers
    based on .messages configuration file, eliminating manual subscribe() calls.
    """

    def __init__(self, node_name: str, config_path: str = None):
        self.node_name = node_name
        self.config_path = config_path or f"nodes/{node_name}/.messages"
        self.status = NodeStatus.INITIALIZING

        # Threading components
        self.main_thread = None
        self.message_thread = None
        self.heartbeat_thread = None
        self.shutdown_event = threading.Event()
        self.thread_lock = threading.RLock()

        # Message system
        self.message_queues = {}  # topic -> queue
        self.message_callbacks = {}  # topic -> callback method name
        self.published_topics = set()   # topics this node publishes
        self.subscribed_topics = set()  # topics this node subscribes to
        self.message_bus = None   # Set by framework during startup

        # Configuration and logging
        self.config = self._load_config()
        self.logger = self._setup_logging()

        # Health monitoring
        self.last_heartbeat = time.time()
        self.error_count = 0
        self.max_errors = 10

        # DON'T set up signal handlers in nodes - let the main process handle them
        # This was causing signals to be caught by node threads instead of main thread
        # signal.signal(signal.SIGTERM, self._signal_handler)
        # signal.signal(signal.SIGINT, self._signal_handler)

        # Declarative messaging setup - runs once during initialization
        self.init_messages()

        self.logger.info(f"Node {self.node_name} initialized with messaging configured")

    def _load_config(self) -> Dict[str, Any]:
        """Load node configuration from .messages file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    print(f"[{self.node_name}] Loaded config from {self.config_path}")
                    return config or {}
            else:
                print(f"[{self.node_name}] No config file found at {self.config_path}, using defaults")
                return {}
        except Exception as e:
            print(f"[{self.node_name}] Error loading config: {e}")
            return {}

    def _setup_logging(self) -> logging.Logger:
        """Setup node-specific logging with file and console handlers"""
        logger = logging.getLogger(self.node_name)
        logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        # Create logs directory structure
        log_dir = f"logs"
        os.makedirs(log_dir, exist_ok=True)

        # File handler for node logs
        file_handler = logging.FileHandler(f"{log_dir}/{self.node_name}.log")
        file_handler.setLevel(logging.INFO)

        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Enhanced formatter with EST timestamps and color coding
        formatter = logging.Formatter(
            '[%(asctime)s EST] [%(levelname)-8s] [%(name)-20s] [%(threadName)-15s] %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def start(self):
        """Start the node and all its threads"""
        try:
            self.status = NodeStatus.RUNNING
            self.logger.info(f"Starting node {self.node_name}")

            # Initialize node-specific components
            self.initialize()

            # Start message handling thread
            self.message_thread = threading.Thread(
                target=self._message_loop,
                name=f"{self.node_name}_messages",
                daemon=False
            )
            self.message_thread.start()

            # Start main processing thread
            self.main_thread = threading.Thread(
                target=self._main_loop,
                name=f"{self.node_name}_main",
                daemon=False
            )
            self.main_thread.start()

            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                name=f"{self.node_name}_heartbeat",
                daemon=True
            )
            self.heartbeat_thread.start()

            self.logger.info(f"Node {self.node_name} started successfully")

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.logger.error(f"Failed to start node {self.node_name}: {e}")
            raise

    def stop(self, timeout: float = 10.0):
        """Stop the node gracefully"""
        self.logger.info(f"Stopping node {self.node_name}")
        self.status = NodeStatus.STOPPING

        # Signal shutdown
        self.shutdown_event.set()

        # Stop node-specific components
        try:
            self.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        # Wait for threads to finish
        threads_to_join = [self.main_thread, self.message_thread]

        for thread in threads_to_join:
            if thread and thread.is_alive():
                thread.join(timeout=timeout/len(threads_to_join))
                if thread.is_alive():
                    self.logger.warning(f"Thread {thread.name} did not stop gracefully")

        self.status = NodeStatus.STOPPED
        self.logger.info(f"Node {self.node_name} stopped")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown")
        self.stop()

    def _main_loop(self):
        """Main processing loop - calls subclass main_loop() method"""
        try:
            while not self.shutdown_event.is_set():
                try:
                    # Call subclass main loop
                    self.main_loop()

                    # Update heartbeat
                    self.last_heartbeat = time.time()

                except Exception as e:
                    self.error_count += 1
                    self.logger.error(f"Error in main loop: {e}")

                    if self.error_count >= self.max_errors:
                        self.logger.critical(f"Too many errors ({self.error_count}), stopping node")
                        self.status = NodeStatus.ERROR
                        break

                    # Brief pause before retry
                    time.sleep(1.0)

        except Exception as e:
            self.logger.critical(f"Critical error in main loop: {e}")
            self.status = NodeStatus.ERROR

    def _message_loop(self):
        """Message handling loop - processes incoming messages"""
        while not self.shutdown_event.is_set():
            try:
                # Process incoming messages for all subscribed topics
                for topic, message_queue in self.message_queues.items():
                    try:
                        message = message_queue.get_nowait()
                        self._handle_message(topic, message)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing message on topic {topic}: {e}")

                # Brief pause to prevent busy waiting
                time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"Error in message loop: {e}")
                time.sleep(0.1)

    def _handle_message(self, topic: str, message: Message):
        """Handle incoming message using declaratively configured callbacks"""
        try:
            if topic in self.message_callbacks:
                callback_name = self.message_callbacks[topic]
                callback_method = getattr(self, callback_name, None)

                if callback_method and callable(callback_method):
                    # Call the callback method with the message
                    callback_method(message)
                    self.logger.debug(f"Processed message on topic {topic} via {callback_name}")
                else:
                    self.logger.error(f"Callback method '{callback_name}' not found or not callable for topic {topic}")
            else:
                self.logger.warning(f"No callback configured for topic {topic}")
        except Exception as e:
            self.logger.error(f"Error in message callback for topic {topic}: {e}")

    def _heartbeat_loop(self):
        """Send periodic heartbeat messages for health monitoring"""
        while not self.shutdown_event.is_set():
            try:
                heartbeat_data = {
                    "node_name": self.node_name,
                    "status": self.status.value,
                    "timestamp": time.time(),
                    "error_count": self.error_count,
                    "thread_count": threading.active_count(),
                    "uptime": time.time() - self.last_heartbeat
                }

                # Publish heartbeat if we have system_heartbeat topic configured
                if "system_heartbeat" in self.published_topics:
                    self.publish("system_heartbeat", heartbeat_data)

                time.sleep(5.0)  # Heartbeat every 5 seconds

            except Exception as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                time.sleep(5.0)

    def init_messages(self):
        """
        Initialize messaging based on .messages configuration file.

        This method runs once during __init__ and automatically sets up all
        publishers and subscribers for the life of the node based on the
        declarative configuration in the .messages file.

        KEY FEATURE: This eliminates the need for manual subscribe() calls!
        """
        try:
            if not self.config:
                self.logger.warning(f"No .messages configuration found for {self.node_name}")
                return

            # Set up publishers (topics this node will publish to)
            publishes = self.config.get('publishes', [])
            for pub_config in publishes:
                topic = pub_config.get('topic')
                if topic:
                    self.published_topics.add(topic)
                    self.logger.debug(f"Configured to publish to topic: {topic}")

            # Set up subscribers (topics this node will subscribe to)
            subscribes = self.config.get('subscribes', [])
            for sub_config in subscribes:
                topic = sub_config.get('topic')
                callback_name = sub_config.get('callback')

                if topic and callback_name:
                    # Verify callback method exists
                    if hasattr(self, callback_name):
                        self.subscribed_topics.add(topic)
                        self.message_callbacks[topic] = callback_name

                        # Create message queue for this topic
                        self.message_queues[topic] = queue.Queue(maxsize=100)

                        self.logger.debug(f"Configured to subscribe to topic: {topic} -> {callback_name}")
                    else:
                        self.logger.error(f"Callback method '{callback_name}' not found for topic '{topic}'")

            # Register with message bus when it becomes available
            if self.message_bus:
                self._register_with_message_bus()

            self.logger.info(f"Messaging initialized: {len(self.published_topics)} publishers, {len(self.subscribed_topics)} subscribers")

        except Exception as e:
            self.logger.error(f"Error initializing messages: {e}")

    def set_message_bus(self, message_bus: MessageBus):
        """Set the message bus and register subscriptions"""
        self.message_bus = message_bus
        self._register_with_message_bus()

    def _register_with_message_bus(self):
        """Register subscriptions with the message bus"""
        try:
            for topic in self.subscribed_topics:
                if topic in self.message_queues:
                    self.message_bus.subscribe(self.node_name, topic, self.message_queues[topic])
                    self.logger.debug(f"Registered subscription for topic: {topic}")
        except Exception as e:
            self.logger.error(f"Error registering with message bus: {e}")

    def publish(self, topic: str, data: Any, priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Publish message to topic.

        Note: Topic must be declared in .messages file under 'publishes' section.
        """
        try:
            # Verify topic is declared for publishing
            if topic not in self.published_topics:
                self.logger.warning(f"Topic '{topic}' not declared in .messages file for publishing")
                return False

            message = create_message(
                topic=topic,
                data=data,
                source_node=self.node_name,
                priority=priority
            )

            if self.message_bus:
                success = self.message_bus.publish(message)
                if success:
                    self.logger.debug(f"Published message to topic '{topic}'")
                return success
            else:
                self.logger.warning(f"No message bus available for publishing to {topic}")
                return False

        except Exception as e:
            self.logger.error(f"Error publishing to topic {topic}: {e}")
            return False

    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def initialize(self):
        """Initialize node-specific components"""
        pass

    @abstractmethod
    def main_loop(self):
        """Main processing loop - called repeatedly"""
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup node-specific resources"""
        pass

    # Utility methods
    def get_status(self) -> Dict[str, Any]:
        """Get current node status for monitoring"""
        return {
            "node_name": self.node_name,
            "status": self.status.value,
            "error_count": self.error_count,
            "published_topics": list(self.published_topics),
            "subscribed_topics": list(self.subscribed_topics),
            "uptime": time.time() - self.last_heartbeat,
            "thread_count": threading.active_count()
        }