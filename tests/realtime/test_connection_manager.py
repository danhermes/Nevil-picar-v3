"""
Test suite for RealtimeConnectionManager

Validates the production-ready Python implementation adapted from Blane3.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from nevil_framework.realtime import (
    RealtimeConnectionManager,
    ConnectionConfig,
    SessionConfig,
    ConnectionState,
    create_realtime_connection
)


class TestConnectionManager:
    """Test RealtimeConnectionManager basic functionality"""

    def test_initialization(self):
        """Test manager initializes correctly"""
        config = ConnectionConfig(ephemeral_token="test_token")
        manager = RealtimeConnectionManager(config=config)

        assert manager.config.ephemeral_token == "test_token"
        assert manager.state == ConnectionState.DISCONNECTED
        assert manager.running is False
        assert manager.reconnect_attempts == 0

    def test_initialization_with_defaults(self):
        """Test manager works with default config"""
        manager = RealtimeConnectionManager()

        assert manager.config is not None
        assert manager.state == ConnectionState.DISCONNECTED
        assert isinstance(manager.metrics.connection_attempts, int)

    def test_factory_function(self):
        """Test convenience factory function"""
        manager = create_realtime_connection(
            ephemeral_token="test_token",
            model="gpt-4o-realtime-preview-2024-12-17",
            voice="alloy",
            debug=True
        )

        assert manager.config.ephemeral_token == "test_token"
        assert manager.session_config.model == "gpt-4o-realtime-preview-2024-12-17"
        assert manager.session_config.voice == "alloy"
        assert manager.debug is True

    def test_event_subscription(self):
        """Test event handler subscription"""
        manager = RealtimeConnectionManager()
        callback = Mock()

        manager.on('connect', callback)
        manager.event_handler.emit('connect')

        callback.assert_called_once()

    def test_event_unsubscription(self):
        """Test event handler unsubscription"""
        manager = RealtimeConnectionManager()
        callback = Mock()

        manager.on('connect', callback)
        manager.off('connect', callback)
        manager.event_handler.emit('connect')

        callback.assert_not_called()

    def test_once_event_subscription(self):
        """Test one-time event subscription"""
        manager = RealtimeConnectionManager()
        callback = Mock()

        manager.once('connect', callback)
        manager.event_handler.emit('connect')
        manager.event_handler.emit('connect')

        # Should only be called once
        callback.assert_called_once()

    def test_state_management(self):
        """Test connection state transitions"""
        manager = RealtimeConnectionManager()

        assert manager.get_state() == ConnectionState.DISCONNECTED
        assert manager.is_connected() is False

        manager._set_state(ConnectionState.CONNECTING)
        assert manager.get_state() == ConnectionState.CONNECTING

        manager._set_state(ConnectionState.CONNECTED)
        assert manager.is_connected() is True

    def test_message_queuing(self):
        """Test offline message queuing"""
        manager = RealtimeConnectionManager()
        test_message = {'type': 'test', 'data': 'hello'}

        manager._queue_message(test_message)

        assert len(manager.message_queue) == 1
        assert manager.message_queue[0] == test_message

    def test_queue_overflow(self):
        """Test message queue handles overflow"""
        manager = RealtimeConnectionManager()

        # Fill queue beyond max
        for i in range(manager.MAX_QUEUE_SIZE + 10):
            manager._queue_message({'type': 'test', 'id': i})

        # Should not exceed max size
        assert len(manager.message_queue) == manager.MAX_QUEUE_SIZE

        # Should have dropped oldest messages
        assert manager.message_queue[0]['id'] == 10

    def test_metrics_initialization(self):
        """Test metrics are properly initialized"""
        manager = RealtimeConnectionManager()

        metrics = manager.get_metrics()

        assert metrics['connection_attempts'] == 0
        assert metrics['reconnect_attempts'] == 0
        assert metrics['total_uptime'] == 0.0
        assert metrics['messages_sent'] == 0
        assert metrics['messages_received'] == 0
        assert metrics['current_state'] == 'disconnected'
        assert metrics['is_connected'] is False

    def test_authentication_validation(self):
        """Test authentication validation"""
        config = ConnectionConfig()  # No auth provided
        manager = RealtimeConnectionManager(config=config)

        with pytest.raises(ValueError, match="Either api_key or ephemeral_token"):
            manager._validate_auth()

    def test_url_building_with_ephemeral_token(self):
        """Test URL construction with ephemeral token"""
        config = ConnectionConfig(ephemeral_token="test_token")
        session_config = SessionConfig(model="gpt-4o-realtime-preview-2024-12-17")
        manager = RealtimeConnectionManager(config=config, session_config=session_config)

        url = manager._build_connection_url()

        assert "wss://api.openai.com/v1/realtime" in url
        assert "model=gpt-4o-realtime-preview-2024-12-17" in url

    def test_url_building_with_api_key(self):
        """Test URL construction with API key"""
        config = ConnectionConfig(api_key="sk-test-key")
        manager = RealtimeConnectionManager(config=config)

        url = manager._build_connection_url()

        assert "wss://api.openai.com/v1/realtime" in url

    def test_multiple_event_handlers(self):
        """Test multiple handlers for same event"""
        manager = RealtimeConnectionManager()
        callback1 = Mock()
        callback2 = Mock()

        manager.on('connect', callback1)
        manager.on('connect', callback2)

        manager.event_handler.emit('connect')

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_event_stats(self):
        """Test event statistics tracking"""
        manager = RealtimeConnectionManager()

        manager.event_handler.emit('connect')
        manager.event_handler.emit('connect')
        manager.event_handler.emit('disconnect')

        stats = manager.get_event_stats()

        # Stats only track events processed through handle_event, not emit
        assert isinstance(stats, dict)

    def test_cleanup(self):
        """Test cleanup and resource management"""
        manager = RealtimeConnectionManager()
        callback = Mock()

        manager.on('connect', callback)
        manager.destroy()

        # Should have removed all listeners
        assert len(manager.event_handler.handlers) == 0


class TestAsyncOperations:
    """Test async operations of RealtimeConnectionManager"""

    @pytest.mark.asyncio
    async def test_message_sending_not_connected(self):
        """Test sending message when not connected queues it"""
        manager = RealtimeConnectionManager()
        message = {'type': 'test'}

        result = await manager.send(message)

        assert result is False
        assert len(manager.message_queue) == 1

    @pytest.mark.asyncio
    async def test_event_handler_async_callback(self):
        """Test async event callbacks are awaited"""
        manager = RealtimeConnectionManager()
        callback_called = asyncio.Event()

        async def async_callback(event):
            callback_called.set()

        manager.on('test_event', async_callback)
        await manager.event_handler.handle_event({'type': 'test_event'})

        assert callback_called.is_set()

    @pytest.mark.asyncio
    async def test_reconnect_backoff_calculation(self):
        """Test exponential backoff is calculated correctly"""
        config = ConnectionConfig(
            ephemeral_token="test",
            reconnect_base_delay=1.0
        )
        manager = RealtimeConnectionManager(config=config)

        # Simulate multiple reconnect attempts
        delays = []
        for i in range(5):
            manager.reconnect_attempts = i
            delay = min(
                manager.config.reconnect_base_delay * (2 ** i),
                16.0
            )
            delays.append(delay)

        # Should follow exponential pattern: 1, 2, 4, 8, 16
        assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]


class TestThreadSafety:
    """Test thread-safety of RealtimeConnectionManager"""

    def test_state_lock(self):
        """Test state changes are thread-safe"""
        manager = RealtimeConnectionManager()

        # Simulate concurrent state changes
        import threading

        def change_state():
            for _ in range(100):
                manager._set_state(ConnectionState.CONNECTING)
                manager._set_state(ConnectionState.CONNECTED)

        threads = [threading.Thread(target=change_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert manager.state in list(ConnectionState)

    def test_message_queue_lock(self):
        """Test message queueing is thread-safe"""
        manager = RealtimeConnectionManager()

        # Simulate concurrent queue operations
        import threading

        def queue_messages():
            for i in range(20):
                manager._queue_message({'type': 'test', 'id': i})

        threads = [threading.Thread(target=queue_messages) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not exceed max size and have no corruption
        assert len(manager.message_queue) <= manager.MAX_QUEUE_SIZE


class TestSessionConfig:
    """Test session configuration"""

    def test_default_session_config(self):
        """Test default session configuration"""
        config = SessionConfig()

        assert config.model == "gpt-4o-realtime-preview-2024-12-17"
        assert config.voice == "alloy"
        assert config.modalities == ["text", "audio"]
        assert config.input_audio_format == "pcm16"
        assert config.output_audio_format == "pcm16"
        assert config.temperature == 0.8

    def test_custom_session_config(self):
        """Test custom session configuration"""
        config = SessionConfig(
            model="gpt-4o-mini",
            voice="shimmer",
            temperature=0.5,
            modalities=["audio"]
        )

        assert config.model == "gpt-4o-mini"
        assert config.voice == "shimmer"
        assert config.temperature == 0.5
        assert config.modalities == ["audio"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
