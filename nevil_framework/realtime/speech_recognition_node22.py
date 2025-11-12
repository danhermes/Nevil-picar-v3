"""
Speech Recognition Node v2.2 for Nevil Framework
Realtime API Streaming STT with OpenAI WebSocket

This is a WRAPPER that integrates audio_capture_manager.py with NevilNode base class.
The heavy lifting is done by audio_capture_manager and realtime_connection_manager.

Key Features:
- Inherits from NevilNode base class
- Publishes to voice_command topic
- Uses .messages configuration pattern
- Integrates with RealtimeConnectionManager WebSocket
- Handles response.audio_transcript.delta events
- Streaming speech-to-text via OpenAI Realtime API
"""

import os
import time
import threading
import queue
import logging
from typing import Optional, Dict, Any
from nevil_framework.base_node import NevilNode
from nevil_framework.busy_state import busy_state
from nevil_framework.microphone_mutex import microphone_mutex
from nevil_framework.chat_logger import get_chat_logger

# Import realtime components
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager
from nevil_framework.realtime.audio_capture_manager import AudioCaptureManager, AudioCaptureConfig

logger = logging.getLogger(__name__)


class SpeechRecognitionNode22(NevilNode):
    """
    Speech Recognition Node v2.2 - Realtime API Streaming STT

    This wrapper node:
    1. Inherits from NevilNode (same as speech_recognition_node.py)
    2. Uses .messages configuration for declarative messaging
    3. Publishes to voice_command topic
    4. Integrates audio_capture_manager for streaming audio
    5. Connects to OpenAI Realtime API via WebSocket
    6. Handles response.audio_transcript.delta events
    7. Accumulates streaming transcripts into final text
    """

    def __init__(self, config_path: str = None):
        # Initialize base node with name
        super().__init__(
            node_name="speech_recognition_realtime",
            config_path=config_path or "nevil_framework/realtime/.messages"
        )

        # Chat logger for performance tracking
        self.chat_logger = get_chat_logger()

        # OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            self.logger.warning("No OpenAI API key found - realtime STT will not work")

        # Realtime connection manager
        self.connection_manager: Optional[RealtimeConnectionManager] = None

        # Audio capture manager
        self.audio_capture: Optional[AudioCaptureManager] = None

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.realtime_config = config.get('realtime', {})
        self.audio_config = config.get('audio', {})
        self.recognition_config = config.get('recognition', {})

        # State management (same pattern as speech_recognition_node.py)
        self.is_listening = False
        self.system_mode = "idle"
        self.speaking_active = False
        self.navigation_active = False

        # Transcript accumulation
        self.current_transcript = ""
        self.transcript_lock = threading.Lock()
        self.last_transcript_time = 0

        # Streaming state
        self.is_streaming = False
        self.stream_lock = threading.Lock()

        # Performance tracking
        self.recognition_count = 0
        self.error_count = 0
        self.last_recognition_time = 0

        # Threading (same pattern as speech_recognition_node.py)
        self.stop_event = threading.Event()
        self.transcript_thread = None

        self.logger.info("Speech Recognition Node v2.2 (Realtime API) initialized")

    def initialize(self):
        """Initialize realtime API components"""
        self.logger.info("Initializing Speech Recognition Node v2.2...")

        try:
            if not self.openai_api_key:
                self.logger.error("Cannot initialize without OpenAI API key")
                return

            # Initialize Realtime Connection Manager
            model = self.realtime_config.get('model', 'gpt-4o-realtime-preview-2024-10-01')
            self.connection_manager = RealtimeConnectionManager(
                api_key=self.openai_api_key,
                model=model
            )

            # Register event handlers for streaming transcripts
            self.connection_manager.register_event_handler(
                "response.audio_transcript.delta",
                self._on_transcript_delta
            )
            self.connection_manager.register_event_handler(
                "response.audio_transcript.done",
                self._on_transcript_done
            )
            self.connection_manager.register_event_handler(
                "error",
                self._on_error_event
            )

            # Start WebSocket connection
            self.connection_manager.start()
            self.logger.info("Realtime API connection started")

            # Initialize audio capture manager
            audio_config = AudioCaptureConfig(
                sample_rate=self.audio_config.get('sample_rate', 24000),
                channel_count=self.audio_config.get('channel_count', 1),
                chunk_size=self.audio_config.get('chunk_size', 4800),
                buffer_size=self.audio_config.get('buffer_size', 4096)
            )

            self.audio_capture = AudioCaptureManager(
                config=audio_config,
                callbacks={
                    'on_audio_data': self._on_audio_data,
                    'on_error': self._on_audio_error,
                    'on_state_change': self._on_audio_state_change
                }
            )
            self.audio_capture.initialize()
            self.logger.info("Audio capture manager initialized")

            # Start listening state
            self.is_listening = True

            # Start transcript processing thread (same pattern as speech_recognition_node.py)
            self.transcript_thread = threading.Thread(
                target=self._transcript_processing_loop,
                daemon=True
            )
            self.transcript_thread.start()

            self.logger.info("Speech Recognition Node v2.2 initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize realtime speech recognition: {e}")
            raise

    def _on_transcript_delta(self, event: Dict[str, Any]):
        """
        Handle streaming transcript delta events from Realtime API

        Event format:
        {
            "type": "response.audio_transcript.delta",
            "delta": "partial text..."
        }
        """
        try:
            delta = event.get("delta", "")
            if not delta:
                return

            with self.transcript_lock:
                self.current_transcript += delta
                self.last_transcript_time = time.time()

            self.logger.debug(f"Transcript delta: '{delta}' (total: {len(self.current_transcript)} chars)")

        except Exception as e:
            self.logger.error(f"Error processing transcript delta: {e}")

    def _on_transcript_done(self, event: Dict[str, Any]):
        """
        Handle final transcript completion event

        Event format:
        {
            "type": "response.audio_transcript.done",
            "transcript": "final complete text"
        }
        """
        try:
            # Get final transcript from event or use accumulated
            final_transcript = event.get("transcript", "")

            with self.transcript_lock:
                if not final_transcript:
                    final_transcript = self.current_transcript

                # Process completed transcript
                if final_transcript and final_transcript.strip():
                    self._process_transcript(final_transcript.strip())

                # Reset accumulator
                self.current_transcript = ""

        except Exception as e:
            self.logger.error(f"Error processing transcript completion: {e}")

    def _process_transcript(self, text: str):
        """
        Process completed transcript and publish to voice_command topic
        (Same pattern as speech_recognition_node.py _process_audio_discrete)
        """
        # Generate unique conversation ID
        conversation_id = self.chat_logger.generate_conversation_id()

        try:
            self.logger.info(f"🎙️ Starting conversation: {conversation_id}")

            # Log REQUEST
            with self.chat_logger.log_step(
                conversation_id, "request",
                metadata={"source": "realtime_api", "stream": "websocket"}
            ):
                pass

            # Log STT completion
            with self.chat_logger.log_step(
                conversation_id, "stt",
                input_text="<realtime_audio_stream>",
                metadata={
                    "model": self.realtime_config.get('model', 'gpt-4o-realtime'),
                    "mode": "streaming",
                    "api": "realtime"
                }
            ) as stt_log:
                stt_log["output_text"] = text

            # Log recognized speech
            self.logger.info(f"🎤 [REALTIME STT] Recognized: '{text}'")

            # Calculate confidence (realtime API provides high quality)
            confidence = 0.95  # Realtime API has high accuracy

            # Prepare voice command data (same schema as speech_recognition_node.py)
            voice_command_data = {
                "text": text,
                "confidence": confidence,
                "timestamp": time.time(),
                "language": self.recognition_config.get('language', 'en-US'),
                "duration": 0.0,  # TODO: Track actual duration
                "conversation_id": conversation_id,
                "mode": "realtime_streaming"
            }

            # Publish to voice_command topic (declarative from .messages)
            if self.publish("voice_command", voice_command_data):
                self.logger.info(f"✓ Realtime STT processed: '{text}' (conf: {confidence:.2f})")
                self.recognition_count += 1
                self.last_recognition_time = time.time()
            else:
                self.logger.error("Failed to publish voice command")

        except Exception as e:
            self.logger.error(f"Error processing transcript: {e}")
            self.error_count += 1

    def _on_error_event(self, event: Dict[str, Any]):
        """Handle error events from Realtime API"""
        error_msg = event.get("error", {}).get("message", "Unknown error")
        self.logger.error(f"Realtime API error: {error_msg}")
        self.error_count += 1

    def _on_audio_data(self, base64_audio: str, volume_level: float):
        """
        Callback from audio_capture_manager when audio data is ready
        Sends to Realtime API via WebSocket
        """
        try:
            if not self.connection_manager or not self.is_listening:
                return

            # Send audio event to Realtime API
            event = {
                "type": "input_audio_buffer.append",
                "audio": base64_audio
            }
            self.connection_manager.send_event(event)

        except Exception as e:
            self.logger.error(f"Error sending audio data: {e}")

    def _on_audio_error(self, error: Exception):
        """Handle audio capture errors"""
        self.logger.error(f"Audio capture error: {error}")
        self.error_count += 1

    def _on_audio_state_change(self, state: str):
        """Handle audio capture state changes"""
        self.logger.debug(f"Audio capture state: {state}")

    def _transcript_processing_loop(self):
        """
        Background thread for transcript timeout detection
        (Same pattern as speech_recognition_node.py _discrete_recording_loop)
        """
        self.logger.info("Starting transcript processing loop...")

        while not self.stop_event.is_set():
            try:
                # Check for transcript timeout (no new deltas in 2 seconds)
                with self.transcript_lock:
                    if self.current_transcript and self.last_transcript_time:
                        elapsed = time.time() - self.last_transcript_time

                        if elapsed > 2.0:
                            # Timeout - process accumulated transcript
                            self.logger.debug(f"Transcript timeout ({elapsed:.1f}s) - processing")
                            self._process_transcript(self.current_transcript.strip())
                            self.current_transcript = ""

                time.sleep(0.5)

            except Exception as e:
                if not self.stop_event.is_set():
                    self.logger.error(f"Error in transcript processing loop: {e}")
                    time.sleep(1.0)

        self.logger.info("Transcript processing loop stopped")

    def main_loop(self):
        """
        Main processing loop - minimal since WebSocket handles everything
        (Same pattern as speech_recognition_node.py)
        """
        try:
            if self.stop_event.is_set():
                return

            # Brief pause - WebSocket connection handles all processing
            time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.error_count += 1
            time.sleep(1.0)

    def cleanup(self):
        """
        Cleanup resources
        (Same pattern as speech_recognition_node.py)
        """
        self.logger.info("Cleaning up realtime speech recognition...")

        try:
            # Stop listening
            self.is_listening = False

            # Stop connection manager
            if self.connection_manager:
                self.connection_manager.stop()

            # Stop and cleanup audio capture
            if self.audio_capture:
                self.audio_capture.dispose()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

        self.logger.info(f"Realtime STT stopped after {self.recognition_count} recognitions")

    def stop(self, timeout: float = 10.0):
        """
        Stop the node gracefully
        (Same pattern as speech_recognition_node.py)
        """
        self.logger.info("Stopping Speech Recognition Node v2.2...")

        # Set stop event
        self.stop_event.set()

        # Stop listening
        self.is_listening = False

        # Wait for transcript thread
        if self.transcript_thread and self.transcript_thread.is_alive():
            self.transcript_thread.join(timeout=timeout)

        self.logger.info("Speech Recognition Node v2.2 stopped")

        # Call parent stop
        super().stop(timeout)

    # ========================================================================
    # Declarative callback methods (from .messages file)
    # Same as speech_recognition_node.py
    # ========================================================================

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
                self._start_listening()

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
                self.logger.info("Paused realtime STT - system is speaking")
            elif not speaking and not self.is_listening and not self.navigation_active:
                self._start_listening()
                self.logger.info("Resumed realtime STT - system finished speaking")

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

            # Pause listening during action execution
            if status == "executing" and self.is_listening:
                self._stop_listening()
                self.logger.info("Paused realtime STT - robot is executing actions")
            elif status in ["completed", "idle"] and not self.is_listening and not self.speaking_active:
                self._start_listening()
                self.logger.info("Resumed realtime STT - robot finished actions")

        except Exception as e:
            self.logger.error(f"Error handling navigation status change: {e}")

    # ========================================================================
    # Helper methods
    # ========================================================================

    def _start_listening(self):
        """Start listening for speech (streaming mode)"""
        if self.is_listening:
            return

        try:
            self.is_listening = True

            # Start audio capture
            if self.audio_capture:
                self.audio_capture.start_recording()

            # Publish listening status change
            self._publish_listening_status(True, "started")

            self.logger.info("Started realtime streaming STT")

        except Exception as e:
            self.logger.error(f"Error starting listening: {e}")

    def _stop_listening(self):
        """Stop listening for speech (streaming mode)"""
        if not self.is_listening:
            return

        try:
            self.is_listening = False

            # Stop audio capture
            if self.audio_capture:
                self.audio_capture.stop_recording()

            # Publish listening status change
            self._publish_listening_status(False, "stopped")

            self.logger.info("Stopped realtime streaming STT")

        except Exception as e:
            self.logger.error(f"Error stopping listening: {e}")

    def _publish_listening_status(self, listening: bool, reason: str):
        """Publish listening status change"""
        status_data = {
            "listening": listening,
            "reason": reason
        }
        self.publish("listening_status", status_data)

    def get_speech_stats(self) -> Dict[str, Any]:
        """
        Get speech recognition statistics
        (Same as speech_recognition_node.py)
        """
        stats = {
            "recognition_count": self.recognition_count,
            "error_count": self.error_count,
            "is_listening": self.is_listening,
            "system_mode": self.system_mode,
            "speaking_active": self.speaking_active,
            "last_recognition_time": self.last_recognition_time,
            "mode": "realtime_streaming"
        }

        if self.connection_manager:
            stats["connection_stats"] = self.connection_manager.get_stats()

        return stats
