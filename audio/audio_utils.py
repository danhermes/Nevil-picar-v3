"""
Audio Utilities - Extracted from v1.0

These functions are used VERBATIM from the working v1.0 implementation.
DO NOT modify these - they work perfectly.
"""

import os
import sys
import time

# Color printing utilities (from v1.0 utils.py)
GRAY = '1;30'
RED = '0;31'
GREEN = '0;32'
YELLOW = '0;33'
BLUE = '0;34'
PURPLE = '0;35'
DARK_GREEN = '0;36'
WHITE = '0;37'

def print_color(msg, end='\n', file=sys.stdout, flush=False, color=''):
    print('\033[%sm%s\033[0m'%(color, msg), end=end, file=file, flush=flush)

def gray_print(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=GRAY)

def warn(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=YELLOW)

def error(msg, end='\n', file=sys.stdout, flush=False):
    print_color(msg, end=end, file=file, flush=flush, color=RED)


def sox_volume(input_file, output_file, volume):
    """
    Volume adjustment using sox - EXACT v1.0 implementation

    DO NOT MODIFY - This works perfectly in v1.0
    """
    import sox

    try:
        transform = sox.Transformer()
        transform.vol(volume)
        transform.build(input_file, output_file)
        return True
    except Exception as e:
        print(f"sox_volume err: {e}")
        return False


def generate_tts_filename(prefix="", volume_db=None):
    """
    Generate timestamped filenames for TTS files - EXACT v1.0 implementation

    DO NOT MODIFY - This works perfectly in v1.0
    """
    timestamp = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
    raw_file = f"./tts/{prefix}{timestamp}_raw.wav"

    if volume_db is not None:
        processed_file = f"./tts/{prefix}{timestamp}_{volume_db}dB.wav"
        return raw_file, processed_file
    return raw_file


def play_audio_file(music, tts_file):
    """
    Play audio file and clean up after - EXACT v1.0 implementation

    DO NOT MODIFY - This works perfectly in v1.0
    Uses Music() from robot_hat exactly as specified
    """
    try:
        if os.path.exists(tts_file):
            music.music_play(tts_file)
            while music.pygame.mixer.music.get_busy():
                time.sleep(0.1)
            music.music_stop()
            os.remove(tts_file)
    except Exception as e:
        print(f"Error playing TTS: {e}")


def ensure_tts_directory():
    """Ensure TTS directory exists"""
    os.makedirs("./tts", exist_ok=True)