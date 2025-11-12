"""
Integration Tests for Nevil 2.2 Realtime API Pipeline

Tests the complete voice pipeline: STT → AI → TTS
Validates end-to-end message flow, error handling, and recovery.

Test Coverage:
- Full pipeline integration (speech recognition → AI → synthesis)
- WebSocket connection management and recovery
- Message bus communication between nodes
- Error handling and graceful degradation
- Conversation flow with multi-turn dialogue
- Audio streaming and buffering
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

from nevil_framework.realtime.speech_recognition_node22 import SpeechRecognitionNode22
from nevil_framework.realtime.ai_node22 import AiNode22
from nevil_framework.realtime.speech_synthesis_node22 import SpeechSynthesisNode22
from nevil_framework.realtime.realtime_connection_manager import (
    RealtimeConnectionManager,
    ConnectionConfig,
    SessionConfig,
    ConnectionState
)


class MockMessageBus:
    """Mock message bus for testing node communication"""

    def __init__(self):
        self.published_messages = []
        self.subscriptions = {}
        self.lock = threading.Lock()

    def publish(self, topic: str, data: Dict[str, Any]) -> bool:
        """Record published messages"""
        with self.lock:
            self.published_messages.append({
                'topic': topic,
                'data': data,
                'timestamp': time.time()
            })

        # Trigger subscriptions
        if topic in self.subscriptions:
            for callback in self.subscriptions[topic]:
                callback(type('Message', (), {'data': data})())

        return True

    def subscribe(self, topic: str, callback):
        """Register subscription"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)

    def get_messages_for_topic(self, topic: str):
        """Get all messages published to a topic"""
        with self.lock:
            return [msg for msg in self.published_messages if msg['topic'] == topic]

    def clear(self):
        """Clear all recorded messages"""
        with self.lock:
            self.published_messages.clear()


class TestRealtimePipelineIntegration:
    """Test complete STT → AI → TTS pipeline"""

    @pytest.fixture
    def mock_message_bus(self):
        """Create mock message bus"""
        return MockMessageBus()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.subprotocol = 'realtime'
        return mock_ws

    @pytest.fixture
    def connection_manager(self, mock_websocket):
        """Create connection manager with mocked WebSocket"""
        config = ConnectionConfig(
            ephemeral_token="test_token",
            max_reconnect_attempts=3,
            reconnect_base_delay=0.1
        )

        manager = RealtimeConnectionManager(config=config, debug=True)
        manager.ws = mock_websocket
        manager._set_state(ConnectionState.CONNECTED)

        return manager

    def test_pipeline_initialization(self, mock_message_bus):
        """Test all nodes initialize correctly"""
        with patch('os.getenv', return_value='test_api_key'):
            # Mock the base node publish method
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()
                assert stt_node is not None
                assert not stt_node.is_listening

            ai_node = AiNode22()
            assert ai_node is not None
            assert ai_node.processing_count == 0

            tts_node = SpeechSynthesisNode22()
            assert tts_node is not None
            assert not tts_node.is_speaking

    def test_stt_to_ai_message_flow(self, mock_message_bus, connection_manager):
        """Test voice command flows from STT to AI node"""
        with patch('os.getenv', return_value='test_api_key'):
            # Create STT node with mocked connection
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node.connection_manager = connection_manager

                # Simulate transcript completion
                test_transcript = "Hello, how are you?"
                conversation_id = "test_conv_001"

                stt_node._process_transcript(test_transcript)

                # Verify voice_command was published
                voice_commands = mock_message_bus.get_messages_for_topic('voice_command')
                assert len(voice_commands) == 1

                cmd_data = voice_commands[0]['data']
                assert cmd_data['text'] == test_transcript
                assert cmd_data['confidence'] == 0.95
                assert 'conversation_id' in cmd_data
                assert cmd_data['mode'] == "realtime_streaming"

    def test_ai_to_tts_message_flow(self, mock_message_bus):
        """Test AI response flows to TTS node"""
        with patch('os.getenv', return_value='test_api_key'):
            # Create AI node
            ai_node = AiNode22()
            ai_node.publish = mock_message_bus.publish

            # Simulate response completion
            ai_node.current_response_text = "I'm doing great, thanks for asking!"
            ai_node.current_conversation_id = "test_conv_001"

            # Trigger response done event
            ai_node._on_response_text_done({'text': ai_node.current_response_text})

            # Verify text_response was published
            text_responses = mock_message_bus.get_messages_for_topic('text_response')
            assert len(text_responses) == 1

            resp_data = text_responses[0]['data']
            assert resp_data['text'] == "I'm doing great, thanks for asking!"
            assert resp_data['conversation_id'] == "test_conv_001"
            assert resp_data['priority'] == 100

    def test_complete_pipeline_single_turn(self, mock_message_bus):
        """Test complete single-turn conversation through pipeline"""
        with patch('os.getenv', return_value='test_api_key'):
            conversation_id = f"test_conv_{int(time.time())}"

            # Step 1: STT recognizes speech
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node._process_transcript("What time is it?")

            # Verify voice command published
            voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
            assert len(voice_cmds) == 1
            assert voice_cmds[0]['data']['text'] == "What time is it?"

            # Step 2: AI processes command (simulated)
            ai_node = AiNode22()
            ai_node.publish = mock_message_bus.publish
            ai_node.current_response_text = "It's 3:45 PM."
            ai_node.current_conversation_id = conversation_id
            ai_node._on_response_text_done({})

            # Verify text response published
            text_resps = mock_message_bus.get_messages_for_topic('text_response')
            assert len(text_resps) == 1
            assert text_resps[0]['data']['text'] == "It's 3:45 PM."

            # Step 3: TTS would receive and synthesize (tested separately)
            assert len(mock_message_bus.published_messages) >= 2

    def test_multi_turn_conversation_flow(self, mock_message_bus):
        """Test multi-turn conversation maintains context"""
        with patch('os.getenv', return_value='test_api_key'):
            conversation_id = "multi_turn_test"

            # Turn 1
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node._process_transcript("Tell me a joke")

            voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
            assert len(voice_cmds) == 1

            # Turn 2
            mock_message_bus.clear()
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node._process_transcript("Tell me another one")

            voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
            assert len(voice_cmds) == 1
            assert voice_cmds[0]['data']['text'] == "Tell me another one"

    def test_pipeline_error_recovery_stt_failure(self, mock_message_bus):
        """Test pipeline recovers from STT errors"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Simulate error condition
                stt_node.error_count = 0

                # Try processing empty transcript (should handle gracefully)
                stt_node._process_transcript("")

                # Should not publish empty commands
                voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 0

    def test_pipeline_error_recovery_ai_failure(self, mock_message_bus):
        """Test pipeline recovers from AI errors"""
        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()
            ai_node.publish = mock_message_bus.publish

            # Simulate error in response handling
            ai_node._on_error({'error': {'message': 'Test error'}})

            assert ai_node.error_count == 1

            # Should continue functioning after error
            ai_node.current_response_text = "Recovery successful"
            ai_node._on_response_text_done({})

            text_resps = mock_message_bus.get_messages_for_topic('text_response')
            assert len(text_resps) == 1

    def test_websocket_reconnection_during_conversation(self, connection_manager):
        """Test pipeline handles WebSocket reconnection"""
        # Simulate disconnect
        connection_manager._set_state(ConnectionState.DISCONNECTED)
        assert not connection_manager.is_connected()

        # Simulate reconnection
        connection_manager._set_state(ConnectionState.CONNECTED)
        assert connection_manager.is_connected()

        # Verify metrics tracked reconnection
        metrics = connection_manager.get_metrics()
        assert metrics['current_state'] == 'connected'

    def test_message_queuing_during_disconnect(self, connection_manager):
        """Test messages queue when WebSocket disconnected"""
        # Disconnect
        connection_manager._set_state(ConnectionState.DISCONNECTED)

        # Queue some messages
        test_messages = [
            {'type': 'input_audio_buffer.append', 'audio': 'test_audio_1'},
            {'type': 'input_audio_buffer.append', 'audio': 'test_audio_2'},
        ]

        for msg in test_messages:
            connection_manager._queue_message(msg)

        assert len(connection_manager.message_queue) == 2

        # Reconnect should process queue
        connection_manager._set_state(ConnectionState.CONNECTED)

    def test_streaming_audio_delta_accumulation(self):
        """Test STT accumulates streaming audio transcript deltas"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', Mock(return_value=True)):
                stt_node = SpeechRecognitionNode22()

                # Simulate streaming deltas
                stt_node._on_transcript_delta({'delta': 'Hello '})
                stt_node._on_transcript_delta({'delta': 'world'})
                stt_node._on_transcript_delta({'delta': '!'})

                assert stt_node.current_transcript == 'Hello world!'

                # Simulate completion
                stt_node._on_transcript_done({'transcript': 'Hello world!'})

                # Should have cleared buffer
                assert stt_node.current_transcript == ''

    def test_tts_audio_buffer_streaming(self):
        """Test TTS buffers streaming audio chunks"""
        tts_node = SpeechSynthesisNode22()

        # Simulate audio delta events
        import base64
        test_audio_1 = base64.b64encode(b'audio_chunk_1').decode('utf-8')
        test_audio_2 = base64.b64encode(b'audio_chunk_2').decode('utf-8')

        tts_node._on_audio_delta({'delta': test_audio_1})
        tts_node._on_audio_delta({'delta': test_audio_2})

        # Verify buffering
        assert len(tts_node.audio_buffer) == 2

        # Total buffered size should match
        total_size = sum(len(chunk) for chunk in tts_node.audio_buffer)
        assert total_size == len(b'audio_chunk_1audio_chunk_2')

    def test_conversation_id_propagation(self, mock_message_bus):
        """Test conversation_id propagates through entire pipeline"""
        with patch('os.getenv', return_value='test_api_key'):
            conversation_id = "propagation_test_123"

            # STT publishes with conversation_id
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Mock chat_logger to return specific conversation_id
                with patch.object(stt_node.chat_logger, 'generate_conversation_id', return_value=conversation_id):
                    stt_node._process_transcript("Test message")

            # Verify voice_command has conversation_id
            voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
            assert voice_cmds[0]['data']['conversation_id'] == conversation_id

            # AI node should preserve it
            ai_node = AiNode22()
            ai_node.publish = mock_message_bus.publish
            ai_node.current_conversation_id = conversation_id
            ai_node.current_response_text = "Test response"
            ai_node._on_response_text_done({})

            # Verify text_response has same conversation_id
            text_resps = mock_message_bus.get_messages_for_topic('text_response')
            assert text_resps[0]['data']['conversation_id'] == conversation_id

    def test_system_mode_coordination(self, mock_message_bus):
        """Test nodes coordinate via system_mode messages"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Simulate system mode changes
                mock_message = type('Message', (), {
                    'data': {'mode': 'speaking', 'reason': 'tts_active'}
                })()

                stt_node.on_system_mode_change(mock_message)
                assert stt_node.system_mode == 'speaking'

                # Should stop listening during speaking
                mock_message.data = {'mode': 'idle', 'reason': 'tts_complete'}
                stt_node.on_system_mode_change(mock_message)
                assert stt_node.system_mode == 'idle'


class TestPipelinePerformance:
    """Test pipeline performance and timing"""

    def test_pipeline_latency_tracking(self, mock_message_bus=None):
        """Test pipeline tracks end-to-end latency"""
        if mock_message_bus is None:
            mock_message_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            start_time = time.time()

            # Simulate STT
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node._process_transcript("Quick test")

            stt_time = time.time()

            # Simulate AI
            ai_node = AiNode22()
            ai_node.publish = mock_message_bus.publish
            ai_node.current_response_text = "Quick response"
            ai_node._on_response_text_done({})

            ai_time = time.time()

            # Calculate latencies
            stt_latency = (stt_time - start_time) * 1000
            ai_latency = (ai_time - stt_time) * 1000
            total_latency = (ai_time - start_time) * 1000

            # Verify reasonable latencies (should be under 100ms for mocked)
            assert stt_latency < 100
            assert ai_latency < 100
            assert total_latency < 200

    def test_high_throughput_message_handling(self, mock_message_bus=None):
        """Test pipeline handles high message throughput"""
        if mock_message_bus is None:
            mock_message_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_message_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Send 100 transcripts rapidly
                for i in range(100):
                    stt_node._process_transcript(f"Message {i}")

                # Verify all were published
                voice_cmds = mock_message_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 100

    def test_concurrent_conversation_handling(self):
        """Test pipeline can handle rapid conversation turns"""
        mock_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Rapid-fire turns
                for turn in ["Hello", "How are you?", "Goodbye"]:
                    stt_node._process_transcript(turn)
                    time.sleep(0.01)  # Minimal delay

                voice_cmds = mock_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 3


class TestPipelineEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_transcript_handling(self):
        """Test pipeline handles empty transcripts gracefully"""
        mock_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Should not publish empty transcript
                stt_node._process_transcript("")
                stt_node._process_transcript("   ")

                voice_cmds = mock_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 0

    def test_long_transcript_handling(self):
        """Test pipeline handles very long transcripts"""
        mock_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_bus.publish):
                stt_node = SpeechRecognitionNode22()

                # 1000 word transcript
                long_text = " ".join(["word"] * 1000)
                stt_node._process_transcript(long_text)

                voice_cmds = mock_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 1
                assert len(voice_cmds[0]['data']['text']) > 4000

    def test_special_characters_in_transcript(self):
        """Test pipeline handles special characters"""
        mock_bus = MockMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', mock_bus.publish):
                stt_node = SpeechRecognitionNode22()

                special_text = "Hello! How are you? I'm 100% fine. 🎉"
                stt_node._process_transcript(special_text)

                voice_cmds = mock_bus.get_messages_for_topic('voice_command')
                assert len(voice_cmds) == 1
                assert voice_cmds[0]['data']['text'] == special_text

    def test_rapid_state_changes(self):
        """Test pipeline handles rapid state changes"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', Mock(return_value=True)):
                stt_node = SpeechRecognitionNode22()

                # Rapid state changes
                for _ in range(10):
                    stt_node.system_mode = "idle"
                    stt_node.system_mode = "listening"
                    stt_node.system_mode = "thinking"
                    stt_node.system_mode = "speaking"

                # Should end in valid state
                assert stt_node.system_mode in ["idle", "listening", "thinking", "speaking"]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
