"""
AI Cognition Node for Nevil v3.0

Intelligent AI processing using OpenAI GPT for natural conversation.
Handles voice commands and generates contextual responses.
"""

import os
import time
import random
import json
from nevil_framework.base_node import NevilNode


class AiCognitionNode(NevilNode):
    """
    AI Cognition Node using OpenAI GPT for intelligent conversation.

    Features:
    - OpenAI GPT chat completions for natural responses
    - Conversation context and memory
    - Fallback to stub mode if OpenAI unavailable
    - Configurable personality and behavior
    """

    def __init__(self):
        super().__init__("ai_cognition")

        # Load OpenAI API key and assistant ID
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        self.openai_client = None
        
        # Thread management for Assistants API
        self.current_thread = None
        self.thread_created = False

        # This will be logged later once logger is available

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.ai_config = config.get('ai', {})
        self.processing_config = config.get('processing', {})

        # AI behavior settings - mode will be determined in initialize()
        self.mode = 'echo'  # Default to echo mode
        self.model = self.ai_config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = self.ai_config.get('max_tokens', 150)
        self.temperature = self.ai_config.get('temperature', 0.7)
        self.confidence_threshold = self.ai_config.get('confidence_threshold', 0.3)
        self.processing_delay = self.ai_config.get('processing_delay', 0.1)

        # Conversation context
        self.conversation_history = []
        self.max_history_length = self.ai_config.get('max_history_length', 10)
        self.system_prompt = self.ai_config.get('system_prompt',
            "You are Nevil, a helpful and friendly robot assistant. "
            "You should respond conversationally and helpfully to user questions. "
            "Keep responses concise and natural for speech synthesis.")

        # Processing state
        self.processing_count = 0
        self.last_response_time = 0
        self.openai_error_count = 0

        # Fallback responses for stub mode
        self.echo_responses = [
            "I heard you say: {text}",
            "You said: {text}",
            "I got: {text}"
        ]

    def initialize(self):
        """Initialize AI cognition with OpenAI integration"""
        self.logger.info("Initializing AI Cognition Node...")

        # Debug logging for API key and assistant ID (without exposing sensitive data)
        if self.openai_api_key:
            self.logger.info("OpenAI API key found in environment")
            if self.openai_assistant_id:
                self.logger.info(f"OpenAI Assistant ID found: {self.openai_assistant_id} (will be used with Assistants API)")
            else:
                self.logger.warning("No OpenAI Assistant ID found - Assistants API requires assistant_id")
        else:
            self.logger.warning("No OpenAI API key found in environment variables")

        try:
            # Determine mode based on available credentials
            if self.openai_api_key and self.openai_assistant_id:
                self.mode = self.ai_config.get('mode', 'openai')
            else:
                self.mode = 'echo'
                if not self.openai_api_key:
                    self.logger.warning("No OpenAI API key - using echo mode")
                if not self.openai_assistant_id:
                    self.logger.warning("No OpenAI Assistant ID - using echo mode")
            
            # Initialize OpenAI client if API key available
            if self.openai_api_key and self.mode == 'openai':
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                self.logger.info("OpenAI client initialized successfully")

            # Log configuration
            self.logger.info("AI Cognition Configuration:")
            self.logger.info(f"  Mode: {self.mode}")
            if self.mode == 'openai':
                self.logger.info(f"  Model: {self.model}")
                self.logger.info(f"  Max tokens: {self.max_tokens}")
                self.logger.info(f"  Temperature: {self.temperature}")
            self.logger.info(f"  Confidence threshold: {self.confidence_threshold}")
            self.logger.info(f"  Processing delay: {self.processing_delay}s")

            # Initialize conversation with system prompt
            if self.mode == 'openai':
                self.conversation_history = [
                    {"role": "system", "content": self.system_prompt}
                ]
                self.logger.info(f"Conversation initialized with system prompt")

            # Start in idle mode
            self._set_system_mode("idle", "ai_ready")

            self.logger.info("AI Cognition Node initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize AI cognition: {e}")
            self.mode = 'echo'  # Fallback to echo mode
            self.logger.warning("Falling back to echo mode due to initialization error")

    def main_loop(self):
        """Main processing loop - minimal for stub"""
        # Brief pause to prevent busy waiting
        time.sleep(0.1)

    def on_voice_command(self, message):
        """
        Handle voice commands (declaratively configured callback)

        This is the core of the audio loop test - convert recognized speech
        back into text response for TTS synthesis.
        """
        try:
            text = message.data.get("text", "")
            confidence = message.data.get("confidence", 0.0)
            timestamp = message.data.get("timestamp", time.time())

            self.logger.info(f"Processing voice command: '{text}' (confidence: {confidence:.2f})")

            # Check confidence threshold
            if confidence < self.confidence_threshold:
                self.logger.warning(f"Low confidence ({confidence:.2f}), ignoring command")
                return

            # Set system to thinking mode
            self._set_system_mode("thinking", "processing_voice_command")

            # Simulate AI thinking time
            if self.processing_delay > 0:
                time.sleep(self.processing_delay)

            # Generate response based on mode
            response_text = self._generate_response(text)

            if response_text:
                # Prepare text response message
                text_response_data = {
                    "text": response_text,
                    "voice": "onyx",  # Default voice
                    "priority": 100,
                    "context_id": f"stub_{int(timestamp)}",
                    "timestamp": time.time()
                }

                # Publish text response (will be picked up by speech synthesis)
                if self.publish("text_response", text_response_data):
                    self.logger.info(f"✓ Generated response: '{response_text}'")
                    self.processing_count += 1
                    self.last_response_time = time.time()

                    # Publish actions and mood if available
                    if hasattr(self, '_last_parsed_response'):
                        self._publish_actions_and_mood(self._last_parsed_response, text, message.data)

                    # Set system to speaking mode
                    self._set_system_mode("speaking", "generated_response")
                else:
                    self.logger.error("Failed to publish text response")
                    self._set_system_mode("error", "publish_failed")

            else:
                self.logger.warning("No response generated")
                self._set_system_mode("idle", "no_response")

        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")
            self._set_system_mode("error", f"processing_error: {e}")

    def _generate_response(self, input_text):
        """Generate response using OpenAI or fallback modes"""
        try:
            if not input_text.strip():
                return "I didn't catch that."

            text = input_text.strip()

            if self.mode == "openai" and self.openai_client:
                return self._generate_openai_response(text)
            elif self.mode == "echo":
                return f"I heard you say: {text}"
            else:
                # Default fallback
                return f"I got: {text}"

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            self.openai_error_count += 1
            return "I had trouble processing that."

    def _generate_openai_response(self, user_input):
        """Generate response using OpenAI Assistants API with thread management"""
        try:
            # Create thread if it doesn't exist
            if not self.thread_created:
                self.current_thread = self.openai_client.beta.threads.create()
                self.thread_created = True
                self.logger.debug(f"Created new thread: {self.current_thread.id}")

            # Add the user message to the thread
            self.openai_client.beta.threads.messages.create(
                thread_id=self.current_thread.id,
                role="user",
                content=user_input
            )

            self.logger.debug(f"Added user message to thread {self.current_thread.id}")

            # Run the assistant on the thread
            run = self.openai_client.beta.threads.runs.create(
                thread_id=self.current_thread.id,
                assistant_id=self.openai_assistant_id
            )

            self.logger.debug(f"Started assistant run: {run.id}")

            # Wait for the run to complete
            import time
            while run.status in ['queued', 'in_progress']:
                time.sleep(0.5)
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=self.current_thread.id,
                    run_id=run.id
                )
                self.logger.debug(f"Run status: {run.status}")

            if run.status == 'completed':
                # Get the assistant's response
                messages = self.openai_client.beta.threads.messages.list(
                    thread_id=self.current_thread.id
                )

                # Get the latest assistant message
                for message in messages.data:
                    if message.role == 'assistant':
                        response_text = message.content[0].text.value
                        self.logger.debug(f"OpenAI Assistant raw response: '{response_text}'")

                        # Parse JSON response and return only the answer field
                        parsed_response = self._parse_json_response(response_text)
                        return parsed_response.get('answer', response_text)

                self.logger.warning("No assistant response found in completed run")
                return "I'm not sure how to respond to that."

            elif run.status == 'failed':
                self.logger.error(f"Assistant run failed: {run.last_error}")
                return "I had trouble processing that request."

            else:
                self.logger.warning(f"Unexpected run status: {run.status}")
                return "I'm not sure how to respond to that."

        except Exception as e:
            self.logger.error(f"Error calling OpenAI Assistants API: {e}")
            self.openai_error_count += 1

            # Fallback to echo mode for this response
            return f"I heard: {user_input}"

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse AI response to extract answer, actions, and mood"""
        try:
            # Try to parse as JSON
            response_data = json.loads(response_text)

            if isinstance(response_data, dict):
                parsed = {
                    'answer': response_data.get('answer', ''),
                    'actions': response_data.get('actions', []),
                    'mood': response_data.get('mood', 'neutral')
                }

                self.logger.debug(f"Parsed JSON response: answer='{parsed['answer'][:50]}...', "
                                f"actions={parsed['actions']}, mood={parsed['mood']}")

                # Store for publishing in message handler
                self._last_parsed_response = parsed
                return parsed
            else:
                # Not a dict, treat as plain text
                self.logger.debug("Response is JSON but not a dict, treating as plain text")
                return {'answer': str(response_data), 'actions': [], 'mood': 'neutral'}

        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            self.logger.debug("Response is not JSON, treating as plain text")
            return {'answer': response_text, 'actions': [], 'mood': 'neutral'}
        except Exception as e:
            self.logger.warning(f"Error parsing JSON response: {e}")
            return {'answer': response_text, 'actions': [], 'mood': 'neutral'}

    def _publish_actions_and_mood(self, parsed_response: dict, original_text: str, original_command: dict):
        """Publish robot actions and mood changes to navigation node"""
        try:
            current_time = time.time()

            # Publish robot actions if any
            actions = parsed_response.get('actions', [])
            if actions:
                robot_action_data = {
                    "actions": actions,
                    "source_text": original_text,
                    "mood": parsed_response.get('mood', 'neutral'),
                    "priority": 100,
                    "timestamp": current_time
                }

                if self.publish("robot_action", robot_action_data):
                    self.logger.info(f"✓ Published robot actions: {actions}")
                else:
                    self.logger.warning("Failed to publish robot actions")

            # Publish mood change if not neutral
            mood = parsed_response.get('mood', 'neutral')
            if mood and mood != 'neutral':
                mood_change_data = {
                    "mood": mood,
                    "source": "ai_response",
                    "context": original_text,
                    "timestamp": current_time
                }

                if self.publish("mood_change", mood_change_data):
                    self.logger.info(f"✓ Published mood change: {mood}")
                else:
                    self.logger.warning("Failed to publish mood change")

        except Exception as e:
            self.logger.error(f"Error publishing actions and mood: {e}")

    def _set_system_mode(self, mode, reason):
        """Set system mode and publish change"""
        mode_data = {
            "mode": mode,
            "reason": reason,
            "timestamp": time.time()
        }

        self.publish("system_mode", mode_data)
        self.logger.debug(f"Set system mode: {mode} ({reason})")

    def cleanup(self):
        """Cleanup AI cognition resources"""
        self.logger.info("Cleaning up AI cognition...")

        # Set system to idle
        self._set_system_mode("idle", "shutting_down")

        # Clear conversation history
        if hasattr(self, 'conversation_history'):
            self.conversation_history.clear()

        # Reset thread state
        self.current_thread = None
        self.thread_created = False

        self.logger.info(f"AI cognition stopped after {self.processing_count} responses")
        if self.openai_error_count > 0:
            self.logger.info(f"OpenAI errors encountered: {self.openai_error_count}")

    def get_ai_stats(self):
        """Get AI cognition statistics"""
        return {
            "mode": self.mode,
            "model": self.model if self.mode == 'openai' else None,
            "processing_count": self.processing_count,
            "openai_error_count": self.openai_error_count,
            "confidence_threshold": self.confidence_threshold,
            "last_response_time": self.last_response_time,
            "conversation_length": len(self.conversation_history) if hasattr(self, 'conversation_history') else 0,
            "openai_available": self.openai_client is not None
        }

    def reset_conversation(self):
        """Reset conversation history to start fresh"""
        if self.mode == 'openai':
            # Reset thread state for Assistants API
            self.current_thread = None
            self.thread_created = False
            self.logger.info("Thread reset - new conversation will start with fresh thread")
        else:
            # For echo mode, just clear conversation history
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
            self.logger.info("Conversation history reset")

    def get_conversation_summary(self):
        """Get a summary of recent conversation"""
        if not hasattr(self, 'conversation_history') or len(self.conversation_history) <= 1:
            return "No conversation history"

        # Return last few exchanges (excluding system message)
        recent = self.conversation_history[-6:]  # Last 3 exchanges (user + assistant)
        summary = []
        for msg in recent:
            if msg['role'] != 'system':
                role = "User" if msg['role'] == 'user' else "Nevil"
                summary.append(f"{role}: {msg['content']}")

        return "\n".join(summary)