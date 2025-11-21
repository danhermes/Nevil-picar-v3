"""
RealtimeConnectionManager - Production-ready WebSocket client for OpenAI Realtime API

Adapted from Blane3 RealtimeClient.ts with full Python async/await patterns.
Provides robust connection management, auto-reconnection, and thread-safe operations.

Key Features:
- Async WebSocket connection to wss://api.openai.com/v1/realtime
- Exponential backoff reconnection strategy
- Thread-safe message queuing for offline messages
- Comprehensive event handling with custom callbacks
- Connection metrics and monitoring
- Integration with Nevil's threading model

Translation date: 2025-11-11
Status: Production-ready
"""

import asyncio
import websockets
import json
import base64
import logging
import time
from typing import Dict, Callable, Any, Optional, List, Union
from threading import Thread, RLock
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Type Definitions (Translated from RealtimeTypes.ts)
# ============================================================================

class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    connection_attempts: int = 0
    reconnect_attempts: int = 0
    total_uptime: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    last_connected_at: Optional[datetime] = None
    last_disconnected_at: Optional[datetime] = None


@dataclass
class ConnectionConfig:
    """WebSocket connection configuration"""
    api_key: Optional[str] = None
    ephemeral_token: Optional[str] = None
    url: str = 'wss://api.openai.com/v1/realtime'
    max_reconnect_attempts: int = 5
    reconnect_base_delay: float = 1.0  # seconds
    connection_timeout: float = 30.0  # seconds


@dataclass
class SessionConfig:
    """OpenAI Realtime API session configuration"""
    model: str = "gpt-4o-realtime-preview-2024-12-17"
    modalities: List[str] = field(default_factory=lambda: ["text", "audio"])
    instructions: Optional[str] = None
    voice: str = "cedar"
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"
    input_audio_transcription: Optional[Dict[str, Any]] = None
    turn_detection: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: str = "auto"
    temperature: float = 0.8
    max_response_output_tokens: Union[int, str] = "inf"


@dataclass
class ReconnectOptions:
    """Reconnection attempt details"""
    attempt: int
    max_attempts: int
    delay: float
    reason: str


# ============================================================================
# Event Handler System
# ============================================================================

class RealtimeEventHandler:
    """
    Event handling system for OpenAI Realtime API events.
    Manages event listeners and dispatches events to registered callbacks.
    """

    def __init__(self, handlers: Dict[str, Callable] = None, debug: bool = False):
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_stats: Dict[str, int] = {}
        self.debug = debug
        self._lock = RLock()

        # Register initial handlers
        if handlers:
            for event_type, callback in handlers.items():
                self.on(event_type, callback)

    def on(self, event: str, listener: Callable) -> None:
        """Subscribe to an event"""
        with self._lock:
            if event not in self.handlers:
                self.handlers[event] = []
            self.handlers[event].append(listener)

    def off(self, event: str, listener: Callable) -> None:
        """Unsubscribe from an event"""
        with self._lock:
            if event in self.handlers and listener in self.handlers[event]:
                self.handlers[event].remove(listener)

    def once(self, event: str, listener: Callable) -> None:
        """Subscribe to an event once"""
        def once_wrapper(*args, **kwargs):
            self.off(event, once_wrapper)
            listener(*args, **kwargs)

        self.on(event, once_wrapper)

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Process an event and call registered handlers"""
        event_type = event.get('type')
        if not event_type:
            logger.warning(f"Event missing type field: {event}")
            return

        # Update statistics
        with self._lock:
            self.event_stats[event_type] = self.event_stats.get(event_type, 0) + 1

        # Call all registered handlers
        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in handler for {event_type}: {e}", exc_info=True)

    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event synchronously"""
        handlers = self.handlers.get(event, [])
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in emit handler for {event}: {e}", exc_info=True)

    def get_event_stats(self) -> Dict[str, int]:
        """Get event statistics"""
        with self._lock:
            return self.event_stats.copy()

    def update_handlers(self, handlers: Dict[str, Callable]) -> None:
        """Update handlers at runtime"""
        for event_type, callback in handlers.items():
            self.on(event_type, callback)

    def remove_all_listeners(self) -> None:
        """Remove all event listeners"""
        with self._lock:
            self.handlers.clear()


# ============================================================================
# Main RealtimeConnectionManager Class
# ============================================================================

class RealtimeConnectionManager:
    """
    Production-ready WebSocket client for OpenAI Realtime API.

    This class manages the complete lifecycle of a WebSocket connection including:
    - Authentication with API keys or ephemeral tokens
    - Automatic reconnection with exponential backoff
    - Thread-safe message queuing
    - Event-driven architecture
    - Connection monitoring and metrics

    Usage:
        config = ConnectionConfig(ephemeral_token="your_token")
        manager = RealtimeConnectionManager(config)
        manager.on('connect', lambda: print("Connected!"))
        manager.on('server.response.audio.delta', handle_audio)
        manager.start()  # Starts connection in background thread
    """

    # Constants
    DEFAULT_REALTIME_URL = 'wss://api.openai.com/v1/realtime'
    DEFAULT_MAX_RECONNECT_ATTEMPTS = 5
    DEFAULT_RECONNECT_BASE_DELAY = 1.0
    DEFAULT_CONNECTION_TIMEOUT = 30.0
    MAX_QUEUE_SIZE = 100

    def __init__(
        self,
        config: ConnectionConfig = None,
        session_config: SessionConfig = None,
        handlers: Dict[str, Callable] = None,
        debug: bool = False
    ):
        """
        Initialize the Realtime Connection Manager.

        Args:
            config: Connection configuration (API key, URL, timeouts, etc.)
            session_config: OpenAI session configuration (model, voice, etc.)
            handlers: Initial event handlers
            debug: Enable debug logging
        """
        # Configuration
        self.config = config or ConnectionConfig()
        self.session_config = session_config
        self.debug = debug

        # Connection state
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        self._state_lock = RLock()

        # Event handling
        self.event_handler = RealtimeEventHandler(handlers or {}, debug)

        # Reconnection management
        self.reconnect_attempts = 0
        self.reconnect_task: Optional[asyncio.Task] = None
        self.connection_start_time: Optional[float] = None

        # Metrics
        self.metrics = ConnectionMetrics()

        # Message queue for offline messages
        self.message_queue: List[Dict[str, Any]] = []
        self.message_lock = RLock()

        # Asyncio event loop management
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[Thread] = None
        self.running = False

        # Response state tracking (shared with audio_capture_manager to prevent queue buildup)
        self.response_in_progress = False
        self.shutdown_event: Optional[asyncio.Event] = None  # Created in event loop thread

        logger.info(f"RealtimeConnectionManager initialized (debug={debug})")

    # ========================================================================
    # Thread Management (Nevil Integration)
    # ========================================================================

    def start(self) -> None:
        """
        Start the connection manager in a background thread.
        Thread-safe method compatible with Nevil's threading model.
        """
        if self.running:
            logger.warning("Connection manager already running")
            return

        self.running = True
        self.loop_thread = Thread(target=self._run_event_loop, daemon=True, name="RealtimeConnection")
        self.loop_thread.start()
        logger.info("Connection manager started in background thread")

    def stop(self, reason: str = "Client stopped") -> None:
        """
        Stop the connection manager and cleanup resources.
        Thread-safe method compatible with Nevil's threading model.
        """
        if not self.running:
            return

        logger.info(f"Stopping connection manager: {reason}")
        self.running = False

        # Schedule disconnect in the event loop
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_disconnect(reason), self.loop)

        # Wait for thread to complete
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=5.0)

        logger.info("Connection manager stopped")

    def _run_event_loop(self) -> None:
        """Run asyncio event loop in dedicated thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Create shutdown event for this loop
            self.shutdown_event = asyncio.Event()

            # Run the main connection loop
            self.loop.run_until_complete(self._connection_loop())
        except Exception as e:
            logger.error(f"Event loop error: {e}", exc_info=True)
        finally:
            # Cleanup
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.loop.close()
            logger.info("Event loop closed")

    async def _connection_loop(self) -> None:
        """Main connection loop with auto-reconnection"""
        logger.info("Starting connection loop")

        # Initial connection
        await self.connect()

        # Keep loop running until stopped
        try:
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            pass
        finally:
            await self._async_disconnect("Connection loop shutting down")

    # ========================================================================
    # Connection Management
    # ========================================================================

    async def connect(self) -> None:
        """
        Connect to OpenAI Realtime API.
        Handles authentication, WebSocket setup, and event handlers.
        """
        logger.debug(f"connect() called, current state: {self.state}")

        if self.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING]:
            logger.info("Already connected or connecting")
            return

        self._set_state(ConnectionState.CONNECTING)
        self.metrics.connection_attempts += 1
        self.connection_start_time = time.time()

        try:
            # Validate authentication
            self._validate_auth()
            logger.debug("Authentication validated")

            # Build WebSocket URL
            url = self._build_connection_url()
            logger.debug(f"Connecting to: {url}")

            # Create WebSocket connection
            if self.config.ephemeral_token:
                # Use ephemeral token via Sec-WebSocket-Protocol header
                logger.debug(f"Using ephemeral token (first 20 chars): {self.config.ephemeral_token[:20]}")

                self.ws = await asyncio.wait_for(
                    websockets.connect(
                        url,
                        subprotocols=[
                            'realtime',
                            f'openai-insecure-api-key.{self.config.ephemeral_token}',
                            'openai-beta.realtime-v1'
                        ],
                        ping_interval=20,
                        ping_timeout=10
                    ),
                    timeout=self.config.connection_timeout
                )
            else:
                # Use API key in URL (note: ephemeral tokens are recommended)
                self.ws = await asyncio.wait_for(
                    websockets.connect(
                        url,
                        extra_headers={
                            'Authorization': f'Bearer {self.config.api_key}',
                            'OpenAI-Beta': 'realtime=v1'
                        },
                        ping_interval=20,
                        ping_timeout=10
                    ),
                    timeout=self.config.connection_timeout
                )

            logger.info(f"WebSocket connected (protocol: {self.ws.subprotocol})")

            # Handle successful connection
            await self._handle_open()

            # Start receiving messages
            await self._receive_loop()

        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            await self._handle_connection_error(Exception("Connection timeout"))
        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
            await self._handle_connection_error(e)

    async def _async_disconnect(self, reason: str = "Disconnected") -> None:
        """Disconnect from server (async version)"""
        logger.info(f"Disconnecting: {reason}")

        # Cancel reconnection if scheduled
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()
            self.reconnect_task = None

        # Close WebSocket
        if self.ws:
            try:
                await self.ws.close(code=1000, reason=reason)
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.ws = None

        # Update metrics
        self._update_uptime()

        # Update state
        self._set_state(ConnectionState.DISCONNECTED)

        # Emit disconnect event
        self.event_handler.emit('disconnect', reason)

    async def reconnect(self, reason: str = "Reconnecting") -> None:
        """
        Reconnect with exponential backoff.
        Implements the proven Blane3 reconnection strategy.
        """
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.config.max_reconnect_attempts}) reached")
            self._set_state(ConnectionState.FAILED)
            self.event_handler.emit('error', Exception('Max reconnection attempts reached'))
            return

        self.reconnect_attempts += 1
        self.metrics.reconnect_attempts += 1
        self._set_state(ConnectionState.RECONNECTING)

        # Calculate exponential backoff: 1s, 2s, 4s, 8s, 16s
        delay = min(
            self.config.reconnect_base_delay * (2 ** (self.reconnect_attempts - 1)),
            16.0
        )

        options = ReconnectOptions(
            attempt=self.reconnect_attempts,
            max_attempts=self.config.max_reconnect_attempts,
            delay=delay,
            reason=reason
        )

        logger.info(
            f"Reconnecting in {delay}s "
            f"(attempt {self.reconnect_attempts}/{self.config.max_reconnect_attempts})"
        )
        self.event_handler.emit('reconnecting', options)

        # Schedule reconnection
        await asyncio.sleep(delay)

        try:
            await self.connect()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            await self.reconnect(str(e))

    # ========================================================================
    # WebSocket Event Handlers
    # ========================================================================

    async def _handle_open(self) -> None:
        """Handle WebSocket connection opened"""
        logger.info("WebSocket connection opened")

        # Reset reconnection attempts
        self.reconnect_attempts = 0

        # Update state
        self._set_state(ConnectionState.CONNECTED)

        # Update metrics
        self.metrics.last_connected_at = datetime.now()

        # Send session configuration if provided
        if self.session_config:
            await self.update_session(self.session_config)

        # Process queued messages
        await self._process_message_queue()

        # Emit connect event
        self.event_handler.emit('connect')
        logger.info("Connection established successfully")

    async def _receive_loop(self) -> None:
        """Continuously receive and process messages"""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket closed: code={e.code}, reason={e.reason}")
            await self._handle_close(e.code, e.reason or "Connection closed")
        except Exception as e:
            logger.error(f"Receive loop error: {e}", exc_info=True)
            await self._handle_error(e)

    async def _handle_message(self, data: Union[str, bytes]) -> None:
        """Process incoming WebSocket message"""
        try:
            # Handle both string and binary data
            if isinstance(data, bytes):
                message_str = data.decode('utf-8')
            else:
                message_str = data

            self.metrics.messages_received += 1

            # Parse server event
            event = json.loads(message_str)

            if self.debug:
                logger.debug(f"Received event: {event.get('type', 'unknown')}")

            # Process event through handler
            await self.event_handler.handle_event(event)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.event_handler.emit('error', e)

    async def _handle_error(self, error: Exception) -> None:
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")
        self.event_handler.emit('error', error)

    async def _handle_close(self, code: int, reason: str) -> None:
        """Handle WebSocket connection closed"""
        logger.info(f"WebSocket closed: code={code}, reason={reason}")

        # Update metrics
        self._update_uptime()

        # Check if we were connected
        was_connected = self.state == ConnectionState.CONNECTED
        self._set_state(ConnectionState.DISCONNECTED)

        # Emit disconnect event
        self.event_handler.emit('disconnect', reason or f"Connection closed with code {code}")

        # Attempt reconnection if it was unexpected
        if was_connected and code != 1000 and self.running:
            await self.reconnect(f"Connection closed unexpectedly: {code}")

    async def _handle_connection_error(self, error: Exception) -> None:
        """Handle connection establishment error"""
        logger.error(f"Connection error: {error}")
        self._set_state(ConnectionState.FAILED)
        self.event_handler.emit('error', error)

        if self.running:
            await self.reconnect(str(error))

    # ========================================================================
    # Message Sending
    # ========================================================================

    async def send(self, message: Dict[str, Any]) -> bool:
        """
        Send message to server.
        Queues message if not connected.

        Args:
            message: Message dictionary to send

        Returns:
            True if sent successfully, False otherwise
        """
        if self.state != ConnectionState.CONNECTED:
            logger.debug(f"Not connected, queueing message: {message.get('type')}")
            self._queue_message(message)
            return False

        try:
            json_str = json.dumps(message)
            await self.ws.send(json_str)
            self.metrics.messages_sent += 1

            if self.debug:
                logger.debug(f"Sent message: {message.get('type')}")

            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.event_handler.emit('error', e)
            self._queue_message(message)
            return False

    def send_sync(self, message: Dict[str, Any]) -> bool:
        """
        Thread-safe synchronous message sending.
        Schedules send in the asyncio event loop.

        Args:
            message: Message dictionary to send

        Returns:
            True if scheduled successfully, False otherwise
        """
        if not self.loop or not self.loop.is_running():
            logger.warning("Event loop not running, queueing message")
            self._queue_message(message)
            return False

        try:
            future = asyncio.run_coroutine_threadsafe(self.send(message), self.loop)
            return future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Error in sync send: {e}")
            return False

    async def update_session(self, config: SessionConfig) -> None:
        """Update session configuration"""
        self.session_config = config
        await self.send({
            'type': 'session.update',
            'session': {
                'modalities': config.modalities,
                'instructions': config.instructions,
                'voice': config.voice,
                'input_audio_format': config.input_audio_format,
                'output_audio_format': config.output_audio_format,
                'input_audio_transcription': config.input_audio_transcription,
                'turn_detection': config.turn_detection,
                'tools': config.tools,
                'tool_choice': config.tool_choice,
                'temperature': config.temperature,
                'max_response_output_tokens': config.max_response_output_tokens
            }
        })

    async def append_input_audio(self, audio_base64: str) -> None:
        """Append audio to input buffer"""
        await self.send({
            'type': 'input_audio_buffer.append',
            'audio': audio_base64
        })

    async def commit_input_audio(self) -> None:
        """Commit audio buffer"""
        await self.send({
            'type': 'input_audio_buffer.commit'
        })

    async def clear_input_audio(self) -> None:
        """Clear audio buffer"""
        await self.send({
            'type': 'input_audio_buffer.clear'
        })

    async def create_response(self, config: Dict[str, Any] = None) -> None:
        """Create response"""
        message = {'type': 'response.create'}
        if config:
            message['response'] = config
        await self.send(message)

    async def cancel_response(self) -> None:
        """Cancel response"""
        await self.send({
            'type': 'response.cancel'
        })

    # ========================================================================
    # State Management
    # ========================================================================

    def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and emit event"""
        with self._state_lock:
            old_state = self.state
            self.state = new_state

            if old_state != new_state:
                logger.debug(f"State changed: {old_state.value} -> {new_state.value}")
                self.event_handler.emit('state_change', {'from': old_state, 'to': new_state})

    def get_state(self) -> ConnectionState:
        """Get current connection state"""
        with self._state_lock:
            return self.state

    def is_connected(self) -> bool:
        """Check if currently connected"""
        return self.state == ConnectionState.CONNECTED

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _validate_auth(self) -> None:
        """Validate authentication configuration"""
        if not self.config.api_key and not self.config.ephemeral_token:
            raise ValueError('Either api_key or ephemeral_token must be provided')

    def _build_connection_url(self) -> str:
        """Build WebSocket connection URL"""
        base_url = self.config.url or self.DEFAULT_REALTIME_URL

        # For ephemeral tokens, include model in query string
        if self.config.ephemeral_token:
            model = self.session_config.model if self.session_config else "gpt-4o-realtime-preview-2024-12-17"
            return f"{base_url}?model={model}"

        # For API keys (not recommended in browser)
        elif self.config.api_key:
            model = self.session_config.model if self.session_config else "gpt-4o-realtime-preview-2024-12-17"
            return f"{base_url}?model={model}"

        return base_url

    def _queue_message(self, message: Dict[str, Any]) -> None:
        """Queue message for later sending"""
        with self.message_lock:
            if len(self.message_queue) >= self.MAX_QUEUE_SIZE:
                logger.warning("Message queue full, dropping oldest message")
                self.message_queue.pop(0)
            self.message_queue.append(message)

    async def _process_message_queue(self) -> None:
        """Process queued messages"""
        with self.message_lock:
            queue_size = len(self.message_queue)
            if queue_size == 0:
                return

            logger.info(f"Processing {queue_size} queued messages")

            while self.message_queue:
                message = self.message_queue.pop(0)
                await self.send(message)

    def _update_uptime(self) -> None:
        """Update connection uptime metrics"""
        if self.connection_start_time:
            uptime = time.time() - self.connection_start_time
            self.metrics.total_uptime += uptime
            self.metrics.last_disconnected_at = datetime.now()
            self.connection_start_time = None

    # ========================================================================
    # Public API
    # ========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Get connection metrics"""
        return {
            'connection_attempts': self.metrics.connection_attempts,
            'reconnect_attempts': self.metrics.reconnect_attempts,
            'total_uptime': self.metrics.total_uptime,
            'messages_sent': self.metrics.messages_sent,
            'messages_received': self.metrics.messages_received,
            'last_connected_at': self.metrics.last_connected_at.isoformat() if self.metrics.last_connected_at else None,
            'last_disconnected_at': self.metrics.last_disconnected_at.isoformat() if self.metrics.last_disconnected_at else None,
            'current_state': self.state.value,
            'is_connected': self.is_connected()
        }

    def get_event_stats(self) -> Dict[str, int]:
        """Get event statistics"""
        return self.event_handler.get_event_stats()

    def update_handlers(self, handlers: Dict[str, Callable]) -> None:
        """Update event handlers at runtime"""
        self.event_handler.update_handlers(handlers)

    def on(self, event: str, listener: Callable) -> 'RealtimeConnectionManager':
        """Subscribe to events"""
        self.event_handler.on(event, listener)
        return self

    def off(self, event: str, listener: Callable) -> 'RealtimeConnectionManager':
        """Unsubscribe from events"""
        self.event_handler.off(event, listener)
        return self

    def once(self, event: str, listener: Callable) -> 'RealtimeConnectionManager':
        """Subscribe to event once"""
        self.event_handler.once(event, listener)
        return self

    def destroy(self) -> None:
        """Clean up resources"""
        self.stop("Client destroyed")
        self.event_handler.remove_all_listeners()
        logger.info("RealtimeConnectionManager destroyed")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_realtime_connection(
    api_key: str = None,
    ephemeral_token: str = None,
    model: str = "gpt-4o-realtime-preview-2024-12-17",
    voice: str = "cedar",
    debug: bool = False
) -> RealtimeConnectionManager:
    """
    Factory function to create a configured RealtimeConnectionManager.

    Args:
        api_key: OpenAI API key (or use ephemeral_token)
        ephemeral_token: Ephemeral token (recommended for browser use)
        model: Model to use
        voice: Voice to use for audio output
        debug: Enable debug logging

    Returns:
        Configured RealtimeConnectionManager instance
    """
    config = ConnectionConfig(
        api_key=api_key,
        ephemeral_token=ephemeral_token
    )

    session_config = SessionConfig(
        model=model,
        voice=voice
    )

    return RealtimeConnectionManager(
        config=config,
        session_config=session_config,
        debug=debug
    )
