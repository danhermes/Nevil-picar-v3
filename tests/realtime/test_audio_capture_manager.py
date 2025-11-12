"""
Test suite for AudioCaptureManager

Tests audio capture functionality for OpenAI Realtime API integration.
"""

import unittest
import time
import threading
import logging
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from nevil_framework.realtime.audio_capture_manager import (
    AudioCaptureManager,
    AudioCaptureConfig,
    AudioCaptureCallbacks,
    CaptureState,
    create_audio_capture
)


# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestAudioCaptureConfig(unittest.TestCase):
    """Test AudioCaptureConfig class"""

    def test_default_config(self):
        """Test default configuration values"""
        config = AudioCaptureConfig()

        self.assertEqual(config.sample_rate, 24000)
        self.assertEqual(config.channel_count, 1)
        self.assertEqual(config.chunk_size, 4800)
        self.assertEqual(config.buffer_size, 4096)
        self.assertIsNone(config.device_index)
        self.assertFalse(config.vad_enabled)
        self.assertEqual(config.vad_threshold, 0.02)
        self.assertEqual(config.auto_flush_ms, 200)

    def test_custom_config(self):
        """Test custom configuration values"""
        config = AudioCaptureConfig(
            sample_rate=48000,
            channel_count=2,
            chunk_size=9600,
            vad_enabled=True,
            vad_threshold=0.05
        )

        self.assertEqual(config.sample_rate, 48000)
        self.assertEqual(config.channel_count, 2)
        self.assertEqual(config.chunk_size, 9600)
        self.assertTrue(config.vad_enabled)
        self.assertEqual(config.vad_threshold, 0.05)


class TestAudioCaptureCallbacks(unittest.TestCase):
    """Test AudioCaptureCallbacks class"""

    def test_default_callbacks(self):
        """Test default callbacks are None"""
        callbacks = AudioCaptureCallbacks()

        self.assertIsNone(callbacks.on_audio_data)
        self.assertIsNone(callbacks.on_volume_change)
        self.assertIsNone(callbacks.on_error)
        self.assertIsNone(callbacks.on_state_change)
        self.assertIsNone(callbacks.on_vad_speech_start)
        self.assertIsNone(callbacks.on_vad_speech_end)

    def test_custom_callbacks(self):
        """Test setting custom callbacks"""
        on_audio = Mock()
        on_volume = Mock()
        on_error = Mock()

        callbacks = AudioCaptureCallbacks(
            on_audio_data=on_audio,
            on_volume_change=on_volume,
            on_error=on_error
        )

        self.assertEqual(callbacks.on_audio_data, on_audio)
        self.assertEqual(callbacks.on_volume_change, on_volume)
        self.assertEqual(callbacks.on_error, on_error)


class TestAudioCaptureManager(unittest.TestCase):
    """Test AudioCaptureManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = AudioCaptureConfig()
        self.callbacks = AudioCaptureCallbacks()
        self.connection_manager = Mock()

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_initialization(self, mock_pyaudio):
        """Test manager initialization"""
        manager = AudioCaptureManager(
            config=self.config,
            callbacks=self.callbacks,
            connection_manager=self.connection_manager
        )

        self.assertEqual(manager.config, self.config)
        self.assertEqual(manager.callbacks, self.callbacks)
        self.assertEqual(manager.connection_manager, self.connection_manager)
        self.assertEqual(manager.state, CaptureState.INACTIVE)
        self.assertFalse(manager.is_recording)
        self.assertFalse(manager.is_paused)
        self.assertEqual(manager.buffer_length, 0)
        self.assertEqual(manager.total_samples_processed, 0)
        self.assertEqual(manager.total_chunks_sent, 0)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_initialize_pyaudio(self, mock_pyaudio_class):
        """Test PyAudio initialization"""
        # Set up mocks
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'name': 'Test Device',
            'maxInputChannels': 2,
            'defaultSampleRate': 44100.0
        }

        manager = AudioCaptureManager(config=self.config)
        manager.initialize()

        # Verify PyAudio was created
        mock_pyaudio_class.assert_called_once()

        # Verify stream was opened with correct parameters
        mock_audio.open.assert_called_once()
        call_kwargs = mock_audio.open.call_args[1]
        self.assertEqual(call_kwargs['rate'], 24000)
        self.assertEqual(call_kwargs['channels'], 1)
        self.assertTrue(call_kwargs['input'])

        # Verify stream was stopped initially
        mock_stream.stop_stream.assert_called_once()

        self.assertEqual(manager.state, CaptureState.INACTIVE)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_state_transitions(self, mock_pyaudio):
        """Test state transitions during recording"""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        mock_stream.is_active.return_value = True

        state_callback = Mock()
        callbacks = AudioCaptureCallbacks(on_state_change=state_callback)

        manager = AudioCaptureManager(config=self.config, callbacks=callbacks)
        manager.initialize()

        # Start recording
        manager.start_recording()
        self.assertEqual(manager.state, CaptureState.RECORDING)
        self.assertTrue(manager.is_recording)
        self.assertFalse(manager.is_paused)

        # Pause
        manager.pause()
        self.assertEqual(manager.state, CaptureState.PAUSED)
        self.assertTrue(manager.is_recording)
        self.assertTrue(manager.is_paused)

        # Resume
        manager.resume()
        self.assertEqual(manager.state, CaptureState.RECORDING)
        self.assertTrue(manager.is_recording)
        self.assertFalse(manager.is_paused)

        # Stop
        manager.stop_recording()
        self.assertEqual(manager.state, CaptureState.INACTIVE)
        self.assertFalse(manager.is_recording)
        self.assertFalse(manager.is_paused)

        # Cleanup
        manager.dispose()

    def test_calculate_volume(self):
        """Test volume calculation"""
        manager = AudioCaptureManager(config=self.config)

        # Test silence
        silence = np.zeros(1000, dtype=np.float32)
        volume = manager._calculate_volume(silence)
        self.assertAlmostEqual(volume, 0.0, places=5)

        # Test full scale signal
        full_scale = np.ones(1000, dtype=np.float32)
        volume = manager._calculate_volume(full_scale)
        self.assertAlmostEqual(volume, 1.0, places=5)

        # Test sine wave (should be ~0.707 RMS)
        t = np.linspace(0, 1, 1000, dtype=np.float32)
        sine = np.sin(2 * np.pi * 440 * t)
        volume = manager._calculate_volume(sine)
        self.assertGreater(volume, 0.6)
        self.assertLess(volume, 0.8)

    def test_float32_to_pcm16(self):
        """Test float32 to PCM16 conversion"""
        manager = AudioCaptureManager(config=self.config)

        # Test conversion
        audio_float = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        pcm_bytes = manager._float32_to_pcm16(audio_float)

        # Convert back to verify
        pcm_array = np.frombuffer(pcm_bytes, dtype=np.int16)

        self.assertEqual(len(pcm_array), 5)
        self.assertEqual(pcm_array[0], 0)
        self.assertAlmostEqual(pcm_array[1], 16383, delta=1)
        self.assertAlmostEqual(pcm_array[2], -16383, delta=1)
        self.assertEqual(pcm_array[3], 32767)
        self.assertEqual(pcm_array[4], -32767)

    def test_encode_base64(self):
        """Test base64 encoding"""
        manager = AudioCaptureManager(config=self.config)

        # Create test PCM data
        pcm_data = bytes([0, 1, 2, 3, 4, 5])
        encoded = manager._encode_base64(pcm_data)

        # Verify it's a valid base64 string
        self.assertIsInstance(encoded, str)
        self.assertGreater(len(encoded), 0)

        # Verify we can decode it back
        import base64
        decoded = base64.b64decode(encoded)
        self.assertEqual(decoded, pcm_data)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_flush_empty_buffer(self, mock_pyaudio):
        """Test flushing empty buffer"""
        manager = AudioCaptureManager(config=self.config)

        # Flush empty buffer (should not raise)
        manager.flush()

        # Verify buffer is still empty
        self.assertEqual(manager.buffer_length, 0)
        self.assertEqual(len(manager.audio_buffer), 0)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_flush_with_data(self, mock_pyaudio):
        """Test flushing buffer with audio data"""
        audio_callback = Mock()
        callbacks = AudioCaptureCallbacks(on_audio_data=audio_callback)
        manager = AudioCaptureManager(config=self.config, callbacks=callbacks)

        # Add test audio data to buffer
        test_audio = np.random.rand(1000).astype(np.float32) * 0.1
        manager.audio_buffer.append(test_audio)
        manager.buffer_length = len(test_audio)

        # Flush
        manager.flush()

        # Verify callback was called
        audio_callback.assert_called_once()
        base64_audio, volume = audio_callback.call_args[0]
        self.assertIsInstance(base64_audio, str)
        self.assertGreater(volume, 0.0)

        # Verify buffer was cleared
        self.assertEqual(manager.buffer_length, 0)
        self.assertEqual(len(manager.audio_buffer), 0)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_send_to_connection_manager(self, mock_pyaudio):
        """Test sending audio to connection manager"""
        connection_manager = Mock()
        manager = AudioCaptureManager(
            config=self.config,
            connection_manager=connection_manager
        )

        # Add test audio and flush
        test_audio = np.random.rand(1000).astype(np.float32) * 0.1
        manager.audio_buffer.append(test_audio)
        manager.buffer_length = len(test_audio)
        manager.flush()

        # Verify connection manager received event
        connection_manager.send_event.assert_called_once()
        event = connection_manager.send_event.call_args[0][0]
        self.assertEqual(event['type'], 'input_audio_buffer.append')
        self.assertIn('audio', event)
        self.assertIsInstance(event['audio'], str)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_vad_speech_detection(self, mock_pyaudio):
        """Test Voice Activity Detection"""
        config = AudioCaptureConfig(vad_enabled=True, vad_threshold=0.1)
        speech_start_callback = Mock()
        speech_end_callback = Mock()
        callbacks = AudioCaptureCallbacks(
            on_vad_speech_start=speech_start_callback,
            on_vad_speech_end=speech_end_callback
        )

        manager = AudioCaptureManager(config=config, callbacks=callbacks)

        # Test speech detection
        manager._process_vad(0.15)  # Above threshold
        self.assertTrue(manager.vad_speech_active)
        speech_start_callback.assert_called_once()

        # Test silence (but not enough to end speech)
        manager._process_vad(0.05)  # Below threshold
        self.assertTrue(manager.vad_speech_active)
        speech_end_callback.assert_not_called()

        # Test prolonged silence
        for _ in range(manager.vad_silence_threshold):
            manager._process_vad(0.05)

        self.assertFalse(manager.vad_speech_active)
        speech_end_callback.assert_called_once()

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_get_stats(self, mock_pyaudio):
        """Test getting statistics"""
        manager = AudioCaptureManager(config=self.config)
        manager.total_samples_processed = 48000
        manager.total_chunks_sent = 10

        stats = manager.get_stats()

        self.assertEqual(stats['state'], 'inactive')
        self.assertFalse(stats['is_recording'])
        self.assertEqual(stats['total_samples'], 48000)
        self.assertEqual(stats['total_chunks'], 10)
        self.assertEqual(stats['sample_rate'], 24000)
        self.assertEqual(stats['channels'], 1)

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_dispose(self, mock_pyaudio):
        """Test resource cleanup"""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        mock_stream.is_active.return_value = False

        manager = AudioCaptureManager(config=self.config)
        manager.initialize()
        manager.dispose()

        # Verify cleanup
        mock_stream.close.assert_called_once()
        mock_audio.terminate.assert_called_once()
        self.assertIsNone(manager.stream)
        self.assertIsNone(manager.audio)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""

    @patch('nevil_framework.realtime.audio_capture_manager.pyaudio.PyAudio')
    def test_create_audio_capture(self, mock_pyaudio):
        """Test create_audio_capture convenience function"""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_pyaudio.return_value = mock_audio
        mock_audio.open.return_value = mock_stream
        mock_audio.get_device_count.return_value = 0

        connection_manager = Mock()
        manager = create_audio_capture(
            connection_manager=connection_manager,
            sample_rate=24000,
            vad_enabled=True
        )

        # Verify manager was created and initialized
        self.assertIsInstance(manager, AudioCaptureManager)
        self.assertEqual(manager.config.sample_rate, 24000)
        self.assertTrue(manager.config.vad_enabled)
        self.assertEqual(manager.connection_manager, connection_manager)
        self.assertIsNotNone(manager.audio)


class TestIntegration(unittest.TestCase):
    """Integration tests (require actual hardware)"""

    @unittest.skip("Requires actual audio hardware")
    def test_real_hardware_capture(self):
        """Test with real audio hardware (manual test)"""
        # This test requires actual microphone hardware
        # Uncomment and run manually on Raspberry Pi

        callbacks = AudioCaptureCallbacks(
            on_audio_data=lambda audio, volume: print(f"Audio: {len(audio)} bytes, Volume: {volume:.3f}"),
            on_volume_change=lambda volume: print(f"Volume: {volume:.3f}"),
            on_state_change=lambda state: print(f"State: {state.value}")
        )

        manager = create_audio_capture(vad_enabled=True)
        manager.callbacks = callbacks

        print("Starting 5-second recording test...")
        manager.start_recording()
        time.sleep(5)
        manager.stop_recording()
        manager.dispose()

        print(f"Stats: {manager.get_stats()}")


if __name__ == '__main__':
    unittest.main()
