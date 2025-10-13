"""Direct espeak TTS provider - bypasses broken pyttsx3"""

import logging
import subprocess
import os
from typing import Optional
from .base import TTSProviderBase

logger = logging.getLogger(__name__)


class EspeakTTSProvider(TTSProviderBase):
    """
    TTS provider using espeak directly (not pyttsx3).

    Pros:
        - Very fast (~instant generation)
        - No API costs
        - Works offline
        - No network latency
        - Bypasses broken pyttsx3 wrapper

    Cons:
        - Robotic/synthetic voice quality
        - Limited voice options
    """

    def __init__(self):
        """Initialize espeak TTS provider"""
        # Check if espeak is available
        try:
            result = subprocess.run(
                ["espeak", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                raise RuntimeError("espeak not found or not working")

            logger.info(f"espeak TTS provider initialized: {result.stdout.strip()}")

        except Exception as e:
            logger.error(f"Failed to initialize espeak: {e}")
            raise

    def generate_speech(self, text: str, output_file: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using espeak command directly.

        Args:
            text: Text to convert to speech
            output_file: Path to save WAV file
            voice: Voice name (e.g., "en", "en-us", "en-gb") - optional

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"[ESPEAK] Starting generation for: '{text[:50]}...' -> {output_file}")

        if not text or not text.strip():
            logger.error("[ESPEAK] Empty text provided")
            return False

        try:
            # Generate to temp file, then resample to match OpenAI format (24000 Hz)
            temp_file = output_file + ".temp.wav"
            logger.debug(f"[ESPEAK] Temp file: {temp_file}")

            # Build espeak command
            cmd = ["espeak", "-w", temp_file]

            # Map OpenAI voices to espeak voices
            # OpenAI voices: onyx, alloy, echo, fable, nova, shimmer
            # espeak voices: en-us, en-gb, en-scottish, etc.
            voice_mapping = {
                "onyx": "en-us",
                "alloy": "en-us",
                "echo": "en-gb",
                "fable": "en-us",
                "nova": "en-us",
                "shimmer": "en-gb"
            }

            # Use mapped voice or default to en-us
            if voice in voice_mapping:
                espeak_voice = voice_mapping[voice]
                logger.info(f"[ESPEAK] Mapped OpenAI voice '{voice}' -> espeak voice '{espeak_voice}'")
            elif voice and voice in ["en", "en-us", "en-gb", "en-uk", "en-scottish"]:
                # Already a valid espeak voice
                espeak_voice = voice
            else:
                # No voice or unknown voice, use default
                espeak_voice = "en-us"
                logger.info(f"[ESPEAK] Using default voice '{espeak_voice}'")

            cmd.extend(["-v", espeak_voice])

            # Add speed control (default 175 wpm, range 80-450)
            cmd.extend(["-s", "160"])  # Slightly slower for clarity

            # Add the text
            cmd.append(text)

            logger.info(f"[ESPEAK] Running command: {' '.join(cmd[:5])}... (text truncated)")

            # Execute espeak
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            logger.info(f"[ESPEAK] espeak return code: {result.returncode}")
            if result.stdout:
                logger.debug(f"[ESPEAK] stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"[ESPEAK] stderr: {result.stderr}")

            if result.returncode != 0:
                logger.error(f"[ESPEAK] espeak command failed with code {result.returncode}")
                return False

            if not os.path.exists(temp_file):
                logger.error(f"[ESPEAK] Temp file not created: {temp_file}")
                return False

            temp_size = os.path.getsize(temp_file)
            logger.info(f"[ESPEAK] Temp file created: {temp_size} bytes")

            # Resample to 24000 Hz to match OpenAI format (so Music() plays it correctly)
            logger.debug(f"[ESPEAK] Resampling {temp_file} -> {output_file}")
            sox_result = subprocess.run(
                ["sox", temp_file, "-r", "24000", output_file],
                capture_output=True,
                text=True,
                timeout=5
            )

            logger.info(f"[ESPEAK] sox return code: {sox_result.returncode}")
            if sox_result.stderr:
                logger.warning(f"[ESPEAK] sox stderr: {sox_result.stderr}")

            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"[ESPEAK] Temp file removed")

            if sox_result.returncode == 0 and os.path.exists(output_file):
                final_size = os.path.getsize(output_file)
                logger.info(f"[ESPEAK] SUCCESS! Output file: {output_file} ({final_size} bytes)")
                return True
            else:
                logger.error(f"[ESPEAK] sox resample failed: {sox_result.stderr}")
                return False

        except Exception as e:
            logger.error(f"[ESPEAK] Exception during TTS: {e}", exc_info=True)
            return False

    def get_available_voices(self) -> list:
        """Get list of available espeak voices"""
        try:
            result = subprocess.run(
                ["espeak", "--voices"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse output and extract voice names
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                voices = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4:
                        voices.append(parts[3])  # VoiceName column
                return voices
            return []
        except:
            return ["en", "en-us", "en-gb"]  # Fallback defaults

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "espeak"
