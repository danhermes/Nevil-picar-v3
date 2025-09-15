"""
Audio Input - Combines v1.0 basics with v2.0 advanced chunking

Preserves v1.0 speech recognition parameters with v2.0's threading architecture.
Uses default devices only as specified.
"""

import os
import time
import queue
import threading
import logging
import speech_recognition as sr


class AudioInput:
    """
    Audio input wrapper combining:
    - v1.0 speech recognition parameters (EXACT)
    - v2.0 threading and chunking architecture
    - Default devices only (no manual specification)

    Key: Uses defaults only, no device index specification
    """

    def __init__(self, logger=None):
        """Initialize audio input with v1.0 parameters and v2.0 architecture"""

        # Use provided logger or create a basic one
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("audio_input")

        # v1.0 EXACT parameters - DO NOT MODIFY
        self.recognizer = sr.Recognizer()

        self.recognizer.energy_threshold = 1000  # Audio energy level for speech detection (50-4000) - LOWER = more sensitive to ambient noise
        self.recognizer.dynamic_energy_adjustment_damping = 0.1  # Rate of dynamic energy threshold adjustment (0.0-1.0) - controls adaptation speed
        self.recognizer.dynamic_energy_ratio = 1.2  # Ratio for dynamic energy adjustment - multiplier for energy threshold changes
        self.recognizer.pause_threshold = 0.5  # Seconds of silence to mark phrase end - SHORTER = more responsive but may cut off speech
        self.recognizer.operation_timeout = 18  # Maximum seconds to wait for speech input before timeout
        self.phrase_threshold = 0.5  # Minimum speaking duration before considering phrase - filters out brief noise
        self.non_speaking_duration = 0.2  # Non-speaking audio to keep on both sides of phrase for context

        # v1.0 audio configuration - DELAYED INITIALIZATION
        # DON'T initialize PyAudio here - it blocks at import time!
        self.audio = None  # Will be initialized lazily
        self.audio_device = None  # Use system default
        self.chunk_size = 32768  # v1.0 setting

        # v2.0 threading architecture - for chunking and processing
        self.audio_queue = queue.Queue(maxsize=10)
        self.stop_event = threading.Event()
        self.is_listening = False

        # Thread-safe microphone initialization
        self.microphone = None
        self.hardware_mutex = threading.Lock()

        # Microphone will be initialized on first use
        self.microphone_ready = False
        # REMOVED: Non-existent initialization thread that was blocking

        # Microphone device index (None = use system default)
        self.MICROPHONE_DEVICE_INDEX = None

        # Start microphone initialization in background
        self.initialization_thread = threading.Thread(
            target=self._initialize_microphone_async,
            name="AudioInput_Init",
            daemon=True
        )
        self.initialization_thread.start()

        self.logger.info("Initialized with v1.0 parameters + v2.0 threading")

    def _ensure_audio_initialized(self):
        """Lazily initialize PyAudio when first needed"""
        if self.audio is None:
            import pyaudio
            self.logger.info("Initializing PyAudio...")
            self.audio = pyaudio.PyAudio()
            self.logger.info("PyAudio initialized")

    def stop(self):
        """Stop audio input and cleanup resources"""
        self.logger.info("Stopping audio input...")

        # Signal stop to all threads
        self.stop_event.set()

        # Stop listening
        self.is_listening = False

        # Wait for initialization thread to finish
        if hasattr(self, 'initialization_thread') and self.initialization_thread.is_alive():
            self.initialization_thread.join(timeout=2.0)

        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        # Clean up microphone
        with self.hardware_mutex:
            self.microphone = None
            self.microphone_ready = False

        # Clean up PyAudio
        if hasattr(self, 'audio') and self.audio:
            try:
                self.audio.terminate()
                self.audio = None
            except:
                pass

        self.logger.info("Audio input stopped")

    def stop_listening_continuous(self):
        """Stop continuous listening (alias for stop method)"""
        self.stop()

    def _initialize_microphone_async(self):
        """Initialize microphone asynchronously to avoid blocking node startup"""
        try:
            with self.hardware_mutex:
                self.logger.info("Initializing microphone with default device in background...")

                # Check for stop event during initialization
                if self.stop_event.is_set():
                    self.logger.info("Stop requested during microphone initialization")
                    return

                # v2.0 approach: try different sample rates for compatibility
                sample_rates_to_try = [44100, 48000, 16000, 22050]

                for sample_rate in sample_rates_to_try:
                    if self.stop_event.is_set():
                        self.logger.info("Stop requested, aborting microphone initialization")
                        return

                    try:
                        self.logger.info(f"Attempting microphone with sample rate {sample_rate}...")

                        # # CRITICAL: Use NO device_index - let system choose default
                        # self.microphone = sr.Microphone(
                        #     chunk_size=self.chunk_size,
                        #     sample_rate=sample_rate
                        # )
                        if self.MICROPHONE_DEVICE_INDEX is None:
                            self.microphone = sr.Microphone(chunk_size=self.chunk_size, sample_rate=sample_rate)
                        else:
                            self.microphone = sr.Microphone(device_index=self.MICROPHONE_DEVICE_INDEX,
                                  chunk_size=self.chunk_size, sample_rate=sample_rate)


                        self.sample_rate = sample_rate
                        self.microphone_ready = True
                        self.logger.info(f"✓ Microphone initialized with default device at {sample_rate}Hz")
                        return

                    except Exception as e:
                        self.logger.warning(f"Failed with sample rate {sample_rate}: {e}")
                        if self.stop_event.is_set():
                            return
                        continue

                self.logger.error("Failed to initialize microphone with any sample rate")
                self.microphone = None

        except Exception as e:
            self.logger.error(f"Error initializing microphone: {e}")
            self.microphone = None

    def _initialize_microphone(self):
        """Legacy synchronous initialization - kept for compatibility"""
        # This now just waits for async initialization or returns False
        timeout = 10.0
        start_time = time.time()

        while not self.microphone_ready and not self.stop_event.is_set():
            if time.time() - start_time > timeout:
                self.logger.warning("Microphone initialization timeout")
                return False
            time.sleep(0.1)

        return self.microphone_ready

    def listen_for_speech(self, timeout=10.0, phrase_time_limit=10.0, adjust_for_ambient_noise=True):
        """
        Listen for speech - v2.0 implementation with v1.0 parameters
        Now checks if microphone is ready before attempting to listen
        """
        # Check if microphone is ready
        if not self.microphone_ready or self.microphone is None:
            return None

        # Check for stop event
        if self.stop_event.is_set():
            return None

        try:
            with self.hardware_mutex:
                with self.microphone as source:
                    self.logger.debug(f"Listening for speech (timeout={timeout}s)...")

                    # v2.0 ambient noise adjustment
                    if adjust_for_ambient_noise:
                        try:
                            self.logger.debug("Adjusting for ambient noise...")
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        except Exception as e:
                            self.logger.warning(f"Failed to adjust for ambient noise: {e}")

                    # Listen with v1.0/v2.0 combined parameters
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )

                    # Calculate audio length in seconds
                    audio_length = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
                    self.logger.debug(f"✓✓✓✓✓✓✓✓✓✓✓ -- Speech captured ({audio_length:.2f}s) -- ✓✓✓✓✓✓✓✓✓✓✓")
                    return audio

        except sr.WaitTimeoutError:
            self.logger.debug("Listening timeout - no speech detected")
            return None
        except Exception as e:
            self.logger.error(f"Error during speech capture: {e}")
            return None

    def recognize_speech(self, audio, openai_helper=None, language="en-US"):
        """
        Recognize speech using OpenAI Whisper (following v1.0/v2.0 pattern)

        Args:
            audio: Audio data to recognize
            openai_helper: OpenAI helper instance for API calls
            language: Language code for recognition

        Returns:
            Recognized text or None
        """
        if not audio:
            return None

        try:
            if openai_helper:
                # Use OpenAI Whisper via helper (v1.0 pattern)
                self.logger.debug("Using OpenAI Whisper for speech recognition...")

                # Convert audio to the format expected by OpenAI
                # This follows the v1.0/v2.0 approach
                text = openai_helper.speech_to_text(audio, language=language)

                if text:
                    self.logger.info(f"✓ Speech recognized: '{text}'")
                    return text
                else:
                    self.logger.debug("No speech recognized by OpenAI")
                    return None
            else:
                self.logger.error("No OpenAI helper provided for speech recognition")
                return None

        except Exception as e:
            self.logger.error(f"Error during speech recognition: {e}")
            return None


    def get_audio_from_queue(self, timeout=1.0):
        """Get audio data from processing queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def cleanup(self):
        """Cleanup audio resources"""
        try:
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            self.logger.error(f"Error during audio cleanup: {e}")

    def get_status(self):
        """Get audio input status"""
        return {
            "microphone_available": self.microphone is not None,
            "is_listening": self.is_listening,
            "energy_threshold": self.recognizer.energy_threshold,
            "pause_threshold": self.recognizer.pause_threshold,
            "sample_rate": getattr(self, 'sample_rate', 'unknown'),
            "chunk_size": self.chunk_size,
            "queue_size": self.audio_queue.qsize(),
            "audio_device": "system_default"
        }