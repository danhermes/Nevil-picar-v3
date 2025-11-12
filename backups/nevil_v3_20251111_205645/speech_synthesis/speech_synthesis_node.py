"""
Speech Synthesis Node for Nevil v3.0

Uses v1.0 Music() playback VERBATIM and exact TTS pipeline.
NO modifications to working audio output - preserves defaults exactly.
"""

import time
import os
import queue
import threading
import warnings
from dotenv import load_dotenv
from nevil_framework.base_node import NevilNode
from nevil_framework.chat_logger import get_chat_logger

# Load environment variables from .env file
load_dotenv()

# Suppress ALSA warnings if environment variable is set
if os.getenv('HIDE_ALSA_LOGGING', '').lower() == 'true':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="ALSA")

# Set ALSA verbosity to 0 if specified
if os.getenv('ALSA_VERBOSITY') == '0':
    os.environ['ALSA_VERBOSITY'] = '0'
from nevil_framework.busy_state import busy_state
from nevil_framework.microphone_mutex import microphone_mutex
from audio.audio_output import AudioOutput


class SpeechSynthesisNode(NevilNode):
    """
    Speech Synthesis Node using v1.0 Music() playback VERBATIM.

    Features:
    - v1.0 EXACT Music() initialization and playback (DO NOT MODIFY)
    - v1.0 EXACT TTS pipeline: OpenAI API → sox_volume → Music()
    - Default audio devices only (no manual device specification)
    - Queue-based text processing for multiple requests
    - Declarative messaging via .messages configuration
    """

    def __init__(self):
        super().__init__("speech_synthesis")

        # Initialize chat logger for performance tracking
        self.chat_logger = get_chat_logger()

        # Load OpenAI API key for TTS
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            self.logger.warning("No OpenAI API key found - speech synthesis may not work")

        # Initialize OpenAI helper (will be set by launcher or manually)
        self.openai_helper = None

        # Audio output using v1.0 Music() VERBATIM
        self.audio_output = None

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.audio_config = config.get('audio', {})
        self.tts_config = config.get('tts', {})
        self.performance_config = config.get('performance', {})

        # Load TTS provider using factory pattern
        from audio.tts_providers.factory import get_tts_provider

        config_model = self.tts_config.get('model', 'tts-1')
        self.tts_model = os.getenv('NEVIL_TTS', config_model)

        try:
            self.tts_provider = get_tts_provider(self.tts_model)
            if os.getenv('NEVIL_TTS'):
                self.logger.info(f"TTS Provider: {self.tts_provider.get_provider_name()} (from NEVIL_TTS env var)")
            else:
                self.logger.info(f"TTS Provider: {self.tts_provider.get_provider_name()} (from .messages config)")
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS provider: {e}")
            self.tts_provider = None

        # TTS processing queue (like v2.0 but simpler)
        max_queue_size = self.performance_config.get('max_queue_size', 5)
        self.tts_queue = queue.PriorityQueue(maxsize=max_queue_size)

        # State management
        self.is_speaking = False
        self.current_text = ""
        self.speaking_lock = threading.Lock()

        # Performance tracking
        self.synthesis_count = 0
        self.error_count = 0
        self.last_synthesis_time = 0

    def initialize(self):
        """Initialize speech synthesis components"""
        self.logger.info("Initializing Speech Synthesis Node...")

        try:
            # Initialize audio output with v1.0 Music() VERBATIM
            self.audio_output = AudioOutput()

            # Initialize OpenAI helper if we have API key
            if self.openai_api_key:
                # For now, we'll implement OpenAI calls directly
                # Will integrate v1.0 OpenAI helper in Phase 2
                self.logger.info("OpenAI API key available for speech synthesis")
                self.openai_helper = self  # Temporary - use self for OpenAI calls
            else:
                self.logger.error("Cannot initialize speech synthesis without OpenAI API key")
                return

            # Log our configuration
            self.logger.info("Speech Synthesis Configuration:")
            self.logger.info(f"  Default voice: {self.tts_config.get('default_voice', 'onyx')}")
            self.logger.info(f"  Volume: {self.audio_config.get('volume_db', -10)} dB")
            self.logger.info(f"  Format: {self.tts_config.get('response_format', 'wav')}")
            self.logger.info(f"  Queue size: {self.tts_queue.maxsize}")

            # Ensure audio directories exist (handled by audio_utils)

            # Publish initial audio output status
            self._publish_audio_output_status()

            self.logger.info("Speech Synthesis Node initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize speech synthesis: {e}")
            raise

    def main_loop(self):
        """Main processing loop - handle TTS queue"""
        try:
            # Process TTS queue
            try:
                # Get next TTS request with timeout
                priority, timestamp, tts_request = self.tts_queue.get(timeout=1.0)
                self._process_tts_request(tts_request)
                self.tts_queue.task_done()

            except queue.Empty:
                # No TTS requests to process
                pass

            # Brief pause to prevent busy waiting
            time.sleep(0.01)

        except Exception as e:
            self.logger.error(f"Error in speech synthesis main loop: {e}")
            self.error_count += 1
            time.sleep(1.0)

    def _process_tts_request(self, tts_request):
        """Process TTS request using v1.0 EXACT pipeline"""
        text = tts_request.get("text", "")
        conversation_id = tts_request.get("conversation_id")
        queued_at = tts_request.get("queued_at", time.time())

        processing_start = time.time()
        queue_wait = processing_start - queued_at
        self.logger.info(f"[TTS TIMING] Processing TTS at {processing_start:.3f} (waited {queue_wait:.3f}s in queue)")

        if not text.strip():
            self.logger.warning("Empty text for TTS, skipping")
            return

        # Fallback if conversation_id not provided
        if not conversation_id:
            conversation_id = self.chat_logger.generate_conversation_id()
            self.logger.warning(f"No conversation_id in TTS request, generated: {conversation_id}")

        # Acquire busy state for speaking - TTS can interrupt actions!
        # DISABLED: Commenting out busy_state to allow speech and actions simultaneously
        acquire_start = time.time()
        # self.logger.info(f"[TTS TIMING] Acquiring busy_state at {acquire_start:.3f}...")
        # if not busy_state.acquire("speaking", timeout=5.0, can_interrupt=True, interruptible=False):
        #     self.logger.error("Could not acquire busy state for TTS, aborting")
        #     return

        # NEW: Use microphone mutex instead - allows parallel TTS+navigation but blocks speech recognition
        microphone_mutex.acquire_noisy_activity("speaking")

        acquire_end = time.time()
        busy_wait = acquire_end - acquire_start
        # self.logger.info(f"[TTS TIMING] Acquired busy_state after {busy_wait:.3f}s")

        try:
            voice = tts_request.get("voice", self.tts_config.get("default_voice", "onyx"))
            volume_db = self.audio_config.get("volume_db", -10)

            self.logger.info(f"Processing TTS: '{text}' (conv: {conversation_id})")

            with self.speaking_lock:
                self.is_speaking = True
                self.current_text = text

            # Publish speaking status
            self._publish_speaking_status(True, text, voice)

            # STEP 4: Log TTS (combined for backward compatibility)
            tts_metadata = {
                "voice": voice,
                "model": self.tts_model,  # Log actual TTS model used
                "volume_db": volume_db,
                "queue_wait_ms": queue_wait * 1000,  # Time in queue
                "busy_wait_ms": busy_wait * 1000  # Time waiting for busy_state
            }

            with self.chat_logger.log_step(
                conversation_id, "tts",
                input_text=text[:200],  # Limit input text length
                metadata=tts_metadata
            ) as tts_log:
                generation_start = time.time()
                result = self.audio_output.generate_and_play_tts(
                    message=text,
                    openai_helper=self,
                    volume_db=volume_db,
                    voice=voice
                )

                # Unpack result: (success, generation_time, playback_time)
                if isinstance(result, tuple):
                    success, gen_time, play_time = result
                    # Add timing breakdown to metadata
                    tts_metadata["generation_ms"] = gen_time * 1000
                    tts_metadata["playback_ms"] = play_time * 1000
                else:
                    # Backwards compatibility if old code returns just boolean
                    success = result

                total_tts_time = time.time() - generation_start
                tts_log["output_text"] = "<audio_file>" if success else "<tts_failed>"
                # Note: total TTS duration includes generation + playback, logged automatically
                # The breakdown is now stored in metadata for analytics

            # STEP 5: Log RESPONSE (playback completion)
            with self.chat_logger.log_step(
                conversation_id, "response",
                input_text="<audio_file>",
                metadata={
                    "success": success,
                    "device": "speaker"
                }
            ) as resp_log:
                resp_log["output_text"] = "playback_complete" if success else "playback_failed"

            if success:
                self.logger.info(f"✓ Conversation complete: {conversation_id}")
                self.synthesis_count += 1
                self.last_synthesis_time = time.time()
            else:
                self.logger.error(f"TTS failed for: '{text}'")
                self.error_count += 1

        except Exception as e:
            self.logger.error(f"Error processing TTS request: {e}")
            self.error_count += 1

        finally:
            # Always clear speaking status
            with self.speaking_lock:
                self.is_speaking = False
                self.current_text = ""

            # STEP 6: Log sleep delay (audio buffer clearing time)
            with self.chat_logger.log_step(
                conversation_id, "sleep",
                input_text="post_tts_delay",
                metadata={
                    "reason": "audio_buffer_clear",
                    "delay_ms": 1000
                }
            ) as sleep_log:
                # Reduced to 1 second to improve response time
                # Still prevents microphone from picking up residual audio
                time.sleep(1.0)
                sleep_log["output_text"] = "delay_complete"

            # Publish speaking status
            self._publish_speaking_status(False, "", "")

            # Release busy state
            # DISABLED: Commenting out busy_state to allow speech and actions simultaneously
            # busy_state.release()
            # self.logger.debug("Released busy state after TTS")

            # NEW: Release microphone mutex
            microphone_mutex.release_noisy_activity("speaking")

    def _publish_speaking_status(self, speaking, text, voice):
        """Publish speaking status change"""
        status_data = {
            "speaking": speaking,
            "text": text,
            "voice": voice,
            "progress": 1.0 if not speaking else 0.0,
            "timestamp": time.time()
        }
        self.publish("speaking_status", status_data)

    def _publish_audio_output_status(self):
        """Publish audio output status"""
        status_data = {
            "available": self.audio_output is not None,
            "device": "system_default_music",
            "volume": 1.0  # Music() handles volume internally
        }
        self.publish("audio_output_status", status_data)

    def stop(self, timeout=10.0):
        """Stop the node gracefully and dispose of Music() resources"""
        self.logger.info("Stopping Speech Synthesis Node...")

        # Stop any active TTS processing
        if hasattr(self, 'is_speaking'):
            with self.speaking_lock:
                self.is_speaking = False

        # Clear TTS queue
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break

        # Dispose of audio output (this will dispose of Music() properly)
        if self.audio_output:
            self.audio_output.stop()
            self.audio_output = None

        self.logger.info("Speech Synthesis Node stopped")

        # Call parent stop method
        super().stop(timeout)

    # Declaratively configured callback methods (from .messages file)

    def on_text_response(self, message):
        """Handle text response messages (declaratively configured callback)"""
        try:
            text = message.data.get("text", "")
            voice = message.data.get("voice", self.tts_config.get("default_voice", "onyx"))
            priority = message.data.get("priority", 100)
            speed = message.data.get("speed", 1.0)

            if not text.strip():
                self.logger.warning("Received empty text response, ignoring")
                return

            # Create TTS request with conversation_id
            tts_request = {
                "text": text.strip(),
                "voice": voice,
                "speed": speed,
                "source": message.source_node,
                "timestamp": message.timestamp,
                "conversation_id": message.data.get("conversation_id"),  # Pass through
                "queued_at": time.time()  # Track when queued
            }

            # Add to priority queue (lower priority number = higher priority)
            try:
                self.tts_queue.put_nowait((priority, message.timestamp, tts_request))
                self.logger.info(f"[TTS TIMING] Queued TTS at {tts_request['queued_at']:.3f}: '{text[:50]}'")

            except queue.Full:
                self.logger.warning(f"TTS queue full, dropping request: '{text}'")

        except Exception as e:
            self.logger.error(f"Error handling text response: {e}")

    def on_system_mode_change(self, message):
        """Handle system mode changes (declaratively configured callback)"""
        try:
            mode = message.data.get("mode", "idle")
            self.logger.debug(f"System mode changed to: {mode}")

            # Stop current synthesis if switching away from speaking mode
            if mode != "speaking" and self.is_speaking:
                self.logger.info("Stopping current synthesis due to mode change")
                if self.audio_output:
                    self.audio_output.stop_playback()

        except Exception as e:
            self.logger.error(f"Error handling system mode change: {e}")

    def on_tts_request(self, message):
        """Handle direct TTS requests from automatic mode (declaratively configured callback)"""
        try:
            text = message.data.get("text", "")
            voice = message.data.get("voice", self.tts_config.get("default_voice", "onyx"))
            priority = message.data.get("priority", 100)

            if not text.strip():
                self.logger.warning("Received empty text for TTS request, ignoring")
                return

            # Create TTS request with conversation_id
            tts_request = {
                "text": text.strip(),
                "voice": voice,
                "speed": 1.0,
                "source": message.source_node,
                "timestamp": message.timestamp,
                "conversation_id": message.data.get("conversation_id")  # Pass through
            }

            # Add to priority queue (lower priority number = higher priority)
            try:
                self.tts_queue.put_nowait((priority, message.timestamp, tts_request))
                self.logger.debug(f"Queued TTS request from auto mode: '{text}' (priority: {priority})")

            except queue.Full:
                self.logger.warning(f"TTS queue full, dropping auto mode request: '{text}'")

        except Exception as e:
            self.logger.error(f"Error handling TTS request: {e}")

    def on_sound_effect(self, message):
        """Handle sound effect playback requests (declaratively configured callback)"""
        try:
            effect = message.data.get("effect", "")
            volume = message.data.get("volume", 100)
            priority = message.data.get("priority", 50)

            if not effect:
                self.logger.warning("Received empty sound effect request")
                return

            self.logger.info(f"🔊 Playing sound effect: {effect} (volume: {volume})")

            # Import sound mappings from action_helper
            from nodes.navigation.action_helper import SOUND_MAPPINGS

            # Map effect names to full sound file paths
            sound_files = {
                name: f"/home/dan/Nevil-picar-v3/audio/sounds/{filename}"
                for name, filename in SOUND_MAPPINGS.items()
            }

            sound_file = sound_files.get(effect)
            if not sound_file:
                self.logger.error(f"Unknown sound effect: {effect}")
                return

            # Check if file exists
            if not os.path.exists(sound_file):
                self.logger.error(f"Sound file not found: {sound_file}")
                return

            # Play the sound using the audio output's Music() instance
            if self.audio_output and self.audio_output.music:
                # Acquire busy state for sound playback
                # DISABLED: Commenting out busy_state to allow sounds and actions simultaneously
                # if not busy_state.acquire("sound_effect"):
                #     self.logger.warning("Could not acquire busy state for sound effect")
                #     return

                # NEW: Use microphone mutex - allows parallel sounds+navigation but blocks speech recognition
                microphone_mutex.acquire_noisy_activity("sound_effect")

                try:
                    self.audio_output.music.sound_play(sound_file, volume)
                    # Wait for sound to finish
                    while self.audio_output.music.pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    self.logger.info(f"✓ Sound effect completed: {effect}")
                finally:
                    # DISABLED: Commenting out busy_state to allow sounds and actions simultaneously
                    # busy_state.release()

                    # NEW: Release microphone mutex
                    microphone_mutex.release_noisy_activity("sound_effect")
            else:
                self.logger.error("Audio output not available for sound effects")

        except Exception as e:
            self.logger.error(f"Error playing sound effect: {e}")

    def cleanup(self):
        """Cleanup speech synthesis resources"""
        self.logger.info("Cleaning up speech synthesis...")

        try:
            # Stop any current playback
            if self.audio_output:
                self.audio_output.stop_playback()
                self.audio_output.cleanup()

            # Clear TTS queue
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break

        except Exception as e:
            self.logger.error(f"Error during speech synthesis cleanup: {e}")

        self.logger.info(f"Speech synthesis stopped after {self.synthesis_count} syntheses")

    def text_to_speech(self, text, output_file, voice="onyx", response_format="wav"):
        """
        Convert text to speech using configured TTS provider

        Args:
            text: Text to convert to speech
            output_file: Output file path
            voice: Voice to use (default: onyx)
            response_format: Output format (default: wav) - ignored by some providers

        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        if not self.tts_provider:
            self.logger.error("No TTS provider available")
            return False

        self.logger.debug(f"Starting TTS ({self.tts_provider.get_provider_name()}) for text: '{text[:50]}...'")

        try:
            success = self.tts_provider.generate_speech(text, output_file, voice)
            if success:
                self.logger.debug(f"TTS completed: {output_file}")
            else:
                self.logger.error(f"TTS generation failed for provider: {self.tts_provider.get_provider_name()}, file: {output_file}")
            return success

        except Exception as e:
            self.logger.error(f"Error in text-to-speech ({self.tts_provider.get_provider_name()}): {e}", exc_info=True)
            return False

    def get_synthesis_stats(self):
        """Get speech synthesis statistics"""
        return {
            "synthesis_count": self.synthesis_count,
            "error_count": self.error_count,
            "is_speaking": self.is_speaking,
            "current_text": self.current_text,
            "queue_size": self.tts_queue.qsize(),
            "last_synthesis_time": self.last_synthesis_time,
            "audio_status": self.audio_output.get_status() if self.audio_output else None
        }