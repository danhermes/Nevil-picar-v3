"""
Nevil v3.0 Framework

A lightweight, declarative robotics framework that preserves proven v1.0 audio components
while providing modern node-based architecture with threading, messaging, and launch capabilities.

Core Philosophy: "Simple architecture = working robot"
"""

__version__ = "3.0.0"
__author__ = "Nevil Framework Team"

from .base_node import NevilNode
from .message_bus import MessageBus, Message
from .config_loader import ConfigLoader
from .launcher import NevilLauncher

__all__ = [
    'NevilNode',
    'MessageBus',
    'Message',
    'ConfigLoader',
    'NevilLauncher'
]