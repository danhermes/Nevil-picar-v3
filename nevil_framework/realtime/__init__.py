"""
Nevil Realtime Module

OpenAI Realtime API integration with production-ready connection management,
audio capture, and buffering capabilities.
"""

from .realtime_connection_manager import (
    RealtimeConnectionManager,
    ConnectionState,
    ConnectionConfig,
    ConnectionMetrics,
    SessionConfig,
    ReconnectOptions,
    RealtimeEventHandler,
    create_realtime_connection
)

from .audio_capture_manager import (
    AudioCaptureManager,
    AudioCaptureConfig,
    AudioCaptureCallbacks,
    CaptureState,
    create_audio_capture
)

__all__ = [
    # Connection Manager
    'RealtimeConnectionManager',
    'ConnectionState',
    'ConnectionConfig',
    'ConnectionMetrics',
    'SessionConfig',
    'ReconnectOptions',
    'RealtimeEventHandler',
    'create_realtime_connection',
    # Audio Capture Manager
    'AudioCaptureManager',
    'AudioCaptureConfig',
    'AudioCaptureCallbacks',
    'CaptureState',
    'create_audio_capture'
]
