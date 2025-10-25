"""
AI Cognition Node for Nevil v3.0

Intelligent AI processing using OpenAI GPT for natural conversation.
Handles voice commands and generates contextual responses.
"""

import os
import time
import random
import json
import sys
from pathlib import Path

# Add the ai_cognition directory to sys.path for completion imports
_ai_cognition_dir = Path(__file__).parent
if str(_ai_cognition_dir) not in sys.path:
    sys.path.insert(0, str(_ai_cognition_dir))

from nevil_framework.base_node import NevilNode
from nevil_framework.chat_logger import get_chat_logger
from completion.factory import get_completion_provider


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

        # Initialize chat logger for performance tracking
        self.chat_logger = get_chat_logger()

        # Get AI provider type from environment (default: ollama)
        self.ai_provider_type = os.getenv('NEVIL_AI', 'openai_completion')
        self.completion_provider = None

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.ai_config = config.get('ai', {})
        self.processing_config = config.get('processing', {})

        # AI behavior settings
        self.mode = 'echo'  # Will be set in initialize()
        self.model = self.ai_config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = self.ai_config.get('max_tokens', 150)
        self.temperature = self.ai_config.get('temperature', 0.7)
        self.confidence_threshold = self.ai_config.get('confidence_threshold', 0.3)
        self.processing_delay = self.ai_config.get('processing_delay', 0.1)

        # Conversation context
        self.conversation_history = []
        self.max_history_length = self.ai_config.get('max_history_length', 10)

        # System prompt - MUST be configured in .messages file (nodes/ai_cognition/.messages)
        # No fallback - if missing, we want to fail loudly so it's fixed in config
        self.system_prompt = self.ai_config.get('system_prompt')
        if not self.system_prompt:
            raise ValueError("system_prompt must be configured in nodes/ai_cognition/.messages")


        # Processing state
        self.processing_count = 0
        self.last_response_time = 0
        self.ai_error_count = 0

        # Visual data storage
        self.latest_image = None

        # Fallback responses for echo mode
        self.echo_responses = [
            "I heard you say: {text}",
            "You said: {text}",
            "I got: {text}"
        ]

    def initialize(self):
        """Initialize AI cognition with completion provider factory"""
        self.logger.info("Initializing AI Cognition Node...")
        self.logger.info(f"AI Provider: {self.ai_provider_type} (from NEVIL_AI env var)")

        try:
            # Initialize completion provider from factory
            try:
                self.completion_provider = get_completion_provider(self.ai_provider_type)
                self.mode = 'ai'  # Using AI provider
                self.logger.info(f"✓ Successfully initialized {self.ai_provider_type} provider")
            except Exception as e:
                self.logger.error(f"Failed to initialize AI provider '{self.ai_provider_type}': {e}")
                self.mode = 'echo'  # Fallback to echo mode
                self.logger.warning("Falling back to echo mode")

            # Log configuration
            self.logger.info("AI Cognition Configuration:")
            self.logger.info(f"  Mode: {self.mode}")
            self.logger.info(f"  Provider: {self.ai_provider_type}")
            if self.mode == 'ai':
                self.logger.info(f"  Max tokens: {self.max_tokens}")
                self.logger.info(f"  Temperature: {self.temperature}")
            self.logger.info(f"  Confidence threshold: {self.confidence_threshold}")
            self.logger.info(f"  Processing delay: {self.processing_delay}s")

            # Initialize conversation with system prompt
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

    def on_visual_data(self, message):
        """
        Handle visual data from camera (declaratively configured callback)

        Automatically sends image to OpenAI for analysis.
        """
        try:
            image_data = message.data.get("image_data", "")
            capture_id = message.data.get("capture_id", "")
            timestamp = message.data.get("timestamp", time.time())

            if image_data:
                # Store the latest image
                self.latest_image = {
                    "data": image_data,
                    "capture_id": capture_id,
                    "timestamp": timestamp
                }
                self.logger.info(f"✓ Received visual data: {capture_id}")

                # Immediately send to OpenAI for analysis
                self._process_image_with_ai(image_data, capture_id)

            else:
                self.logger.warning("Received empty visual data")

        except Exception as e:
            self.logger.error(f"Error handling visual data: {e}")

    def _process_image_with_ai(self, image_data, capture_id):
        """Send image to OpenAI for analysis and generate speech response"""
        try:
            self.logger.info(f"🖼️ Processing image {capture_id} with OpenAI...")

            # Set system to thinking mode
            self._set_system_mode("thinking", "processing_image")

            # Generate AI response about the image
            if self.mode == "ai" and self.completion_provider:
                response_text = self._generate_ai_image_response(image_data)
            else:
                response_text = "I can see an image, but I'm in echo mode and cannot analyze it."

            if response_text:
                # Prepare text response message
                text_response_data = {
                    "text": response_text,
                    "voice": "onyx",
                    "priority": 90,  # High priority for image responses
                    "context_id": f"image_{capture_id}",
                    "timestamp": time.time()
                }

                # Publish text response for speech synthesis
                if self.publish("text_response", text_response_data):
                    if "error" in response_text.lower() or "trouble" in response_text.lower():
                        self.logger.error(f"❌ Image analysis failed: {response_text}")
                    else:
                        self.logger.info(f"✓ Image analysis successful: {response_text}")
                    self._set_system_mode("speaking", "image_analysis_response")
                else:
                    self.logger.error("❌ Failed to publish image analysis response")
                    self._set_system_mode("error", "publish_failed")
            else:
                self.logger.warning("No image analysis response generated")
                self._set_system_mode("idle", "no_image_response")

        except Exception as e:
            self.logger.error(f"Error processing image with AI: {e}")
            self._set_system_mode("error", f"image_processing_error: {e}")

    def _generate_ai_image_response(self, image_data):
        """Generate response with image analysis using AI provider"""
        try:
            # Check if provider supports image analysis
            if hasattr(self.completion_provider, 'get_completion_with_image'):
                return self.completion_provider.get_completion_with_image(
                    "You are Nevil, a witty robot dog/car with a camera. Describe what you see in your characteristic poetic, brief, and playful style (1-2 sentences). Be specific about interesting details you notice.",
                    image_data
                )
            else:
                self.logger.warning(f"Provider {self.ai_provider_type} does not support image analysis")
                return "I see an image, but my GPT provider doesn't allow that."
        except Exception as e:
            self.logger.error(f"Error processing image with AI provider: {e}")
            return "I see an image but encountered an error during analysis."

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
            conversation_id = message.data.get("conversation_id")

            # Fallback if conversation_id not provided
            if not conversation_id:
                conversation_id = self.chat_logger.generate_conversation_id()
                self.logger.warning(f"No conversation_id provided, generated: {conversation_id}")

            self.logger.info(f"Processing voice command: '{text}' (conv: {conversation_id})")

            # Check confidence threshold
            if confidence < self.confidence_threshold:
                self.logger.warning(f"Low confidence ({confidence:.2f}), ignoring command")
                return

            # Set system to thinking mode
            self._set_system_mode("thinking", "processing_voice_command")

            # Simulate AI thinking time
            if self.processing_delay > 0:
                time.sleep(self.processing_delay)

            # STEP 3: Log GPT processing with real timing
            with self.chat_logger.log_step(
                conversation_id, "gpt",
                input_text=text,
                metadata={
                    "model": self.model,
                    "mode": self.mode,
                    "provider": self.ai_provider_type,
                    "confidence": confidence
                }
            ) as gpt_log:
                response_text = self._generate_response(text)
                gpt_log["output_text"] = response_text if response_text else "<no_response>"

            if response_text:
                # Prepare text response message
                text_response_data = {
                    "text": response_text,
                    "voice": "onyx",  # Default voice
                    "priority": 100,
                    "context_id": f"stub_{int(timestamp)}",
                    "timestamp": time.time(),
                    "conversation_id": conversation_id  # Pass to next step
                }

                # Publish text response (will be picked up by speech synthesis)
                if self.publish("text_response", text_response_data):
                    self.logger.info(f"✓ Generated response: '{response_text}'")
                    self.processing_count += 1
                    self.last_response_time = time.time()

                    # Actions and mood are already published in _generate_openai_response
                    # No need to publish again here

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
        """Generate response using completion provider or fallback"""
        try:
            if not input_text.strip():
                return "I didn't catch that."

            text = input_text.strip()

            if self.mode == "ai" and self.completion_provider:
                return self._generate_ai_response(text)
            elif self.mode == "echo":
                return f"I heard you say: {text}"
            else:
                # Default fallback
                return f"I got: {text}"

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            self.ai_error_count += 1
            return "I had trouble processing that."

    def _generate_ai_response(self, user_input):
        """Generate response using completion provider (factory-based)"""
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            # Trim conversation history to max length
            if len(self.conversation_history) > self.max_history_length:
                # Keep system prompt + most recent messages
                self.conversation_history = [
                    self.conversation_history[0]  # System prompt
                ] + self.conversation_history[-(self.max_history_length - 1):]

            # Get completion from provider
            response_text = self.completion_provider.get_completion(
                messages=self.conversation_history,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            if response_text:
                self.logger.debug(f"AI raw response: '{response_text[:100]}...'")

                # Add assistant response to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response_text
                })

                # Parse JSON response
                parsed_response = self._parse_json_response(response_text)

                # Publish actions and mood to navigation node
                self._publish_actions_and_mood(
                    parsed_response,
                    user_input,
                    {"text": user_input}
                )

                # Return only the answer field
                return parsed_response.get('answer', response_text)
            else:
                self.logger.warning("No AI response received")
                return "I'm not sure how to respond to that."

        except Exception as e:
            self.logger.error(f"Error calling AI provider: {e}")
            self.ai_error_count += 1

            # Fallback to echo mode for this response
            return f"I heard: {user_input}"

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse AI response to extract answer, actions, mood, and tool calls"""
        try:
            # Try to parse as JSON
            response_data = json.loads(response_text)

            if isinstance(response_data, dict):
                parsed = {
                    'answer': response_data.get('answer', ''),
                    'actions': response_data.get('actions', []),
                    'mood': response_data.get('mood', 'neutral')
                }

                # Check for simple tool flags
                if response_data.get('take_snapshot'):
                    self.logger.info("🎯 Detected take_snapshot flag in AI response")
                    self._handle_take_snapshot()

                # Also check if take_snapshot is in the actions list
                actions = response_data.get('actions', [])
                if 'take_snapshot' in actions:
                    self.logger.info("🎯 Detected take_snapshot in actions array")
                    self._handle_take_snapshot()
                    # Remove it from actions so it doesn't get sent to navigation
                    parsed['actions'] = [a for a in actions if a != 'take_snapshot']

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

    def _process_tool_calls(self, tool_calls: list):
        """Process tool calls from AI response"""
        try:
            for tool_call in tool_calls:
                tool_name = tool_call.get('name', '')
                tool_args = tool_call.get('arguments', {})

                self.logger.info(f"Processing tool call: {tool_name} with args: {tool_args}")

                if tool_name == 'take_snapshot':
                    self._handle_take_snapshot(tool_args)
                else:
                    self.logger.warning(f"Unknown tool call: {tool_name}")

        except Exception as e:
            self.logger.error(f"Error processing tool calls: {e}")

    def _handle_take_snapshot(self):
        """Handle take_snapshot request"""
        try:
            self.logger.info("🔍 AI requested camera snapshot via take_snapshot tool")

            # Publish snap_pic request to visual node
            snap_pic_data = {
                "requested_by": "ai_cognition",
                "timestamp": time.time()
            }

            if self.publish("snap_pic", snap_pic_data):
                self.logger.info("✓ Snapshot request published to visual node")
            else:
                self.logger.error("❌ Failed to publish snap_pic request")

        except Exception as e:
            self.logger.error(f"❌ Error handling take_snapshot: {e}")

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

        # Cleanup completion provider
        if self.completion_provider and hasattr(self.completion_provider, 'refresh_session'):
            self.completion_provider.refresh_session()

        self.logger.info(f"AI cognition stopped after {self.processing_count} responses")
        if self.ai_error_count > 0:
            self.logger.info(f"AI errors encountered: {self.ai_error_count}")

    def get_ai_stats(self):
        """Get AI cognition statistics"""
        return {
            "mode": self.mode,
            "provider": self.ai_provider_type,
            "processing_count": self.processing_count,
            "ai_error_count": self.ai_error_count,
            "confidence_threshold": self.confidence_threshold,
            "last_response_time": self.last_response_time,
            "conversation_length": len(self.conversation_history) if hasattr(self, 'conversation_history') else 0,
            "ai_available": self.completion_provider is not None
        }

    def reset_conversation(self):
        """Reset conversation history to start fresh"""
        # Reset conversation history
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Reset provider session if supported
        if self.completion_provider and hasattr(self.completion_provider, 'refresh_session'):
            self.completion_provider.refresh_session()

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