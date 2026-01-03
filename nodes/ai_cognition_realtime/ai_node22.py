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
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

from nevil_framework.base_node import NevilNode
from nevil_framework.chat_logger import get_chat_logger
from nevil_framework.youtube_library import YouTubeLibrary
from nevil_framework.gesture_injector import get_gesture_injector
from nevil_framework.realtime.realtime_connection_manager import (
    RealtimeConnectionManager,
    ConnectionConfig,
    SessionConfig
)

# Import OpenAI for vision processing (Chat Completions API)
from openai import OpenAI

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
                              self.realtime_config.get('voice', 'echo'))
        self.temperature = float(os.getenv('NEVIL_REALTIME_TEMPERATURE',
                                          self.realtime_config.get('temperature', 0.6)))
        self.modalities = self.realtime_config.get('modalities', ['text', 'audio'])

        # Get system instructions from config
        self.system_instructions = self.ai_config.get('system_prompt')
        if not self.system_instructions:
            raise ValueError("system_prompt must be configured in .messages file")

        # Connection manager
        self.connection_manager: Optional[RealtimeConnectionManager] = None

        # OpenAI client for vision (Chat Completions API)
        # Realtime API doesn't support vision, so we use standard API for images
        self.openai_vision_client: Optional[OpenAI] = None
        self.vision_model = os.getenv('NEVIL_VISION_MODEL', 'gpt-4o')  # gpt-4o or gpt-4-vision-preview

        # Response streaming state
        self.current_response_text = ""
        self.current_function_call = None
        self.current_conversation_id = None
        self.response_in_progress = False  # Track if API is generating a response
        self.response_start_time = None  # Track when response started (for timeout safety)
        self.gesture_count_in_response = 0  # Count how many times GPT called perform_gesture
        self.last_response_text = ""  # Store last response for gesture injection

        # Visual data storage
        self.latest_image: Optional[Dict[str, Any]] = None
        self.pending_vision_image: Optional[Dict[str, Any]] = None  # Queue for images arriving during responses

        # Autonomous vision settings
        # Philosophy: 80% vision during interactions, 20% unsolicited autonomous
        # Longer intervals = vision happens mostly when you talk to Nevil
        self.autonomous_vision_enabled = os.getenv('NEVIL_AUTONOMOUS_VISION', 'true').lower() == 'true'
        self.autonomous_vision_interval_base = int(os.getenv('NEVIL_VISION_INTERVAL', '180'))  # Base interval (3 minutes)
        self.autonomous_vision_randomness = 0.5  # ±50% randomness (e.g., 180s ± 90s = 90-270s = 1.5-4.5min)
        self.next_vision_time = 0  # When next autonomous vision should trigger
        self.last_vision_time = 0  # Track when we last took a snapshot
        self.min_vision_interval = 15  # Minimum seconds between snapshots (prevent spam)

        # Statistics
        self.processing_count = 0
        self.function_call_count = 0
        self.error_count = 0
        self.vision_call_count = 0
        self.vision_error_count = 0
        self.autonomous_vision_count = 0  # Track autonomous snapshots

        # Initialize YouTube music library BEFORE loading gestures (needed by gesture library)
        self.youtube_library = YouTubeLibrary()
        self.logger.info(f"YouTube library initialized with {len(self.youtube_library.library)} songs")

        # Load gesture library for function calling
        self._load_gesture_library()

    def _load_gesture_library(self):
        """Load gesture library with single perform_gesture function (93% cost reduction)"""
        try:
            # Import gesture functions
            import sys
            gestures_path = Path(__file__).parent.parent.parent / "nodes" / "navigation"
            if str(gestures_path) not in sys.path:
                sys.path.insert(0, str(gestures_path))

            import extended_gestures

            # Build gesture name → function mapping (for execution)
            self.gesture_functions = {}
            gesture_names = [
                name for name in dir(extended_gestures)
                if callable(getattr(extended_gestures, name))
                and not name.startswith('_')
                and name not in ['time', 'Enum', 'GestureSpeed', 'play_sound', 'honk', 'rev_engine']
            ]

            for gesture_name in gesture_names:
                self.gesture_functions[gesture_name] = getattr(extended_gestures, gesture_name)

            # Build gesture list string for function description
            gesture_list = ", ".join(gesture_names)

            # Create SINGLE function definition with ALL gestures
            self.gesture_definitions = [
                {
                    "type": "function",
                    "name": "perform_gesture",
                    "description": f"IMPORTANT: You are a physical robot - USE GESTURES FREQUENTLY to be expressive and engaging! Perform gestures while talking to bring your responses to life. Match gestures to your emotions and the conversation: wave when greeting, nod when agreeing, show excitement with spins/bounces, tilt head when curious. Be animated and physical - you're not just a voice, you're a robot with a body! Available gestures: {gesture_list}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "gesture_name": {
                                "type": "string",
                                "description": "Name of gesture to perform (choose from the list above)"
                            },
                            "speed": {
                                "type": "string",
                                "enum": ["slow", "med", "fast"],
                                "description": "Speed: slow=gentle/thoughtful, med=normal, fast=excited/emphatic",
                                "default": "med"
                            }
                        },
                        "required": ["gesture_name"]
                    }
                },

                # Sound effects as single function
                {
                    "type": "function",
                    "name": "play_sound",
                    "description": "Play a sound effect. Available: honk, rev_engine, airhorn, train_horn, wolf_howl, ghost, alien_voice, dubstep, reggae, machine_gun",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sound_name": {
                                "type": "string",
                                "description": "Name of sound to play"
                            }
                        },
                        "required": ["sound_name"]
                    }
                },

                # Camera
                {
                    "type": "function",
                    "name": "take_snapshot",
                    "description": "✅ YOU HAVE WORKING VISION! Call this function to capture and analyze what your camera sees. The system will process the image and tell you exactly what's in view. Your vision WORKS and you SHOULD use it often - when exploring, when curious, when asked about surroundings, when moving to new locations, or when someone shows you something. After calling this function, you will receive a description of what your camera sees and you can talk about it naturally. BE VISUALLY ENGAGED - you're a robot with working eyes!",
                    "parameters": {"type": "object", "properties": {}}
                },

                # Memory
                {
                    "type": "function",
                    "name": "remember",
                    "description": "Store a memory for later recall",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "response": {"type": "string"},
                            "category": {"type": "string", "enum": ["preference", "personal", "intense", "general"]},
                            "importance": {"type": "number"}
                        },
                        "required": ["message", "response", "category", "importance"]
                    }
                },

                {
                    "type": "function",
                    "name": "recall",
                    "description": "Recall memories using semantic search",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            ]

            # Add YouTube music function
            youtube_func = self.youtube_library.get_ai_function_definition()
            self.gesture_definitions.append(youtube_func)
            self.logger.info(f"✅ Added YouTube music function: {youtube_func['name']}")

            self.logger.info(f"Loaded {len(self.gesture_functions)} gestures via single function (93% cost reduction)")
            self.logger.info(f"Total functions available to AI: {len(self.gesture_definitions)}")

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

            # Initialize OpenAI client for vision (Chat Completions API)
            # Realtime API doesn't support images, so we use standard API
            if api_key:
                self.openai_vision_client = OpenAI(api_key=api_key, max_retries=2)
                self.logger.info(f"✅ Vision API initialized with model: {self.vision_model}")
            else:
                self.logger.warning("⚠️ No OPENAI_API_KEY - vision disabled (Realtime API doesn't support images)")

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
            self.last_response_text += delta  # Store for gesture injection

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

                # Process any pending vision images that arrived during response
                if self.pending_vision_image:
                    pending = self.pending_vision_image
                    self.pending_vision_image = None
                    self.logger.info(f"🔄 Processing queued vision image: {pending['capture_id']}")

                    # Create a mock message to process the queued image
                    from types import SimpleNamespace
                    queued_message = SimpleNamespace(data=pending)
                    # Schedule vision processing on next event loop iteration to avoid blocking
                    import threading
                    threading.Timer(0.1, lambda: self.on_visual_data(queued_message, force_process=True)).start()

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

            # Handle gesture performance (new single function)
            if function_name == "perform_gesture":
                self.gesture_count_in_response += 1  # Increment gesture counter
                return self._handle_perform_gesture(args)

            # Handle sound effects
            elif function_name == "play_sound":
                return self._handle_play_sound(args)

            # Handle camera snapshot
            elif function_name == "take_snapshot":
                self.logger.info("📸 Handling camera snapshot")
                return self._handle_take_snapshot()

            # Handle memory functions
            elif function_name == "remember":
                self.logger.info("🧠 Handling memory storage")
                return self._handle_remember(args)

            elif function_name == "recall":
                self.logger.info("🧠 Handling memory recall")
                return self._handle_recall(args)

            # Handle YouTube music streaming
            elif function_name == "stream_youtube_music":
                self.logger.info("🎵 Handling YouTube music streaming")
                return self._handle_stream_youtube_music(args)

            else:
                self.logger.warning(f"❌ Unknown function: {function_name}")
                return {"status": "error", "message": f"Unknown function: {function_name}"}

        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_perform_gesture(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle gesture performance - AI chose gesture by name"""
        try:
            gesture_name = args.get('gesture_name', '')
            speed = args.get('speed', 'med')

            if not gesture_name:
                return {"status": "error", "message": "No gesture_name provided"}

            # Validate gesture exists
            if gesture_name not in self.gesture_functions:
                available = ", ".join(list(self.gesture_functions.keys())[:10]) + "..."
                return {
                    "status": "error",
                    "message": f"Unknown gesture '{gesture_name}'. Available: {available}"
                }

            # Build action string
            action = f"{gesture_name}:{speed}"
            self.logger.info(f"🤖 AI chose gesture: {action}")

            # Publish gesture
            robot_action_data = {
                "actions": [action],
                "source_text": "ai_gesture",
                "mood": "neutral",
                "priority": 100,
                "timestamp": time.time()
            }

            if self.publish("robot_action", robot_action_data):
                return {"status": "success", "gesture": action}
            else:
                return {"status": "error", "message": "Failed to publish gesture"}

        except Exception as e:
            self.logger.error(f"Error performing gesture: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_play_sound(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sound effect playback"""
        try:
            sound_name = args.get('sound_name', 'honk')
            self.logger.info(f"🔊 AI chose sound: {sound_name}")

            # Publish sound action
            robot_action_data = {
                "actions": [f"play_sound {sound_name}"],
                "source_text": "ai_sound",
                "mood": "neutral",
                "priority": 100,
                "timestamp": time.time()
            }

            if self.publish("robot_action", robot_action_data):
                return {"status": "success", "sound": sound_name}
            else:
                return {"status": "error", "message": "Failed to publish sound"}

        except Exception as e:
            self.logger.error(f"Error playing sound: {e}")
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

    def _handle_stream_youtube_music(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle YouTube music streaming"""
        try:
            category = args.get('category')
            mood = args.get('mood')

            self.logger.info(f"🎵 Streaming YouTube music: category={category}, mood={mood}")

            # Stream audio via youtube library
            result = self.youtube_library.stream_audio(
                category=category,
                mood=mood
            )

            return result

        except Exception as e:
            self.logger.error(f"Error in _handle_stream_youtube_music: {e}")
            return {"status": "error", "message": str(e)}

    def _on_response_done(self, event):
        """Handle complete response"""
        try:
            self.logger.info(f"✅✅✅ response.done EVENT RECEIVED: {event}")

            # 🎭 ADDITIVE GESTURE INJECTION: Top up to minimum gesture count
            MIN_GESTURES = 3
            MAX_ADDITIONAL = 6

            if self.last_response_text:
                gestures_needed = MIN_GESTURES - self.gesture_count_in_response

                if gestures_needed > 0:
                    self.logger.warning(f"⚠️  GPT only called perform_gesture {self.gesture_count_in_response} times! Need {gestures_needed} more to reach minimum {MIN_GESTURES}")
                    injector = get_gesture_injector()
                    # Inject just enough to reach minimum, or up to MAX_ADDITIONAL
                    auto_gestures = injector.analyze_and_inject(
                        self.last_response_text,
                        min_gestures=gestures_needed,
                        max_gestures=min(gestures_needed + 3, MAX_ADDITIONAL)
                    )

                    if auto_gestures:
                        self.logger.info(f"🎭 TOP-UP INJECTING {len(auto_gestures)} gestures: {auto_gestures}")
                        # Publish gestures immediately
                        self.publish("robot_action", {
                            "actions": auto_gestures,
                            "source_text": "auto_inject",
                            "mood": "neutral",
                            "priority": 100,
                            "timestamp": time.time()
                        })
                else:
                    self.logger.info(f"✅ GPT called perform_gesture {self.gesture_count_in_response} times - sufficient gestures!")

            # Reset gesture tracking for next response
            self.gesture_count_in_response = 0
            self.last_response_text = ""

            # Clear response in progress flag
            # ⚠️ CRITICAL: Clear flag on connection_manager so audio_capture knows we're ready
            if self.response_in_progress:
                elapsed = time.time() - self.response_start_time if self.response_start_time else 0
                self.response_in_progress = False
                if self.connection_manager:
                    self.connection_manager.response_in_progress = False
                self.response_start_time = None
                self.logger.info(f"🚦 Response flag cleared after {elapsed:.2f}s - ready for next command")

                # Process any pending vision images that arrived during response
                if self.pending_vision_image:
                    pending = self.pending_vision_image
                    self.pending_vision_image = None
                    self.logger.info(f"🔄 Processing queued vision image: {pending['capture_id']}")

                    # Create a mock message to process the queued image
                    from types import SimpleNamespace
                    queued_message = SimpleNamespace(data=pending)
                    # Schedule vision processing on next event loop iteration to avoid blocking
                    import threading
                    threading.Timer(0.1, lambda: self.on_visual_data(queued_message, force_process=True)).start()
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

            # ========================================================================
            # 🎥 VISION INTENT DETECTION (NOT relying on function calling!)
            # ========================================================================
            # The Realtime API model knows it doesn't support images natively,
            # so it won't call take_snapshot() even though our hybrid system works.
            # Solution: Detect vision intents and trigger camera ourselves!

            text_lower = text.lower()

            # Direct vision request keywords
            vision_keywords = [
                "what do you see", "what can you see", "what are you looking at",
                "what's in front", "look at", "describe what you see",
                "tell me what you see", "what do you observe", "what's around you",
                "look around", "take a look", "show me what you see", "check your camera"
            ]

            # Context keywords that suggest vision would be helpful
            surroundings_keywords = [
                "where are you", "what's around", "what room", "describe your location",
                "what's nearby", "what's in the room", "environment", "surroundings"
            ]

            # Check for direct vision request
            if any(keyword in text_lower for keyword in vision_keywords):
                self.logger.info(f"🎥 DIRECT VISION REQUEST - triggering camera")

                # Add user's question to conversation
                if self.connection_manager and self.connection_manager.is_connected():
                    self.connection_manager.send_sync({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": text}]
                        }
                    })

                # Trigger camera
                self._trigger_vision_snapshot(trigger="voice_direct")
                self.logger.info("⏸️ Waiting for vision data before responding...")
                return  # Vision handler will inject description and trigger response

            # Check for surroundings discussion (trigger vision but continue with conversation)
            elif any(keyword in text_lower for keyword in surroundings_keywords):
                self.logger.info(f"🌍 SURROUNDINGS CONTEXT detected - triggering autonomous vision")
                # Trigger vision in background (don't wait for it)
                self._trigger_vision_snapshot(trigger="context_surroundings")
                # Continue processing the voice command normally

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

    def on_visual_data(self, message, force_process=False):
        """
        Handle visual data from camera using hybrid approach:
        - Use Chat Completions API for vision (Realtime API doesn't support images)
        - Inject vision analysis back into Realtime conversation as text

        Args:
            message: Message containing image data
            force_process: If True, process immediately even if response in progress (for queued images)
        """
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

                self.logger.info(f"📸 Received visual data: {capture_id} (force_process={force_process})")

                # Check if vision is available
                if not self.openai_vision_client:
                    self.logger.warning("⚠️ Vision client not available - skipping image analysis")
                    return

                # Don't process if already responding - queue for later (UNLESS force_process=True)
                if self.response_in_progress and not force_process:
                    self.logger.info(f"⏳ Response in progress - queuing image for processing after response: {capture_id}")
                    self.pending_vision_image = {
                        "data": image_data,
                        "capture_id": capture_id,
                        "timestamp": timestamp
                    }
                    return

                # If force_process but response in progress, log warning but proceed
                if self.response_in_progress and force_process:
                    self.logger.warning(f"⚠️ Force processing queued image {capture_id} even though response in progress")

                # Use Chat Completions API to analyze the image
                # Realtime API doesn't support images, so we use standard API
                try:
                    self.logger.info(f"🔍 Analyzing image with {self.vision_model}...")

                    # Build vision prompt
                    # Describe the scene objectively - Nevil will interpret it in his own voice
                    vision_prompt = (
                        "Describe this camera view objectively in 2-3 concise sentences. "
                        "Be specific about: objects, people, colors, spatial relationships, and notable details. "
                        "Format: Just describe what's visible, like a camera feed description. "
                        "Example: 'A wooden desk with a laptop and red mug. Natural lighting from a window on the left.'"
                    )

                    # Call Chat Completions API with vision
                    # Note: Using max_tokens=200 for detailed descriptions, temperature=0.7 for natural language
                    response = self.openai_vision_client.chat.completions.create(
                        model=self.vision_model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": vision_prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_data}",
                                            "detail": "low"  # Use low detail for faster/cheaper processing (65 tokens vs 1105 for high)
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=200,  # Increased from 150 to allow more detailed descriptions
                        temperature=0.7,
                        timeout=10.0  # 10 second timeout to prevent hanging
                    )

                    self.vision_call_count += 1

                    # Extract vision analysis
                    if response and response.choices and response.choices[0].message.content:
                        vision_description = response.choices[0].message.content.strip()
                        self.logger.info(f"👁️ Vision analysis: {vision_description}")

                        # Inject vision description into Realtime conversation context
                        # CRITICAL: Frame this as information ABOUT Nevil's camera, not from the user
                        # Make it crystal clear this is what HIS camera sees
                        if self.connection_manager and self.connection_manager.is_connected():
                            # Add vision as system-style context informing Nevil what his camera sees
                            # Use clear, direct language: "Your camera sees: ..."
                            self.connection_manager.send_sync({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": f"[SYSTEM: Your camera is showing you this view: {vision_description}]"
                                        }
                                    ]
                                }
                            })

                            # Only trigger a response if not already in progress
                            # If response is already happening, vision description will be available for next interaction
                            if not self.response_in_progress:
                                # Mark response as in progress
                                self.response_in_progress = True
                                self.response_start_time = time.time()
                                if self.connection_manager:
                                    self.connection_manager.response_in_progress = True
                                self.logger.debug("🚦 Response flag set to in_progress (vision)")

                                # Trigger response - the user's question is already in conversation
                                # No need to add another prompt
                                self.connection_manager.send_sync({
                                    "type": "response.create"
                                })

                                self._set_system_mode("thinking", "processing_vision")
                                self.logger.info(f"✅ Vision context provided, triggering response to user's question: {capture_id}")
                            else:
                                self.logger.info(f"✅ Vision analysis added to conversation context (response in progress): {capture_id}")

                    else:
                        self.logger.error("No valid vision response from API")

                except Exception as vision_error:
                    self.vision_error_count += 1
                    self.logger.error(f"Vision API error ({self.vision_error_count} total): {vision_error}")
                    self.logger.exception("Full vision error traceback:")

                    # If we have too many consecutive errors, disable vision temporarily
                    if self.vision_error_count > 5:
                        self.logger.error(f"⚠️ Too many vision errors ({self.vision_error_count}), consider checking API key and quota")

                    # Don't crash - just skip this image and continue operating

        except Exception as e:
            self.logger.error(f"Error handling visual data: {e}")

    # ========================================================================
    # NevilNode Lifecycle Methods
    # ========================================================================

    def main_loop(self):
        """Main processing loop with autonomous vision (randomized timing)"""
        # Check if it's time for autonomous vision
        if self.autonomous_vision_enabled:
            current_time = time.time()

            # Initialize next_vision_time on first run
            if self.next_vision_time == 0:
                self.next_vision_time = current_time + self._get_random_vision_interval()

            # Check if it's time for next autonomous snapshot
            if current_time >= self.next_vision_time:
                interval = current_time - self.last_vision_time if self.last_vision_time > 0 else 0
                self.logger.info(f"🤖 AUTONOMOUS VISION - Random interval ({interval:.1f}s), taking snapshot")

                if self._trigger_vision_snapshot(trigger="autonomous_random"):
                    # Schedule next random snapshot
                    self.next_vision_time = current_time + self._get_random_vision_interval()
                    next_in = self.next_vision_time - current_time
                    self.logger.debug(f"🔮 Next autonomous vision in ~{next_in:.1f}s")
                else:
                    # Throttled - try again in a bit
                    self.next_vision_time = current_time + 5

        time.sleep(0.1)

    def cleanup(self):
        """Cleanup Realtime API connection"""
        self.logger.info("Cleaning up AI Node v2.2...")

        self._set_system_mode("idle", "shutting_down")

        if self.connection_manager:
            self.connection_manager.stop("Node shutdown")
            self.connection_manager.destroy()

        self.logger.info(f"AI Node v2.2 stopped: {self.processing_count} responses, "
                        f"{self.function_call_count} function calls, "
                        f"{self.vision_call_count} vision analyses "
                        f"({self.autonomous_vision_count} autonomous) "
                        f"({self.vision_error_count} errors)")

    def _trigger_vision_snapshot(self, trigger: str = "manual") -> bool:
        """
        Trigger a vision snapshot with throttling to prevent spam.

        Args:
            trigger: Source of the trigger (voice_direct, context_surroundings, autonomous_periodic)

        Returns:
            True if snapshot was triggered, False if throttled
        """
        current_time = time.time()
        time_since_last = current_time - self.last_vision_time

        # Throttle: Don't allow snapshots more frequent than min_vision_interval
        if time_since_last < self.min_vision_interval:
            self.logger.debug(f"⏸️ Vision throttled ({time_since_last:.1f}s < {self.min_vision_interval}s)")
            return False

        # Trigger camera snapshot
        snap_pic_data = {
            "requested_by": "ai_node22_vision",
            "timestamp": current_time,
            "trigger": trigger
        }
        self.publish("snap_pic", snap_pic_data)
        self.last_vision_time = current_time

        if trigger in ["autonomous_periodic", "autonomous_random"]:
            self.autonomous_vision_count += 1

        self.logger.info(f"📸 Vision snapshot triggered (source: {trigger})")
        return True

    def _get_random_vision_interval(self) -> float:
        """
        Calculate a randomized interval for next autonomous vision.

        Returns random interval within ±randomness of base interval.
        Example: base=45s, randomness=0.5 → returns 23-67s
        """
        variance = self.autonomous_vision_interval_base * self.autonomous_vision_randomness
        min_interval = self.autonomous_vision_interval_base - variance
        max_interval = self.autonomous_vision_interval_base + variance

        # Ensure we don't go below min_vision_interval
        min_interval = max(min_interval, self.min_vision_interval)

        random_interval = random.uniform(min_interval, max_interval)
        return random_interval

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
            "vision_model": self.vision_model,
            "processing_count": self.processing_count,
            "function_call_count": self.function_call_count,
            "error_count": self.error_count,
            "vision_call_count": self.vision_call_count,
            "vision_error_count": self.vision_error_count,
            "autonomous_vision_count": self.autonomous_vision_count,
            "vision_enabled": self.openai_vision_client is not None,
            "autonomous_vision_enabled": self.autonomous_vision_enabled,
            "autonomous_vision_interval_base": self.autonomous_vision_interval_base,
            "autonomous_vision_randomness": f"±{self.autonomous_vision_randomness*100:.0f}%",
            "connected": self.connection_manager.is_connected() if self.connection_manager else False,
            "gesture_library_size": len(self.gesture_functions)
        }

        if self.connection_manager:
            stats["connection_metrics"] = self.connection_manager.get_metrics()
            stats["event_stats"] = self.connection_manager.get_event_stats()

        return stats

# Alias for launcher compatibility
AiCognitionRealtimeNode = AiNode22
