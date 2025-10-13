"""Factory for creating TTS providers"""

import os
import logging
from .base import TTSProviderBase
from .openai_tts import OpenAITTSProvider
from .espeak_tts import EspeakTTSProvider

logger = logging.getLogger(__name__)


def get_tts_provider(provider_type: str = None) -> TTSProviderBase:
    """
    Get a TTS provider based on environment variable or explicit type.

    Args:
        provider_type: Explicit provider type ("tts-1", "tts-1-hd", "pyttsx3")
                      If None, reads from NEVIL_TTS env var (default: "tts-1")

    Returns:
        TTSProviderBase implementation instance

    Raises:
        ValueError: If provider_type is invalid

    Environment Variables:
        NEVIL_TTS: TTS engine to use
                   - "tts-1" or "tts-1-hd" = OpenAI (cloud, high quality)
                   - "espeak" = Local (instant, robotic)
        OPENAI_API_KEY: Required for tts-1/tts-1-hd

    Examples:
        # Use environment variable
        provider = get_tts_provider()  # Uses NEVIL_TTS

        # Explicit provider
        provider = get_tts_provider("espeak")   # Fast local TTS
        provider = get_tts_provider("tts-1")    # OpenAI standard
        provider = get_tts_provider("tts-1-hd") # OpenAI high quality
    """
    if provider_type is None:
        provider_type = os.getenv("NEVIL_TTS", "tts-1").lower()

    logger.info(f"Creating TTS provider: {provider_type}")

    # OpenAI providers
    if provider_type in ["tts-1", "tts-1-hd"]:
        return OpenAITTSProvider()
    elif provider_type == "espeak":
        return EspeakTTSProvider()
    else:
        raise ValueError(
            f"Invalid TTS provider: {provider_type}. "
            f"Valid options: tts-1, tts-1-hd, espeak"
        )
