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
    Generate timestamped filenames for TTS files - Updated for new folder structure
    """
    timestamp = time.strftime("%y-%m-%d_%H-%M-%S", time.localtime())
    raw_file = f"./audio/nevil_wavs/{prefix}{timestamp}_raw.wav"

    if volume_db is not None:
        processed_file = f"./audio/nevil_wavs/{prefix}{timestamp}_{volume_db}dB.wav"
        return raw_file, processed_file
    return raw_file


def play_audio_file(music, tts_file):
    """
    Play audio file and maintain only last 10 files
    Uses Music() from robot_hat exactly as specified
    """
    try:
        if os.path.exists(tts_file):
            music.music_play(tts_file)
            while music.pygame.mixer.music.get_busy():
                time.sleep(0.1)
            music.music_stop()

            # Clean up old files, keeping only the last 10
            cleanup_old_audio_files("./audio/nevil_wavs/", max_files=10)
    except Exception as e:
        print(f"Error playing TTS: {e}")


def ensure_tts_directory():
    """Ensure TTS directory exists"""
    os.makedirs("./audio/nevil_wavs", exist_ok=True)
    os.makedirs("./audio/user_wavs", exist_ok=True)


def cleanup_old_audio_files(directory, max_files=10):
    """
    Keep only the most recent max_files in the directory
    """
    try:
        # Get all .wav files in the directory
        wav_files = []
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith('.wav'):
                    file_path = os.path.join(directory, file)
                    wav_files.append((file_path, os.path.getmtime(file_path)))

            # Sort by modification time (oldest first)
            wav_files.sort(key=lambda x: x[1])

            # Remove oldest files if we have more than max_files
            if len(wav_files) > max_files:
                files_to_remove = len(wav_files) - max_files
                for i in range(files_to_remove):
                    try:
                        os.remove(wav_files[i][0])
                        print(f"Removed old audio file: {os.path.basename(wav_files[i][0])}")
                    except Exception as e:
                        print(f"Error removing file {wav_files[i][0]}: {e}")

    except Exception as e:
        print(f"Error cleaning up audio files: {e}")