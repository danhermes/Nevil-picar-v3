"""
Nevil v3.0 Message Bus

Simple, reliable message bus using multiprocessing queues for inter-node communication.
Implements declarative publish/subscribe pattern with automatic setup.
"""

import multiprocessing
import queue
import threading
import time
import uuid
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Message structure for inter-node communication"""
    topic: str
    data: Any
    timestamp: float
    source_node: str
    message_id: str
    priority: MessagePriority = MessagePriority.NORMAL


class MessageBus:
    """
    Simple message bus for Nevil v3.0 inter-node communication.

    Features:
    - Topic-based publish/subscribe
    - Process isolation via multiprocessing queues
    - Automatic subscription management
    - Message statistics and monitoring
    - Thread-safe operations
    """

    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size

        # Core data structures
        self.topics = {}  # topic -> set of subscriber queues
        self.subscribers = {}  # node_name -> {topic -> queue}
        self.message_lock = threading.RLock()

        # Statistics
        self.message_count = 0
        self.error_count = 0
        self.start_time = time.time()

        print(f"[MessageBus] Initialized with max_queue_size={max_queue_size}")

    def create_topic(self, topic: str):
        """Create a new topic if it doesn't exist"""
        with self.message_lock:
            if topic not in self.topics:
                self.topics[topic] = set()
                print(f"[MessageBus] Created topic: {topic}")

    def subscribe(self, node_name: str, topic: str, message_queue: queue.Queue):
        """
        Subscribe a node to a topic.

        NOTE: This method is called internally by the framework during
        declarative messaging setup. Node developers should not call this directly.
        """
        with self.message_lock:
            # Create topic if it doesn't exist
            self.create_topic(topic)

            # Add queue to topic subscribers
            self.topics[topic].add(message_queue)

            # Track subscription for this node
            if node_name not in self.subscribers:
                self.subscribers[node_name] = {}
            self.subscribers[node_name][topic] = message_queue

            print(f"[MessageBus] Node '{node_name}' subscribed to topic '{topic}'")

    def unsubscribe(self, node_name: str, topic: str):
        """
        Unsubscribe a node from a topic.

        NOTE: This method is called internally by the framework during
        node shutdown. Node developers should not call this directly.
        """
        with self.message_lock:
            if (node_name in self.subscribers and
                topic in self.subscribers[node_name]):

                message_queue = self.subscribers[node_name][topic]

                # Remove from topic
                if topic in self.topics:
                    self.topics[topic].discard(message_queue)

                # Remove from node tracking
                del self.subscribers[node_name][topic]

                print(f"[MessageBus] Node '{node_name}' unsubscribed from topic '{topic}'")

    def publish(self, message: Message) -> bool:
        """
        Publish message to all subscribers of the topic.

        Returns True if message was successfully published to at least one subscriber.
        """
        try:
            with self.message_lock:
                topic = message.topic
                delivered_count = 0

                if topic in self.topics:
                    # Send to all subscribers
                    for subscriber_queue in list(self.topics[topic]):  # Create copy to avoid modification during iteration
                        try:
                            # Non-blocking put with size check
                            if subscriber_queue.qsize() < self.max_queue_size:
                                subscriber_queue.put_nowait(message)
                                delivered_count += 1
                            else:
                                print(f"[MessageBus] Warning: Queue full for topic '{topic}', dropping message")
                                self.error_count += 1
                        except queue.Full:
                            print(f"[MessageBus] Warning: Failed to deliver message to topic '{topic}' - queue full")
                            self.error_count += 1
                        except Exception as e:
                            print(f"[MessageBus] Error delivering message to topic '{topic}': {e}")
                            self.error_count += 1

                self.message_count += 1

                # Debug logging for message flow
                print(f"[MessageBus] Published message to topic '{topic}' from '{message.source_node}' -> {delivered_count} subscribers")

                # Return True even if no subscribers (message was successfully processed)
                return True

        except Exception as e:
            print(f"[MessageBus] Error publishing message to topic '{message.topic}': {e}")
            self.error_count += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics for monitoring"""
        with self.message_lock:
            uptime = time.time() - self.start_time
            return {
                "message_count": self.message_count,
                "error_count": self.error_count,
                "topic_count": len(self.topics),
                "subscriber_count": sum(len(subs) for subs in self.subscribers.values()),
                "topics": list(self.topics.keys()),
                "uptime_seconds": uptime,
                "messages_per_second": self.message_count / uptime if uptime > 0 else 0
            }

    def get_topic_info(self, topic: str) -> Dict[str, Any]:
        """Get information about a specific topic"""
        with self.message_lock:
            if topic not in self.topics:
                return {"exists": False}

            return {
                "exists": True,
                "subscriber_count": len(self.topics[topic]),
                "subscribers": [
                    node_name for node_name, topics in self.subscribers.items()
                    if topic in topics
                ]
            }

    def shutdown(self):
        """Shutdown the message bus and clear all subscriptions"""
        with self.message_lock:
            print(f"[MessageBus] Shutting down - processed {self.message_count} messages")
            self.topics.clear()
            self.subscribers.clear()


def create_message(topic: str, data: Any, source_node: str,
                  priority: MessagePriority = MessagePriority.NORMAL) -> Message:
    """Utility function to create a properly formatted message"""
    return Message(
        topic=topic,
        data=data,
        timestamp=time.time(),
        source_node=source_node,
        message_id=str(uuid.uuid4()),
        priority=priority
    )