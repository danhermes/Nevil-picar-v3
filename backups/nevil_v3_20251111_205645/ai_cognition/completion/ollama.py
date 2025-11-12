"""Ollama completion provider"""

from .base import CompletionBase
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
import os
import time

logger = logging.getLogger(__name__)


class OllamaCompletion(CompletionBase):
    """
    Completion provider using Ollama via OpenAI-compatible API.

    Uses the Ollama server with OpenAI client for compatibility.
    """

    def __init__(self):
        """Initialize Ollama client"""
        self.load_env_variables()

        self.api_key = "ollama"  # Ollama doesn't require a real key
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://91.99.169.12:11434/v1")
        self.model = os.getenv("OLLAMA_MODEL")

        if not self.model:
            raise ValueError("OLLAMA_MODEL required for Ollama completion provider")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=ollama_base_url,
            max_retries=0
        )

        logger.info(f"OllamaCompletion initialized with base_url: {ollama_base_url}")

    def load_env_variables(self):
        """Load environment variables from .env files"""
        logger.info(f"OLLAMA_BASE_URL before dotenv: {os.getenv('OLLAMA_BASE_URL')}")

        # Try to load from current directory
        load_dotenv()

        # Also try to load from root directory (one level up from helpers)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        root_env_path = os.path.join(root_dir, '.env')
        if os.path.exists(root_env_path):
            load_dotenv(root_env_path)
            logger.info(f"Loaded environment variables from root .env file: {root_env_path}")
        else:
            logger.warning(f".env file not found at: {root_env_path}")

        logger.info(f"OLLAMA_BASE_URL after dotenv: {os.getenv('OLLAMA_BASE_URL')}")

    def get_completion(self, messages: List[Dict[str, str]],
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      **kwargs) -> str:
        """
        Get completion from Ollama.

        Args:
            messages: Message list in standard format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama-specific parameters

        Returns:
            Generated completion text
        """
        if not messages:
            logger.error("No messages provided to Ollama")
            return None

        # Convert messages if needed
        converted_messages = self.convert_messages(messages)

        logger.info(f"Sending {len(converted_messages)} messages to Ollama model: {self.model}")

        max_retries = kwargs.get('max_retries', 3)

        for attempt in range(max_retries):
            try:
                response = self.get_response_with_continuity(
                    messages=converted_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

                if response and response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    logger.error("No valid response content received from Ollama")
                    return None

            except Exception as e:
                logger.error(f"Error getting Ollama completion (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2)

    def convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to Ollama format.

        Ollama supports standard OpenAI message format, so minimal conversion needed.
        Just ensures proper role and content keys.

        Args:
            messages: Standard message format

        Returns:
            Messages in Ollama-compatible format
        """
        converted = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                converted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            else:
                logger.warning(f"Skipping invalid message: {msg}")

        return converted

    def get_response_with_continuity(self, messages: List[Dict[str, str]],
                                    temperature: Optional[float] = None,
                                    max_tokens: Optional[int] = None,
                                    **kwargs):
        """
        Call Ollama with retry logic for resilience.

        Args:
            messages: Message list
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            OpenAI-compatible response object
        """
        while True:
            try:
                logger.info(f"-------- Calling Ollama --------")
                params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature if temperature is not None else 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 1.1,
                }
                logger.info(f"-------- Called Ollama --------")
                logger.info(f"Model: {self.model}")
                logger.info(f"Messages: {len(messages)} messages")
                logger.info(f"Temperature: {temperature}")

                if max_tokens is not None:
                    params["max_tokens"] = max_tokens

                response = self.client.chat.completions.create(**params)

                logger.info(f"Ollama response received")

                if response is None:
                    logger.error("Ollama returned None")
                    return None

                return response

            except Exception as e:
                logger.error(f"Unexpected Ollama error: {e}. Retrying in 5s...")
                time.sleep(5)

    def refresh_session(self):
        """
        Clear Ollama session context.

        Sends a request to unload the model from memory.
        """
        try:
            import subprocess
            logger.info(f"SceneLoader: Clearing session for {self.model}")

            # Use curl to send unload request to Ollama
            cmd = [
                'curl', '-s',
                os.getenv("OLLAMA_BASE_URL", "http://91.99.169.12:11434").replace("/v1", ""),
                '/api/generate',
                '-d', f'{{"model": "{self.model}", "keep_alive": 0}}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            logger.info(f"Session clear result: {result.stdout}")

        except Exception as e:
            logger.warning(f"Could not clear Ollama session: {e}")
