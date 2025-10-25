"""OpenAI completion provider"""

from .base import CompletionBase
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
import os
import time

# Use ai_cognition logger name so logs appear in ai_cognition.log
logger = logging.getLogger("ai_cognition")


class OpenAICompletion(CompletionBase):
    """
    Completion provider using OpenAI API.

    Uses official OpenAI API for GPT models.
    """

    def __init__(self):
        """Initialize OpenAI client"""
        self.load_env_variables()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY required for OpenAI completion provider")

        self.model = os.getenv("OPENAI_MODEL")
        if not self.model:
            logger.error("OPENAI_MODEL not found in environment variables")
            raise ValueError("OPENAI_MODEL required for OpenAI completion provider")

        self.client = OpenAI(
            api_key=self.api_key,
            max_retries=0
        )

        logger.info("OpenAICompletion initialized")

    def load_env_variables(self):
        """Load environment variables from .env files"""
        # Try to load from current directory
        load_dotenv()

        # Also try to load from root directory
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        root_env_path = os.path.join(root_dir, '.env')
        if os.path.exists(root_env_path):
            load_dotenv(root_env_path)
            logger.info(f"Loaded environment variables from root .env file: {root_env_path}")
        else:
            logger.warning(f".env file not found at: {root_env_path}")

    def get_completion(self, messages: List[Dict[str, str]],
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      **kwargs) -> str:
        """
        Get completion from OpenAI.

        Args:
            messages: Message list in standard format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            Generated completion text
        """
        if not messages:
            logger.error("No messages provided to OpenAI")
            return None

        # Convert messages if needed
        converted_messages = self.convert_messages(messages)

        logger.info(f"Sending {len(converted_messages)} messages to OpenAI model: {self.model}")

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
                    logger.error("No valid response content received from OpenAI")
                    return None

            except Exception as e:
                logger.error(f"Error getting OpenAI completion (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2)

    def convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to OpenAI format.

        OpenAI expects standard format, so minimal conver
        OpenAI expects standard format, so minimal conversion needed.

        Args:
            messages: Standard message format

        Returns:
            Messages in OpenAI-compatible format
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
        Call OpenAI with retry logic for resilience.

        Args:
            messages: Message list
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            OpenAI response object
        """
        try:
            logger.info(f"-------- Calling OpenAI --------")
            logger.info(f"Model: {self.model}")
            logger.info(f"Temperature: {temperature}")
            logger.info(f"Messages: {len(messages)} messages")
            logger.info(f"Message: {messages} ")

            params = {
                "model": self.model,
                "messages": messages,
                "response_format": {"type": "json_object"}  # Enforce JSON output
            }

            if temperature is not None:
                params["temperature"] = temperature

            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)

            logger.info(f"OpenAI response received")

            if response is None:
                logger.error("OpenAI returned None")
                return None

            return response

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def get_completion_with_image(self, prompt: str, image_data: str,
                                  temperature: Optional[float] = 0.7,
                                  max_tokens: Optional[int] = 300) -> str:
        """
        Get completion from OpenAI with image analysis (Vision API).

        Args:
            prompt: Text prompt/question about the image
            image_data: Base64-encoded image data
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated completion text describing the image
        """
        try:
            logger.info(f"-------- Calling OpenAI Vision API --------")
            logger.info(f"Model: {self.model}")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Image data length: {len(image_data)} chars")

            # Build the message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens
            }

            if temperature is not None:
                params["temperature"] = temperature

            response = self.client.chat.completions.create(**params)

            logger.info(f"OpenAI Vision response received")

            if response and response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                logger.error("No valid response content received from OpenAI Vision")
                return "I see an image but got no response from the vision API."

        except Exception as e:
            logger.error(f"OpenAI Vision API error: {e}")
            return f"I see an image but encountered an error analyzing it: {str(e)}"
