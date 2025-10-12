"""Gemma3 Direct completion provider using transformers/torch"""

from .base import CompletionBase
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)


class Gemma3DirectCompletion(CompletionBase):
    """
    Completion provider using direct Gemma3 model loading with transformers/torch.

    Loads model from local filesystem and runs inference directly without API.
    """

    def __init__(self):
        """Initialize Gemma3 Direct provider"""
        self.load_env_variables()

        # Model path - can be overridden by env var
        self.model_path = os.getenv(
            "GEMMA3_MODEL_PATH",
            "/mnt/bigred/models/nidum-gemma-3-4b-it-uncensored_q8_0"
        )

        # Model and tokenizer will be loaded on first use
        self.model = None
        self.tokenizer = None

        logger.info(f"Gemma3DirectCompletion initialized with model path: {self.model_path}")

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

    def _load_model(self):
        """
        Load model and tokenizer if not already loaded.

        Lazy loading to avoid loading model on init.
        """
        if self.model is not None and self.tokenizer is not None:
            logger.info("Model already loaded (using cached instance)")
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            p = Path(self.model_path)
            logger.info(f"Loading Gemma model from: {p}")
            logger.info(f"Path exists: {p.exists()}, Is directory: {p.is_dir()}")

            if p.exists():
                logger.info(f"Directory contents: {list(p.iterdir())}")

            self.tokenizer = AutoTokenizer.from_pretrained(p, use_fast=True, local_files_only=True)

            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                p,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                local_files_only=True
            )

            # Set generation config
            self.model.generation_config.do_sample = True
            self.model.generation_config.temperature = 0.7
            self.model.generation_config.top_p = 0.9
            self.model.generation_config.repetition_penalty = 1.1

            logger.info("Gemma model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading Gemma model: {e}")
            raise

    def get_completion(self, messages: List[Dict[str, str]],
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      **kwargs) -> str:
        """
        Get completion using direct Gemma3 inference.

        Args:
            messages: Message list in standard format
            temperature: Sampling temperature (applied during generation)
            max_tokens: Maximum tokens to generate (default: 200)
            **kwargs: Additional parameters

        Returns:
            Generated completion text
        """
        if not messages:
            logger.error("No messages provided to Gemma3 Direct")
            return None

        try:
            # Ensure model is loaded
            self._load_model()

            # Convert messages to single prompt
            prompt = self._messages_to_prompt(messages)

            # Tokenize input and check length - truncate to 1900 tokens to leave room for generation
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1900)
            input_token_count = inputs['input_ids'].shape[1]
            logger.info(f"========== INPUT TOKEN COUNT: {input_token_count} (max 2048) ==========")

            # Log prompt preview
            logger.info(f"Prompt preview (first 500 chars): {prompt[:500]}")
            logger.info(f"Prompt preview (last 500 chars): {prompt[-500:]}")

            # Warn if we had to truncate
            original_token_count = len(self.tokenizer.encode(prompt))
            if original_token_count > 1900:
                logger.warning(
                    f"Truncated context from {original_token_count} to {input_token_count} tokens (model max: 2048)"
                )

            logger.info("Calling Gemma Direct (Transformers/Torch) =========================>>>>")

            # Override temperature if provided
            if temperature is not None:
                self.model.generation_config.temperature = temperature

            # Generate output
            max_new_tokens = max_tokens or 200
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
            )

            # Decode the output
            output = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
            logger.info("<<<<<<<<<<<<<<<<<<<<<<<<<<===== Gemma Direct Output")
            logger.info(f"Generated output: {output}")

            return output

        except Exception as e:
            logger.error(f"Error calling Gemma Direct: {str(e)}")
            return f"Error: Could not call Gemma Direct - {str(e)}"

    def convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to Gemma3 format (no conversion needed for direct call).

        Args:
            messages: Standard message format

        Returns:
            Messages as-is (conversion happens in _messages_to_prompt)
        """
        return messages

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message list to single prompt string for Gemma3.

        Args:
            messages: List of message dicts

        Returns:
            Combined prompt string
        """
        prompt_parts = []
        for msg in messages:
            if msg["role"] == "system":
                prompt_parts.append(msg["content"])
            elif msg["role"] == "user":
                prompt_parts.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                prompt_parts.append(f"Assistant: {msg['content']}")

        return "\n\n".join(prompt_parts)

    def refresh_session(self, model_name: str = None):
        """
        Refresh session by unloading model from memory.

        Args:
            model_name: Model identifier (ignored, uses self.model_path)
        """
        logger.info(f"Gemma3Direct: Unloading model from memory (path: {self.model_path})")
        self.model = None
        self.tokenizer = None

        # Force garbage collection
        import gc
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        logger.info("Gemma3Direct: Model unloaded")
