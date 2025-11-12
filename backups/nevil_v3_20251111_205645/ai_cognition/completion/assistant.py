"""OpenAI Assistant completion provider (legacy)"""

from .base import CompletionBase
from openai import OpenAI
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging
import os
import time

logger = logging.getLogger(__name__)


class OpenAIAssistant(CompletionBase):
    """
    Completion provider using OpenAI Assistants API (legacy).

    Uses the Assistants API with thread management for stateful conversations.
    Note: This is slower than Chat Completions (4-7s vs 2-3s response time).
    Being sunset in H1 2026.
    """

    def __init__(self):
        """Initialize OpenAI Assistant client"""
        self.load_env_variables()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY required for OpenAI Assistant provider")

        self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID")
        if not self.assistant_id:
            logger.error("OPENAI_ASSISTANT_ID not found in environment variables")
            raise ValueError("OPENAI_ASSISTANT_ID required for OpenAI Assistant provider")

        self.client = OpenAI(api_key=self.api_key)

        # Thread management for stateful conversation
        self.current_thread = None
        self.thread_created = False

        logger.info(f"OpenAIAssistant initialized with assistant_id: {self.assistant_id}")

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
        Get completion from OpenAI Assistant.

        Uses thread-based conversation. Only the last user message is sent,
        as the assistant maintains conversation history in the thread.

        Args:
            messages: Message list (only last user message is used)
            temperature: Ignored (assistant uses configured temperature)
            max_tokens: Ignored (assistant uses configured max_tokens)
            **kwargs: Additional parameters

        Returns:
            Generated completion text
        """
        if not messages:
            logger.error("No messages provided to OpenAI Assistant")
            return None

        # Extract last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content")
                break

        if not user_message:
            logger.error("No user message found in messages list")
            return None

        try:
            # Create thread if it doesn't exist
            if not self.thread_created:
                self.current_thread = self.client.beta.threads.create()
                self.thread_created = True
                logger.info(f"Created new thread: {self.current_thread.id}")

            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=self.current_thread.id,
                role="user",
                content=user_message
            )

            logger.debug(f"Added user message to thread {self.current_thread.id}")

            # Run the assistant on the thread
            run = self.client.beta.threads.runs.create(
                thread_id=self.current_thread.id,
                assistant_id=self.assistant_id
            )

            logger.debug(f"Started assistant run: {run.id}")

            # Wait for the run to complete
            while run.status in ['queued', 'in_progress']:
                time.sleep(0.5)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.current_thread.id,
                    run_id=run.id
                )
                logger.debug(f"Run status: {run.status}")

            if run.status == 'completed':
                # Get the assistant's response
                messages_list = self.client.beta.threads.messages.list(
                    thread_id=self.current_thread.id
                )

                # Get the latest assistant message
                for message in messages_list.data:
                    if message.role == 'assistant':
                        response_text = message.content[0].text.value
                        logger.debug(f"OpenAI Assistant response: '{response_text[:100]}...'")
                        return response_text

                logger.warning("No assistant response found in completed run")
                return None

            elif run.status == 'failed':
                logger.error(f"Assistant run failed: {run.last_error}")
                return None

            else:
                logger.warning(f"Unexpected run status: {run.status}")
                return None

        except Exception as e:
            logger.error(f"Error calling OpenAI Assistant API: {e}")
            return None

    def convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to OpenAI Assistant format.

        For Assistant API, only the last user message matters as conversation
        is maintained in the thread.

        Args:
            messages: Standard message format

        Returns:
            Messages in OpenAI-compatible format (passthrough)
        """
        return messages

    def refresh_session(self):
        """Reset the assistant thread to start a fresh conversation"""
        self.current_thread = None
        self.thread_created = False
        logger.info("Assistant thread reset - next conversation will create new thread")

    def get_completion_with_image(self, user_input: str, image_data: str) -> str:
        """
        Get completion from Assistant with image analysis.

        Args:
            user_input: Text prompt about the image
            image_data: Base64 encoded image data

        Returns:
            Generated completion text
        """
        try:
            # Create thread if it doesn't exist
            if not self.thread_created:
                self.current_thread = self.client.beta.threads.create()
                self.thread_created = True
                logger.info(f"Created new thread for image: {self.current_thread.id}")

            import base64
            import tempfile

            # Decode base64 to binary data
            image_binary = base64.b64decode(image_data)
            logger.info(f"Image decoded: {len(image_binary)} bytes")

            # Save image permanently
            timestamp = int(time.time())
            image_filename = f"images/nevil_image_{timestamp}.jpg"
            os.makedirs("images", exist_ok=True)

            with open(image_filename, "wb") as perm_file:
                perm_file.write(image_binary)
            logger.info(f"Saved image to: {image_filename}")

            # Upload file with purpose="vision"
            logger.info(f"Uploading image file to OpenAI with purpose=vision...")
            img_file = self.client.files.create(
                file=open(image_filename, "rb"),
                purpose="vision"
            )

            logger.info(f"Image uploaded, file_id: {img_file.id}")

            # Add message using image_file
            self.client.beta.threads.messages.create(
                thread_id=self.current_thread.id,
                role="user",
                content=[
                    {
                        "type": "text",
                        "text": user_input
                    },
                    {
                        "type": "image_file",
                        "image_file": {"file_id": img_file.id}
                    }
                ]
            )

            # Use create_and_poll for simpler run management
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.current_thread.id,
                assistant_id=self.assistant_id
            )

            if run.status == 'completed':
                # Get the assistant's response
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.current_thread.id
                )

                # Get the latest assistant message
                for message in messages.data:
                    if message.role == 'assistant':
                        response_text = message.content[0].text.value
                        logger.info(f"Image analysis successful: {response_text[:100]}...")
                        return response_text

                logger.warning("No assistant response found in completed run")
                return "I see an image but couldn't analyze it properly."

            else:
                logger.error(f"Assistant run failed with status: {run.status}")
                return "I had trouble analyzing that image."

        except Exception as e:
            logger.error(f"Error processing image with Assistant: {e}")
            return "I see an image but encountered an error during analysis."
