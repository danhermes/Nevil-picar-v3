"""
Speech Synthesis Node for Nevil v3.0

Uses v1.0 Music() playback VERBATIM and exact TTS pipeline.
NO modifications to working audio output - preserves defaults exactly.
"""

import time
import os
import queue
import threading
from nevil_framework.base_node import NevilNode
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

            # Create TTS directory
            os.makedirs("./tts", exist_ok=True)

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
        try:
            text = tts_request.get("text", "")
            voice = tts_request.get("voice", self.tts_config.get("default_voice", "onyx"))
            volume_db = self.audio_config.get("volume_db", -10)

            if not text.strip():
                self.logger.warning("Empty text for TTS, skipping")
                return

            self.logger.info(f"Processing TTS: '{text}' (voice: {voice})")

            with self.speaking_lock:
                self.is_speaking = True
                self.current_text = text

            # Publish speaking status
            self._publish_speaking_status(True, text, voice)

            synthesis_start = time.time()

            # Use v1.0 EXACT TTS pipeline via AudioOutput
            success = self.audio_output.generate_and_play_tts(
                message=text,
                openai_helper=self,  # Pass self directly as openai_helper
                volume_db=volume_db,
                voice=voice
            )

            synthesis_time = time.time() - synthesis_start

            if success:
                self.logger.info(f"✓ TTS completed: '{text}' in {synthesis_time:.3f}s")
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

            # Publish speaking status
            self._publish_speaking_status(False, "", "")

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

            # Create TTS request
            tts_request = {
                "text": text.strip(),
                "voice": voice,
                "speed": speed,
                "source": message.source_node,
                "timestamp": message.timestamp
            }

            # Add to priority queue (lower priority number = higher priority)
            try:
                self.tts_queue.put_nowait((priority, message.timestamp, tts_request))
                self.logger.debug(f"Queued TTS request: '{text}' (priority: {priority})")

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
        Convert text to speech using OpenAI TTS API

        Args:
            text: Text to convert to speech
            output_file: Output file path
            voice: Voice to use (default: onyx)
            response_format: Output format (default: wav)

        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        self.logger.debug(f"Starting OpenAI TTS for text: '{text[:50]}...'")

        try:
            import openai

            # Create OpenAI client
            client = openai.OpenAI(api_key=self.openai_api_key)

            # Generate speech
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format=response_format
            )

            # Save to file
            with open(output_file, "wb") as f:
                f.write(response.content)

            self.logger.debug(f"OpenAI TTS completed: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error in OpenAI text-to-speech: {e}")
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