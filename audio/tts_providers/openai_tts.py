"""OpenAI TTS provider"""

import os
import logging
from typing import Optional
from .base import TTSProviderBase

logger = logging.getLogger(__name__)


class OpenAITTSProvider(TTSProviderBase):
    """
    TTS provider using OpenAI API (tts-1 or tts-1-hd).

    Requires:
        - OPENAI_API_KEY environment variable
        - NEVIL_TTS environment variable (defaults to 'tts-1')
    """

    def __init__(self):
        """Initialize OpenAI TTS provider"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.model = os.getenv('NEVIL_TTS', 'tts-1')

        # Speed parameter: 0.25 to 4.0 (default 1.0)
        # <1.0 = slower, >1.0 = faster
        self.speed = float(os.getenv('NEVIL_TTS_SPEED', '1.0'))

        logger.info(f"OpenAI TTS provider initialized with model: {self.model}, speed: {self.speed}")

    def generate_speech(self, text: str, output_file: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using OpenAI TTS API.

        Args:
            text: Text to convert to speech
            output_file: Path to save WAV file
            voice: Voice name (onyx, alloy, echo, fable, nova, shimmer)

        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            return False

        if voice is None:
            voice = "onyx"

        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            response = client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                response_format="wav",
                speed=self.speed  # Control speech speed
            )

            with open(output_file, "wb") as f:
                f.write(response.content)

            logger.debug(f"OpenAI TTS completed: {output_file}")
            return True

        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return False

    def get_available_voices(self) -> list:
        """Get list of available OpenAI voices"""
        return ["onyx", "alloy", "echo", "fable", "nova", "shimmer"]

    def get_provider_name(self) -> str:
        """Get provider name"""
        return f"openai_{self.model}"
