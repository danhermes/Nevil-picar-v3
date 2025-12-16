"""
AudioCaptureManager - Production-ready audio capture for OpenAI Realtime API

Adapted from Blane3 TypeScript implementation for Nevil Raspberry Pi hardware.

Features:
- PyAudio integration for Raspberry Pi (Linux)
- 24kHz mono PCM16 format (OpenAI Realtime API specs)
- Streaming audio chunks to WebSocket
- Voice Activity Detection (VAD) support
- Thread-safe operation with proper synchronization
- Integration with RealtimeConnectionManager
- Comprehensive error handling and logging

Configuration:
- Sample Rate: 24000 Hz (Realtime API requirement)
- Channels: 1 (mono)
- Format: PCM16 (16-bit signed integers)
- Chunk Size: 4800 samples (200ms at 24kHz)
"""

import pyaudio
import numpy as np
import base64
import logging
import threading
import queue
import time
from typing import Callable, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class CaptureState(Enum):
    """Audio capture states"""
    INACTIVE = "inactive"
    RECORDING = "recording"
    PAUSED = "paused"


class AudioCaptureConfig:
    """Configuration for audio capture"""

    def __init__(
        self,
        sample_rate: int = 24000,
        channel_count: int = 1,
        chunk_size: int = 4800,
        buffer_size: int = 4096,
        device_index: Optional[int] = None,
        vad_enabled: bool = True,  # Enable VAD by default for manual commit mode
        vad_threshold: float = 0.02,
        vad_min_speech_duration: float = 0.3,  # Minimum speech duration in seconds
        auto_flush_ms: int = 200,
        speech_timeout_ms: int = 1500,  # Commit after 1.5s of silence
        gate_audio_on_silence: bool = True,  # COST OPTIMIZATION: Don't send silence to API
        silence_padding_ms: int = 300  # Send 300ms of padding before/after speech for context
    ):
        """
        Initialize audio capture configuration.

        Args:
            sample_rate: Audio sample rate (24000 Hz for Realtime API)
            channel_count: Number of audio channels (1 = mono)
            chunk_size: Samples per processing chunk (4800 = 200ms at 24kHz)
            buffer_size: PyAudio buffer size for reading
            device_index: Specific audio device (None = default)
            vad_enabled: Enable Voice Activity Detection
            vad_threshold: VAD volume threshold (0.0-1.0)
            vad_min_speech_duration: Minimum speech duration in seconds (filters brief noise)
            auto_flush_ms: Auto-flush buffered audio after this many ms
        """
        self.sample_rate = sample_rate
        self.channel_count = channel_count
        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        self.device_index = device_index
        self.vad_enabled = vad_enabled
        self.vad_threshold = vad_threshold
        self.vad_min_speech_duration = vad_min_speech_duration
        self.auto_flush_ms = auto_flush_ms
        self.speech_timeout_ms = speech_timeout_ms
        self.gate_audio_on_silence = gate_audio_on_silence
        self.silence_padding_ms = silence_padding_ms


class AudioCaptureCallbacks:
    """Callbacks for audio capture events"""

    def __init__(
        self,
        on_audio_data: Optional[Callable[[str, float], None]] = None,
        on_volume_change: Optional[Callable[[float], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_state_change: Optional[Callable[[CaptureState], None]] = None,
        on_vad_speech_start: Optional[Callable[[], None]] = None,
        on_vad_speech_end: Optional[Callable[[], None]] = None
    ):
        """
        Initialize callbacks.

        Args:
            on_audio_data: Called with (base64_audio, volume_level) when audio is ready
            on_volume_change: Called with volume_level on volume changes
            on_error: Called with exception on errors
            on_state_change: Called with new state on state changes
            on_vad_speech_start: Called when speech detected (VAD)
            on_vad_speech_end: Called when speech ends (VAD)
        """
        self.on_audio_data = on_audio_data
        self.on_volume_change = on_volume_change
        self.on_error = on_error
        self.on_state_change = on_state_change
        self.on_vad_speech_start = on_vad_speech_start
        self.on_vad_speech_end = on_vad_speech_end


class AudioCaptureManager:
    """
    Microphone capture manager for Nevil Realtime API integration.

    Handles audio input, real-time processing, PCM16 encoding, and streaming
    to WebSocket connection for OpenAI Realtime API.

    Thread-safe with proper synchronization for Raspberry Pi hardware.
    """

    def __init__(
        self,
        config: Optional[AudioCaptureConfig] = None,
        callbacks: Optional[AudioCaptureCallbacks] = None,
        connection_manager: Optional[Any] = None,
        custom_logger: Optional[logging.Logger] = None
    ):
        """
        Initialize audio capture manager.

        Args:
            config: Audio capture configuration
            callbacks: Event callbacks
            connection_manager: RealtimeConnectionManager for sending audio
            custom_logger: Optional logger to use (if not provided, uses module logger)
        """
        self.config = config or AudioCaptureConfig()
        self.callbacks = callbacks or AudioCaptureCallbacks()
        self.connection_manager = connection_manager

        # Use custom logger if provided, otherwise use module logger
        self.logger = custom_logger if custom_logger else logger

        # PyAudio state
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # Capture state
        self.state = CaptureState.INACTIVE
        self.is_recording = False
        self.is_paused = False

        # Audio buffer for chunking
        self.audio_buffer: list = []
        self.buffer_length = 0
        self.buffer_lock = threading.Lock()

        # Processing thread
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # VAD state
        self.vad_speech_active = False
        self.vad_silence_frames = 0
        self.vad_silence_threshold = 10  # Frames of silence to trigger speech_end
        self.vad_speech_start_time = 0  # Track when speech started

        # Commit cooldown (prevent rapid re-commits that cause empty buffer errors)
        self.last_commit_time = 0
        self.commit_cooldown = 0.5  # 500ms between commits (reduced from 2.0s to prevent audio accumulation)

        # Auto-flush timer
        self.last_flush_time = time.time()

        # Statistics
        self.total_samples_processed = 0
        self.total_chunks_sent = 0
        self.total_chunks_skipped = 0  # Track chunks NOT sent due to silence gating

        # Silence padding buffer (for context around speech)
        self.padding_buffer: list = []  # Circular buffer for pre-speech padding
        self.padding_samples = int((self.config.silence_padding_ms / 1000.0) * self.config.sample_rate)
        self.post_speech_padding_remaining = 0  # Countdown for post-speech padding

        self.logger.info(
            f"AudioCaptureManager initialized: "
            f"{self.config.sample_rate}Hz, "
            f"{self.config.channel_count}ch, "
            f"chunk={self.config.chunk_size}, "
            f"VAD={'enabled' if self.config.vad_enabled else 'disabled'}"
        )

    def initialize(self) -> None:
        """
        Initialize PyAudio and prepare for capture.

        Must be called before starting recording.

        Raises:
            Exception: If initialization fails
        """
        try:
            self.logger.info("Initializing PyAudio...")

            # Create PyAudio instance
            self.audio = pyaudio.PyAudio()

            # Log available devices (helpful for debugging)
            self._log_audio_devices()

            # Verify device configuration
            if self.config.device_index is not None:
                device_info = self.audio.get_device_info_by_index(self.config.device_index)
                mic_name = device_info['name']
                mic_index = self.config.device_index
                self.logger.info(f"🎤 USING MIC: {mic_name} (index={mic_index})")
                # Write to file
                with open("/tmp/nevil_mic_status.txt", "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] MICROPHONE SELECTED\n")
                    f.write(f"Device: {mic_name}\n")
                    f.write(f"Index: {mic_index}\n")
            else:
                default_info = self.audio.get_default_input_device_info()
                mic_name = default_info['name']
                mic_index = default_info['index']
                self.logger.info(f"🎤 USING DEFAULT MIC: {mic_name} (index={mic_index})")
                # Write to file
                with open("/tmp/nevil_mic_status.txt", "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] MICROPHONE SELECTED (DEFAULT)\n")
                    f.write(f"Device: {mic_name}\n")
                    f.write(f"Index: {mic_index}\n")

            # Create input stream (but don't start yet)
            self.stream = self.audio.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=self.config.channel_count,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.device_index,
                frames_per_buffer=self.config.buffer_size,
                stream_callback=None  # We'll read manually for better control
            )

            # Stop stream initially
            self.stream.stop_stream()

            self._set_state(CaptureState.INACTIVE)
            self.logger.info("PyAudio initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize audio capture: {e}"
            self.logger.error(error_msg)
            self._handle_error(Exception(error_msg))
            raise

    def start_recording(self) -> None:
        """
        Start recording audio from microphone.

        Raises:
            RuntimeError: If not initialized or already recording
        """
        if not self.audio or not self.stream:
            raise RuntimeError("Audio capture not initialized. Call initialize() first.")

        if self.is_recording:
            self.logger.warning("Already recording")
            return

        self.logger.info("Starting audio recording...")

        # Reset state
        self.is_recording = True
        self.is_paused = False
        self.stop_event.clear()

        # Reset buffer
        with self.buffer_lock:
            self.audio_buffer = []
            self.buffer_length = 0

        # Reset statistics
        self.total_samples_processed = 0
        self.total_chunks_sent = 0
        self.last_flush_time = time.time()

        # Start audio stream
        # Write to file for debugging (bypasses all logging/stdout issues)
        with open("/tmp/nevil_mic_status.txt", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] START_RECORDING CALLED\n")
            f.write(f"is_recording: {self.is_recording}\n")
            f.write(f"stream exists: {self.stream is not None}\n")

        self.stream.start_stream()

        with open("/tmp/nevil_mic_status.txt", "a") as f:
            f.write(f"stream.is_active(): {self.stream.is_active()}\n")

        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            name="AudioCapture_Processing",
            daemon=True
        )
        self.processing_thread.start()

        with open("/tmp/nevil_mic_status.txt", "a") as f:
            f.write(f"processing_thread.is_alive(): {self.processing_thread.is_alive()}\n")
            f.write(f"processing_thread.name: {self.processing_thread.name}\n")

        self._set_state(CaptureState.RECORDING)
        self.logger.info("✅ Audio recording started")

    def stop_recording(self) -> None:
        """Stop recording and flush remaining audio."""
        if not self.is_recording:
            self.logger.warning("Not recording")
            return

        self.logger.info("Stopping audio recording...")

        # Flush any remaining buffered audio
        self.flush()

        # Signal stop
        self.stop_event.set()
        self.is_recording = False
        self.is_paused = False

        # Wait for processing thread
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        # Stop stream
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()

        self._set_state(CaptureState.INACTIVE)
        # Calculate cost savings for log
        cost_saved_msg = ""
        if self.total_chunks_skipped > 0:
            total = self.total_chunks_sent + self.total_chunks_skipped
            skipped_pct = (self.total_chunks_skipped / total) * 100 if total > 0 else 0
            cost_saved = self.total_chunks_skipped * 0.012
            cost_saved_msg = f", Skipped: {self.total_chunks_skipped} ({skipped_pct:.1f}% saved ${cost_saved:.4f})"

        self.logger.info(
            f"Audio recording stopped. "
            f"Processed: {self.total_samples_processed} samples, "
            f"Sent: {self.total_chunks_sent} chunks"
            f"{cost_saved_msg}"
        )

    def pause(self) -> None:
        """Pause recording (audio still captured but not processed)."""
        if not self.is_recording or self.is_paused:
            return

        self.logger.info("Pausing audio recording...")
        self.is_paused = True
        self._set_state(CaptureState.PAUSED)

    def resume(self) -> None:
        """Resume recording after pause."""
        if not self.is_recording or not self.is_paused:
            return

        self.logger.info("Resuming audio recording...")
        self.is_paused = False
        self._set_state(CaptureState.RECORDING)

    def flush(self) -> None:
        """
        Flush any remaining buffered audio.

        Converts buffered samples to PCM16, encodes to base64,
        and sends via callback or connection manager.
        """
        # ⚠️ CRITICAL: Check mutex BEFORE flushing
        # Don't send buffered audio if TTS is active
        from nevil_framework.microphone_mutex import microphone_mutex
        if not microphone_mutex.is_microphone_available():
            # Mutex blocked - clear buffer and return without sending
            with self.buffer_lock:
                if self.audio_buffer:
                    self.audio_buffer.clear()
                    self.buffer_length = 0
                    self.logger.debug("🚫 Flush cancelled - mutex blocked, buffer cleared")
            return

        with self.buffer_lock:
            if self.buffer_length == 0:
                self.logger.debug("No audio to flush (buffer empty)")
                return

            self.logger.debug(
                f"Flushing {self.buffer_length} samples "
                f"({self.buffer_length / self.config.sample_rate * 1000:.1f}ms)"
            )

            try:
                # Concatenate buffered audio
                concatenated = np.concatenate(self.audio_buffer)

                # Convert to PCM16 and encode
                pcm16 = self._float32_to_pcm16(concatenated)
                base64_audio = self._encode_base64(pcm16)

                # Calculate volume
                volume_level = self._calculate_volume(concatenated)

                # Send via callback
                if self.callbacks.on_audio_data:
                    self.callbacks.on_audio_data(base64_audio, volume_level)

                # Send via connection manager
                if self.connection_manager:
                    self._send_audio_to_realtime(base64_audio)

                self.total_chunks_sent += 1
                self.logger.debug("Flushed audio sent successfully")

                # Reset buffer
                self.audio_buffer = []
                self.buffer_length = 0
                self.last_flush_time = time.time()

            except Exception as e:
                self.logger.error(f"Error flushing audio: {e}")
                self._handle_error(e)

    def get_current_volume(self) -> float:
        """
        Get current volume level (0.0-1.0).

        Returns:
            Current volume level or 0.0 if not available
        """
        with self.buffer_lock:
            if self.buffer_length == 0:
                return 0.0

            # Calculate volume from most recent buffer chunk
            if self.audio_buffer:
                return self._calculate_volume(self.audio_buffer[-1])

            return 0.0

    def get_state(self) -> CaptureState:
        """Get current capture state."""
        return self.state

    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "state": self.state.value,
            "is_recording": self.is_recording,
            "is_paused": self.is_paused,
            "total_samples": self.total_samples_processed,
            "total_chunks_sent": self.total_chunks_sent,
            "total_chunks_skipped": self.total_chunks_skipped,
            "buffer_samples": self.buffer_length,
            "buffer_ms": self.buffer_length / self.config.sample_rate * 1000,
            "vad_enabled": self.config.vad_enabled,
            "vad_speech_active": self.vad_speech_active,
            "sample_rate": self.config.sample_rate,
            "channels": self.config.channel_count,
            "silence_gating_enabled": self.config.gate_audio_on_silence
        }

        # Calculate cost savings
        if self.total_chunks_sent + self.total_chunks_skipped > 0:
            total_chunks = self.total_chunks_sent + self.total_chunks_skipped
            skipped_percentage = (self.total_chunks_skipped / total_chunks) * 100
            stats["skipped_percentage"] = f"{skipped_percentage:.1f}%"

            # Estimate cost savings (assuming $0.06 per minute audio input)
            # Each chunk is 200ms = 0.2 minutes = 0.2 * $0.06 = $0.012 per chunk
            cost_per_chunk = 0.012
            cost_saved = self.total_chunks_skipped * cost_per_chunk
            stats["estimated_cost_saved_usd"] = f"${cost_saved:.4f}"

        return stats

    def set_callbacks(self, callbacks: AudioCaptureCallbacks) -> None:
        """Update callbacks."""
        self.callbacks = callbacks

    def dispose(self) -> None:
        """Clean up all resources."""
        self.logger.info("Disposing audio capture manager...")

        # Stop recording if active
        if self.is_recording:
            self.stop_recording()

        # Close stream
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Terminate PyAudio
        if self.audio:
            self.audio.terminate()
            self.audio = None

        self.logger.info("Audio capture manager disposed")

    # Private methods

    def _processing_loop(self) -> None:
        """
        Main processing loop (runs in separate thread).

        Continuously reads audio from stream, buffers it,
        and processes chunks when ready.
        """
        # Write to file to confirm processing loop started
        with open("/tmp/nevil_mic_status.txt", "a") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] PROCESSING LOOP STARTED\n")
            f.write(f"Thread name: {threading.current_thread().name}\n")
            f.write(f"is_recording: {self.is_recording}\n")
            f.write(f"stream.is_active(): {self.stream.is_active() if self.stream else 'NO STREAM'}\n")

        self.logger.info("🎤 AUDIO PROCESSING LOOP STARTING...")
        self.logger.info(f"🎤 Stream active: {self.stream.is_active() if self.stream else 'NO STREAM'}")
        self.logger.info(f"🎤 is_recording: {self.is_recording}")

        try:
            while not self.stop_event.is_set() and self.is_recording:
                # Check if stream is active
                if not self.stream or not self.stream.is_active():
                    time.sleep(0.01)
                    continue

                try:
                    # Read audio data from stream
                    audio_data = self.stream.read(
                        self.config.buffer_size,
                        exception_on_overflow=False
                    )

                    # Convert bytes to numpy array (int16)
                    audio_int16 = np.frombuffer(audio_data, dtype=np.int16)

                    # Convert to float32 (-1.0 to 1.0)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    # Skip processing if paused
                    if self.is_paused:
                        continue

                    # Calculate volume
                    volume_level = self._calculate_volume(audio_float32)

                    # Only log mic signals at DEBUG level (too verbose for INFO)
                    self.logger.debug(f"🎤 MIC SIGNAL: volume={volume_level:.4f}, samples={len(audio_float32)}")

                    # ⚠️ CRITICAL: Check mutex BEFORE doing ANYTHING with audio
                    # If Nevil is speaking, skip ALL processing - don't buffer, don't send, nothing
                    from nevil_framework.microphone_mutex import microphone_mutex
                    if not microphone_mutex.is_microphone_available():
                        # Mutex blocked - discard this audio chunk entirely
                        continue

                    # Volume change callback
                    if self.callbacks.on_volume_change:
                        self.callbacks.on_volume_change(volume_level)

                    # VAD processing
                    if self.config.vad_enabled:
                        self._process_vad(volume_level)

                    # Buffer audio data
                    with self.buffer_lock:
                        self.audio_buffer.append(audio_float32)
                        self.buffer_length += len(audio_float32)
                        self.total_samples_processed += len(audio_float32)

                        # ✅ PROOF: Audio successfully buffered during speech
                        if self.vad_speech_active:
                            self.logger.debug(f"✅ BUFFERED during speech: {len(audio_float32)} samples, buffer_length={self.buffer_length}")

                    # Process when we have enough data
                    if self.buffer_length >= self.config.chunk_size:
                        if self.vad_speech_active:
                            self.logger.debug(f"🔥 CALLING _process_audio_chunk during speech! buffer_length={self.buffer_length}")
                        self._process_audio_chunk()

                    # Auto-flush check (prevent buffer from growing too large)
                    time_since_flush = time.time() - self.last_flush_time
                    if time_since_flush > (self.config.auto_flush_ms / 1000.0):
                        if self.buffer_length > 0:
                            self.flush()

                except IOError as e:
                    # Handle buffer overflow (just log and continue)
                    self.logger.warning(f"Audio buffer overflow: {e}")
                    continue

                except Exception as e:
                    self.logger.error(f"Error in processing loop: {e}")
                    self._handle_error(e)
                    break

        finally:
            self.logger.debug("Audio processing loop ended")

    def _process_audio_chunk(self) -> None:
        """
        Process buffered audio chunk and send.

        With silence gating enabled, only sends audio when:
        1. Speech is active (VAD detected speech)
        2. During padding periods (before/after speech)
        3. VAD is disabled (sends all audio)

        This can reduce API costs by 70-90% by not sending silence!
        """
        self.logger.debug(f"📦 _process_audio_chunk called, buffer_length={self.buffer_length}")

        # ⚠️ CRITICAL: Check mutex BEFORE processing buffered audio
        # This prevents sending already-buffered audio when TTS starts mid-buffer
        from nevil_framework.microphone_mutex import microphone_mutex
        if not microphone_mutex.is_microphone_available():
            # Mutex blocked - clear buffer and return without sending
            with self.buffer_lock:
                if self.audio_buffer:
                    self.audio_buffer.clear()
                    self.buffer_length = 0
                    self.logger.debug("🚫 Buffered audio discarded - mutex blocked during chunk processing")
            return

        with self.buffer_lock:
            if self.buffer_length < self.config.chunk_size:
                self.logger.debug(f"⏸️  Buffer too small ({self.buffer_length} < {self.config.chunk_size}), waiting for more audio")
                return

            try:
                # Concatenate buffered audio
                concatenated = np.concatenate(self.audio_buffer)

                # Take exactly chunk_size samples
                chunk = concatenated[:self.config.chunk_size]
                remainder = concatenated[self.config.chunk_size:]

                # Convert to PCM16 and encode
                pcm16 = self._float32_to_pcm16(chunk)
                base64_audio = self._encode_base64(pcm16)

                # Calculate volume
                volume_level = self._calculate_volume(chunk)

                # 💰 COST OPTIMIZATION: Silence gating
                # Determine if we should send this chunk to the API
                should_send = True
                skip_reason = ""

                if self.config.gate_audio_on_silence and self.config.vad_enabled:
                    # Check if we're in an "active" state where audio should be sent
                    is_speech_active = self.vad_speech_active
                    is_post_padding = self.post_speech_padding_remaining > 0

                    if not is_speech_active and not is_post_padding:
                        # Pure silence - don't send to API (SAVES MONEY!)
                        should_send = False
                        skip_reason = "silence"

                        # BUT: Maintain circular padding buffer for pre-speech context
                        # Store this chunk for potential use when speech starts
                        self.padding_buffer.append(base64_audio)

                        # Keep buffer size limited to padding duration
                        max_padding_chunks = max(1, int(self.padding_samples / self.config.chunk_size))
                        if len(self.padding_buffer) > max_padding_chunks:
                            self.padding_buffer.pop(0)  # Remove oldest chunk

                        self.total_chunks_skipped += 1
                        self.logger.debug(f"💰 SKIPPED chunk (silence) - saving $$ | buffer: {len(self.padding_buffer)} chunks")

                # Send via callback (always, for local monitoring)
                if self.callbacks.on_audio_data:
                    self.callbacks.on_audio_data(base64_audio, volume_level)

                # Send via connection manager (only if should_send)
                if should_send:
                    if self.connection_manager:
                        self._send_audio_to_realtime(base64_audio)
                    self.total_chunks_sent += 1

                    # Decrement post-speech padding counter
                    if self.post_speech_padding_remaining > 0:
                        self.post_speech_padding_remaining -= 1
                        self.logger.debug(f"📤 Sent post-speech padding chunk ({self.post_speech_padding_remaining} remaining)")
                else:
                    # Chunk was skipped - already handled above
                    pass

                # Update buffer with remainder
                if len(remainder) > 0:
                    self.audio_buffer = [remainder]
                    self.buffer_length = len(remainder)
                else:
                    self.audio_buffer = []
                    self.buffer_length = 0

                self.last_flush_time = time.time()

            except Exception as e:
                self.logger.error(f"Error processing audio chunk: {e}")
                self._handle_error(e)

    def _process_vad(self, volume_level: float) -> None:
        """
        Process Voice Activity Detection.

        Args:
            volume_level: Current volume level (0.0-1.0)
        """
        # ⚠️ CRITICAL FIX: Check mutex BEFORE processing VAD
        # If Nevil is speaking, skip VAD entirely AND clear buffers
        from nevil_framework.microphone_mutex import microphone_mutex
        if not microphone_mutex.is_microphone_available():
            # Mutex blocked - reset VAD state, clear buffer, skip processing
            if self.vad_speech_active:
                self.vad_speech_active = False
                self.vad_silence_frames = 0
                # CRITICAL: Clear audio buffer to prevent committing Nevil's speech later
                with self.buffer_lock:
                    self.audio_buffer.clear()
                    self.buffer_length = 0
                self.logger.debug("🚫 VAD disabled + buffer cleared - mutex blocked (Nevil speaking)")
            return

        speech_detected = volume_level > self.config.vad_threshold

        if speech_detected:
            # Speech detected
            self.vad_silence_frames = 0

            if not self.vad_speech_active:
                # Speech started
                self.vad_speech_active = True
                self.vad_speech_start_time = time.time()  # Track start time
                self.logger.info("🎤 VAD: Speech started")

                # ⚠️ CRITICAL: Clear API buffer at START of speech to prevent accumulation
                # BUT ONLY if microphone is available (not during TTS playback)
                # This prevents clearing buffer when detecting Nevil's own speech
                from nevil_framework.microphone_mutex import microphone_mutex
                if microphone_mutex.is_microphone_available():
                    if self.connection_manager:
                        try:
                            clear_event = {"type": "input_audio_buffer.clear"}
                            self.connection_manager.send_sync(clear_event)
                            self.logger.debug("🗑️ Cleared API audio buffer at speech start")
                        except Exception as e:
                            self.logger.error(f"Error clearing API buffer at speech start: {e}")

                        # 💰 COST OPTIMIZATION: Send pre-speech padding for context
                        # This gives the API ~300ms of audio before speech started
                        if self.config.gate_audio_on_silence and self.padding_buffer:
                            self.logger.info(f"📤 Sending {len(self.padding_buffer)} padding chunks for context")
                            for padding_audio in self.padding_buffer:
                                self._send_audio_to_realtime(padding_audio, is_padding=True)
                            self.padding_buffer.clear()
                else:
                    self.logger.debug("🚫 Skipping API buffer clear - mutex blocked (Nevil is speaking)")

                if self.callbacks.on_vad_speech_start:
                    self.callbacks.on_vad_speech_start()
        else:
            # Silence detected
            if self.vad_speech_active:
                self.vad_silence_frames += 1

                if self.vad_silence_frames >= self.vad_silence_threshold:
                    # Speech ended - check minimum duration before committing
                    speech_duration = time.time() - self.vad_speech_start_time

                    self.vad_speech_active = False
                    self.vad_silence_frames = 0

                    # 💰 COST OPTIMIZATION: Set up post-speech padding
                    # Continue sending audio for ~300ms after speech ends (for natural cutoff)
                    if self.config.gate_audio_on_silence:
                        padding_chunks = max(1, int(self.config.silence_padding_ms / 200))  # 200ms per chunk
                        self.post_speech_padding_remaining = padding_chunks
                        self.logger.info(f"📤 VAD: Speech ended - will send {padding_chunks} more padding chunks")

                    # FILTER: Ignore very short speech bursts (likely noise)
                    if speech_duration < self.config.vad_min_speech_duration:
                        self.logger.debug(f"🚫 VAD: Speech too short ({speech_duration:.2f}s < {self.config.vad_min_speech_duration}s) - ignoring")
                        self.post_speech_padding_remaining = 0  # Cancel padding for noise
                        return

                    # ⚠️ CRITICAL: Cooldown check to prevent rapid re-commits
                    # Realtime API clears buffer after commit, so rapid commits cause empty buffer errors
                    time_since_last_commit = time.time() - self.last_commit_time
                    if time_since_last_commit < self.commit_cooldown:
                        self.logger.debug(f"VAD: Speech ended but cooldown active ({time_since_last_commit:.1f}s < {self.commit_cooldown}s) - skipping commit")
                        if self.callbacks.on_vad_speech_end:
                            self.callbacks.on_vad_speech_end()
                        return

                    # Check if Nevil is speaking (mutex blocks microphone during TTS)
                    # If TTS is speaking, this "speech" is probably Nevil hearing himself
                    from nevil_framework.microphone_mutex import microphone_mutex
                    if not microphone_mutex.is_microphone_available():
                        self.logger.info("VAD: Speech ended but mutex blocked - NOT committing (preventing feedback loop)")
                        if self.callbacks.on_vad_speech_end:
                            self.callbacks.on_vad_speech_end()
                        return

                    # FILTER: Don't commit if buffer is empty or too small (silence/ambient noise)
                    # This prevents transcribing silence as "Thanks for watching" etc.
                    # 50ms minimum allows short words like "yes", "no", "stop"
                    MIN_BUFFER_SIZE = int(self.config.sample_rate * 0.05)  # 50ms minimum (1200 samples at 24kHz)
                    if self.buffer_length < MIN_BUFFER_SIZE:
                        self.logger.debug(f"🚫 VAD: Speech ended but buffer too small ({self.buffer_length} < {MIN_BUFFER_SIZE}) - ignoring")
                        # Clear the small buffer - it's just noise
                        with self.buffer_lock:
                            self.audio_buffer.clear()
                            self.buffer_length = 0
                        if self.callbacks.on_vad_speech_end:
                            self.callbacks.on_vad_speech_end()
                        return

                    self.logger.info(f"VAD: Speech ended - committing {self.buffer_length} samples for transcription")

                    # ⚠️ CRITICAL: Commit audio buffer and request response (manual mode without Server VAD)
                    # With turn_detection=None, we must manually:
                    # 1. STOP sending new audio immediately (pause streaming)
                    # 2. Commit the audio buffer
                    # 3. Request a response
                    # 4. Clear local buffer to prevent re-sending
                    if self.connection_manager:
                        try:
                            # ⚠️ CRITICAL FIX: Pause audio streaming IMMEDIATELY to prevent race condition
                            # This prevents new audio chunks from being added to the buffer during commit
                            was_recording = self.is_recording
                            self.is_recording = False  # Temporarily stop processing new audio
                            self.logger.debug("🛑 Paused audio streaming for clean commit")

                            # Small delay to ensure in-flight audio chunks are processed (reduced from 200ms to 50ms)
                            import time as time_module
                            time_module.sleep(0.05)  # 50ms delay - just enough for in-flight chunks

                            # Step 1: Commit audio
                            commit_event = {"type": "input_audio_buffer.commit"}
                            self.connection_manager.send_sync(commit_event)
                            self.last_commit_time = time.time()  # Update cooldown timer
                            self.logger.debug("✅ Committed audio buffer to Realtime API")

                            # Step 2: Clear LOCAL buffer to prevent re-sending committed audio
                            with self.buffer_lock:
                                self.audio_buffer.clear()
                                self.buffer_length = 0
                            self.logger.debug("🗑️  Cleared local audio buffer after commit")

                            # Step 3: Request transcription + response (ONE response.create for everything)
                            # With manual VAD (turn_detection=None), we must explicitly request response
                            # ⚠️ CRITICAL: Only request response if NOT already generating one
                            # This prevents multiple responses from being queued when user pauses mid-speech
                            if hasattr(self.connection_manager, 'response_in_progress') and self.connection_manager.response_in_progress:
                                self.logger.info("🚫 Response already in progress - skipping response.create to prevent queue buildup")
                            else:
                                response_event = {
                                    "type": "response.create",
                                    "response": {
                                        "modalities": ["text", "audio"]  # Generate BOTH text and audio in ONE response
                                    }
                                }
                                self.connection_manager.send_sync(response_event)
                                self.logger.debug("🎯 Requested text+audio response")

                            # Resume audio streaming after commit
                            if was_recording:
                                self.is_recording = True
                                self.logger.debug("▶️  Resumed audio streaming")

                            # DON'T acquire mutex here - let speech_synthesis handle it
                            # speech_synthesis will acquire when it receives the first audio chunk
                            # and release after playback completes (same key = proper pairing)

                        except Exception as e:
                            self.logger.error(f"Error committing audio buffer: {e}")

                    if self.callbacks.on_vad_speech_end:
                        self.callbacks.on_vad_speech_end()

    def _send_audio_to_realtime(self, base64_audio: str, is_padding: bool = False) -> None:
        """
        Send audio to Realtime API via connection manager.

        Args:
            base64_audio: Base64-encoded PCM16 audio
            is_padding: True if this is padding audio (for logging)
        """
        if not self.connection_manager:
            self.logger.error("❌ Cannot send audio - no connection_manager!")
            return

        try:
            event = {
                "type": "input_audio_buffer.append",
                "audio": base64_audio
            }
            self.connection_manager.send_sync(event)  # Thread-safe synchronous send

            if is_padding:
                self.logger.debug("📤 Sent padding audio chunk to Realtime API (for context)")
            else:
                self.logger.debug("📤 Sent audio chunk to Realtime API")

        except Exception as e:
            self.logger.error(f"Error sending audio to Realtime API: {e}")
            self._handle_error(e)

    def _calculate_volume(self, audio_data: np.ndarray) -> float:
        """
        Calculate volume level from audio data (RMS).

        Args:
            audio_data: Float32 audio samples (-1.0 to 1.0)

        Returns:
            Volume level (0.0 to 1.0)
        """
        if len(audio_data) == 0:
            return 0.0

        # Calculate RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio_data ** 2))

        # Clamp to 0.0-1.0 range
        return float(np.clip(rms, 0.0, 1.0))

    def _float32_to_pcm16(self, audio_data: np.ndarray) -> bytes:
        """
        Convert float32 audio to PCM16 bytes.

        Args:
            audio_data: Float32 audio samples (-1.0 to 1.0)

        Returns:
            PCM16 bytes (16-bit signed integers)
        """
        # Apply software gain (3x for good sensitivity without excessive feedback)
        audio_data = audio_data * 3.0

        # Clamp to valid range to prevent clipping
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Convert to bytes
        return audio_int16.tobytes()

    def _encode_base64(self, pcm_data: bytes) -> str:
        """
        Encode PCM16 data to base64 string.

        Args:
            pcm_data: PCM16 bytes

        Returns:
            Base64-encoded string
        """
        return base64.b64encode(pcm_data).decode('utf-8')

    def _set_state(self, new_state: CaptureState) -> None:
        """
        Update state and trigger callback.

        Args:
            new_state: New capture state
        """
        if self.state != new_state:
            self.state = new_state
            self.logger.debug(f"State changed to: {new_state.value}")

            if self.callbacks.on_state_change:
                self.callbacks.on_state_change(new_state)

    def _handle_error(self, error: Exception) -> None:
        """
        Handle error and trigger callback.

        Args:
            error: Exception that occurred
        """
        self.logger.error(f"Audio capture error: {error}")

        if self.callbacks.on_error:
            self.callbacks.on_error(error)

    def _log_audio_devices(self) -> None:
        """Log available audio devices (helpful for debugging)."""
        if not self.audio:
            return

        try:
            device_count = self.audio.get_device_count()
            self.logger.debug(f"Available audio devices: {device_count}")

            for i in range(device_count):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    self.logger.debug(
                        f"  [{i}] {info['name']} "
                        f"(in:{info['maxInputChannels']}, "
                        f"rate:{int(info['defaultSampleRate'])}Hz)"
                    )
        except Exception as e:
            self.logger.warning(f"Could not enumerate audio devices: {e}")


# Convenience function for quick setup
def create_audio_capture(
    connection_manager: Optional[Any] = None,
    sample_rate: int = 24000,
    vad_enabled: bool = False,
    **kwargs
) -> AudioCaptureManager:
    """
    Create and initialize an AudioCaptureManager with common defaults.

    Args:
        connection_manager: RealtimeConnectionManager instance
        sample_rate: Audio sample rate (default: 24000 for Realtime API)
        vad_enabled: Enable Voice Activity Detection
        **kwargs: Additional config parameters

    Returns:
        Initialized AudioCaptureManager

    Example:
        >>> capture = create_audio_capture(connection_manager, vad_enabled=True)
        >>> capture.start_recording()
    """
    config = AudioCaptureConfig(
        sample_rate=sample_rate,
        vad_enabled=vad_enabled,
        **kwargs
    )

    manager = AudioCaptureManager(
        config=config,
        connection_manager=connection_manager
    )

    manager.initialize()
    return manager
