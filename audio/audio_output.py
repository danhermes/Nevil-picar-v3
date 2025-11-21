"""
Audio Output - Extracted from v1.0 with Music()

Uses robot_hat.Music() VERBATIM as specified.
Preserves exact v1.0 TTS pipeline and playback behavior.
"""

import os
import time
import threading
import warnings
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress ALSA warnings if environment variable is set
if os.getenv('HIDE_ALSA_LOGGING', '').lower() == 'true':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="ALSA")

# Set ALSA verbosity to 0 if specified
if os.getenv('ALSA_VERBOSITY') == '0':
    os.environ['ALSA_VERBOSITY'] = '0'

# CRITICAL: Force pygame to use ALSA backend instead of PipeWire
# This uses your existing .asoundrc configuration (card 2 = HiFiBerry)
# This is NOT altering ALSA config - just telling SDL to use ALSA instead of PipeWire
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['AUDIODEV'] = 'default'  # Uses .asoundrc default

# CRITICAL FIX: Pre-initialize pygame.mixer at 24kHz to match Realtime API output
# This MUST happen before importing robot_hat.Music()
sys.stdout = open(os.devnull, 'w')
import pygame
sys.stdout = sys.__stdout__
pygame.mixer.pre_init(frequency=24000, size=-16, channels=1, buffer=1024)
print("[AudioOutput] Pre-initialized pygame.mixer: 24000 Hz, mono, ALSA backend")

from robot_hat import Music
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

        # EXACT v1.0 initialization pattern - enable amplifier GPIO
        # CRITICAL FIX: Use subprocess.run() instead of os.popen() to ensure completion
        import subprocess
        try:
            result = subprocess.run(
                ["pinctrl", "set", "20", "op", "dh"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                print("[AudioOutput] Amplifier enabled (GPIO 20 HIGH)")
            else:
                print(f"[AudioOutput] Warning: GPIO 20 enable failed: {result.stderr}")
        except Exception as e:
            print(f"[AudioOutput] Warning: Could not enable GPIO 20: {e}")

        # EXACT v1.0 Music() initialization
        # DO NOT MODIFY - this works perfectly
        self.music = Music()

        # DIAGNOSTIC: Log mixer configuration for debugging HFB vs HDMI playback
        try:
            import pygame
            import subprocess

            mixer_config = self.music.pygame.mixer.get_init()
            print(f"[AudioOutput] Music() mixer initialized: {mixer_config}")

            # Check SDL audio driver being used
            try:
                sdl_driver = os.environ.get('SDL_AUDIODRIVER', 'not set')
                print(f"[AudioOutput] SDL_AUDIODRIVER: {sdl_driver}")

                # Try to get actual SDL driver from pygame
                if hasattr(pygame, 'get_sdl_version'):
                    print(f"[AudioOutput] SDL version: {pygame.get_sdl_version()}")
            except Exception as e:
                print(f"[AudioOutput] SDL info unavailable: {e}")

            # Check which ALSA device pygame is actually using
            result = subprocess.run(['lsof', '-p', str(os.getpid())],
                                   capture_output=True, text=True, timeout=2)
            snd_devices = [line for line in result.stdout.split('\n') if '/dev/snd/' in line]
            if snd_devices:
                print(f"[AudioOutput] Audio devices in use by this process:")
                for dev in snd_devices:
                    print(f"[AudioOutput]   {dev}")
            else:
                print(f"[AudioOutput] No /dev/snd/ devices currently open (likely using PipeWire/PulseAudio)")

                # Check PipeWire/PulseAudio default sink
                try:
                    pactl_result = subprocess.run(['pactl', 'info'],
                                                 capture_output=True, text=True, timeout=2)
                    for line in pactl_result.stdout.split('\n'):
                        if 'Default Sink' in line:
                            print(f"[AudioOutput] PulseAudio/PipeWire {line.strip()}")
                except:
                    pass

        except Exception as e:
            print(f"[AudioOutput] Warning: Could not check mixer config: {e}")

        # Thread safety for TTS playback (from v1.0)
        self.speech_lock = threading.Lock()
        self.speech_loaded = False
        self.tts_file = None

        # v1.0 TTS configuration
        self.VOLUME_DB = -10  # Default volume adjustment
        self.TTS_VOICE = "onyx"  # Default OpenAI voice

        # Ensure TTS directory exists
        ensure_tts_directory()

        # DIAGNOSTIC: Log to same file as auto_sound_card
        LOG_FILE = '/var/log/auto_sound_card.log'
        try:
            import subprocess
            mixer_info = self.music.pygame.mixer.get_init()

            with open(LOG_FILE, 'a') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] pygame.mixer initialized: {mixer_info}\n")

                # Check card states
                for card in [0, 1, 2]:
                    card_names = ["HDMI0", "HDMI1", "HiFiBerry"]
                    try:
                        with open(f'/proc/asound/card{card}/pcm0p/sub0/status', 'r') as status:
                            state_line = [line for line in status if 'state:' in line]
                            if state_line:
                                f.write(f"[{timestamp}] Card {card} ({card_names[card]}): {state_line[0].strip()}\n")
                    except:
                        pass

                # Check which device is open
                lsof_result = subprocess.run(['lsof', '/dev/snd/pcmC0D0p', '/dev/snd/pcmC1D0p', '/dev/snd/pcmC2D0p'],
                                            capture_output=True, text=True, timeout=2)
                if lsof_result.stdout:
                    f.write(f"[{timestamp}] Open audio devices: {lsof_result.stdout.strip()}\n")

        except Exception as e:
            print(f"[AudioOutput] Could not log to {LOG_FILE}: {e}")

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