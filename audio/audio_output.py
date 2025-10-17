"""
Audio Output - Extracted from v1.0 with Music()

Uses robot_hat.Music() VERBATIM as specified.
Preserves exact v1.0 TTS pipeline and playback behavior.
"""

import os
import time
import threading
import warnings
from dotenv import load_dotenv
from robot_hat import Music

# Load environment variables from .env file
load_dotenv()

# Suppress ALSA warnings if environment variable is set
if os.getenv('HIDE_ALSA_LOGGING', '').lower() == 'true':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="ALSA")

# Set ALSA verbosity to 0 if specified
if os.getenv('ALSA_VERBOSITY') == '0':
    os.environ['ALSA_VERBOSITY'] = '0'
from .audio_utils import play_audio_file, generate_tts_filename, ensure_tts_directory


class AudioOutput:
    """
    Audio output wrapper using v1.0 Music() implementation VERBATIM.

    Key Points:
    - Uses Music() from robot_hat exactly as in v1.0
    - NO manual device/channel specification - uses defaults only
    - Preserves exact TTS pipeline: OpenAI → sox_volume → Music()
    - Thread-safe playback management
    """

    def __init__(self):
        """Initialize audio output using EXACT v1.0 pattern"""

        # EXACT v1.0 initialization pattern
        # DO NOT MODIFY - this is from init_system()
        os.popen("pinctrl set 20 op dh")  # enable robot_hat speaker switch

        # EXACT v1.0 Music() initialization
        # DO NOT MODIFY - this works perfectly
        self.music = Music()

        # Thread safety for TTS playback (from v1.0)
        self.speech_lock = threading.Lock()
        self.speech_loaded = False
        self.tts_file = None

        # v1.0 TTS configuration
        self.VOLUME_DB = -10  # Default volume adjustment
        self.TTS_VOICE = "onyx"  # Default OpenAI voice

        # Ensure TTS directory exists
        ensure_tts_directory()

        print("[AudioOutput] Initialized with Music() - using defaults only")

    def generate_and_play_tts(self, message, openai_helper, volume_db=None, voice=None):
        """
        Generate TTS and play audio - EXACT v1.0 implementation

        This preserves the EXACT v1.0 TTS pipeline:
        1. OpenAI text_to_speech() API call
        2. sox_volume() processing
        3. Music() playback via play_audio_file()

        Args:
            message: Text to convert to speech
            openai_helper: OpenAI helper instance (from v1.0)
            volume_db: Volume adjustment in dB (default: self.VOLUME_DB)
            voice: Voice to use (default: self.TTS_VOICE)
        """
        if volume_db is None:
            volume_db = self.VOLUME_DB
        if voice is None:
            voice = self.TTS_VOICE

        # EXACT v1.0 handle_TTS_generation() implementation
        tts_start = time.time()
        try:
            tts_status = False
            generation_time = 0
            playback_time = 0

            if message != '':
                raw_file, processed_file = generate_tts_filename(volume_db=volume_db)

                # Time the generation
                gen_start = time.time()
                # EXACT v1.0 OpenAI API call pattern
                tts_status = openai_helper.text_to_speech(
                    message, raw_file, voice, response_format='wav'
                )
                generation_time = time.time() - gen_start
                print(f'[TTS BREAKDOWN] Generation: {generation_time*1000:.1f}ms')

            if tts_status:
                # Skip sox - use Music() directly like v1.0
                # Music() handles volume internally
                self.tts_file = raw_file
                with self.speech_lock:
                    self.speech_loaded = True

                # Time the playback
                play_start = time.time()
                # Play immediately using Music() VERBATIM
                self.play_loaded_speech()
                playback_time = time.time() - play_start
                print(f'[TTS BREAKDOWN] Playback: {playback_time*1000:.1f}ms')

            total_time = time.time() - tts_start
            print(f'[TTS BREAKDOWN] Total: {total_time*1000:.1f}ms (gen: {generation_time*1000:.1f}ms + play: {playback_time*1000:.1f}ms)')

            # Return tuple: (success, generation_time, playback_time)
            return (tts_status, generation_time, playback_time)

        except Exception as e:
            print(f'TTS generation error: {e}')
            return (False, 0, 0)

    def play_loaded_speech(self):
        """
        Play loaded TTS file - EXACT v1.0 speech_handler() logic

        DO NOT MODIFY - uses v1.0 play_audio_file() verbatim
        """
        with self.speech_lock:
            if not self.speech_loaded:
                return False

        try:
            print(f"Playing TTS file: {self.tts_file}")

            # EXACT v1.0 playback using Music()
            # DO NOT CHANGE - uses defaults only, no device specification
            play_audio_file(self.music, self.tts_file)

            with self.speech_lock:
                self.speech_loaded = False

            return True

        except Exception as e:
            print(f"Error playing TTS: {e}")
            with self.speech_lock:
                self.speech_loaded = False
            return False

    def is_playing(self):
        """Check if audio is currently playing"""
        try:
            return self.music.pygame.mixer.music.get_busy()
        except:
            return False

    def stop_playback(self):
        """Stop current playback"""
        try:
            self.music.music_stop()
        except Exception as e:
            print(f"Error stopping playback: {e}")

    def cleanup(self):
        """Cleanup audio resources"""
        try:
            self.stop_playback()
            with self.speech_lock:
                self.speech_loaded = False
                if self.tts_file and os.path.exists(self.tts_file):
                    os.remove(self.tts_file)
        except Exception as e:
            print(f"Error during audio cleanup: {e}")

    def stop(self):
        """Stop and cleanup audio resources - dispose of Music() properly"""
        try:
            print("[AudioOutput] Stopping and disposing of Music()...")

            # Stop any active playback
            if self.music:
                self.music.music_stop()

            # Clean up speech files
            with self.speech_lock:
                self.speech_loaded = False
                if self.tts_file and os.path.exists(self.tts_file):
                    os.remove(self.tts_file)
                    self.tts_file = None

            # Dispose of Music() object properly - this releases audio resources
            if hasattr(self.music, 'pygame') and self.music.pygame:
                if hasattr(self.music.pygame, 'mixer'):
                    self.music.pygame.mixer.quit()

            # Clear the music reference
            self.music = None

            print("[AudioOutput] Music() disposed successfully")

        except Exception as e:
            print(f"Error disposing of Music(): {e}")

    def __del__(self):
        """Ensure Music() is disposed when object is destroyed"""
        if hasattr(self, 'music') and self.music:
            self.stop()

    def get_status(self):
        """Get audio output status"""
        return {
            "music_initialized": self.music is not None,
            "is_playing": self.is_playing(),
            "speech_loaded": self.speech_loaded,
            "tts_file": self.tts_file,
            "volume_db": self.VOLUME_DB,
            "voice": self.TTS_VOICE
        }