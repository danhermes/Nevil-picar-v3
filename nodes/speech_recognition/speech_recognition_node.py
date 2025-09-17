"""
Speech Recognition Node for Nevil v3.0

Combines v1.0 proven parameters with v2.0 advanced threading architecture.
Uses default audio devices only and preserves exact working parameters.
"""

import time
import os
import threading
import queue
from nevil_framework.base_node import NevilNode
from nevil_framework.busy_state import busy_state
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from audio.audio_input import AudioInput


class SpeechRecognitionNode(NevilNode):
    """
    Speech Recognition Node using extracted v1.0 + v2.0 code.

    Features:
    - v1.0 EXACT speech recognition parameters (DO NOT MODIFY)
    - v2.0 threading architecture for robust processing
    - Default audio devices only (no manual device specification)
    - Declarative messaging via .messages configuration
    - OpenAI Whisper integration
    """

    def __init__(self):
        super().__init__("speech_recognition")

        # Load OpenAI API key for speech recognition
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            self.logger.warning("No OpenAI API key found - speech recognition may not work")

        # Initialize OpenAI helper (will be set by launcher or manually)
        self.openai_helper = None

        # Audio input using extracted v1.0 + v2.0 code
        self.audio_input = None

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.audio_config = config.get('audio', {})
        self.recognition_config = config.get('recognition', {})
        self.performance_config = config.get('performance', {})

        # State management (v2.0 pattern)
        self.is_listening = False
        self.system_mode = "idle"
        self.speaking_active = False
        self.navigation_active = False

        # Shutdown handling (v2.0 pattern)
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.audio_thread = None

        # Performance tracking
        self.last_recognition_time = 0
        self.recognition_count = 0
        self.error_count = 0

    def initialize(self):
        """Initialize speech recognition components"""
        self.logger.info("Initializing Speech Recognition Node...")

        try:
            # Initialize audio input with v1.0 + v2.0 extracted code
            self.audio_input = AudioInput(logger=self.logger)

            # Initialize OpenAI helper if we have API key
            if self.openai_api_key:
                # For now, we'll implement OpenAI calls directly
                # Will integrate v1.0 OpenAI helper in Phase 2
                self.logger.info("OpenAI API key available for speech recognition")
                self.openai_helper = self  # Temporary - use self for OpenAI calls
            else:
                self.logger.error("Cannot initialize speech recognition without OpenAI API key")
                return

            # Log our configuration
            self.logger.info("Speech Recognition Configuration:")
            self.logger.info(f"  Energy threshold: {self.audio_input.recognizer.energy_threshold}")
            self.logger.info(f"  Pause threshold: {self.audio_input.recognizer.pause_threshold}")
            self.logger.info(f"  Language: {self.recognition_config.get('language', 'en-US')}")
            self.logger.info(f"  Timeout: {self.recognition_config.get('timeout', 10.0)}s")

            # Set listening state for discrete recording
            self.is_listening = True

            # Start discrete recording thread (v2.0 pattern)
            self.audio_thread = threading.Thread(target=self._discrete_recording_loop, daemon=True)
            self.audio_thread.start()

            self.logger.info("Speech Recognition Node initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            raise

    def _discrete_recording_loop(self):
        """Discrete recording loop - v2.0 approach: Mic on → Record → Mic off → Process"""
        self.logger.info("Starting discrete recording loop...")

        while not self.stop_event.is_set():
            try:
                if not self.is_listening:
                    time.sleep(0.5)
                    continue

                # DISCRETE RECORDING CYCLE - Acquire busy state first
                self.logger.debug("Waiting for busy state...")

                # Acquire busy state - prevents recording during TTS/actions
                # Using default 2-minute timeout to prevent freezing
                if not busy_state.acquire("listening"):
                    self.logger.warning("System busy, skipping recording cycle")
                    time.sleep(1.0)
                    continue

                try:
                    self.logger.debug("Starting discrete recording cycle (not busy)...")

                    # 1. Mic ON - single recording session
                    audio = self.audio_input.listen_for_speech(
                        timeout=10.0,  # Wait for speech
                        phrase_time_limit=10.0  # Max recording time
                    )

                    # 2. Mic OFF (happens automatically when listen_for_speech returns)

                    if audio:
                        # 3. PROCESS: Save → STT → AI → TTS
                        self.logger.debug("Processing captured audio...")
                        self._process_audio_discrete(audio)
                    else:
                        self.logger.debug("No speech detected, continuing...")

                finally:
                    # ALWAYS release the busy state
                    busy_state.release()
                    self.logger.debug("Released busy state")

                # 4. Brief pause before next cycle
                time.sleep(0.5)

            except Exception as e:
                if not self.stop_event.is_set():
                    self.logger.error(f"Error in discrete recording cycle: {e}")
                    time.sleep(2.0)  # Longer pause on error

        self.logger.info("Discrete recording loop stopped")

    def stop(self, timeout=10.0):
        """Stop the node gracefully (v2.0 shutdown pattern)"""
        self.logger.info("Stopping Speech Recognition Node...")

        # Set stop event to signal threads to stop
        self.stop_event.set()

        # Stop listening
        self.is_listening = False

        # Wait for audio thread to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=timeout)

        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break

        self.logger.info("Speech Recognition Node stopped")

        # Call parent stop method
        super().stop(timeout)

    def main_loop(self):
        """Main processing loop - minimal since discrete recording handles everything"""
        try:
            # Check if we should stop (v2.0 shutdown pattern)
            if self.stop_event.is_set():
                return

            # Brief pause - discrete recording thread handles all audio processing
            time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in speech recognition main loop: {e}")
            self.error_count += 1
            time.sleep(1.0)

    def _process_audio_discrete(self, audio):
        """Discrete audio processing - v2.0 approach: Save → STT → AI → TTS"""
        try:
            self.logger.info("🎙️  Starting discrete audio processing cycle")

            # STEP 1: Save audio file
            recognition_start = time.time()
            language = self.recognition_config.get('language', 'en-US')

            # STEP 2: Speech-to-Text (creates and saves audio file)
            text = self.speech_to_text(audio, language)

            if text and text.strip():
                # STEP 3: Calculate metrics and publish to AI
                recognition_time = time.time() - recognition_start
                confidence = self._estimate_confidence(text, recognition_time)

                voice_command_data = {
                    "text": text.strip(),
                    "confidence": confidence,
                    "timestamp": time.time(),
                    "language": language,
                    "duration": recognition_time
                }

                # STEP 4: Send to AI for processing (which triggers TTS)
                if self.publish("voice_command", voice_command_data):
                    self.logger.info(f"✓ Speech processed: '{text}' (conf: {confidence:.2f})")
                    self.recognition_count += 1
                    self.last_recognition_time = time.time()

                    # STEP 5: Lock will handle synchronization
                    # No need to wait - the lock prevents overlap
                else:
                    self.logger.error("Failed to publish voice command")

            else:
                self.logger.debug("No speech recognized - continuing to next cycle")

        except Exception as e:
            self.logger.error(f"Error in discrete audio processing: {e}")
            self.error_count += 1

    def _wait_for_tts_completion(self):
        """Wait for TTS to complete before starting next recording cycle"""
        # Simple approach: wait for speaking status to go false
        # This prevents barge-in during TTS playback
        self.logger.debug("Waiting for TTS completion...")
        timeout = time.time() + 30.0  # Max 30 second wait

        while time.time() < timeout and not self.stop_event.is_set():
            if not self.speaking_active:
                break
            time.sleep(0.1)

        # Additional buffer time after TTS ends
        time.sleep(1.0)
        self.logger.debug("TTS completion wait finished")

    def _estimate_confidence(self, text, recognition_time):
        """Estimate confidence based on text quality and timing (v1.0 pattern)"""
        base_confidence = 0.8  # OpenAI Whisper baseline

        # Length factor - moderate length is better
        word_count = len(text.split())
        if 2 <= word_count <= 10:
            length_factor = 1.0
        elif word_count == 1:
            length_factor = 0.8
        else:
            length_factor = 0.9

        # Timing factor - reasonable processing time
        if 0.5 <= recognition_time <= 3.0:
            timing_factor = 1.0
        else:
            timing_factor = 0.9

        # Content factor - avoid gibberish
        if text.isalpha() and len(text) > 2:
            content_factor = 1.0
        else:
            content_factor = 0.7

        confidence = base_confidence * length_factor * timing_factor * content_factor
        return min(max(confidence, 0.0), 1.0)

    def _start_listening(self):
        """Start listening for speech (discrete recording mode)"""
        if self.is_listening:
            return

        try:
            # In discrete mode, just set the flag - the recording loop handles everything
            self.is_listening = True

            # Publish listening status change
            self._publish_listening_status(True, "started")

            self.logger.info("Started discrete speech listening")

        except Exception as e:
            self.logger.error(f"Error starting speech listening: {e}")

    def _stop_listening(self):
        """Stop listening for speech (discrete recording mode)"""
        if not self.is_listening:
            return

        try:
            # In discrete mode, just set the flag - the recording loop will stop
            self.is_listening = False

            # Publish listening status change
            self._publish_listening_status(False, "stopped")

            self.logger.info("Stopped discrete speech listening")

        except Exception as e:
            self.logger.error(f"Error stopping speech listening: {e}")

    def _publish_listening_status(self, listening, reason):
        """Publish listening status change"""
        status_data = {
            "listening": listening,
            "reason": reason
        }
        self.publish("listening_status", status_data)

    # Declaratively configured callback methods (from .messages file)

    def on_system_mode_change(self, message):
        """Handle system mode changes (declaratively configured callback)"""
        try:
            mode = message.data.get("mode", "idle")
            self.system_mode = mode

            self.logger.debug(f"System mode changed to: {mode}")

            # Start/stop listening based on mode
            if mode == "listening" and not self.is_listening:
                self._start_listening()
            elif mode == "speaking" and self.is_listening:
                self._stop_listening()
            elif mode == "idle" and not self.is_listening:
                self._start_listening()  # Resume listening in idle mode

        except Exception as e:
            self.logger.error(f"Error handling system mode change: {e}")

    def on_speaking_status_change(self, message):
        """Handle speaking status changes (declaratively configured callback)"""
        try:
            speaking = message.data.get("speaking", False)
            self.speaking_active = speaking

            self.logger.debug(f"Speaking status changed: {speaking}")

            # Pause listening during speech synthesis
            if speaking and self.is_listening:
                self._stop_listening()
                self.logger.info("Paused speech recognition - system is speaking")
            elif not speaking and not self.is_listening and not self.navigation_active:
                self._start_listening()
                self.logger.info("Resumed speech recognition - system finished speaking")

        except Exception as e:
            self.logger.error(f"Error handling speaking status change: {e}")

    def on_navigation_status_change(self, message):
        """Handle navigation status changes (declaratively configured callback)"""
        try:
            status = message.data.get("status", "idle")
            current_action = message.data.get("current_action", "")

            # Update navigation state
            self.navigation_active = status == "executing"

            self.logger.debug(f"Navigation status changed: {status} (action: {current_action})")

            # Pause listening during action execution to avoid servo noise triggering recognition
            if status == "executing" and self.is_listening:
                self._stop_listening()
                self.logger.info("Paused speech recognition - robot is executing actions")
            elif status in ["completed", "idle"] and not self.is_listening and not self.speaking_active:
                self._start_listening()
                self.logger.info("Resumed speech recognition - robot finished actions")

        except Exception as e:
            self.logger.error(f"Error handling navigation status change: {e}")

    def stop(self, timeout=10.0):
        """Stop the node gracefully and cleanup audio resources"""
        self.logger.info("Stopping Speech Recognition Node...")

        # Set stop event to signal threads to stop
        self.stop_event.set()

        # Stop listening
        self.is_listening = False

        # Stop audio input (this will stop microphone and clear resources)
        if self.audio_input:
            self.audio_input.stop()
            self.audio_input = None

        # Wait for audio thread to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=timeout)

        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break

        self.logger.info("Speech Recognition Node stopped")

        # Call parent stop method
        super().stop(timeout)

    def cleanup(self):
        """Cleanup speech recognition resources"""
        self.logger.info("Cleaning up speech recognition...")

        try:
            self._stop_listening()

            if self.audio_input:
                self.audio_input.cleanup()

        except Exception as e:
            self.logger.error(f"Error during speech recognition cleanup: {e}")

        self.logger.info(f"Speech recognition stopped after {self.recognition_count} recognitions")

    def get_speech_stats(self):
        """Get speech recognition statistics"""
        return {
            "recognition_count": self.recognition_count,
            "error_count": self.error_count,
            "is_listening": self.is_listening,
            "system_mode": self.system_mode,
            "speaking_active": self.speaking_active,
            "last_recognition_time": self.last_recognition_time,
            "audio_status": self.audio_input.get_status() if self.audio_input else None
        }

    def speech_to_text(self, audio, language="en-US"):
        """
        Convert speech audio to text using OpenAI Whisper

        Args:
            audio: Audio data from speech_recognition library
            language: Language code for recognition

        Returns:
            Recognized text or None
        """
        if not audio:
            return None

        self.logger.debug(f"Starting OpenAI transcription for {len(audio.frame_data)} bytes of audio")

        try:
            import openai
            import os
            import datetime

            # Convert speech_recognition AudioData to wav file for OpenAI
            wav_data = audio.get_wav_data()

            # Create audio directory in workspace if it doesn't exist
            audio_dir = os.path.join(os.getcwd(), "audio", "user_wavs")
            os.makedirs(audio_dir, exist_ok=True)

            # Create audio file with timestamp in workspace
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
            audio_filename = f"speech_{timestamp}.wav"
            temp_audio_path = os.path.join(audio_dir, audio_filename)

            with open(temp_audio_path, "wb") as temp_audio:
                temp_audio.write(wav_data)

            self.logger.info(f"Audio file created: {temp_audio_path} ({len(wav_data)} bytes)")

            # Prune user_wavs directory to keep only last 10 files
            self._prune_audio_files(audio_dir, max_files=10)

            try:
                # Use OpenAI Whisper API
                self.logger.debug("Creating OpenAI client and sending transcription request")
                client = openai.OpenAI(api_key=self.openai_api_key)

                with open(temp_audio_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language.split('-')[0] if language else None  # Convert en-US to en
                    )

                self.logger.debug(f"OpenAI transcription completed: '{transcript.text[:50]}...'")
                return transcript.text if transcript.text.strip() else None

            finally:
                # Clean up temporary file - COMMENTED OUT for debugging
                # if os.path.exists(temp_audio_path):
                #     os.unlink(temp_audio_path)
                self.logger.info(f"Audio file preserved for debugging: {temp_audio_path}")

        except Exception as e:
            self.logger.error(f"Error in OpenAI speech-to-text: {e}")
            return None

    def _prune_audio_files(self, audio_dir: str, max_files: int = 5):
        """Keep only the most recent N audio files in the directory"""
        try:
            # Get all .wav files in the directory
            wav_files = []
            for filename in os.listdir(audio_dir):
                if filename.endswith('.wav'):
                    filepath = os.path.join(audio_dir, filename)
                    # Get file modification time
                    mtime = os.path.getmtime(filepath)
                    wav_files.append((mtime, filepath, filename))

            # Sort by modification time (newest first)
            wav_files.sort(reverse=True)

            # Remove files beyond the limit
            if len(wav_files) > max_files:
                files_to_remove = wav_files[max_files:]
                for _, filepath, filename in files_to_remove:
                    try:
                        os.unlink(filepath)
                        self.logger.debug(f"Pruned old audio file: {filename}")
                    except OSError as e:
                        self.logger.warning(f"Failed to remove {filename}: {e}")

                self.logger.info(f"Pruned {len(files_to_remove)} old audio files, keeping {max_files} most recent")

        except Exception as e:
            self.logger.warning(f"Error pruning audio files: {e}")