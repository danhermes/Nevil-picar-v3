"""Factory for creating completion providers"""

from .base import CompletionBase
from .ollama import OllamaCompletion
from .gemma3_direct import Gemma3DirectCompletion
from .openai import OpenAICompletion
from .chub import ChubCompletion
import logging
import os

logger = logging.getLogger(__name__)


def get_completion_provider(provider_type: str = None) -> CompletionBase:
    """
    Get a completion provider based on environment variable or explicit type.

    Args:
        provider_type: Explicit provider type ("ollama", "gemma3_direct", "openai", "chub")
                      If None, reads from ZOE_AI env var (default: "ollama")

    Returns:
        CompletionBase implementation instance

    Raises:
        ValueError: If provider_type is invalid
    """
    if provider_type is None:
        provider_type = os.getenv("ZOE_AI", "ollama").lower()

    logger.info(f"Creating completion provider: {provider_type}")

    if provider_type == "ollama":
        return OllamaCompletion()
    elif provider_type == "gemma3_direct":
        return Gemma3DirectCompletion()
    elif provider_type == "openai":
        return OpenAICompletion()
    elif provider_type == "chub":
        return ChubCompletion()
    else:
        raise ValueError(
            f"Invalid completion provider: {provider_type}. "
            f"Valid options: ollama, gemma3_direct, openai, chub"
        )
