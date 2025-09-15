"""
Nevil v3.0 Audio Module

Preserves v1.0 audio components with v2.0 enhancements.
"""

from .audio_output import AudioOutput
from .audio_input import AudioInput
from .audio_utils import play_audio_file, generate_tts_filename

__all__ = [
    'AudioOutput',
    'AudioInput',
    'play_audio_file',
    'generate_tts_filename'
]