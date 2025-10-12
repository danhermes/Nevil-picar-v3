"""Abstract base class for completion providers"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CompletionBase(ABC):
    """
    Abstract base class for completion providers.

    Defines the interface that all completion providers must implement.
    Providers can use Ollama, direct model loading, OpenAI, etc.
    """

    @abstractmethod
    def __init__(self):
        """Initialize the completion provider and load environment variables"""
        pass

    @abstractmethod
    def load_env_variables(self):
        """
        Load environment variables from .env files.

        Should handle loading from multiple locations (current dir, root, etc)
        """
        pass

    @abstractmethod
    def get_completion(self, messages: List[Dict[str, str]],
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      **kwargs) -> str:
        """
        Get a completion from the provider.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated completion text
        """
        pass

    @abstractmethod
    def convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to provider-specific format.

        Args:
            messages: Standard message format

        Returns:
            Provider-specific message format
        """
        pass

    def refresh_session(self):
        """
        Refresh/clear session context (optional).

        Default implementation is a no-op. Override if provider needs session management.
        """
        logger.info(f"refresh_session called (no-op in base class)")
        pass

    def get_response_with_continuity(self, messages: List[Dict[str, str]],
                                    temperature: Optional[float] = None,
                                    **kwargs):
        """
        Get response with error handling and retry logic.

        Default implementation calls get_completion. Override for custom retry logic.

        Args:
            messages: Message list
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Response object or text
        """
        return self.get_completion(messages, temperature, **kwargs)
