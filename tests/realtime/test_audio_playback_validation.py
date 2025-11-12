"""
Audio Playback Validation Tests for Nevil 2.2 Realtime API

CRITICAL HARDWARE VALIDATION:
- Verifies speech_synthesis_node22 uses AudioOutput from audio/audio_output.py
- Verifies AudioOutput calls robot_hat.Music() for playback
- Verifies audio is saved to WAV before playback (required for Music())
- Verifies does NOT use PyAudio for playback (PyAudio only for capture)
- Verifies GPIO pin 20 speaker switch is enabled
- Validates complete TTS pipeline matches v3.0 behavior

This test suite ensures the Realtime API TTS implementation uses EXACT same
hardware playback path as the working v3.0 implementation.
"""

import pytest
import os
import time
import wave
import base64
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from nevil_framework.realtime.speech_synthesis_node22 import SpeechSynthesisNode22
from audio.audio_output import AudioOutput
from audio.audio_utils import play_audio_file, generate_tts_filename


class TestAudioOutputIntegration:
    """Test SpeechSynthesisNode22 uses AudioOutput correctly"""

    def test_node_imports_audio_output_class(self):
        """Verify node imports AudioOutput from audio/audio_output.py"""
        from nevil_framework.realtime.speech_synthesis_node22 import AudioOutput as ImportedAudioOutput
        from audio.audio_output import AudioOutput as OriginalAudioOutput

        # Should be the same class
        assert ImportedAudioOutput is OriginalAudioOutput

    def test_node_initializes_audio_output(self):
        """Verify node creates AudioOutput instance"""
        with patch('audio.audio_output.Music') as mock_music:
            with patch('os.popen'):
                tts_node = SpeechSynthesisNode22()
                tts_node.initialize()

                # Should have created AudioOutput instance
                assert tts_node.audio_output is not None
                assert isinstance(tts_node.audio_output, AudioOutput)

    def test_audio_output_initializes_music(self):
        """Verify AudioOutput creates robot_hat.Music() instance"""
        with patch('audio.audio_output.Music') as mock_music_class:
            with patch('os.popen') as mock_popen:
                audio_output = AudioOutput()

                # Verify GPIO pin 20 was enabled for speaker
                mock_popen.assert_called_once_with("pinctrl set 20 op dh")

                # Verify Music() was instantiated
                mock_music_class.assert_called_once()
                assert audio_output.music is not None

    def test_node_does_not_use_pyaudio_for_playback(self):
        """CRITICAL: Verify node does NOT use PyAudio for audio playback"""
        # PyAudio should only be imported in audio_capture_manager, NOT in synthesis
        tts_node = SpeechSynthesisNode22()

        # Check the module's imports
        import nevil_framework.realtime.speech_synthesis_node22 as synthesis_module
        module_globals = dir(synthesis_module)

        # PyAudio should NOT be in speech synthesis imports
        assert 'pyaudio' not in module_globals
        assert 'PyAudio' not in module_globals

    def test_gpio_speaker_switch_enabled(self):
        """Verify GPIO pin 20 speaker switch is enabled during initialization"""
        with patch('audio.audio_output.Music'):
            with patch('os.popen') as mock_popen:
                audio_output = AudioOutput()

                # Verify the EXACT v1.0 GPIO command
                mock_popen.assert_called_once_with("pinctrl set 20 op dh")


class TestWAVFileSaveRequirement:
    """Test audio is saved to WAV file before playback"""

    def test_audio_saved_to_wav_before_playback(self):
        """Verify complete audio is saved to WAV file before Music() playback"""
        with patch('audio.audio_output.Music') as mock_music:
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()
            tts_node.audio_output.music = mock_music.return_value

            # Simulate audio streaming completion
            import base64
            test_pcm_data = b'\x00\x01' * 1000  # 2000 bytes of PCM16
            test_audio_b64 = base64.b64encode(test_pcm_data).decode('utf-8')

            # Buffer audio chunks
            tts_node._on_audio_delta({'delta': test_audio_b64})

            # Mock file operations
            with patch('wave.open', create=True) as mock_wave:
                mock_wav_file = MagicMock()
                mock_wave.return_value.__enter__.return_value = mock_wav_file

                with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                    with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                        with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                            # Trigger audio completion
                            tts_node._on_audio_done({})

                # Verify WAV file was created with correct settings
                assert mock_wave.called
                mock_wav_file.setnchannels.assert_called_once_with(1)  # Mono
                mock_wav_file.setsampwidth.assert_called_once_with(2)  # 16-bit
                mock_wav_file.setframerate.assert_called_once_with(24000)  # 24kHz
                mock_wav_file.writeframes.assert_called_once()

    def test_wav_file_path_generation(self):
        """Verify WAV file paths are generated correctly"""
        raw_file, processed_file = generate_tts_filename(volume_db=-10)

        # Check file paths
        assert raw_file.startswith('./audio/nevil_wavs/')
        assert raw_file.endswith('_raw.wav')
        assert processed_file.endswith('_-10dB.wav')

    def test_pcm16_to_wav_conversion(self):
        """Test PCM16 data is correctly converted to WAV format"""
        tts_node = SpeechSynthesisNode22()

        # Create test PCM16 data
        test_pcm = b'\x00\x01\x02\x03\x04\x05'

        # Mock wave operations
        with patch('wave.open', create=True) as mock_wave:
            mock_wav_file = MagicMock()
            mock_wave.return_value.__enter__.return_value = mock_wav_file

            tts_node._save_pcm16_to_wav(test_pcm, '/tmp/test.wav', sample_rate=24000)

            # Verify correct WAV format settings
            mock_wav_file.setnchannels.assert_called_once_with(1)
            mock_wav_file.setsampwidth.assert_called_once_with(2)
            mock_wav_file.setframerate.assert_called_once_with(24000)
            mock_wav_file.writeframes.assert_called_once_with(test_pcm)


class TestMusicPlaybackPath:
    """Test the actual robot_hat.Music() playback path"""

    def test_uses_play_loaded_speech_method(self):
        """Verify node calls audio_output.play_loaded_speech()"""
        with patch('audio.audio_output.Music') as mock_music:
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()
            tts_node.audio_output.music = mock_music.return_value

            # Mock the play method
            with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True) as mock_play:
                with patch('wave.open', create=True):
                    with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                        with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                            # Buffer and complete audio
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
                            tts_node._on_audio_done({})

                # Verify play_loaded_speech was called
                mock_play.assert_called_once()

    def test_play_audio_file_uses_music_instance(self):
        """Verify play_audio_file() calls Music().music_play()"""
        with patch('audio.audio_output.Music') as mock_music_class:
            mock_music = MagicMock()
            mock_music_class.return_value = mock_music
            mock_music.pygame.mixer.music.get_busy.return_value = False

            # Create test WAV file
            test_file = '/tmp/test_audio.wav'

            with patch('os.path.exists', return_value=True):
                with patch('audio.audio_utils.cleanup_old_audio_files'):
                    play_audio_file(mock_music, test_file)

                # Verify Music().music_play() was called with the file
                mock_music.music_play.assert_called_once_with(test_file)
                mock_music.music_stop.assert_called_once()

    def test_complete_playback_flow_v3_compatibility(self):
        """CRITICAL: Test complete playback flow matches v3.0 exactly"""
        with patch('audio.audio_output.Music') as mock_music_class:
            mock_music = MagicMock()
            mock_music_class.return_value = mock_music
            mock_music.pygame.mixer.music.get_busy.side_effect = [True, True, False]

            with patch('os.popen'):
                # Initialize AudioOutput (v3.0 style)
                audio_output = AudioOutput()
                audio_output.music = mock_music

                # Set up loaded speech (v3.0 pattern)
                test_wav = '/tmp/test.wav'
                audio_output.tts_file = test_wav

                with audio_output.speech_lock:
                    audio_output.speech_loaded = True

                # Play using v3.0 method
                with patch('os.path.exists', return_value=True):
                    with patch('audio.audio_utils.cleanup_old_audio_files'):
                        result = audio_output.play_loaded_speech()

                # Verify v3.0 playback sequence
                assert result is True
                mock_music.music_play.assert_called_once_with(test_wav)
                assert mock_music.pygame.mixer.music.get_busy.call_count >= 3
                mock_music.music_stop.assert_called_once()
                assert audio_output.speech_loaded is False


class TestAudioBuffering:
    """Test audio buffering during streaming"""

    def test_audio_chunks_buffered_correctly(self):
        """Verify audio chunks are buffered in order"""
        tts_node = SpeechSynthesisNode22()

        # Simulate streaming chunks
        chunks = [
            base64.b64encode(b'chunk1').decode(),
            base64.b64encode(b'chunk2').decode(),
            base64.b64encode(b'chunk3').decode(),
        ]

        for chunk in chunks:
            tts_node._on_audio_delta({'delta': chunk})

        # Verify all chunks buffered
        assert len(tts_node.audio_buffer) == 3

        # Verify total size
        total_size = sum(len(chunk) for chunk in tts_node.audio_buffer)
        assert total_size == len(b'chunk1chunk2chunk3')

    def test_buffer_cleared_after_playback(self):
        """Verify buffer is cleared after playback completes"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()

            # Buffer some audio
            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
            assert len(tts_node.audio_buffer) > 0

            # Complete playback
            with patch('wave.open', create=True):
                with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                    with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                        with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                            tts_node._on_audio_done({})

            # Verify buffer cleared
            assert len(tts_node.audio_buffer) == 0

    def test_large_audio_buffer_handling(self):
        """Test handling of large audio buffers (long speech)"""
        tts_node = SpeechSynthesisNode22()

        # Simulate 10 seconds of 24kHz PCM16 audio (480KB)
        samples = 24000 * 10 * 2  # 10 seconds, 2 bytes per sample
        large_chunk = b'\x00\x01' * (samples // 2)

        # Split into reasonable chunks
        chunk_size = 4800 * 2  # 200ms chunks
        for i in range(0, len(large_chunk), chunk_size):
            chunk = large_chunk[i:i+chunk_size]
            encoded = base64.b64encode(chunk).decode()
            tts_node._on_audio_delta({'delta': encoded})

        # Verify all buffered
        total_buffered = sum(len(chunk) for chunk in tts_node.audio_buffer)
        assert total_buffered == len(large_chunk)


class TestHardwareCompatibility:
    """Test hardware-specific compatibility requirements"""

    def test_sample_rate_24khz(self):
        """Verify audio uses 24kHz sample rate (OpenAI Realtime API format)"""
        tts_node = SpeechSynthesisNode22()

        # Check configuration
        assert tts_node.audio_config.get('volume_db', -10) == -10

        # Verify WAV saving uses 24kHz
        test_pcm = b'\x00\x01'
        with patch('wave.open', create=True) as mock_wave:
            mock_wav_file = MagicMock()
            mock_wave.return_value.__enter__.return_value = mock_wav_file

            tts_node._save_pcm16_to_wav(test_pcm, '/tmp/test.wav', sample_rate=24000)

            # Verify 24kHz
            mock_wav_file.setframerate.assert_called_once_with(24000)

    def test_mono_audio_channel(self):
        """Verify audio is mono (1 channel) as required by hardware"""
        tts_node = SpeechSynthesisNode22()

        test_pcm = b'\x00\x01'
        with patch('wave.open', create=True) as mock_wave:
            mock_wav_file = MagicMock()
            mock_wave.return_value.__enter__.return_value = mock_wav_file

            tts_node._save_pcm16_to_wav(test_pcm, '/tmp/test.wav')

            # Verify mono
            mock_wav_file.setnchannels.assert_called_once_with(1)

    def test_pcm16_bit_depth(self):
        """Verify audio uses 16-bit PCM (required by Music())"""
        tts_node = SpeechSynthesisNode22()

        test_pcm = b'\x00\x01'
        with patch('wave.open', create=True) as mock_wave:
            mock_wav_file = MagicMock()
            mock_wave.return_value.__enter__.return_value = mock_wav_file

            tts_node._save_pcm16_to_wav(test_pcm, '/tmp/test.wav')

            # Verify 16-bit (2 bytes per sample)
            mock_wav_file.setsampwidth.assert_called_once_with(2)

    def test_hifiberry_dac_compatibility(self):
        """Verify playback is compatible with HiFiBerry DAC"""
        # Music() uses system default audio device, which should be HiFiBerry
        with patch('audio.audio_output.Music') as mock_music_class:
            mock_music = MagicMock()
            mock_music_class.return_value = mock_music

            with patch('os.popen'):
                audio_output = AudioOutput()

                # Music() should be initialized without device specification
                # (uses system default, which is HiFiBerry DAC)
                mock_music_class.assert_called_once_with()

                # No manual device/channel specification should be present
                assert not hasattr(audio_output, 'device_index')
                assert not hasattr(audio_output, 'output_device_index')


class TestMicrophoneMutex:
    """Test microphone mutex coordination"""

    def test_acquires_mutex_before_playback(self):
        """Verify microphone mutex is acquired before playback"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()

            with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity') as mock_acquire:
                with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                    with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                        with patch('wave.open', create=True):
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
                            tts_node._on_audio_done({})

                # Verify mutex was acquired
                mock_acquire.assert_called_once_with("speaking")

    def test_releases_mutex_after_playback(self):
        """Verify microphone mutex is released after playback"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()

            with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity') as mock_release:
                    with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                        with patch('wave.open', create=True):
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
                            tts_node._on_audio_done({})

                # Verify mutex was released
                mock_release.assert_called_once_with("speaking")

    def test_releases_mutex_on_error(self):
        """Verify mutex is released even if playback fails"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()

            with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity') as mock_release:
                    with patch.object(tts_node.audio_output, 'play_loaded_speech', side_effect=Exception("Test error")):
                        with patch('wave.open', create=True):
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})

                            # Should handle error gracefully
                            try:
                                tts_node._on_audio_done({})
                            except:
                                pass

                # Mutex should still be released
                mock_release.assert_called_once_with("speaking")


class TestPlaybackStatuses:
    """Test playback status publishing"""

    def test_publishes_speaking_status_on_start(self):
        """Verify speaking status is published when playback starts"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()
            tts_node.publish = Mock(return_value=True)

            with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                    with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                        with patch('wave.open', create=True):
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
                            tts_node._on_audio_done({})

            # Verify speaking_status was published (True then False)
            speaking_calls = [call for call in tts_node.publish.call_args_list
                            if call[0][0] == 'speaking_status']

            assert len(speaking_calls) >= 2  # At least start and end

    def test_publishes_speaking_status_on_end(self):
        """Verify speaking status is cleared when playback ends"""
        with patch('audio.audio_output.Music'):
            tts_node = SpeechSynthesisNode22()
            tts_node.audio_output = AudioOutput()
            tts_node.publish = Mock(return_value=True)

            with patch('nevil_framework.microphone_mutex.microphone_mutex.acquire_noisy_activity'):
                with patch('nevil_framework.microphone_mutex.microphone_mutex.release_noisy_activity'):
                    with patch.object(tts_node.audio_output, 'play_loaded_speech', return_value=True):
                        with patch('wave.open', create=True):
                            tts_node._on_audio_delta({'delta': base64.b64encode(b'test').decode()})
                            tts_node._on_audio_done({})

            # Find the final speaking_status call
            speaking_calls = [call for call in tts_node.publish.call_args_list
                            if call[0][0] == 'speaking_status']

            final_call = speaking_calls[-1]
            final_data = final_call[0][1]

            # Should be False at end
            assert final_data['speaking'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
