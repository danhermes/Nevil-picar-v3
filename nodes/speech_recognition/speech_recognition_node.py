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
from nevil_framework.microphone_mutex import microphone_mutex
from nevil_framework.chat_logger import get_chat_logger
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from audio.audio_input import AudioInput

# Import direct command handler
# Add current directory to path for direct_commands import
import sys
import os
_current_dir = os.path.dirname(__file__)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

try:
    from direct_commands import DirectCommandHandler
except ImportError as e:
    print(f"Error importing DirectCommandHandler: {e}")
    raise


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

        # Initialize chat logger for performance tracking
        self.chat_logger = get_chat_logger()

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

        # Direct command handler
        self.direct_command_handler = None

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

            # Initialize direct command handler
            self.direct_command_handler = DirectCommandHandler(self.logger, self.publish)
            self.logger.info("Direct command handler initialized")

            # Start discrete recording thread (v2.0 pattern)
            self.audio_thread = threading.Thread(target=self._discrete_recording_loop, daemon=True)
            self.audio_thread.start()

            self.logger.info("Speech Recognition Node initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {e}")
            raise

    def _listen_with_timeout(self, timeout=10.0, phrase_time_limit=10.0, watchdog_timeout=25.0):
        """
        Wrap listen_for_speech in a thread with timeout.
        If hung (exceeds watchdog_timeout), we know the mutex is stuck in that thread,
        so we can safely replace it and abandon the hung thread.
        """
        import queue
        import threading

        result_queue = queue.Queue()

        def _listen_thread():
            try:
                audio = self.audio_input.listen_for_speech(timeout=timeout, phrase_time_limit=phrase_time_limit)
                result_queue.put(('success', audio))
            except Exception as e:
                result_queue.put(('error', e))

        listen_thread = threading.Thread(target=_listen_thread, daemon=True, name="ListenWatchdog")
        listen_thread.start()
        listen_thread.join(timeout=watchdog_timeout)

        if listen_thread.is_alive():
            # HUNG! The hung thread is stuck in hardware access
            # Try to stop the old AudioInput, then create a new one
            self.logger.error(f"🚨 Microphone hung ({watchdog_timeout}s timeout) - recreating AudioInput...")

            try:
                # Try to stop the old AudioInput (may not fully work if thread is stuck)
                old_audio_input = self.audio_input
                old_audio_input.stop_event.set()  # Signal stop
                old_audio_input.microphone_ready = False  # Mark as not ready

                # Import here to avoid circular dependency
                from audio.audio_input import AudioInput

                # Create new AudioInput (REPLACES old reference, orphaning old instance)
                self.audio_input = AudioInput(logger=self.logger)
                self.logger.info("✓ AudioInput recreated (old instance signaled to stop)")

            except Exception as e:
                self.logger.error(f"Failed to recreate AudioInput: {e}")

            return None

        # Get result
        try:
            status, data = result_queue.get_nowait()
            if status == 'error':
                self.logger.warning(f"Listen error: {data}")
                return None
            return data
        except queue.Empty:
            return None

    def _discrete_recording_loop(self):
        """Discrete recording loop - v2.0 approach: Mic on → Record → Mic off → Process"""
        self.logger.info("Starting discrete recording loop...")

        while not self.stop_event.is_set():
            try:
                if not self.is_listening:
                    time.sleep(0.5)
                    continue

                # Check if system is speaking BEFORE starting to record
                if self.speaking_active:
                    self.logger.debug("Skipping recording - system is speaking")
                    time.sleep(0.5)
                    continue

                # DISCRETE RECORDING CYCLE
                try:
                    # Check if microphone is available (no noisy activities like TTS or navigation)
                    # The microphone mutex allows TTS+navigation to run in parallel
                    # but blocks speech recognition during either one
                    if not microphone_mutex.is_microphone_available():
                        active = microphone_mutex.get_active_activities()
                        self.logger.debug(f"Microphone unavailable, skipping recording (active: {active})")
                        time.sleep(1.0)
                        continue

                    # Double-check speaking status (belt and suspenders approach)
                    if self.speaking_active:
                        self.logger.debug("Skipping recording - system is speaking")
                        time.sleep(0.5)
                        continue

                    self.logger.debug("Starting discrete recording cycle...")

                    # 1. Mic ON - Listen WITHOUT holding busy_state
                    # This allows TTS to interrupt and speak while we're waiting for speech
                    # Wrap in timeout to prevent hardware hang
                    audio = self._listen_with_timeout(
                        timeout=10.0,  # Wait for speech
                        phrase_time_limit=10.0,  # Max recording time
                        watchdog_timeout=25.0  # Watchdog: timeout + phrase_limit + 5s grace
                    )

                    # 2. Mic OFF (happens automatically when listen_for_speech returns)

                    # CRITICAL: Check if TTS/navigation started while we were listening
                    # If so, discard the audio (it's likely Nevil hearing himself or servo noise)
                    if audio and (not microphone_mutex.is_microphone_available() or self.speaking_active):
                        active = microphone_mutex.get_active_activities()
                        self.logger.warning(f"⚠️  Discarding audio - noisy activity started while listening (active: {active})")
                        time.sleep(1.0)  # Wait for activity to finish
                        continue

                    if audio:
                        # 3. PROCESS: Save → STT → AI → TTS (without holding busy_state)
                        self.logger.debug("Processing captured audio...")
                        self._process_audio_discrete(audio)
                    else:
                        self.logger.debug("No speech detected, continuing...")

                except Exception as e:
                    if not self.stop_event.is_set():
                        self.logger.error(f"Error in recording cycle: {e}")
                        time.sleep(2.0)  # Longer pause on error

                # 4. Brief pause before next cycle
                time.sleep(0.5)

            except Exception as e:
                if not self.stop_event.is_set():
                    self.logger.error(f"Error in discrete recording loop: {e}")
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
        # Generate unique conversation ID for this exchange
        conversation_id = self.chat_logger.generate_conversation_id()

        try:
            self.logger.info(f"🎙️  Starting conversation: {conversation_id}")

            # STEP 1: Log REQUEST (audio capture completed)
            with self.chat_logger.log_step(
                conversation_id, "request",
                metadata={"source": "microphone", "device": "default"}
            ):
                # Audio already captured, just log the event
                pass

            # STEP 2: Speech-to-Text with logging
            recognition_start = time.time()
            language = self.recognition_config.get('language', 'en-US')

            with self.chat_logger.log_step(
                conversation_id, "stt",
                input_text="<audio_data>",
                metadata={
                    "model": "whisper-1",
                    "language": language,
                    "audio_format": "wav"
                }
            ) as stt_log:
                text = self.speech_to_text(audio, language)
                stt_log["output_text"] = text if text else "<no_speech_detected>"

            if text and text.strip():
                # DEBUG: Log all recognized speech
                self.logger.info(f"🎤 [SPEECH DEBUG] Recognized: '{text.strip()}'")

                # Check for direct commands BEFORE AI processing
                if self.direct_command_handler and self.direct_command_handler.check_and_handle(text.strip()):
                    self.logger.info("✅ [DIRECT CMD] Command handled, skipping AI processing")
                    return  # Don't process through AI

                # STEP 3: Calculate metrics and publish to AI
                recognition_time = time.time() - recognition_start
                confidence = self._estimate_confidence(text, recognition_time)

                voice_command_data = {
                    "text": text.strip(),
                    "confidence": confidence,
                    "timestamp": time.time(),
                    "language": language,
                    "duration": recognition_time,
                    "conversation_id": conversation_id  # Pass to next step
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
                whisper_start = time.time()
                self.logger.info(f"[STT TIMING] Calling OpenAI Whisper API at {whisper_start:.3f}")
                self.logger.debug("Creating OpenAI client and sending transcription request")
                client = openai.OpenAI(api_key=self.openai_api_key)

                with open(temp_audio_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language.split('-')[0] if language else None  # Convert en-US to en
                    )

                whisper_end = time.time()
                whisper_duration = whisper_end - whisper_start
                self.logger.info(f"[STT TIMING] OpenAI Whisper API completed in {whisper_duration:.3f}s")
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