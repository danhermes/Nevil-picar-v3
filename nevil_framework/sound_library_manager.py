"""
SoundLibraryManager - Curated Sound Effects and Music Library

Similar to gesture library approach - AI calls sounds by name instead of
generating/streaming everything. Massively reduces costs and latency.

AI calls: play_sound(name="calm_music", volume=0.5)
Instead of: streaming audio data continuously
"""

import os
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class SoundLibraryManager:
    """
    Manages curated library of sounds and music for AI-driven playback.

    Approach: AI calls sounds by name (like gestures) instead of streaming audio.
    """

    # Sound library definitions
    # Each sound has: name, file_path, description, category, default_volume
    SOUND_LIBRARY = {
        # === BACKGROUND MUSIC ===
        "calm_music": {
            "type": "music",
            "description": "Calm, peaceful background music for relaxation",
            "file_path": "sounds/music/calm.wav",
            "default_volume": 0.3,
            "duration": "loop"  # Can loop or specify seconds
        },
        "upbeat_music": {
            "type": "music",
            "description": "Upbeat, energetic music for excitement",
            "file_path": "sounds/music/upbeat.wav",
            "default_volume": 0.4,
            "duration": "loop"
        },
        "dramatic_music": {
            "type": "music",
            "description": "Dramatic, intense music for important moments",
            "file_path": "sounds/music/dramatic.wav",
            "default_volume": 0.5,
            "duration": "loop"
        },

        # === SOUND EFFECTS ===
        "beep": {
            "type": "effect",
            "description": "Simple beep sound for notifications",
            "file_path": "sounds/effects/beep.wav",
            "default_volume": 0.5,
            "duration": 0.5
        },
        "chime": {
            "type": "effect",
            "description": "Pleasant chime for positive feedback",
            "file_path": "sounds/effects/chime.wav",
            "default_volume": 0.6,
            "duration": 1.0
        },
        "alert": {
            "type": "effect",
            "description": "Alert sound for important notifications",
            "file_path": "sounds/effects/alert.wav",
            "default_volume": 0.7,
            "duration": 0.8
        },
        "success": {
            "type": "effect",
            "description": "Success sound for achievements",
            "file_path": "sounds/effects/success.wav",
            "default_volume": 0.6,
            "duration": 1.5
        },

        # === AMBIENT SOUNDS ===
        "rain": {
            "type": "ambient",
            "description": "Rain sounds for calming atmosphere",
            "file_path": "sounds/ambient/rain.wav",
            "default_volume": 0.2,
            "duration": "loop"
        },
        "ocean": {
            "type": "ambient",
            "description": "Ocean waves for peaceful atmosphere",
            "file_path": "sounds/ambient/ocean.wav",
            "default_volume": 0.2,
            "duration": "loop"
        },
        "nature": {
            "type": "ambient",
            "description": "Nature sounds (birds, forest) for relaxation",
            "file_path": "sounds/ambient/nature.wav",
            "default_volume": 0.2,
            "duration": "loop"
        },

        # === YOUTUBE MUSIC (uses youtube_music.py) ===
        "youtube_lofi": {
            "type": "youtube",
            "description": "Lo-fi hip hop music from YouTube",
            "url": "https://www.youtube.com/watch?v=jfKfPfyJRdk",  # Lofi Girl
            "default_volume": 0.3,
            "duration": "stream"
        },
        "youtube_jazz": {
            "type": "youtube",
            "description": "Smooth jazz music from YouTube",
            "url": "https://www.youtube.com/watch?v=Dx5qFachd3A",  # Jazz cafe
            "default_volume": 0.3,
            "duration": "stream"
        },
        "youtube_classical": {
            "type": "youtube",
            "description": "Classical music from YouTube",
            "url": "https://www.youtube.com/watch?v=jgpJVI3tDbY",  # Classical music
            "default_volume": 0.3,
            "duration": "stream"
        },
    }

    def __init__(
        self,
        audio_output_callback: Optional[Callable] = None,
        sounds_directory: Optional[str] = None
    ):
        """
        Initialize sound library manager.

        Args:
            audio_output_callback: Callback to play audio (AudioOutput.play_audio_file)
            sounds_directory: Base directory for sound files (default: ./sounds/)
        """
        self.audio_callback = audio_output_callback
        self.sounds_dir = sounds_directory or os.path.join(
            os.path.dirname(__file__), "..", "sounds"
        )

        # Currently playing sound
        self.current_sound = None
        self.is_playing = False

        logger.info(f"SoundLibraryManager initialized with {len(self.SOUND_LIBRARY)} sounds")

    def get_available_sounds(self) -> Dict[str, Dict[str, Any]]:
        """Get all available sounds in the library"""
        return self.SOUND_LIBRARY

    def get_sound_info(self, sound_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific sound.

        Args:
            sound_name: Name of the sound

        Returns:
            Sound info dict or None if not found
        """
        return self.SOUND_LIBRARY.get(sound_name)

    def play_sound(
        self,
        sound_name: str,
        volume: Optional[float] = None,
        loop: bool = False
    ) -> Dict[str, Any]:
        """
        Play a sound from the library.

        Args:
            sound_name: Name of the sound to play
            volume: Volume level (0.0-1.0), uses default if None
            loop: Whether to loop the sound

        Returns:
            Result dict with status
        """
        # Get sound info
        sound_info = self.get_sound_info(sound_name)
        if not sound_info:
            logger.error(f"Sound not found: {sound_name}")
            return {"status": "error", "message": f"Sound '{sound_name}' not found"}

        # Use default volume if not specified
        volume = volume if volume is not None else sound_info["default_volume"]

        logger.info(f"🔊 Playing sound: {sound_name} (volume={volume}, type={sound_info['type']})")

        # Handle different sound types
        try:
            if sound_info["type"] == "youtube":
                return self._play_youtube_sound(sound_info, volume)
            else:
                return self._play_file_sound(sound_info, volume, loop)

        except Exception as e:
            logger.error(f"Error playing sound {sound_name}: {e}")
            return {"status": "error", "message": str(e)}

    def stop_sound(self) -> Dict[str, Any]:
        """
        Stop currently playing sound.

        Returns:
            Result dict with status
        """
        if not self.is_playing:
            return {"status": "info", "message": "No sound currently playing"}

        logger.info(f"🛑 Stopping sound: {self.current_sound}")

        try:
            # Stop via audio callback
            if self.audio_callback:
                # Assuming AudioOutput has a stop_playback method
                self.audio_callback.stop_playback()

            self.is_playing = False
            self.current_sound = None

            return {"status": "success", "message": "Sound stopped"}

        except Exception as e:
            logger.error(f"Error stopping sound: {e}")
            return {"status": "error", "message": str(e)}

    def _play_file_sound(
        self,
        sound_info: Dict[str, Any],
        volume: float,
        loop: bool
    ) -> Dict[str, Any]:
        """Play sound from local file"""
        file_path = os.path.join(self.sounds_dir, sound_info["file_path"])

        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Sound file not found: {file_path}")
            return {
                "status": "error",
                "message": f"Sound file not found: {file_path}"
            }

        # Play via audio callback
        if self.audio_callback:
            # Play the file (implementation depends on AudioOutput interface)
            # This would use robot_hat.Music() like TTS does
            self.audio_callback.music_play(file_path)

            self.is_playing = True
            self.current_sound = sound_info["file_path"]

            return {
                "status": "success",
                "message": f"Playing {sound_info['file_path']}",
                "duration": sound_info.get("duration", "unknown")
            }
        else:
            logger.error("No audio callback configured")
            return {"status": "error", "message": "No audio output available"}

    def _play_youtube_sound(
        self,
        sound_info: Dict[str, Any],
        volume: float
    ) -> Dict[str, Any]:
        """Play sound from YouTube URL"""
        from scripts.youtube_music import YouTubeMusicStreamer

        try:
            streamer = YouTubeMusicStreamer()
            streamer.stream_audio(sound_info["url"])

            self.is_playing = True
            self.current_sound = sound_info["url"]

            return {
                "status": "success",
                "message": f"Streaming from YouTube: {sound_info['description']}",
                "url": sound_info["url"]
            }

        except Exception as e:
            logger.error(f"Error streaming YouTube audio: {e}")
            return {"status": "error", "message": str(e)}

    def get_ai_function_definitions(self) -> list:
        """
        Get function definitions for AI integration.

        Returns list of function definitions that AI can call.
        Similar to gesture library pattern.
        """
        functions = []

        # Play sound function
        functions.append({
            "type": "function",
            "name": "play_sound",
            "description": (
                "Play a sound or music from the curated library. "
                "Use this instead of generating audio. Much faster and cheaper. "
                "\n\nAvailable sounds:\n" +
                "\n".join([
                    f"- {name}: {info['description']}"
                    for name, info in self.SOUND_LIBRARY.items()
                ])
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sound_name": {
                        "type": "string",
                        "enum": list(self.SOUND_LIBRARY.keys()),
                        "description": "Name of the sound to play"
                    },
                    "volume": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Volume level (0.0-1.0). Uses default if not specified."
                    }
                },
                "required": ["sound_name"]
            }
        })

        # Stop sound function
        functions.append({
            "type": "function",
            "name": "stop_sound",
            "description": "Stop currently playing sound or music",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        })

        return functions

    def get_stats(self) -> Dict[str, Any]:
        """Get sound library statistics"""
        return {
            "total_sounds": len(self.SOUND_LIBRARY),
            "is_playing": self.is_playing,
            "current_sound": self.current_sound,
            "sounds_by_type": {
                "music": len([s for s in self.SOUND_LIBRARY.values() if s["type"] == "music"]),
                "effect": len([s for s in self.SOUND_LIBRARY.values() if s["type"] == "effect"]),
                "ambient": len([s for s in self.SOUND_LIBRARY.values() if s["type"] == "ambient"]),
                "youtube": len([s for s in self.SOUND_LIBRARY.values() if s["type"] == "youtube"]),
            }
        }


# Example integration
def example_usage():
    """Example of how to use SoundLibraryManager with AI"""

    # Initialize with audio output
    from audio.audio_output import AudioOutput
    audio_output = AudioOutput()

    # Create sound library
    sound_library = SoundLibraryManager(audio_output_callback=audio_output.music)

    # Get AI function definitions (to add to AI's tools)
    ai_functions = sound_library.get_ai_function_definitions()

    # AI calls function like:
    # play_sound(sound_name="calm_music", volume=0.3)

    # In your AI function handler:
    def execute_ai_function(function_name: str, args: Dict[str, Any]):
        if function_name == "play_sound":
            return sound_library.play_sound(
                sound_name=args["sound_name"],
                volume=args.get("volume")
            )
        elif function_name == "stop_sound":
            return sound_library.stop_sound()

    logger.info("Sound library ready for AI integration")
