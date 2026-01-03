"""
Speech Synthesis Node for Nevil v2.2 - Realtime API Streaming TTS

⚠️ CRITICAL: Uses EXACT same playback as v3.0 (robot_hat.Music())

Changes from v3.0:
- Audio generation: OpenAI Realtime API streaming (200-400ms) - FASTER
- Buffers streaming audio chunks from response.audio.delta events
- Saves complete audio to WAV file on response.audio.done

Preserved from v3.0:
- Audio playback: robot_hat.Music() via AudioOutput class - UNCHANGED
- File: audio/audio_output.py - UNTOUCHED
- Hardware: HiFiBerry DAC, GPIO pin 20 - IDENTICAL
- WAV file format: PCM16, 24kHz mono - SAME

Architecture:
    Realtime API streaming → Buffer chunks → Save to WAV → robot_hat.Music() plays
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^             ^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
    NEW (faster generation)                 SAME           SAME (hardware playback)

Translation date: 2025-11-11
Status: Production-ready
"""

import time
import os
import threading
import wave
import base64
import warnings
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from nevil_framework.base_node import NevilNode
from nevil_framework.chat_logger import get_chat_logger
from nevil_framework.gesture_injector import get_gesture_injector

# Load environment variables
load_dotenv()

# Suppress ALSA warnings if environment variable is set
if os.getenv('HIDE_ALSA_LOGGING', '').lower() == 'true':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="ALSA")

# Set ALSA verbosity to 0 if specified
if os.getenv('ALSA_VERBOSITY') == '0':
    os.environ['ALSA_VERBOSITY'] = '0'

from nevil_framework.microphone_mutex import microphone_mutex

# ⚠️ CRITICAL: Import EXACT audio output class from v3.0
# This contains robot_hat.Music() - DO NOT REPLACE
from audio.audio_output import AudioOutput
from audio.audio_utils import generate_tts_filename


class SpeechSynthesisNode22(NevilNode):
    """
    Speech Synthesis Node using OpenAI Realtime API for streaming TTS.

    ⚠️ CRITICAL: Uses EXACT same playback method as v3.0 (robot_hat.Music())

    Key Features:
    - Streaming audio generation from Realtime API (FASTER)
    - Buffer audio chunks in memory during streaming
    - Save complete audio to WAV file when done
    - Play via robot_hat.Music() (IDENTICAL to v3.0)
    - Thread-safe buffer management
    - Declarative messaging via .messages configuration

    Event Flow:
    1. Subscribe to text_response topic
    2. On text: request audio from Realtime API
    3. Buffer chunks from response.audio.delta events
    4. On response.audio.done: save WAV → play via robot_hat.Music()
    5. Publish speaking_status throughout
    """

    def __init__(self):
        # Initialize with correct config path
        super().__init__(
            "speech_synthesis_realtime",
            config_path="nodes/speech_synthesis_realtime/.messages"
        )

        # Initialize chat logger for performance tracking
        self.chat_logger = get_chat_logger()

        # ⚠️ CRITICAL: Use EXACT v3.0 audio output class
        # Contains robot_hat.Music() - DO NOT REPLACE
        self.audio_output: Optional[AudioOutput] = None

        # Realtime API connection manager (set by launcher)
        self.realtime_manager = None

        # Audio streaming buffer - collect chunks here
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        self.current_item_id: Optional[str] = None
        self.current_conversation_id: Optional[str] = None

        # Transcript buffer for text alongside audio
        self.transcript_buffer = []
        self.transcript_lock = threading.Lock()

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.audio_config = config.get('audio', {})
        self.tts_config = config.get('tts', {})

        # State management
        self.is_speaking = False
        self.current_text = ""
        self.speaking_lock = threading.Lock()
        self.mutex_acquired = False  # Track if we've muted the mic for this TTS session

        # Performance tracking
        self.synthesis_count = 0
        self.error_count = 0
        self.last_synthesis_time = 0

        self.logger.info("Speech Synthesis Node22 (Realtime) initialized")

    def initialize(self):
        """Initialize speech synthesis components and register event handlers"""
        self.logger.info("Initializing Speech Synthesis Node22 (Realtime)...")

        try:
            # ⚠️ CRITICAL: Initialize audio output with v1.0 Music() VERBATIM
            # This is the EXACT same AudioOutput class used in v3.0
            self.audio_output = AudioOutput()
            self.logger.info("AudioOutput initialized with robot_hat.Music()")

            # Register Realtime API event handlers
            if self.realtime_manager:
                self._register_realtime_handlers()
                self.logger.info("Registered Realtime API event handlers")
            else:
                self.logger.warning("No realtime_manager available - will register later")

            # Log configuration
            self.logger.info("Speech Synthesis Node22 Configuration:")
            self.logger.info(f"  Default voice: {self.tts_config.get('default_voice', 'alloy')}")
            self.logger.info(f"  Volume: {self.audio_config.get('volume_db', -10)} dB")
            self.logger.info(f"  Output format: PCM16 24kHz mono")
            self.logger.info(f"  Playback: robot_hat.Music() (EXACT v3.0)")

            # Publish initial status
            self._publish_audio_output_status()

            self.logger.info("Speech Synthesis Node22 initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize speech synthesis: {e}")
            raise

    def set_realtime_manager(self, realtime_manager):
        """Set the realtime connection manager and register event handlers"""
        self.realtime_manager = realtime_manager
        if self.realtime_manager:
            self._register_realtime_handlers()
            self.logger.info("Realtime manager set and event handlers registered")

    def _register_realtime_handlers(self):
        """Register event handlers for Realtime API audio events"""
        if not self.realtime_manager:
            return

        # Register handlers using the event handler system
        event_handlers = self.realtime_manager.event_handler

        # Audio streaming events
        event_handlers.on("response.audio.delta", self._on_audio_delta)
        event_handlers.on("response.audio.done", self._on_audio_done)

        # Transcript events (optional - for monitoring)
        event_handlers.on("response.audio_transcript.delta", self._on_transcript_delta)
        event_handlers.on("response.audio_transcript.done", self._on_transcript_done)

        # Response lifecycle events
        event_handlers.on("response.output_item.added", self._on_output_item_added)
        event_handlers.on("response.done", self._on_response_done)

        self.logger.debug("Registered Realtime API event handlers for streaming TTS")

    def _on_output_item_added(self, event: Dict[str, Any]):
        """Track when a new output item is created"""
        try:
            item = event.get('item', {})
            item_id = item.get('id')
            item_type = item.get('type')

            if item_type == 'message' and item.get('role') == 'assistant':
                with self.buffer_lock:
                    self.current_item_id = item_id
                    self.audio_buffer.clear()

                with self.transcript_lock:
                    self.transcript_buffer.clear()

                # ⚠️ CRITICAL: Acquire mutex IMMEDIATELY when assistant response starts
                # This happens BEFORE audio streaming begins, preventing any audio from
                # being sent to the API while Nevil is speaking
                from nevil_framework.microphone_mutex import microphone_mutex

                if not self.mutex_acquired:
                    microphone_mutex.acquire_noisy_activity("speaking")
                    self.mutex_acquired = True
                    self.logger.info("🔇 Microphone muted - Nevil starting to speak (output_item_added)")

                # Publish speaking status immediately
                self._publish_speaking_status(True, "", "")
                self.logger.info("📢 Published speaking_status=True at response start")

                self.logger.debug(f"Started new audio output item: {item_id}")

        except Exception as e:
            self.logger.error(f"Error in _on_output_item_added: {e}")

    def _on_audio_delta(self, event: Dict[str, Any]):
        """
        Receive streaming audio chunk from Realtime API.
        Buffer it in memory - do NOT play yet.

        ⚠️ CRITICAL: This only buffers - playback uses robot_hat.Music() later

        Note: Mutex should already be acquired in on_text_response() before this is called
        """
        try:
            # Extract base64 encoded audio chunk
            audio_b64 = event.get('delta')
            if not audio_b64:
                return

            # DIAGNOSTIC: Log first chunk to confirm event handler is being called
            if len(self.audio_buffer) == 0:
                self.logger.info(f"🎵 FIRST audio delta received - event handler is working!")

            # Decode from base64 to PCM16 bytes
            audio_chunk = base64.b64decode(audio_b64)

            # Add to buffer
            with self.buffer_lock:
                self.audio_buffer.append(audio_chunk)

            # Safety check: Mutex should already be acquired in _on_output_item_added()
            if not self.mutex_acquired:
                from nevil_framework.microphone_mutex import microphone_mutex
                microphone_mutex.acquire_noisy_activity("speaking")
                self.mutex_acquired = True
                self.logger.error("❌ CRITICAL: Mutex not acquired before audio delta! This indicates event ordering issue.")

            self.logger.debug(f"Buffered audio chunk: {len(audio_chunk)} bytes (total: {sum(len(c) for c in self.audio_buffer)} bytes)")

        except Exception as e:
            self.logger.error(f"Error buffering audio chunk: {e}")

    def _on_transcript_delta(self, event: Dict[str, Any]):
        """Buffer transcript text alongside audio"""
        try:
            delta = event.get('delta', '')
            if delta:
                with self.transcript_lock:
                    self.transcript_buffer.append(delta)

        except Exception as e:
            self.logger.error(f"Error in transcript delta: {e}")

    def _on_transcript_done(self, event: Dict[str, Any]):
        """Log complete transcript"""
        try:
            with self.transcript_lock:
                transcript = ''.join(self.transcript_buffer)
                if transcript:
                    self.logger.info(f"Transcript: {transcript}")

        except Exception as e:
            self.logger.error(f"Error in transcript done: {e}")

    def _on_audio_done(self, event: Dict[str, Any]):
        """
        All audio received. Now save to WAV and play.

        ⚠️ CRITICAL: This is where we use EXISTING playback method (robot_hat.Music())
        """
        try:
            processing_start = time.time()

            # 1. Concatenate all buffered chunks
            with self.buffer_lock:
                if not self.audio_buffer:
                    self.logger.warning("Audio done but buffer is empty")
                    return

                complete_audio = b''.join(self.audio_buffer)
                buffer_size = len(complete_audio)
                self.audio_buffer.clear()

            # 2. Get conversation context and transcript
            conversation_id = self.current_conversation_id
            if not conversation_id:
                conversation_id = self.chat_logger.generate_conversation_id()
                self.logger.warning(f"No conversation_id in TTS, generated: {conversation_id}")

            # Get transcript for logging
            with self.transcript_lock:
                transcript = ''.join(self.transcript_buffer)
                self.transcript_buffer.clear()

            # Log what Nevil is about to say
            duration = buffer_size / (24000 * 2)
            self.logger.info(f"🗣️  NEVIL SAYS: '{transcript}' ({duration:.1f}s, {buffer_size} bytes)")

            # 3. Save to WAV file (REQUIRED for robot_hat.Music())
            volume_db = self.audio_config.get("volume_db", -10)
            wav_file, _ = generate_tts_filename(volume_db=volume_db)

            save_start = time.time()
            self._save_pcm16_to_wav(complete_audio, wav_file, sample_rate=24000)
            save_time = time.time() - save_start

            self.logger.info(f"Saved audio to: {wav_file} ({save_time*1000:.1f}ms)")

            # 4. Microphone mutex already acquired in _on_audio_delta (first chunk)
            # No need to acquire again here

            try:
                with self.speaking_lock:
                    self.is_speaking = True
                    self.current_text = transcript

                # Publish speaking status (if not already done in _on_audio_delta)
                voice = self.tts_config.get("default_voice", "alloy")
                if not self.mutex_acquired:
                    # Fallback: if somehow mutex wasn't acquired yet
                    from nevil_framework.microphone_mutex import microphone_mutex
                    microphone_mutex.acquire_noisy_activity("speaking")
                    self.mutex_acquired = True
                    self._publish_speaking_status(True, transcript, voice)

                # 5. ⚠️ CRITICAL: Use EXACT existing playback method
                # This is the SAME code path as v3.0 speech_synthesis_node
                self.audio_output.tts_file = wav_file
                with self.audio_output.speech_lock:
                    self.audio_output.speech_loaded = True

                # Log TTS step (for compatibility with chat logger)
                tts_metadata = {
                    "voice": voice,
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "volume_db": volume_db,
                    "buffer_size_bytes": buffer_size,
                    "save_time_ms": save_time * 1000
                }

                with self.chat_logger.log_step(
                    conversation_id, "tts",
                    input_text=transcript[:200] if transcript else "<streaming_audio>",
                    metadata=tts_metadata
                ) as tts_log:

                    # 🎭 GESTURE INJECTION: Inject gestures simultaneously with speech
                    # This runs when audio is ready to play, leveraging independent node architecture
                    if transcript:
                        try:
                            injector = get_gesture_injector()
                            auto_gestures = injector.analyze_and_inject(
                                transcript,
                                min_gestures=3,
                                max_gestures=6
                            )

                            if auto_gestures:
                                self.logger.info(f"🎭 Injecting {len(auto_gestures)} gestures: {auto_gestures}")
                                self.publish("robot_action", {
                                    "actions": auto_gestures,
                                    "source_text": transcript[:50],
                                    "mood": "neutral",
                                    "priority": 100,
                                    "timestamp": time.time()
                                })
                            else:
                                self.logger.info("🎭 No gestures generated for this response")
                        except Exception as e:
                            self.logger.error(f"❌ Gesture injection failed: {e}")

                    playback_start = time.time()

                    # This internally calls play_audio_file(self.music, wav_file)
                    # which uses robot_hat.Music() - DO NOT CHANGE
                    self.logger.info(f"🔊 Calling Music().play() for file: {wav_file}")
                    success = self.audio_output.play_loaded_speech()
                    self.logger.info(f"🔊 Music().play() returned: {success}")

                    playback_time = time.time() - playback_start

                    # Update metadata with timing
                    tts_metadata["playback_ms"] = playback_time * 1000
                    tts_log["output_text"] = "<audio_file>" if success else "<tts_failed>"

                # Log response completion
                with self.chat_logger.log_step(
                    conversation_id, "response",
                    input_text="<audio_file>",
                    metadata={"success": success, "device": "speaker"}
                ) as resp_log:
                    resp_log["output_text"] = "playback_complete" if success else "playback_failed"

                if success:
                    total_time = time.time() - processing_start
                    self.logger.info(f"✓ Playback complete (robot_hat.Music()) in {total_time:.3f}s")
                    self.synthesis_count += 1
                    self.last_synthesis_time = time.time()
                else:
                    self.logger.error("❌ Playback failed")
                    self.error_count += 1

            finally:
                # Always clear speaking status
                with self.speaking_lock:
                    self.is_speaking = False
                    self.current_text = ""

                # CRITICAL: Wait for audio playback to complete + minimal echo suppression
                # We MUST wait for the physical speaker to finish to prevent feedback loop
                # But we do this in a non-blocking way for the API response flow
                wait_start = time.time()
                max_wait = 30.0  # Safety timeout for extremely long responses

                with self.chat_logger.log_step(
                    conversation_id, "sleep",
                    input_text="wait_for_playback_completion",
                    metadata={"reason": "prevent_acoustic_feedback"}
                ) as sleep_log:
                    # Wait for audio playback to finish
                    while self.audio_output.is_playing() and (time.time() - wait_start) < max_wait:
                        time.sleep(0.1)

                    playback_duration = time.time() - wait_start

                    # Add minimal post-playback delay for room echo dissipation
                    time.sleep(0.3)  # Short delay after playback completes

                    total_wait = time.time() - wait_start
                    sleep_log["output_text"] = f"playback_complete_after_{total_wait:.2f}s"
                    sleep_log["playback_duration_ms"] = int(playback_duration * 1000)
                    sleep_log["total_wait_ms"] = int(total_wait * 1000)

                # Publish speaking status
                self._publish_speaking_status(False, "", "")

                # Release microphone mutex and reset flag
                if self.mutex_acquired:
                    from nevil_framework.microphone_mutex import microphone_mutex
                    microphone_mutex.release_noisy_activity("speaking")
                    self.mutex_acquired = False
                    self.logger.info("🎤 Microphone unmuted - TTS complete")

        except Exception as e:
            self.logger.error(f"Error in audio done handler: {e}", exc_info=True)
            self.error_count += 1

            # Ensure cleanup on error
            with self.speaking_lock:
                self.is_speaking = False
            if self.mutex_acquired:
                from nevil_framework.microphone_mutex import microphone_mutex
                microphone_mutex.release_noisy_activity("speaking")
                self.mutex_acquired = False

    def _on_response_done(self, event: Dict[str, Any]):
        """Response fully complete - cleanup"""
        try:
            with self.buffer_lock:
                self.current_item_id = None
                self.audio_buffer.clear()

            self.logger.debug("Response complete, buffers cleared")

        except Exception as e:
            self.logger.error(f"Error in response done: {e}")

    def _save_pcm16_to_wav(self, pcm_data: bytes, output_file: str, sample_rate: int = 24000):
        """
        Save raw PCM16 bytes to WAV file.

        Args:
            pcm_data: Raw PCM16 audio bytes from Realtime API
            output_file: Output WAV file path
            sample_rate: Sample rate (default 24000 Hz)
        """
        try:
            with wave.open(output_file, 'wb') as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16-bit (2 bytes per sample)
                wav.setframerate(sample_rate)
                wav.writeframes(pcm_data)

        except Exception as e:
            self.logger.error(f"Error saving PCM16 to WAV: {e}")
            raise

    def main_loop(self):
        """Main processing loop - minimal since streaming is event-driven"""
        try:
            # Brief pause to prevent busy waiting
            # Real work happens in event handlers
            time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in speech synthesis main loop: {e}")
            self.error_count += 1
            time.sleep(1.0)

    def _publish_speaking_status(self, speaking: bool, text: str, voice: str):
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

    # ============================================================================
    # Declaratively configured callback methods (from .messages file)
    # ============================================================================

    def on_text_response(self, message):
        """
        Handle text response messages (declaratively configured callback).

        ⚠️ CRITICAL: This requests audio from Realtime API,
        but playback still uses robot_hat.Music()
        """
        try:
            text = message.data.get("text", "")
            if not text.strip():
                self.logger.warning("Received empty text response, ignoring")
                return

            # Extract parameters
            voice = message.data.get("voice", self.tts_config.get("default_voice", "alloy"))
            conversation_id = message.data.get("conversation_id")

            # Store conversation context
            self.current_conversation_id = conversation_id

            self.logger.info(f"Requesting TTS from Realtime API: '{text[:50]}'... (voice: {voice})")

            # Note: Mutex already acquired in _on_output_item_added() when response started
            # No need to acquire again here

            # Update speaking status with actual text content
            self._publish_speaking_status(True, text, voice)
            self.logger.debug(f"📢 Updated speaking_status with text: '{text[:30]}'...")

            # 4. ⚠️ CRITICAL FIX: DO NOT call response.create here!
            # Calling response.create creates a NEW conversation turn, which triggers
            # another text_response, which calls this handler again → INFINITE LOOP!
            #
            # Instead: The audio should already be generated by ai_node22.py's original
            # response.create call (which has modalities: ["text", "audio"]).
            # If audio is needed separately, use a TTS API call, not response.create.
            #
            # For now: Log that we received the text response
            # The audio generation will be handled by the response.audio.delta events
            # from the ORIGINAL response.create call in ai_node22.py
            self.logger.info(f"📝 Text response received for TTS: '{text[:50]}'...")

        except Exception as e:
            self.logger.error(f"Error handling text response: {e}")

    def on_tts_request(self, message):
        """
        Handle direct TTS requests (e.g., announcements, shutdown messages).

        This is different from on_text_response - it's a direct request for TTS,
        not part of a conversational AI response.
        """
        try:
            text = message.data.get("text", "")
            if not text.strip():
                self.logger.warning("Received empty TTS request, ignoring")
                return

            priority = message.data.get("priority", 50)
            self.logger.info(f"🔊 [TTS REQUEST] Priority {priority}: '{text}'")

            # For direct TTS requests, we need to:
            # 1. Create a conversation item with the text
            # 2. Request audio generation via response.create

            if not self.realtime_manager:
                self.logger.error("No realtime_manager available for TTS request")
                return

            # Acquire mutex BEFORE speaking
            microphone_mutex.acquire("TTS_announcement")

            try:
                # Send the text to Realtime API for TTS generation
                # This creates a conversation turn and generates audio
                self.realtime_manager.send_event({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{
                            "type": "input_text",
                            "text": f"[ANNOUNCEMENT] {text}"
                        }]
                    }
                })

                # Request audio-only response
                self.realtime_manager.send_event({
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio"],  # Audio only, no text
                        "instructions": f"Say exactly: {text}"
                    }
                })

                self.logger.info(f"✅ [TTS REQUEST] Sent to Realtime API for generation")

            except Exception as e:
                self.logger.error(f"Error generating TTS: {e}")
                microphone_mutex.release("TTS_announcement")
                raise

        except Exception as e:
            self.logger.error(f"Error handling TTS request: {e}")

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

    def on_sound_effect(self, message):
        """Handle sound effect playback requests (declaratively configured callback)"""
        try:
            effect = message.data.get("effect", "")
            volume = message.data.get("volume", 100)
            priority = message.data.get("priority", 30)

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
                # Use microphone mutex - allows parallel sounds+navigation but blocks speech recognition
                microphone_mutex.acquire_noisy_activity("sound_effect")

                try:
                    self.audio_output.music.sound_play(sound_file, volume)
                    # Wait for sound to finish
                    while self.audio_output.music.pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    self.logger.info(f"✓ Sound effect completed: {effect}")
                finally:
                    # Release microphone mutex
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

            # Clear buffers
            with self.buffer_lock:
                self.audio_buffer.clear()

            with self.transcript_lock:
                self.transcript_buffer.clear()

        except Exception as e:
            self.logger.error(f"Error during speech synthesis cleanup: {e}")

        self.logger.info(f"Speech synthesis stopped after {self.synthesis_count} syntheses")

    def get_synthesis_stats(self):
        """Get speech synthesis statistics"""
        return {
            "synthesis_count": self.synthesis_count,
            "error_count": self.error_count,
            "is_speaking": self.is_speaking,
            "current_text": self.current_text,
            "buffer_size": sum(len(c) for c in self.audio_buffer),
            "last_synthesis_time": self.last_synthesis_time,
            "audio_status": self.audio_output.get_status() if self.audio_output else None
        }

# Alias for launcher compatibility
SpeechSynthesisRealtimeNode = SpeechSynthesisNode22
