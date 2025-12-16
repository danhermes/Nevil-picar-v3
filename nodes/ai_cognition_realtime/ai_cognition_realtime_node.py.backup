"""
AI Cognition Node v2.2 for Nevil - OpenAI Realtime API Streaming

Implements real-time streaming conversation with OpenAI's Realtime API for
ultra-low-latency voice interaction and multimodal capabilities.

Key Features:
- Streaming audio/text conversation via WebSocket
- Function calling for 106+ robot gestures
- Camera integration for multimodal vision
- Delta event handling for real-time response streaming
- Integration with Nevil's message bus architecture

Version: 2.2 (Realtime API)
Based on: ai_cognition_node.py patterns + RealtimeConnectionManager
"""

import os
import time
import json
import base64
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from nevil_framework.base_node import NevilNode
from nevil_framework.chat_logger import get_chat_logger
from nevil_framework.realtime.realtime_connection_manager import (
    RealtimeConnectionManager,
    ConnectionConfig,
    SessionConfig
)

logger = logging.getLogger(__name__)


class AiNode22(NevilNode):
    """
    AI Cognition Node using OpenAI Realtime API for streaming conversation.

    Subscribes to: voice_command, visual_data
    Publishes to: text_response, robot_action, mood_change, system_mode, snap_pic

    Features:
    - Real-time streaming audio/text responses
    - Function calling for 106+ gesture library
    - Camera integration for multimodal vision
    - Delta event handling for progressive response building
    - Session persistence and conversation context
    """

    def __init__(self):
        super().__init__("ai_cognition_realtime")

        # Chat logger for performance tracking
        self.chat_logger = get_chat_logger()

        # Configuration from .messages file
        config = self.config.get('configuration', {})
        self.ai_config = config.get('ai', {})
        self.realtime_config = config.get('realtime', {})

        # Realtime API settings (with environment variable overrides)
        self.model = os.getenv('NEVIL_REALTIME_MODEL',
                              self.realtime_config.get('model', 'gpt-4o-realtime-preview-2024-12-17'))
        self.voice = os.getenv('NEVIL_REALTIME_VOICE',
                              self.realtime_config.get('voice', 'alloy'))
        self.temperature = float(os.getenv('NEVIL_REALTIME_TEMPERATURE',
                                          self.realtime_config.get('temperature', 0.8)))
        self.modalities = self.realtime_config.get('modalities', ['text', 'audio'])

        # Get system instructions from config
        self.system_instructions = self.ai_config.get('system_prompt')
        if not self.system_instructions:
            raise ValueError("system_prompt must be configured in .messages file")

        # Connection manager
        self.connection_manager: Optional[RealtimeConnectionManager] = None

        # Response streaming state
        self.current_response_text = ""
        self.current_function_call = None
        self.current_conversation_id = None
        self.response_in_progress = False  # Track if API is generating a response
        self.response_start_time = None  # Track when response started (for timeout safety)

        # Visual data storage
        self.latest_image: Optional[Dict[str, Any]] = None

        # Statistics
        self.processing_count = 0
        self.function_call_count = 0
        self.error_count = 0

        # Load gesture library for function calling
        self._load_gesture_library()

    def _load_gesture_library(self):
        """Load gesture library and build function definitions for Realtime API"""
        try:
            # Import gesture functions
            import sys
            gestures_path = Path(__file__).parent.parent.parent / "nodes" / "navigation"
            if str(gestures_path) not in sys.path:
                sys.path.insert(0, str(gestures_path))

            import extended_gestures

            # Build function definitions for all gestures
            self.gesture_functions = {}
            self.gesture_definitions = []

            # Get all gesture function names (exclude sound functions - they're handled separately)
            gesture_names = [
                name for name in dir(extended_gestures)
                if callable(getattr(extended_gestures, name))
                and not name.startswith('_')
                and name not in ['time', 'Enum', 'GestureSpeed', 'play_sound', 'honk', 'rev_engine']
            ]

            for gesture_name in gesture_names:
                self.gesture_functions[gesture_name] = getattr(extended_gestures, gesture_name)

                # Create function definition for OpenAI
                self.gesture_definitions.append({
                    "type": "function",
                    "name": gesture_name,
                    "description": f"Execute {gesture_name.replace('_', ' ')} gesture",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "speed": {
                                "type": "string",
                                "enum": ["slow", "med", "fast"],
                                "description": "Gesture speed (slow=thoughtful, med=normal, fast=excited)",
                                "default": "med"
                            }
                        }
                    }
                })

            # Add movement functions (forward, backward, left, right)
            movement_functions = {
                "move_forward": "Move forward (cm, speed)",
                "move_backward": "Move backward (cm, speed)",
                "turn_left": "Turn left (degrees)",
                "turn_right": "Turn right (degrees)",
                "stop_movement": "Stop all movement"
            }

            for func_name, description in movement_functions.items():
                self.gesture_definitions.append({
                    "type": "function",
                    "name": func_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "distance": {"type": "number", "description": "Distance in cm"},
                            "speed": {"type": "number", "description": "Speed 0-50"}
                        }
                    }
                })

            # Add camera function
            self.gesture_definitions.append({
                "type": "function",
                "name": "take_snapshot",
                "description": "Take a camera snapshot to see what's in front of you",
                "parameters": {"type": "object", "properties": {}}
            })

            # Add sound effect functions with proper parameters
            sound_effects = {
                "honk": "Honk the car horn",
                "rev_engine": "Rev the car engine",
                "airhorn": "Blast an air horn",
                "train_horn": "Sound a train horn",
                "wolf_howl": "Howl like a wolf",
                "ghost": "Make spooky ghost sounds",
                "alien_voice": "Alien voice effects",
                "dubstep": "Play dubstep music",
                "reggae": "Play reggae music",
                "machine_gun": "Machine gun sound effect"
            }

            # Add play_sound function with sound_name parameter
            self.gesture_definitions.append({
                "type": "function",
                "name": "play_sound",
                "description": f"Play a sound effect. Available sounds: {', '.join(sound_effects.keys())}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sound_name": {
                            "type": "string",
                            "enum": list(sound_effects.keys()),
                            "description": "Name of the sound to play: " + ", ".join([f"{k} ({v})" for k, v in sound_effects.items()])
                        },
                        "volume": {
                            "type": "number",
                            "description": "Volume 0-100",
                            "default": 100
                        }
                    },
                    "required": ["sound_name"]
                }
            })

            # Add honk as standalone function
            self.gesture_definitions.append({
                "type": "function",
                "name": "honk",
                "description": "Honk the car horn - quick shortcut for play_sound('honk')",
                "parameters": {"type": "object", "properties": {}}
            })

            # Add rev_engine as standalone function
            self.gesture_definitions.append({
                "type": "function",
                "name": "rev_engine",
                "description": "Rev the car engine - quick shortcut for play_sound('rev_engine')",
                "parameters": {"type": "object", "properties": {}}
            })

            # Add memory functions
            self.gesture_definitions.append({
                "type": "function",
                "name": "remember",
                "description": "Store a memory for later recall. Use this when the user shares preferences, personal information, or important moments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The user's message to remember"
                        },
                        "response": {
                            "type": "string",
                            "description": "Your response acknowledging the memory"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["preference", "personal", "intense", "general"],
                            "description": "Memory category: preference (likes/dislikes), personal (background/experiences), intense (memorable conversations), general (other)"
                        },
                        "importance": {
                            "type": "number",
                            "description": "Importance score 1-10 (10=critical, 8-9=important, 6-7=moderate, 4-5=general, 1-3=low)"
                        }
                    },
                    "required": ["message", "response", "category", "importance"]
                }
            })

            self.gesture_definitions.append({
                "type": "function",
                "name": "recall",
                "description": "Recall memories from the past using semantic search. Use this before responding to questions about user preferences or past conversations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for recalling memories"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["preference", "personal", "intense", "general"],
                            "description": "Optional category filter"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of memories to return (default 5)"
                        },
                        "min_importance": {
                            "type": "number",
                            "description": "Minimum importance score to return (default 3)"
                        }
                    },
                    "required": ["query"]
                }
            })

            self.logger.info(f"Loaded {len(self.gesture_functions)} gestures + movement + camera + sounds + memory")

        except Exception as e:
            self.logger.error(f"Failed to load gesture library: {e}")
            self.gesture_functions = {}
            self.gesture_definitions = []

    def initialize(self):
        """Initialize Realtime API connection"""
        self.logger.info("Initializing AI Node v2.2 (Realtime API)...")

        try:
            # Get authentication from environment
            api_key = os.getenv('OPENAI_API_KEY')
            ephemeral_token = os.getenv('OPENAI_REALTIME_TOKEN')

            if not api_key and not ephemeral_token:
                raise ValueError("Either OPENAI_API_KEY or OPENAI_REALTIME_TOKEN must be set")

            # Create connection configuration
            conn_config = ConnectionConfig(
                api_key=api_key,
                ephemeral_token=ephemeral_token,
                max_reconnect_attempts=5,
                reconnect_base_delay=1.0,
                connection_timeout=30.0
            )

            # Create session configuration with function calling
            # OPTIMIZED: Use server_vad for faster responses (200-500ms improvement)
            # Server-side VAD eliminates manual commit round-trips while maintaining
            # input_audio_transcription.completed events for direct command detection
            session_config = SessionConfig(
                model=self.model,
                modalities=self.modalities,
                instructions=self.system_instructions,
                voice=self.voice,
                temperature=self.temperature,
                tools=self.gesture_definitions,
                tool_choice="auto",
                input_audio_transcription={
                    "model": "whisper-1",
                    "language": "en"  # Force English transcription
                },
                turn_detection={
                    "type": "server_vad",
                    "threshold": 0.5,        # Sensitivity (0.0-1.0, default 0.5)
                    "prefix_padding_ms": 300, # Include 300ms before speech starts
                    "silence_duration_ms": 500 # Wait 500ms of silence before ending turn
                }
            )

            # Create connection manager
            self.connection_manager = RealtimeConnectionManager(
                config=conn_config,
                session_config=session_config,
                debug=True
            )

            # Register event handlers
            self._setup_event_handlers()

            # Start connection
            self.connection_manager.start()

            self.logger.info(f"Realtime API initialized: model={self.model}, voice={self.voice}")
            self._set_system_mode("idle", "realtime_ready")

        except Exception as e:
            self.logger.error(f"Failed to initialize Realtime API: {e}")
            self.error_count += 1
            raise

    def _setup_event_handlers(self):
        """Setup event handlers for Realtime API events"""

        # Connection events
        self.connection_manager.on('connect', self._on_connect)
        self.connection_manager.on('disconnect', self._on_disconnect)
        self.connection_manager.on('error', self._on_error)

        # Response events - streaming deltas
        self.connection_manager.on('response.text.delta', self._on_response_text_delta)
        self.connection_manager.on('response.text.done', self._on_response_text_done)
        self.connection_manager.on('response.audio.delta', self._on_response_audio_delta)
        self.connection_manager.on('response.audio.done', self._on_response_audio_done)
        self.connection_manager.on('response.audio_transcript.delta', self._on_audio_transcript_delta)
        self.connection_manager.on('response.audio_transcript.done', self._on_audio_transcript_done)

        # Function calling events - CRITICAL: output_item.added contains the function name!
        self.connection_manager.on('response.output_item.added', self._on_output_item_added)
        self.connection_manager.on('response.function_call_arguments.delta', self._on_function_args_delta)
        self.connection_manager.on('response.function_call_arguments.done', self._on_function_args_done)

        # Conversation events
        self.connection_manager.on('conversation.item.created', self._on_conversation_item_created)
        self.connection_manager.on('response.done', self._on_response_done)

        # Input audio events
        self.connection_manager.on('input_audio_buffer.speech_started', self._on_speech_started)
        self.connection_manager.on('input_audio_buffer.speech_stopped', self._on_speech_stopped)

    # ========================================================================
    # Connection Event Handlers
    # ========================================================================

    def _on_connect(self):
        """Handle connection established"""
        self.logger.info("Connected to Realtime API")
        self._set_system_mode("idle", "connected")

    def _on_disconnect(self, reason):
        """Handle disconnection"""
        self.logger.warning(f"Disconnected from Realtime API: {reason}")
        self._set_system_mode("error", f"disconnected: {reason}")

    def _on_error(self, error):
        """Handle connection error"""
        self.logger.error(f"Realtime API error: {error}")
        self.error_count += 1

        # Check if this is the "conversation_already_has_active_response" error
        # If so, DON'T clear the flag - a response is actually in progress
        error_code = None
        if isinstance(error, dict):
            error_details = error.get('error', {})
            error_code = error_details.get('code')

        if error_code == 'conversation_already_has_active_response':
            self.logger.warning("⚠️ API says response already in progress - keeping flag set, will wait for response.done")
            return

        # Clear response flag on OTHER errors to prevent stuck state
        if self.response_in_progress:
            self.response_in_progress = False
            self.response_start_time = None
            self.logger.info("🚦 Response flag cleared due to error")

    # ========================================================================
    # Response Streaming Event Handlers
    # ========================================================================

    def _on_response_text_delta(self, event):
        """Handle streaming text response delta"""
        try:
            delta = event.get('delta', '')
            self.current_response_text += delta

            # Log partial response for debugging
            if len(self.current_response_text) % 50 == 0:
                self.logger.debug(f"Response streaming: {len(self.current_response_text)} chars")

        except Exception as e:
            self.logger.error(f"Error handling text delta: {e}")

    def _on_response_text_done(self, event):
        """Handle completed text response"""
        try:
            response_text = self.current_response_text.strip()

            if response_text:
                self.logger.info(f"🤖 NEVIL RESPONSE: '{response_text}'")

                # Publish text response for speech synthesis
                text_response_data = {
                    "text": response_text,
                    "voice": self.voice,
                    "priority": 100,
                    "timestamp": time.time(),
                    "conversation_id": self.current_conversation_id
                }

                if self.publish("text_response", text_response_data):
                    self.processing_count += 1
                    self._set_system_mode("speaking", "response_complete")
                else:
                    self.logger.error("Failed to publish text response")

            # Reset for next response
            self.current_response_text = ""

            # IMPORTANT: Clear response flag here as a fallback
            # The response.done event should clear it, but if that doesn't fire, we clear it here
            # NOTE: We'll wait for response.done event first, so we don't clear prematurely

        except Exception as e:
            self.logger.error(f"Error handling text done: {e}")

    def _on_response_audio_delta(self, event):
        """Handle streaming audio response delta - delegated to speech_synthesis_realtime node"""
        # NOTE: Audio playback is handled by speech_synthesis_realtime node
        # This node only monitors for logging purposes
        pass

    def _on_response_audio_done(self, event):
        """Handle completed audio response - delegated to speech_synthesis_realtime node"""
        # NOTE: Audio playback is handled by speech_synthesis_realtime node
        # This node only monitors for logging purposes
        pass

    def _on_audio_transcript_delta(self, event):
        """Handle audio transcript delta (alternative to text delta for audio responses)"""
        try:
            delta = event.get('delta', '')
            if delta:
                self.current_response_text += delta
                self.logger.debug(f"🎧 Audio transcript delta: '{delta}'")
        except Exception as e:
            self.logger.error(f"Error handling audio transcript delta: {e}")

    def _on_audio_transcript_done(self, event):
        """Handle completed audio transcript"""
        try:
            self.logger.info(f"🎧 Audio transcript done event received")

            transcript = event.get('transcript', '').strip()
            if not transcript and self.current_response_text:
                transcript = self.current_response_text.strip()

            if transcript:
                self.logger.info(f"🤖 NEVIL RESPONSE (audio transcript): '{transcript}'")

                # NOTE: Do NOT publish text_response here - the realtime audio is already
                # being handled by speech_synthesis_realtime which receives the audio stream directly
                # Publishing it here causes DOUBLE speech output and mutex confusion
                self.logger.debug("Audio transcript logged (audio already handled by realtime stream)")

            # Reset for next response
            self.current_response_text = ""

            # CRITICAL: Clear response flag here as FALLBACK since response.done may not fire
            # If we have an audio transcript response, the response IS complete
            if self.response_in_progress:
                elapsed = time.time() - self.response_start_time if self.response_start_time else 0
                self.response_in_progress = False
                self.response_start_time = None
                self.logger.info(f"🚦 Response flag cleared (via audio_transcript_done) after {elapsed:.2f}s - ready for next command")

        except Exception as e:
            self.logger.error(f"Error handling audio transcript done: {e}")

    # ========================================================================
    # Conversation Event Handlers
    # ========================================================================

    def _on_conversation_item_created(self, event):
        """
        Handle conversation item created - captures message content

        Event format:
        {
            "type": "conversation.item.created",
            "item": {
                "id": "...",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "Hello! How can I help you?"
                    }
                ]
            }
        }
        """
        try:
            # Debug: log the entire event to see structure
            self.logger.debug(f"📧 conversation.item.created event: {event}")

            item = event.get('item', {})
            item_type = item.get('type', '')
            role = item.get('role', '')

            self.logger.debug(f"📧 Item type={item_type}, role={role}")

            # Only log assistant messages (Nevil's responses)
            if item_type == 'message' and role == 'assistant':
                content_list = item.get('content', [])

                # Extract text content
                message_text = ""
                for content_item in content_list:
                    if content_item.get('type') == 'text':
                        message_text += content_item.get('text', '')

                if message_text:
                    self.logger.info(f"🤖 NEVIL RESPONSE: '{message_text}'")
                else:
                    self.logger.warning(f"📧 Assistant message but no text content found. Content: {content_list}")

        except Exception as e:
            self.logger.error(f"Error handling conversation item created: {e}")

    # ========================================================================
    # Function Calling Event Handlers
    # ========================================================================

    def _on_output_item_added(self, event):
        """
        Handle output item added - this contains the function name!

        Event format:
        {
            "type": "response.output_item.added",
            "item": {
                "id": "...",
                "type": "function_call",
                "call_id": "...",
                "name": "move_forward",  # ← THE FUNCTION NAME IS HERE!
                "arguments": ""
            }
        }

        OR for message type:
        {
            "type": "response.output_item.added",
            "item": {
                "id": "...",
                "type": "message",
                "role": "assistant",
                "content": [...]
            }
        }
        """
        try:
            item = event.get('item', {})
            item_type = item.get('type', '')

            self.logger.info(f"📋 Output item added: type={item_type}")

            # Mark response as in progress when API starts generating ANY output
            # This catches responses we didn't initiate (shouldn't happen, but defensive)
            # ⚠️ CRITICAL: Set flag on connection_manager so audio_capture can check it
            if not self.response_in_progress:
                self.response_in_progress = True
                if self.connection_manager:
                    self.connection_manager.response_in_progress = True
                self.logger.debug("🚦 Response flag set to in_progress (output_item_added)")

            # If it's a function call, initialize our tracking
            if item_type == 'function_call':
                function_name = item.get('name', '')
                call_id = item.get('call_id', '')

                self.logger.info(f"🎯 Function call starting: {function_name} (call_id={call_id})")

                # Initialize function call tracking
                self.current_function_call = {
                    "name": function_name,
                    "call_id": call_id,
                    "arguments": ""
                }

            # If it's a message, store the item ID for later tracking
            elif item_type == 'message':
                item_id = item.get('id', '')
                self.logger.debug(f"💬 Message item starting: id={item_id}")
                # Note: content will come through conversation.item.created event

        except Exception as e:
            self.logger.error(f"Error handling output item added: {e}")

    def _on_function_args_delta(self, event):
        """
        Handle streaming function call arguments delta

        Event format:
        {
            "type": "response.function_call_arguments.delta",
            "call_id": "...",
            "delta": "{\"distance\""  # Streaming JSON chunks
        }

        NOTE: This event does NOT contain the function name!
        The name comes from response.output_item.added earlier.
        """
        try:
            # Get the delta
            delta = event.get('delta', '')

            # If we don't have a current call initialized, something is wrong
            if not self.current_function_call:
                self.logger.warning(f"⚠️ Received function args delta but no current_function_call! Delta: {delta}")
                return

            # Append the argument delta
            self.current_function_call['arguments'] += delta
            self.logger.debug(f"📝 Function args delta: {len(delta)} chars (total: {len(self.current_function_call['arguments'])})")

        except Exception as e:
            self.logger.error(f"Error handling function args delta: {e}")

    def _on_function_args_done(self, event):
        """Handle completed function call arguments and execute"""
        try:
            if not self.current_function_call:
                return

            function_name = self.current_function_call['name']
            call_id = self.current_function_call['call_id']
            args_json = self.current_function_call['arguments']

            self.logger.info(f"Function call: {function_name}({args_json})")
            self.function_call_count += 1

            # Parse arguments
            try:
                args = json.loads(args_json) if args_json else {}
            except json.JSONDecodeError:
                args = {}

            # Execute function
            result = self._execute_function(function_name, args)
            self.logger.info(f"🎬 Function execution result: {result}")

            # Send function output back to API
            if self.connection_manager:
                self.connection_manager.send_sync({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result)
                    }
                })

            # Reset for next call
            self.current_function_call = None

        except Exception as e:
            self.logger.error(f"Error handling function args done: {e}")

    def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call"""
        try:
            self.logger.info(f"🎬 Executing function: {function_name} with args: {args}")

            # Handle camera snapshot
            if function_name == "take_snapshot":
                self.logger.info("📸 Handling camera snapshot")
                return self._handle_take_snapshot()

            # Handle memory functions
            if function_name == "remember":
                self.logger.info("🧠 Handling memory storage")
                return self._handle_remember(args)

            if function_name == "recall":
                self.logger.info("🧠 Handling memory recall")
                return self._handle_recall(args)

            # Handle movement commands
            if function_name in ["move_forward", "move_backward", "turn_left", "turn_right", "stop_movement"]:
                self.logger.info(f"🚗 Handling movement: {function_name}")
                return self._handle_movement(function_name, args)

            # Handle sound functions
            if function_name in ["play_sound", "honk", "rev_engine"]:
                self.logger.info(f"🔊 Handling sound: {function_name}")
                return self._handle_gesture(function_name, args)

            # Handle gesture from library
            if function_name in self.gesture_functions:
                self.logger.info(f"🤖 Handling gesture: {function_name}")
                return self._handle_gesture(function_name, args)

            self.logger.warning(f"❌ Unknown function: {function_name}")
            return {"status": "error", "message": f"Unknown function: {function_name}"}

        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_gesture(self, gesture_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a gesture and return result"""
        try:
            # Handle play_sound specially - needs sound_name parameter
            if gesture_name == "play_sound":
                sound_name = args.get('sound_name', 'honk')
                volume = args.get('volume', 100)
                action_string = f"play_sound {sound_name} {volume}"
                self.logger.info(f"🔊 Sound action: {action_string}")

            # Handle honk and rev_engine - simple sounds
            elif gesture_name in ["honk", "rev_engine"]:
                action_string = gesture_name
                self.logger.info(f"🔊 Simple sound: {action_string}")

            # Handle regular gestures - use speed parameter
            else:
                speed = args.get('speed', 'med')
                action_string = f"{gesture_name}:{speed}"
                self.logger.info(f"🤖 Gesture action: {action_string}")

            # Publish robot action
            robot_action_data = {
                "actions": [action_string],
                "source_text": "realtime_api_function_call",
                "mood": "neutral",
                "priority": 100,
                "timestamp": time.time()
            }

            if self.publish("robot_action", robot_action_data):
                self.logger.info(f"✓ Executed action: {action_string}")
                return {"status": "success", "action": action_string}
            else:
                return {"status": "error", "message": "Failed to publish gesture"}

        except Exception as e:
            self.logger.error(f"Error handling gesture: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_movement(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle movement commands"""
        try:
            distance = args.get('distance', 10)
            speed = args.get('speed', 20)

            action_map = {
                "move_forward": f"forward {distance} {speed}",
                "move_backward": f"backward {distance} {speed}",
                "turn_left": "left",
                "turn_right": "right",
                "stop_movement": "stop"
            }

            action = action_map.get(function_name, "stop")

            robot_action_data = {
                "actions": [action],
                "source_text": "realtime_api_movement",
                "mood": "neutral",
                "priority": 100,
                "timestamp": time.time()
            }

            if self.publish("robot_action", robot_action_data):
                self.logger.info(f"Executed movement: {action}")
                return {"status": "success", "action": action}
            else:
                return {"status": "error", "message": "Failed to publish movement"}

        except Exception as e:
            self.logger.error(f"Error handling movement: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_take_snapshot(self) -> Dict[str, Any]:
        """Handle camera snapshot request"""
        try:
            self.logger.info("Requesting camera snapshot")

            snap_pic_data = {
                "requested_by": "ai_node22",
                "timestamp": time.time()
            }

            if self.publish("snap_pic", snap_pic_data):
                # If we have a recent image, send it with the response
                if self.latest_image:
                    return {
                        "status": "success",
                        "message": "Snapshot taken",
                        "has_recent_image": True
                    }
                return {"status": "success", "message": "Snapshot requested"}
            else:
                return {"status": "error", "message": "Failed to publish snapshot request"}

        except Exception as e:
            self.logger.error(f"Error handling snapshot: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_remember(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory storage request"""
        try:
            message = args.get('message', '')
            response = args.get('response', '')
            category = args.get('category', 'general')
            importance = args.get('importance', 5)

            if not message:
                return {"status": "error", "message": "No message provided to remember"}

            self.logger.info(f"Storing memory: category={category}, importance={importance}")

            # Publish memory request to memory node
            memory_request_data = {
                "operation": "remember",
                "params": {
                    "message": message,
                    "response": response,
                    "category": category,
                    "importance": importance
                },
                "timestamp": time.time()
            }

            if self.publish("memory_request", memory_request_data):
                self.logger.info(f"✓ Memory request published")
                return {
                    "status": "success",
                    "message": f"Memory stored (category={category}, importance={importance})"
                }
            else:
                return {"status": "error", "message": "Failed to publish memory request"}

        except Exception as e:
            self.logger.error(f"Error handling remember: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_recall(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory recall request"""
        try:
            query = args.get('query', '')
            category = args.get('category')
            limit = args.get('limit', 5)
            min_importance = args.get('min_importance', 3)

            if not query:
                return {"status": "error", "message": "No query provided for recall"}

            self.logger.info(f"Recalling memories for query: {query}")

            # Publish memory request to memory node
            memory_request_data = {
                "operation": "recall",
                "params": {
                    "query": query,
                    "category": category,
                    "limit": limit,
                    "min_importance": min_importance
                },
                "timestamp": time.time()
            }

            if self.publish("memory_request", memory_request_data):
                self.logger.info(f"✓ Memory recall request published")
                # NOTE: The actual memories will be returned via memory_response topic
                # For now, we just acknowledge the request
                return {
                    "status": "success",
                    "message": f"Memory recall requested for: {query}",
                    "note": "Memories will be available via memory_response topic"
                }
            else:
                return {"status": "error", "message": "Failed to publish memory recall request"}

        except Exception as e:
            self.logger.error(f"Error handling recall: {e}")
            return {"status": "error", "message": str(e)}

    def _on_response_done(self, event):
        """Handle complete response"""
        try:
            self.logger.info(f"✅✅✅ response.done EVENT RECEIVED: {event}")

            # Clear response in progress flag
            # ⚠️ CRITICAL: Clear flag on connection_manager so audio_capture knows we're ready
            if self.response_in_progress:
                elapsed = time.time() - self.response_start_time if self.response_start_time else 0
                self.response_in_progress = False
                if self.connection_manager:
                    self.connection_manager.response_in_progress = False
                self.response_start_time = None
                self.logger.info(f"🚦 Response flag cleared after {elapsed:.2f}s - ready for next command")
            else:
                self.logger.warning("⚠️ Response done event but flag was already False")

            self._set_system_mode("idle", "response_done")

        except Exception as e:
            self.logger.error(f"Error handling response done: {e}")
            # Ensure flag is cleared even on error
            self.response_in_progress = False
            if self.connection_manager:
                self.connection_manager.response_in_progress = False
            self.response_start_time = None

    def _on_speech_started(self, event):
        """Handle user speech detected"""
        self.logger.debug("User speech started")
        self._set_system_mode("listening", "speech_detected")

    def _on_speech_stopped(self, event):
        """Handle user speech ended"""
        self.logger.debug("User speech stopped")
        self._set_system_mode("thinking", "speech_ended")

    # ========================================================================
    # Message Bus Callbacks (from NevilNode)
    # ========================================================================

    def on_voice_command(self, message):
        """Handle voice commands from speech recognition"""
        try:
            text = message.data.get("text", "")
            confidence = message.data.get("confidence", 0.0)
            conversation_id = message.data.get("conversation_id")

            if not conversation_id:
                conversation_id = self.chat_logger.generate_conversation_id()

            self.current_conversation_id = conversation_id

            self.logger.info(f"Voice command: '{text}' (conf={confidence:.2f})")

            # Check if response already in progress
            if self.response_in_progress:
                # Safety check: if flag has been set for >30 seconds, clear it (stuck state)
                if self.response_start_time is not None:
                    elapsed = time.time() - self.response_start_time
                    if elapsed > 30.0:
                        self.logger.warning(f"⚠️ Response flag stuck for {elapsed:.1f}s - auto-clearing")
                        self.response_in_progress = False
                        self.response_start_time = None
                    else:
                        self.logger.warning(f"⏳ Response in progress ({elapsed:.1f}s), ignoring new command: '{text}'")
                        return
                else:
                    self.logger.warning(f"⏳ Response in progress, ignoring new command: '{text}'")
                    return

            # Send text to Realtime API (it will generate response)
            if self.connection_manager and self.connection_manager.is_connected():
                # For text input, we create a conversation item
                self.connection_manager.send_sync({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": text
                            }
                        ]
                    }
                })

                # Mark response as in progress before triggering
                self.response_in_progress = True
                self.response_start_time = time.time()
                self.logger.info("🚦 Response flag set to in_progress - waiting for response.done event")

                # Trigger response generation
                self.connection_manager.send_sync({
                    "type": "response.create"
                })

                self._set_system_mode("thinking", "processing_command")
            else:
                self.logger.warning("Not connected to Realtime API")

        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")

    def on_visual_data(self, message):
        """Handle visual data from camera"""
        try:
            image_data = message.data.get("image_data", "")
            capture_id = message.data.get("capture_id", "")
            timestamp = message.data.get("timestamp", time.time())

            if image_data:
                # Store latest image
                self.latest_image = {
                    "data": image_data,
                    "capture_id": capture_id,
                    "timestamp": timestamp
                }

                self.logger.info(f"Received visual data: {capture_id}")

                # Check if response already in progress
                if self.response_in_progress:
                    self.logger.warning(f"⏳ Response in progress, ignoring visual data: {capture_id}")
                    return

                # Send image to Realtime API for multimodal processing
                if self.connection_manager and self.connection_manager.is_connected():
                    # Format image data as data URL if it's base64
                    if not image_data.startswith("data:"):
                        # Assume JPEG if not specified
                        image_url = f"data:image/jpeg;base64,{image_data}"
                    else:
                        image_url = image_data

                    self.connection_manager.send_sync({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_url
                                    }
                                }
                            ]
                        }
                    })

                    # Mark response as in progress before triggering
                    self.response_in_progress = True
                    self.logger.debug("🚦 Response flag set to in_progress (visual)")

                    # Trigger vision response
                    self.connection_manager.send_sync({
                        "type": "response.create"
                    })

                    self._set_system_mode("thinking", "processing_image")

        except Exception as e:
            self.logger.error(f"Error handling visual data: {e}")

    # ========================================================================
    # NevilNode Lifecycle Methods
    # ========================================================================

    def main_loop(self):
        """Main processing loop - minimal for event-driven architecture"""
        time.sleep(0.1)

    def cleanup(self):
        """Cleanup Realtime API connection"""
        self.logger.info("Cleaning up AI Node v2.2...")

        self._set_system_mode("idle", "shutting_down")

        if self.connection_manager:
            self.connection_manager.stop("Node shutdown")
            self.connection_manager.destroy()

        self.logger.info(f"AI Node v2.2 stopped: {self.processing_count} responses, "
                        f"{self.function_call_count} function calls")

    def _set_system_mode(self, mode: str, reason: str):
        """Set system mode and publish change"""
        mode_data = {
            "mode": mode,
            "reason": reason,
            "timestamp": time.time()
        }

        self.publish("system_mode", mode_data)
        self.logger.debug(f"System mode: {mode} ({reason})")

    # ========================================================================
    # Status and Monitoring
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get node statistics"""
        stats = {
            "model": self.model,
            "voice": self.voice,
            "processing_count": self.processing_count,
            "function_call_count": self.function_call_count,
            "error_count": self.error_count,
            "connected": self.connection_manager.is_connected() if self.connection_manager else False,
            "gesture_library_size": len(self.gesture_functions)
        }

        if self.connection_manager:
            stats["connection_metrics"] = self.connection_manager.get_metrics()
            stats["event_stats"] = self.connection_manager.get_event_stats()

        return stats

# Alias for launcher compatibility
AiCognitionRealtimeNode = AiNode22
