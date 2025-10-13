"""Base class for TTS providers"""

from abc import ABC, abstractmethod
from typing import Optional


class TTSProviderBase(ABC):
    """
    Base class for TTS providers.

    All TTS providers must implement this interface.
    """

    @abstractmethod
    def generate_speech(self, text: str, output_file: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech from text and save to file.

        Args:
            text: Text to convert to speech
            output_file: Path to save audio file
            voice: Voice name/ID (provider-specific)

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list:
        """
        Get list of available voices.

        Returns:
            list: List of voice names/IDs
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            str: Provider name (e.g., "openai", "pyttsx3")
        """
        pass
