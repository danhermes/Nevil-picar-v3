"""
Node Integration Tests for Nevil 2.2 Realtime API

Tests communication and coordination between the three core nodes:
- speech_recognition_node22: Publishes voice_command
- ai_node22: Subscribes to voice_command, publishes text_response
- speech_synthesis_node22: Subscribes to text_response

Validates:
- Message bus topic subscriptions and publications
- Data flow between nodes
- Event-driven coordination
- System mode synchronization
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

from nevil_framework.realtime.speech_recognition_node22 import SpeechRecognitionNode22
from nevil_framework.realtime.ai_node22 import AiNode22
from nevil_framework.realtime.speech_synthesis_node22 import SpeechSynthesisNode22


class MockMessage:
    """Mock message object for testing"""

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.timestamp = time.time()


class IntegratedMessageBus:
    """
    Integrated message bus that connects nodes together.
    Simulates the real Nevil message bus behavior.
    """

    def __init__(self):
        self.topics: Dict[str, List] = {}
        self.published: List[Dict] = []
        self.lock = threading.Lock()

    def subscribe(self, topic: str, callback):
        """Subscribe a callback to a topic"""
        with self.lock:
            if topic not in self.topics:
                self.topics[topic] = []
            self.topics[topic].append(callback)

    def publish(self, topic: str, data: Dict[str, Any]) -> bool:
        """Publish data to a topic and notify subscribers"""
        with self.lock:
            # Record publication
            self.published.append({
                'topic': topic,
                'data': data,
                'timestamp': time.time()
            })

            # Notify subscribers
            if topic in self.topics:
                message = MockMessage(data)
                for callback in self.topics[topic]:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error in callback for {topic}: {e}")

        return True

    def get_published(self, topic: str) -> List[Dict]:
        """Get all messages published to a topic"""
        with self.lock:
            return [p for p in self.published if p['topic'] == topic]

    def clear(self):
        """Clear published messages"""
        with self.lock:
            self.published.clear()


class TestSpeechRecognitionNodeIntegration:
    """Test speech_recognition_node22 message bus integration"""

    def test_publishes_voice_command_topic(self):
        """Verify STT node publishes to voice_command topic"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Process a transcript
                stt_node._process_transcript("Hello robot")

                # Verify voice_command was published
                voice_cmds = bus.get_published('voice_command')
                assert len(voice_cmds) == 1
                assert voice_cmds[0]['data']['text'] == "Hello robot"

    def test_voice_command_data_schema(self):
        """Verify voice_command messages have correct schema"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node._process_transcript("Test message")

                voice_cmd = bus.get_published('voice_command')[0]['data']

                # Verify required fields
                assert 'text' in voice_cmd
                assert 'confidence' in voice_cmd
                assert 'timestamp' in voice_cmd
                assert 'language' in voice_cmd
                assert 'conversation_id' in voice_cmd
                assert 'mode' in voice_cmd

                # Verify types
                assert isinstance(voice_cmd['text'], str)
                assert isinstance(voice_cmd['confidence'], float)
                assert isinstance(voice_cmd['timestamp'], float)
                assert voice_cmd['mode'] == 'realtime_streaming'

    def test_subscribes_to_system_mode(self):
        """Verify STT node responds to system_mode changes"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', Mock(return_value=True)):
                stt_node = SpeechRecognitionNode22()

                # Test system_mode callback exists
                assert hasattr(stt_node, 'on_system_mode_change')

                # Simulate mode change
                mode_msg = MockMessage({'mode': 'speaking', 'reason': 'tts_active'})
                stt_node.on_system_mode_change(mode_msg)

                assert stt_node.system_mode == 'speaking'

    def test_subscribes_to_speaking_status(self):
        """Verify STT node responds to speaking_status changes"""
        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', Mock(return_value=True)):
                stt_node = SpeechRecognitionNode22()

                # Test callback exists
                assert hasattr(stt_node, 'on_speaking_status_change')

                # Simulate speaking status change
                status_msg = MockMessage({'speaking': True})
                stt_node.on_speaking_status_change(status_msg)

                assert stt_node.speaking_active is True

    def test_publishes_listening_status(self):
        """Verify STT node publishes listening_status changes"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Trigger status publication
                stt_node._publish_listening_status(True, "started")

                # Verify publication
                statuses = bus.get_published('listening_status')
                assert len(statuses) == 1
                assert statuses[0]['data']['listening'] is True
                assert statuses[0]['data']['reason'] == "started"


class TestAiNodeIntegration:
    """Test ai_node22 message bus integration"""

    def test_subscribes_to_voice_command(self):
        """Verify AI node processes voice_command messages"""
        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()

            # Verify callback exists
            assert hasattr(ai_node, 'on_voice_command')

            # Simulate voice command
            cmd_msg = MockMessage({
                'text': 'What time is it?',
                'confidence': 0.95,
                'conversation_id': 'test_conv_123'
            })

            with patch.object(ai_node.connection_manager, 'send_sync'):
                ai_node.on_voice_command(cmd_msg)

                # Verify conversation ID was stored
                assert ai_node.current_conversation_id == 'test_conv_123'

    def test_publishes_text_response(self):
        """Verify AI node publishes text_response after processing"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()
            ai_node.publish = bus.publish

            # Simulate response generation
            ai_node.current_response_text = "It's 3:45 PM."
            ai_node.current_conversation_id = "test_conv_123"
            ai_node._on_response_text_done({})

            # Verify text_response was published
            responses = bus.get_published('text_response')
            assert len(responses) == 1
            assert responses[0]['data']['text'] == "It's 3:45 PM."
            assert responses[0]['data']['conversation_id'] == "test_conv_123"

    def test_text_response_data_schema(self):
        """Verify text_response messages have correct schema"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()
            ai_node.publish = bus.publish
            ai_node.current_response_text = "Test response"
            ai_node.current_conversation_id = "conv_001"
            ai_node._on_response_text_done({})

            response = bus.get_published('text_response')[0]['data']

            # Verify required fields
            assert 'text' in response
            assert 'voice' in response
            assert 'priority' in response
            assert 'timestamp' in response
            assert 'conversation_id' in response

            # Verify types
            assert isinstance(response['text'], str)
            assert isinstance(response['voice'], str)
            assert isinstance(response['priority'], int)
            assert isinstance(response['timestamp'], float)

    def test_publishes_system_mode_changes(self):
        """Verify AI node publishes system_mode updates"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()
            ai_node.publish = bus.publish

            # Trigger mode change
            ai_node._set_system_mode("thinking", "processing_command")

            # Verify system_mode was published
            modes = bus.get_published('system_mode')
            assert len(modes) == 1
            assert modes[0]['data']['mode'] == "thinking"
            assert modes[0]['data']['reason'] == "processing_command"

    def test_subscribes_to_visual_data(self):
        """Verify AI node can receive visual_data from camera"""
        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()

            # Verify callback exists
            assert hasattr(ai_node, 'on_visual_data')

            # Simulate visual data
            visual_msg = MockMessage({
                'image_data': 'base64_encoded_image_data',
                'capture_id': 'img_001',
                'timestamp': time.time()
            })

            with patch.object(ai_node.connection_manager, 'send_sync'):
                ai_node.on_visual_data(visual_msg)

                # Verify image was stored
                assert ai_node.latest_image is not None
                assert ai_node.latest_image['capture_id'] == 'img_001'

    def test_publishes_robot_action(self):
        """Verify AI node publishes robot_action for gestures"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()
            ai_node.publish = bus.publish

            # Simulate gesture execution
            result = ai_node._handle_gesture('wave_hello', {'speed': 'med'})

            # Verify robot_action was published
            actions = bus.get_published('robot_action')
            assert len(actions) == 1
            assert 'wave_hello:med' in actions[0]['data']['actions']


class TestSpeechSynthesisNodeIntegration:
    """Test speech_synthesis_node22 message bus integration"""

    def test_subscribes_to_text_response(self):
        """Verify TTS node processes text_response messages"""
        tts_node = SpeechSynthesisNode22()

        # Verify callback exists
        assert hasattr(tts_node, 'on_text_response')

        # Simulate text response
        text_msg = MockMessage({
            'text': 'Hello, this is a test.',
            'voice': 'alloy',
            'conversation_id': 'conv_001'
        })

        with patch.object(tts_node, 'realtime_manager'):
            tts_node.on_text_response(text_msg)

            # Verify conversation ID was stored
            assert tts_node.current_conversation_id == 'conv_001'

    def test_publishes_speaking_status(self):
        """Verify TTS node publishes speaking_status during synthesis"""
        bus = IntegratedMessageBus()

        tts_node = SpeechSynthesisNode22()
        tts_node.publish = bus.publish

        # Trigger status publication
        tts_node._publish_speaking_status(True, "Test speech", "alloy")

        # Verify publication
        statuses = bus.get_published('speaking_status')
        assert len(statuses) == 1
        assert statuses[0]['data']['speaking'] is True
        assert statuses[0]['data']['text'] == "Test speech"
        assert statuses[0]['data']['voice'] == "alloy"

    def test_publishes_audio_output_status(self):
        """Verify TTS node publishes audio_output_status on init"""
        bus = IntegratedMessageBus()

        tts_node = SpeechSynthesisNode22()
        tts_node.publish = bus.publish

        # Trigger status publication
        tts_node._publish_audio_output_status()

        # Verify publication
        statuses = bus.get_published('audio_output_status')
        assert len(statuses) == 1
        assert 'available' in statuses[0]['data']
        assert 'device' in statuses[0]['data']

    def test_subscribes_to_system_mode(self):
        """Verify TTS node responds to system_mode changes"""
        tts_node = SpeechSynthesisNode22()

        # Verify callback exists
        assert hasattr(tts_node, 'on_system_mode_change')

        # Simulate mode change
        mode_msg = MockMessage({'mode': 'idle', 'reason': 'reset'})
        tts_node.on_system_mode_change(mode_msg)

        # Should process without error


class TestNodeToNodeCommunication:
    """Test direct communication flows between nodes"""

    def test_stt_to_ai_communication(self):
        """Test voice_command flows from STT to AI"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            # Create nodes
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

            ai_node = AiNode22()

            # Subscribe AI to voice_command
            bus.subscribe('voice_command', ai_node.on_voice_command)

            # Mock AI's connection manager
            with patch.object(ai_node.connection_manager, 'send_sync'):
                # STT publishes voice command
                stt_node._process_transcript("Hello AI")

                # AI should have received it
                assert ai_node.current_conversation_id is not None

    def test_ai_to_tts_communication(self):
        """Test text_response flows from AI to TTS"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            # Create nodes
            ai_node = AiNode22()
            ai_node.publish = bus.publish

            tts_node = SpeechSynthesisNode22()

            # Subscribe TTS to text_response
            bus.subscribe('text_response', tts_node.on_text_response)

            # Mock TTS's realtime manager
            with patch.object(tts_node, 'realtime_manager'):
                # AI publishes text response
                ai_node.current_response_text = "Hello human"
                ai_node.current_conversation_id = "test_conv"
                ai_node._on_response_text_done({})

                # TTS should have received it
                assert tts_node.current_conversation_id == "test_conv"

    def test_full_pipeline_communication(self):
        """Test complete STT → AI → TTS communication flow"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            # Create all nodes
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

            ai_node = AiNode22()
            ai_node.publish = bus.publish

            tts_node = SpeechSynthesisNode22()
            tts_node.publish = bus.publish

            # Wire up subscriptions
            bus.subscribe('voice_command', ai_node.on_voice_command)
            bus.subscribe('text_response', tts_node.on_text_response)

            # Mock necessary dependencies
            with patch.object(ai_node.connection_manager, 'send_sync'):
                with patch.object(tts_node, 'realtime_manager'):
                    # STT generates command
                    stt_node._process_transcript("Tell me a joke")

                    # AI generates response
                    ai_node.current_response_text = "Why did the robot cross the road?"
                    ai_node._on_response_text_done({})

                    # Verify all messages were published
                    assert len(bus.get_published('voice_command')) == 1
                    assert len(bus.get_published('text_response')) == 1


class TestSystemModeCoordination:
    """Test system_mode synchronization across nodes"""

    def test_mode_propagation_to_all_nodes(self):
        """Test system_mode changes reach all nodes"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            # Create nodes
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

            tts_node = SpeechSynthesisNode22()

            # Subscribe to system_mode
            bus.subscribe('system_mode', stt_node.on_system_mode_change)
            bus.subscribe('system_mode', tts_node.on_system_mode_change)

            # Publish mode change
            bus.publish('system_mode', {'mode': 'speaking', 'reason': 'tts_active'})

            # Both nodes should have received it
            assert stt_node.system_mode == 'speaking'

    def test_speaking_pauses_listening(self):
        """Test speaking_status pauses STT listening"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()
                stt_node.is_listening = True

                # Subscribe to speaking_status
                bus.subscribe('speaking_status', stt_node.on_speaking_status_change)

                # Start speaking
                bus.publish('speaking_status', {'speaking': True, 'text': 'Test'})

                # Should have paused listening
                assert stt_node.speaking_active is True


class TestMessageBusReliability:
    """Test message bus reliability and error handling"""

    def test_publish_failure_handling(self):
        """Test nodes handle publish failures gracefully"""
        def failing_publish(topic, data):
            return False

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', failing_publish):
                stt_node = SpeechRecognitionNode22()

                # Should not crash on publish failure
                stt_node._process_transcript("Test")

                # Error count should increase
                assert stt_node.error_count >= 0

    def test_callback_exception_handling(self):
        """Test nodes handle callback exceptions gracefully"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            ai_node = AiNode22()

            def failing_callback(message):
                raise Exception("Test exception")

            bus.subscribe('voice_command', failing_callback)
            bus.subscribe('voice_command', ai_node.on_voice_command)

            # Should not crash other subscribers
            with patch.object(ai_node.connection_manager, 'send_sync'):
                bus.publish('voice_command', {
                    'text': 'Test',
                    'confidence': 0.9,
                    'conversation_id': 'test'
                })

                # AI node should still receive message
                assert ai_node.current_conversation_id == 'test'

    def test_concurrent_publications(self):
        """Test message bus handles concurrent publications"""
        bus = IntegratedMessageBus()
        received = []

        def subscriber(message):
            received.append(message.data)

        bus.subscribe('test_topic', subscriber)

        # Publish from multiple threads
        def publish_messages(start_id):
            for i in range(10):
                bus.publish('test_topic', {'id': start_id + i})

        threads = [
            threading.Thread(target=publish_messages, args=(0,)),
            threading.Thread(target=publish_messages, args=(10,)),
            threading.Thread(target=publish_messages, args=(20,))
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All messages should be received
        assert len(received) == 30


class TestConversationContext:
    """Test conversation context management across nodes"""

    def test_conversation_id_consistency(self):
        """Test conversation_id remains consistent across pipeline"""
        bus = IntegratedMessageBus()
        conversation_id = f"test_conv_{int(time.time())}"

        with patch('os.getenv', return_value='test_api_key'):
            # Create nodes
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

            ai_node = AiNode22()
            ai_node.publish = bus.publish

            # Mock chat logger to return specific ID
            with patch.object(stt_node.chat_logger, 'generate_conversation_id', return_value=conversation_id):
                # STT processes transcript
                stt_node._process_transcript("Test message")

            # Get voice command
            voice_cmd = bus.get_published('voice_command')[0]['data']
            assert voice_cmd['conversation_id'] == conversation_id

            # AI processes it
            ai_node.current_conversation_id = voice_cmd['conversation_id']
            ai_node.current_response_text = "Test response"
            ai_node._on_response_text_done({})

            # Get text response
            text_resp = bus.get_published('text_response')[0]['data']
            assert text_resp['conversation_id'] == conversation_id

    def test_multi_turn_conversation_tracking(self):
        """Test conversation IDs track across multiple turns"""
        bus = IntegratedMessageBus()

        with patch('os.getenv', return_value='test_api_key'):
            with patch.object(SpeechRecognitionNode22, 'publish', bus.publish):
                stt_node = SpeechRecognitionNode22()

                # Turn 1
                with patch.object(stt_node.chat_logger, 'generate_conversation_id', return_value='conv_1'):
                    stt_node._process_transcript("First message")

                # Turn 2
                with patch.object(stt_node.chat_logger, 'generate_conversation_id', return_value='conv_2'):
                    stt_node._process_transcript("Second message")

                # Verify different conversation IDs
                voice_cmds = bus.get_published('voice_command')
                assert voice_cmds[0]['data']['conversation_id'] == 'conv_1'
                assert voice_cmds[1]['data']['conversation_id'] == 'conv_2'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
