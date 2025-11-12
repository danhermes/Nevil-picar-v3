# OpenAI Realtime API Node Technical Specifications
**Swarm ID**: swarm-1762909553486-yd1fw3wqi
**Agent**: CODER AGENT
**Date**: 2025-11-11

## Executive Summary

This document provides comprehensive technical specifications for three new Nevil v3.0 nodes that integrate the OpenAI Realtime API. These specifications bridge the WebSocket-based Realtime API with Nevil's existing node architecture, message bus, and threading model.

The Realtime API provides low-latency, multimodal conversation capabilities through a persistent WebSocket connection, enabling:
- Real-time audio input streaming (speech recognition)
- Real-time text and audio output (AI responses + speech synthesis)
- Function calling for robot actions
- Conversation memory and context management

### Design Philosophy

1. **Minimal Disruption**: Leverage existing Nevil node patterns (NevilNode base class, .messages configuration, message bus)
2. **WebSocket Management**: Implement robust WebSocket connection handling with reconnection logic
3. **Event-Driven Architecture**: Use Realtime API events to drive state changes and message publishing
4. **Backward Compatibility**: Maintain compatibility with existing nodes while providing enhanced real-time capabilities
5. **Resource Efficiency**: Share a single WebSocket connection across all three nodes

---

## Architecture Overview

### Node Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenAI Realtime API                          │
│              (WebSocket: wss://api.openai.com/v1/realtime)      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ WebSocket Connection
                                │
            ┌───────────────────┴────────────────────┐
            │   Realtime Connection Manager          │
            │   (Shared WebSocket, Event Dispatcher) │
            └───────────────────┬────────────────────┘
                                │
            ┌───────────────────┼────────────────────┐
            │                   │                    │
            ▼                   ▼                    ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Speech          │  │ AI Node 22       │  │ Speech           │
│ Recognition     │  │                  │  │ Synthesis        │
│ Node 22         │  │ (Conversation    │  │ Node 22          │
│                 │  │  Management)     │  │                  │
│ (Audio Input)   │  │                  │  │ (Audio Output)   │
└────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                    │                      │
         │                    │                      │
         └────────────────────┼──────────────────────┘
                              │
                     ┌────────▼────────┐
                     │  Nevil Message  │
                     │      Bus        │
                     └─────────────────┘
```

### Message Flow

**Voice Input → Response Cycle**:
1. `speech_recognition_node22` captures audio → streams to Realtime API
2. Realtime API sends `conversation.item.input_audio_transcription.completed` event
3. `ai_node22` publishes `voice_command` to message bus
4. Realtime API generates response → sends `response.audio.delta` events
5. `speech_synthesis_node22` buffers audio chunks → plays audio output
6. `ai_node22` publishes `text_response` and `robot_action` to message bus

---

## 1. speech_recognition_node22

### Overview

This node handles real-time audio input streaming to the OpenAI Realtime API via WebSocket, replacing the discrete record-transcribe cycle with continuous streaming.

### Class Structure

```python
# nodes/speech_recognition22/speech_recognition_node22.py

from nevil_framework.base_node import NevilNode
from realtime_api.connection_manager import RealtimeConnectionManager
from realtime_api.audio_streamer import AudioStreamer
import pyaudio
import threading
import queue


class SpeechRecognitionNode22(NevilNode):
    """
    Real-time speech recognition using OpenAI Realtime API

    Streams audio continuously via WebSocket instead of discrete recording.
    Handles transcription events and publishes voice commands to message bus.
    """

    def __init__(self):
        super().__init__("speech_recognition22")

        # Realtime API connection (shared across nodes)
        self.connection_manager = None  # Injected by launcher

        # Audio streaming components
        self.audio_streamer = None
        self.pyaudio_instance = None
        self.audio_stream = None

        # State management
        self.is_streaming = False
        self.stream_lock = threading.Lock()

        # Event handlers
        self.event_handlers = {
            'input_audio_buffer.speech_started': self._on_speech_started,
            'input_audio_buffer.speech_stopped': self._on_speech_stopped,
            'conversation.item.input_audio_transcription.completed': self._on_transcription_completed,
            'conversation.item.input_audio_transcription.failed': self._on_transcription_failed,
        }

        # Configuration
        config = self.config.get('configuration', {})
        self.audio_config = config.get('audio', {})
        self.realtime_config = config.get('realtime', {})

        # Performance tracking
        self.transcription_count = 0
        self.error_count = 0
```

### Key Methods

#### Initialization

```python
def initialize(self):
    """Initialize real-time speech recognition components"""
    self.logger.info("Initializing Speech Recognition Node 22...")

    # Initialize PyAudio for microphone access
    self.pyaudio_instance = pyaudio.PyAudio()

    # Create audio streamer
    sample_rate = self.audio_config.get('sample_rate', 24000)
    chunk_size = self.audio_config.get('chunk_size', 4800)

    self.audio_streamer = AudioStreamer(
        sample_rate=sample_rate,
        chunk_size=chunk_size,
        logger=self.logger
    )

    # Register event handlers with connection manager
    for event_type, handler in self.event_handlers.items():
        self.connection_manager.register_event_handler(event_type, handler)

    # Configure input audio transcription
    self.connection_manager.send_event({
        "type": "session.update",
        "session": {
            "input_audio_transcription": {
                "model": "whisper-1"
            }
        }
    })

    self.logger.info("Speech Recognition Node 22 initialization complete")


def cleanup(self):
    """Cleanup real-time speech recognition resources"""
    self.logger.info("Cleaning up speech recognition...")

    # Stop streaming
    self._stop_streaming()

    # Unregister event handlers
    for event_type in self.event_handlers.keys():
        self.connection_manager.unregister_event_handler(event_type)

    # Cleanup PyAudio
    if self.audio_stream:
        self.audio_stream.stop_stream()
        self.audio_stream.close()

    if self.pyaudio_instance:
        self.pyaudio_instance.terminate()

    self.logger.info(f"Speech recognition stopped after {self.transcription_count} transcriptions")
```

#### Audio Streaming

```python
def _start_streaming(self):
    """Start streaming audio to Realtime API"""
    if self.is_streaming:
        return

    with self.stream_lock:
        try:
            # Open audio stream
            sample_rate = self.audio_config.get('sample_rate', 24000)
            chunk_size = self.audio_config.get('chunk_size', 4800)

            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size,
                stream_callback=self._audio_callback
            )

            self.audio_stream.start_stream()
            self.is_streaming = True

            self.logger.info("Started audio streaming to Realtime API")

            # Publish listening status
            self.publish("listening_status", {
                "listening": True,
                "reason": "realtime_streaming_started"
            })

        except Exception as e:
            self.logger.error(f"Failed to start audio streaming: {e}")


def _stop_streaming(self):
    """Stop streaming audio to Realtime API"""
    if not self.is_streaming:
        return

    with self.stream_lock:
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

            self.is_streaming = False

            self.logger.info("Stopped audio streaming")

            # Publish listening status
            self.publish("listening_status", {
                "listening": False,
                "reason": "realtime_streaming_stopped"
            })

        except Exception as e:
            self.logger.error(f"Error stopping audio streaming: {e}")


def _audio_callback(self, in_data, frame_count, time_info, status):
    """PyAudio callback for continuous audio capture"""
    try:
        if status:
            self.logger.warning(f"PyAudio status: {status}")

        # Convert audio bytes to base64 and send to Realtime API
        self.audio_streamer.stream_audio(in_data, self.connection_manager)

    except Exception as e:
        self.logger.error(f"Error in audio callback: {e}")

    return (in_data, pyaudio.paContinue)
```

#### Event Handlers

```python
def _on_speech_started(self, event):
    """Handle speech started event from Realtime API"""
    self.logger.info("🎤 Speech detected - user started speaking")

    # Publish speech detection event
    self.publish("speech_detected", {
        "detected": True,
        "timestamp": time.time()
    })


def _on_speech_stopped(self, event):
    """Handle speech stopped event from Realtime API"""
    self.logger.info("🎤 Speech ended - user stopped speaking")

    # Publish speech detection event
    self.publish("speech_detected", {
        "detected": False,
        "timestamp": time.time()
    })


def _on_transcription_completed(self, event):
    """Handle completed transcription event from Realtime API"""
    try:
        item_id = event.get('item_id')
        content_index = event.get('content_index', 0)
        transcript = event.get('transcript', '')

        if not transcript.strip():
            self.logger.debug("Empty transcription received")
            return

        self.logger.info(f"🎤 Transcribed: '{transcript}'")

        # Publish voice command to message bus
        voice_command_data = {
            "text": transcript.strip(),
            "confidence": 0.95,  # Realtime API doesn't provide confidence
            "timestamp": time.time(),
            "language": "en-US",
            "source": "realtime_api",
            "item_id": item_id
        }

        if self.publish("voice_command", voice_command_data):
            self.transcription_count += 1
            self.logger.info(f"✓ Published voice command: '{transcript}'")
        else:
            self.logger.error("Failed to publish voice command")

    except Exception as e:
        self.logger.error(f"Error handling transcription: {e}")
        self.error_count += 1


def _on_transcription_failed(self, event):
    """Handle failed transcription event from Realtime API"""
    error = event.get('error', {})
    self.logger.error(f"Transcription failed: {error}")
    self.error_count += 1
```

#### Message Callbacks

```python
def on_speaking_status_change(self, message):
    """Handle speaking status changes from speech synthesis"""
    try:
        speaking = message.data.get("speaking", False)

        if speaking:
            # Pause streaming while robot is speaking
            self._stop_streaming()
            self.logger.info("Paused audio streaming - robot is speaking")
        else:
            # Resume streaming when robot finishes speaking
            self._start_streaming()
            self.logger.info("Resumed audio streaming - robot finished speaking")

    except Exception as e:
        self.logger.error(f"Error handling speaking status: {e}")


def on_system_mode_change(self, message):
    """Handle system mode changes"""
    try:
        mode = message.data.get("mode", "idle")

        if mode in ["listening", "idle"]:
            self._start_streaming()
        elif mode in ["speaking", "thinking"]:
            # Keep streaming during thinking, stop during speaking
            if mode == "speaking":
                self._stop_streaming()

    except Exception as e:
        self.logger.error(f"Error handling mode change: {e}")
```

### Configuration (.messages file)

```yaml
# nodes/speech_recognition22/.messages

node_name: "speech_recognition22"
version: "1.0"
description: "Real-time speech recognition using OpenAI Realtime API"

publishes:
  - topic: "voice_command"
    message_type: "VoiceCommand"
    description: "Recognized voice commands from Realtime API"
    frequency: "on_demand"

  - topic: "speech_detected"
    message_type: "SpeechDetection"
    description: "Speech detection events (started/stopped)"
    frequency: "on_change"

  - topic: "listening_status"
    message_type: "ListeningStatus"
    description: "Audio streaming status"
    frequency: "on_change"

subscribes:
  - topic: "speaking_status"
    callback: "on_speaking_status_change"
    description: "Speech synthesis status updates"

  - topic: "system_mode"
    callback: "on_system_mode_change"
    description: "System mode changes"

configuration:
  audio:
    sample_rate: 24000  # Required by Realtime API
    chunk_size: 4800    # 200ms chunks at 24kHz
    channels: 1
    format: "pcm16"

  realtime:
    enable_vad: true  # Voice Activity Detection
    vad_threshold: 0.5
    vad_prefix_padding_ms: 300
    vad_silence_duration_ms: 500
```

### Dependencies

- `pyaudio` - Microphone access and audio capture
- `websockets` - WebSocket client (via RealtimeConnectionManager)
- `base64` - Audio data encoding

### Error Handling

1. **Connection Loss**: Handled by RealtimeConnectionManager with automatic reconnection
2. **Audio Device Errors**: Logged, retry with exponential backoff
3. **Transcription Failures**: Logged, increment error counter, continue streaming
4. **Queue Overflow**: Drop oldest audio chunks, log warning

### Performance Considerations

- **Latency**: ~200-500ms from speech to transcription (vs 2-5s for discrete mode)
- **Bandwidth**: ~48 KB/s for 24kHz PCM16 audio streaming
- **CPU**: Low (<5% for audio capture and base64 encoding)
- **Memory**: ~10MB for audio buffers and event queues

---

## 2. ai_node22

### Overview

This node manages the AI conversation session via the OpenAI Realtime API, handling function calling, context management, and response orchestration.

### Class Structure

```python
# nodes/ai_cognition22/ai_node22.py

from nevil_framework.base_node import NevilNode
from realtime_api.connection_manager import RealtimeConnectionManager
import json
import time


class AiNode22(NevilNode):
    """
    AI Cognition using OpenAI Realtime API

    Manages conversation session, function calling, and response generation.
    Bridges Realtime API responses with Nevil's message bus.
    """

    def __init__(self):
        super().__init__("ai_cognition22")

        # Realtime API connection (shared across nodes)
        self.connection_manager = None  # Injected by launcher

        # Conversation state
        self.conversation_items = []
        self.current_response_id = None

        # Function calling registry
        self.function_registry = {}

        # Event handlers
        self.event_handlers = {
            'response.created': self._on_response_created,
            'response.done': self._on_response_done,
            'response.function_call_arguments.done': self._on_function_call,
            'conversation.item.created': self._on_item_created,
            'error': self._on_error,
        }

        # Configuration
        config = self.config.get('configuration', {})
        self.ai_config = config.get('ai', {})
        self.function_config = config.get('functions', {})

        # System prompt
        self.system_prompt = self.ai_config.get('system_prompt', '')

        # Performance tracking
        self.response_count = 0
        self.function_call_count = 0
        self.error_count = 0
```

### Key Methods

#### Initialization

```python
def initialize(self):
    """Initialize AI cognition with Realtime API"""
    self.logger.info("Initializing AI Node 22...")

    # Register event handlers
    for event_type, handler in self.event_handlers.items():
        self.connection_manager.register_event_handler(event_type, handler)

    # Register robot action functions
    self._register_functions()

    # Configure session with system instructions and tools
    self._configure_session()

    self.logger.info("AI Node 22 initialization complete")


def cleanup(self):
    """Cleanup AI cognition resources"""
    self.logger.info("Cleaning up AI cognition...")

    # Unregister event handlers
    for event_type in self.event_handlers.keys():
        self.connection_manager.unregister_event_handler(event_type)

    # Clear conversation history
    self.conversation_items.clear()

    self.logger.info(f"AI stopped after {self.response_count} responses")
```

#### Session Configuration

```python
def _configure_session(self):
    """Configure Realtime API session with system prompt and tools"""
    try:
        # Build tools/functions list
        tools = []
        for func_name, func_config in self.function_registry.items():
            tools.append({
                "type": "function",
                "name": func_name,
                "description": func_config['description'],
                "parameters": func_config['parameters']
            })

        # Send session update
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.system_prompt,
                "voice": self.ai_config.get('voice', 'alloy'),
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": tools,
                "tool_choice": "auto",
                "temperature": self.ai_config.get('temperature', 0.7),
                "max_response_output_tokens": self.ai_config.get('max_tokens', 4096)
            }
        }

        self.connection_manager.send_event(session_config)
        self.logger.info(f"Configured session with {len(tools)} tools")

    except Exception as e:
        self.logger.error(f"Failed to configure session: {e}")


def _register_functions(self):
    """Register robot action functions for function calling"""

    # Register movement functions
    self.function_registry['move_forward'] = {
        'description': 'Move the robot forward',
        'parameters': {
            'type': 'object',
            'properties': {
                'distance': {
                    'type': 'number',
                    'description': 'Distance to move in centimeters (default: 30)'
                },
                'speed': {
                    'type': 'number',
                    'description': 'Speed percentage 0-100 (default: 50)'
                }
            }
        },
        'handler': self._handle_move_forward
    }

    self.function_registry['turn'] = {
        'description': 'Turn the robot left or right',
        'parameters': {
            'type': 'object',
            'properties': {
                'direction': {
                    'type': 'string',
                    'enum': ['left', 'right'],
                    'description': 'Direction to turn'
                },
                'angle': {
                    'type': 'number',
                    'description': 'Angle to turn in degrees (default: 90)'
                }
            },
            'required': ['direction']
        },
        'handler': self._handle_turn
    }

    # Register camera functions
    self.function_registry['take_snapshot'] = {
        'description': 'Take a picture with the camera',
        'parameters': {
            'type': 'object',
            'properties': {}
        },
        'handler': self._handle_snapshot
    }

    # Register sound functions
    self.function_registry['play_sound'] = {
        'description': 'Play a sound effect',
        'parameters': {
            'type': 'object',
            'properties': {
                'sound_name': {
                    'type': 'string',
                    'enum': ['beep', 'happy', 'sad', 'excited'],
                    'description': 'Name of the sound effect to play'
                }
            },
            'required': ['sound_name']
        },
        'handler': self._handle_play_sound
    }

    self.logger.info(f"Registered {len(self.function_registry)} functions")
```

#### Event Handlers

```python
def _on_response_created(self, event):
    """Handle response creation event"""
    response = event.get('response', {})
    response_id = response.get('id')

    self.current_response_id = response_id
    self.logger.info(f"AI response started: {response_id}")

    # Set system to thinking mode
    self.publish("system_mode", {
        "mode": "thinking",
        "reason": "ai_processing",
        "timestamp": time.time()
    })


def _on_response_done(self, event):
    """Handle response completion event"""
    response = event.get('response', {})
    response_id = response.get('id')
    output = response.get('output', [])

    self.logger.info(f"AI response completed: {response_id}")

    # Extract text from response items
    text_responses = []
    for item in output:
        if item.get('type') == 'message':
            content = item.get('content', [])
            for c in content:
                if c.get('type') == 'text':
                    text_responses.append(c.get('text', ''))

    # Publish text response if available
    if text_responses:
        combined_text = ' '.join(text_responses)
        self.publish("text_response", {
            "text": combined_text,
            "voice": self.ai_config.get('voice', 'alloy'),
            "priority": 100,
            "timestamp": time.time(),
            "response_id": response_id
        })

    self.response_count += 1
    self.current_response_id = None


def _on_function_call(self, event):
    """Handle function call event from Realtime API"""
    try:
        item_id = event.get('item_id')
        call_id = event.get('call_id')
        name = event.get('name')
        arguments = event.get('arguments', '{}')

        self.logger.info(f"Function call: {name} with args: {arguments}")

        # Parse arguments
        args = json.loads(arguments)

        # Execute function if registered
        if name in self.function_registry:
            handler = self.function_registry[name]['handler']
            result = handler(args)

            # Send function call output back to Realtime API
            self.connection_manager.send_event({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result)
                }
            })

            self.function_call_count += 1
        else:
            self.logger.warning(f"Unknown function call: {name}")

            # Send error response
            self.connection_manager.send_event({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps({"error": f"Unknown function: {name}"})
                }
            })

    except Exception as e:
        self.logger.error(f"Error handling function call: {e}")
        self.error_count += 1


def _on_item_created(self, event):
    """Handle conversation item creation event"""
    item = event.get('item', {})
    item_id = item.get('id')

    # Store conversation item for context
    self.conversation_items.append(item)

    # Trim conversation history
    max_items = self.ai_config.get('max_conversation_items', 50)
    if len(self.conversation_items) > max_items:
        self.conversation_items = self.conversation_items[-max_items:]


def _on_error(self, event):
    """Handle error events from Realtime API"""
    error = event.get('error', {})
    error_type = error.get('type', 'unknown')
    message = error.get('message', 'Unknown error')

    self.logger.error(f"Realtime API error: {error_type} - {message}")
    self.error_count += 1

    # Publish error to message bus
    self.publish("system_mode", {
        "mode": "error",
        "reason": f"realtime_api_error: {error_type}",
        "timestamp": time.time()
    })
```

#### Function Handlers

```python
def _handle_move_forward(self, args):
    """Handle move_forward function call"""
    distance = args.get('distance', 30)
    speed = args.get('speed', 50)

    self.logger.info(f"Executing move_forward: distance={distance}, speed={speed}")

    # Publish robot action
    self.publish("robot_action", {
        "actions": ["forward"],
        "distance": distance,
        "speed": speed,
        "priority": 100,
        "timestamp": time.time()
    })

    return {"status": "success", "action": "move_forward", "distance": distance}


def _handle_turn(self, args):
    """Handle turn function call"""
    direction = args.get('direction')
    angle = args.get('angle', 90)

    self.logger.info(f"Executing turn: direction={direction}, angle={angle}")

    # Map to Nevil actions
    action = "left" if direction == "left" else "right"

    # Publish robot action
    self.publish("robot_action", {
        "actions": [action],
        "angle": angle,
        "priority": 100,
        "timestamp": time.time()
    })

    return {"status": "success", "action": "turn", "direction": direction, "angle": angle}


def _handle_snapshot(self, args):
    """Handle take_snapshot function call"""
    self.logger.info("Executing take_snapshot")

    # Publish snap_pic request
    self.publish("snap_pic", {
        "requested_by": "ai_cognition22",
        "timestamp": time.time()
    })

    return {"status": "success", "action": "snapshot_requested"}


def _handle_play_sound(self, args):
    """Handle play_sound function call"""
    sound_name = args.get('sound_name')

    self.logger.info(f"Executing play_sound: {sound_name}")

    # Publish sound effect request
    self.publish("sound_effect", {
        "effect": sound_name,
        "volume": 100,
        "priority": 50,
        "timestamp": time.time()
    })

    return {"status": "success", "action": "play_sound", "sound": sound_name}
```

#### Message Callbacks

```python
def on_voice_command(self, message):
    """Handle voice commands (for backward compatibility)"""
    # Note: With Realtime API, voice commands are automatically
    # processed as conversation items. This callback is for
    # compatibility with other nodes that publish voice_command.
    pass


def on_visual_data(self, message):
    """Handle visual data from camera"""
    try:
        image_data = message.data.get("image_data", "")
        capture_id = message.data.get("capture_id", "")

        if not image_data:
            return

        self.logger.info(f"Received visual data: {capture_id}")

        # Add image to conversation as a user message
        self.connection_manager.send_event({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Here is what I see with my camera. Please describe what you observe."
                    },
                    {
                        "type": "input_image",
                        "image": image_data  # Base64 encoded image
                    }
                ]
            }
        })

        # Trigger response generation
        self.connection_manager.send_event({
            "type": "response.create"
        })

    except Exception as e:
        self.logger.error(f"Error handling visual data: {e}")
```

### Configuration (.messages file)

```yaml
# nodes/ai_cognition22/.messages

node_name: "ai_cognition22"
version: "1.0"
description: "AI cognition using OpenAI Realtime API with function calling"

publishes:
  - topic: "text_response"
    message_type: "TextResponse"
    description: "AI-generated text responses"
    frequency: "on_demand"

  - topic: "robot_action"
    message_type: "RobotAction"
    description: "Robot actions from function calls"
    frequency: "on_demand"

  - topic: "snap_pic"
    message_type: "SnapPicRequest"
    description: "Camera snapshot requests"
    frequency: "on_demand"

  - topic: "sound_effect"
    message_type: "SoundEffect"
    description: "Sound effect playback requests"
    frequency: "on_demand"

  - topic: "system_mode"
    message_type: "SystemMode"
    description: "System mode changes"
    frequency: "on_change"

subscribes:
  - topic: "voice_command"
    callback: "on_voice_command"
    description: "Voice commands (backward compatibility)"

  - topic: "visual_data"
    callback: "on_visual_data"
    description: "Camera images for analysis"

configuration:
  ai:
    system_prompt: |
      You are Nevil, a witty robot dog/car with a camera and the ability to move.
      You can see, hear, and move around. You have a playful, poetic personality.

      When users ask you to move or perform actions, use the available functions
      to control your body. Be specific about what you're doing.

      Keep responses brief (1-3 sentences) and conversational.

    voice: "alloy"
    temperature: 0.7
    max_tokens: 4096
    max_conversation_items: 50

  functions:
    enable_movement: true
    enable_camera: true
    enable_sounds: true
```

### Dependencies

- `websockets` - WebSocket client (via RealtimeConnectionManager)
- `json` - Function argument parsing
- None (uses shared RealtimeConnectionManager)

### Error Handling

1. **Function Call Errors**: Return error in function output, log, continue
2. **Invalid Arguments**: Validate, use defaults, log warning
3. **Response Timeout**: Handled by Realtime API, logged
4. **Connection Loss**: Handled by RealtimeConnectionManager

### Performance Considerations

- **Latency**: ~500-1500ms from voice input to response generation
- **Bandwidth**: Minimal (text-based function calls and responses)
- **CPU**: Low (<3% for event processing)
- **Memory**: ~50MB for conversation history and function registry

---

## 3. speech_synthesis_node22

### Overview

This node handles real-time audio output from the OpenAI Realtime API, buffering and playing audio chunks as they arrive via WebSocket events.

### Class Structure

```python
# nodes/speech_synthesis22/speech_synthesis_node22.py

from nevil_framework.base_node import NevilNode
from realtime_api.connection_manager import RealtimeConnectionManager
from realtime_api.audio_player import AudioPlayer
import pyaudio
import threading
import queue
import base64


class SpeechSynthesisNode22(NevilNode):
    """
    Real-time speech synthesis using OpenAI Realtime API

    Receives streaming audio chunks via WebSocket and plays them
    in real-time with minimal latency.
    """

    def __init__(self):
        super().__init__("speech_synthesis22")

        # Realtime API connection (shared across nodes)
        self.connection_manager = None  # Injected by launcher

        # Audio playback components
        self.audio_player = None
        self.pyaudio_instance = None
        self.audio_stream = None

        # Audio buffering
        self.audio_buffer = queue.Queue(maxsize=100)
        self.playback_thread = None

        # State management
        self.is_speaking = False
        self.speak_lock = threading.Lock()
        self.current_response_id = None

        # Event handlers
        self.event_handlers = {
            'response.audio.delta': self._on_audio_delta,
            'response.audio.done': self._on_audio_done,
            'response.audio_transcript.delta': self._on_transcript_delta,
            'response.audio_transcript.done': self._on_transcript_done,
        }

        # Configuration
        config = self.config.get('configuration', {})
        self.audio_config = config.get('audio', {})

        # Performance tracking
        self.synthesis_count = 0
        self.audio_chunks_played = 0
        self.error_count = 0
```

### Key Methods

#### Initialization

```python
def initialize(self):
    """Initialize real-time speech synthesis components"""
    self.logger.info("Initializing Speech Synthesis Node 22...")

    # Initialize PyAudio for speaker output
    self.pyaudio_instance = pyaudio.PyAudio()

    # Create audio player
    sample_rate = self.audio_config.get('sample_rate', 24000)

    self.audio_player = AudioPlayer(
        sample_rate=sample_rate,
        logger=self.logger
    )

    # Register event handlers
    for event_type, handler in self.event_handlers.items():
        self.connection_manager.register_event_handler(event_type, handler)

    # Start playback thread
    self.playback_thread = threading.Thread(
        target=self._playback_loop,
        name="audio_playback",
        daemon=True
    )
    self.playback_thread.start()

    self.logger.info("Speech Synthesis Node 22 initialization complete")


def cleanup(self):
    """Cleanup real-time speech synthesis resources"""
    self.logger.info("Cleaning up speech synthesis...")

    # Stop playback
    self._stop_playback()

    # Unregister event handlers
    for event_type in self.event_handlers.keys():
        self.connection_manager.unregister_event_handler(event_type)

    # Wait for playback thread
    if self.playback_thread and self.playback_thread.is_alive():
        self.playback_thread.join(timeout=2.0)

    # Cleanup PyAudio
    if self.audio_stream:
        self.audio_stream.stop_stream()
        self.audio_stream.close()

    if self.pyaudio_instance:
        self.pyaudio_instance.terminate()

    self.logger.info(f"Speech synthesis stopped after {self.synthesis_count} syntheses")
```

#### Audio Playback

```python
def _playback_loop(self):
    """Continuous playback loop for buffered audio chunks"""
    self.logger.info("Starting audio playback loop...")

    while not self.shutdown_event.is_set():
        try:
            # Get audio chunk from buffer (blocking with timeout)
            try:
                audio_data = self.audio_buffer.get(timeout=0.1)
            except queue.Empty:
                continue

            # Play audio chunk
            if audio_data and self.audio_stream:
                try:
                    self.audio_stream.write(audio_data)
                    self.audio_chunks_played += 1
                except Exception as e:
                    self.logger.error(f"Error writing audio: {e}")

            self.audio_buffer.task_done()

        except Exception as e:
            self.logger.error(f"Error in playback loop: {e}")
            time.sleep(0.1)

    self.logger.info("Audio playback loop stopped")


def _start_playback(self, response_id):
    """Start audio playback stream"""
    if self.is_speaking:
        self._stop_playback()

    with self.speak_lock:
        try:
            sample_rate = self.audio_config.get('sample_rate', 24000)

            # Open audio output stream
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
                frames_per_buffer=4800
            )

            self.is_speaking = True
            self.current_response_id = response_id

            self.logger.info(f"Started audio playback for response: {response_id}")

            # Publish speaking status
            self.publish("speaking_status", {
                "speaking": True,
                "text": "",  # Text will be updated as transcript arrives
                "timestamp": time.time()
            })

        except Exception as e:
            self.logger.error(f"Failed to start audio playback: {e}")


def _stop_playback(self):
    """Stop audio playback stream"""
    if not self.is_speaking:
        return

    with self.speak_lock:
        try:
            # Drain audio buffer
            while not self.audio_buffer.empty():
                try:
                    audio_data = self.audio_buffer.get_nowait()
                    if self.audio_stream:
                        self.audio_stream.write(audio_data)
                    self.audio_buffer.task_done()
                except queue.Empty:
                    break

            # Close audio stream
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

            self.is_speaking = False
            self.current_response_id = None

            self.logger.info("Stopped audio playback")

            # Publish speaking status
            self.publish("speaking_status", {
                "speaking": False,
                "text": "",
                "timestamp": time.time()
            })

        except Exception as e:
            self.logger.error(f"Error stopping audio playback: {e}")
```

#### Event Handlers

```python
def _on_audio_delta(self, event):
    """Handle streaming audio chunk from Realtime API"""
    try:
        response_id = event.get('response_id')
        item_id = event.get('item_id')
        content_index = event.get('content_index', 0)
        delta = event.get('delta', '')

        if not delta:
            return

        # Start playback if not already started
        if not self.is_speaking or self.current_response_id != response_id:
            self._start_playback(response_id)

        # Decode base64 audio chunk
        audio_bytes = base64.b64decode(delta)

        # Add to playback buffer
        try:
            self.audio_buffer.put_nowait(audio_bytes)
        except queue.Full:
            self.logger.warning("Audio buffer full, dropping chunk")
            self.error_count += 1

    except Exception as e:
        self.logger.error(f"Error handling audio delta: {e}")
        self.error_count += 1


def _on_audio_done(self, event):
    """Handle audio completion event"""
    try:
        response_id = event.get('response_id')
        item_id = event.get('item_id')

        self.logger.info(f"Audio generation complete: {response_id}")

        # Note: Don't stop playback yet - wait for buffer to drain
        # Playback will be stopped by _on_response_done in ai_node22

        self.synthesis_count += 1

    except Exception as e:
        self.logger.error(f"Error handling audio done: {e}")


def _on_transcript_delta(self, event):
    """Handle streaming transcript chunk"""
    try:
        delta = event.get('delta', '')

        if delta:
            # Update speaking status with partial transcript
            self.publish("speaking_status", {
                "speaking": True,
                "text": delta,
                "partial": True,
                "timestamp": time.time()
            })

    except Exception as e:
        self.logger.error(f"Error handling transcript delta: {e}")


def _on_transcript_done(self, event):
    """Handle transcript completion event"""
    try:
        transcript = event.get('transcript', '')

        self.logger.info(f"🔊 Speaking: '{transcript}'")

        # Update speaking status with complete transcript
        self.publish("speaking_status", {
            "speaking": True,
            "text": transcript,
            "partial": False,
            "timestamp": time.time()
        })

    except Exception as e:
        self.logger.error(f"Error handling transcript done: {e}")
```

#### Message Callbacks

```python
def on_text_response(self, message):
    """Handle text response messages (for backward compatibility)"""
    # Note: With Realtime API, audio is generated automatically
    # as part of the response. This callback is for compatibility
    # with nodes that publish text_response without Realtime API.
    pass


def on_system_mode_change(self, message):
    """Handle system mode changes"""
    try:
        mode = message.data.get("mode", "idle")

        # Stop playback if switching away from speaking mode
        if mode != "speaking" and self.is_speaking:
            self._stop_playback()

    except Exception as e:
        self.logger.error(f"Error handling mode change: {e}")
```

### Configuration (.messages file)

```yaml
# nodes/speech_synthesis22/.messages

node_name: "speech_synthesis22"
version: "1.0"
description: "Real-time speech synthesis using OpenAI Realtime API"

publishes:
  - topic: "speaking_status"
    message_type: "SpeakingStatus"
    description: "Speech playback status with transcript"
    frequency: "continuous"

  - topic: "audio_output_status"
    message_type: "AudioOutputStatus"
    description: "Audio output device status"
    frequency: "on_change"

subscribes:
  - topic: "text_response"
    callback: "on_text_response"
    description: "Text responses (backward compatibility)"

  - topic: "system_mode"
    callback: "on_system_mode_change"
    description: "System mode changes"

configuration:
  audio:
    sample_rate: 24000  # Required by Realtime API
    channels: 1
    format: "pcm16"
    buffer_size: 100  # Max audio chunks in buffer

  playback:
    start_threshold: 5  # Start playback after N chunks buffered
    underrun_recovery: true  # Recover from buffer underruns
```

### Dependencies

- `pyaudio` - Speaker output and audio playback
- `websockets` - WebSocket client (via RealtimeConnectionManager)
- `base64` - Audio data decoding

### Error Handling

1. **Buffer Overflow**: Drop oldest chunks, log warning
2. **Buffer Underrun**: Pause playback, wait for more chunks
3. **Playback Errors**: Logged, attempt recovery
4. **Connection Loss**: Handled by RealtimeConnectionManager

### Performance Considerations

- **Latency**: ~100-300ms from audio delta to speaker output
- **Bandwidth**: ~48 KB/s for 24kHz PCM16 audio streaming
- **CPU**: Low (<5% for audio decoding and playback)
- **Memory**: ~20MB for audio buffers and queues
- **Jitter Handling**: Buffer 5 chunks before starting playback

---

## 4. Realtime Connection Manager (Shared Component)

### Overview

A shared component that manages the WebSocket connection to the OpenAI Realtime API and dispatches events to registered handlers across all three nodes.

### Class Structure

```python
# realtime_api/connection_manager.py

import websockets
import json
import asyncio
import threading
from typing import Dict, Callable, List
import logging


class RealtimeConnectionManager:
    """
    Manages WebSocket connection to OpenAI Realtime API

    Shared across speech_recognition_node22, ai_node22, and speech_synthesis_node22.
    Handles connection, reconnection, event routing, and error recovery.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-realtime-preview-2024-10-01"):
        self.api_key = api_key
        self.model = model
        self.url = f"wss://api.openai.com/v1/realtime?model={model}"

        # WebSocket connection
        self.websocket = None
        self.connected = False
        self.connection_lock = threading.Lock()

        # Event loop and threads
        self.event_loop = None
        self.event_thread = None
        self.receive_thread = None
        self.shutdown_event = threading.Event()

        # Event handlers registry
        self.event_handlers = {}  # event_type -> list of handlers
        self.handler_lock = threading.Lock()

        # Reconnection settings
        self.reconnect_enabled = True
        self.reconnect_delay = 1.0
        self.max_reconnect_delay = 30.0
        self.reconnect_attempts = 0

        # Statistics
        self.events_sent = 0
        self.events_received = 0
        self.errors = 0

        # Logging
        self.logger = logging.getLogger("RealtimeConnectionManager")


    def start(self):
        """Start the connection manager and establish WebSocket connection"""
        self.logger.info("Starting Realtime Connection Manager...")

        # Create event loop in separate thread
        self.event_thread = threading.Thread(
            target=self._run_event_loop,
            name="realtime_event_loop",
            daemon=True
        )
        self.event_thread.start()

        # Wait for event loop to initialize
        while not self.event_loop:
            time.sleep(0.01)

        # Start connection
        asyncio.run_coroutine_threadsafe(self._connect(), self.event_loop)

        self.logger.info("Realtime Connection Manager started")


    def stop(self):
        """Stop the connection manager and close WebSocket"""
        self.logger.info("Stopping Realtime Connection Manager...")

        self.reconnect_enabled = False
        self.shutdown_event.set()

        # Close WebSocket
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.event_loop)

        # Stop event loop
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)

        # Wait for threads
        if self.event_thread and self.event_thread.is_alive():
            self.event_thread.join(timeout=5.0)

        self.logger.info("Realtime Connection Manager stopped")


    def _run_event_loop(self):
        """Run asyncio event loop in dedicated thread"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()


    async def _connect(self):
        """Establish WebSocket connection to Realtime API"""
        try:
            self.logger.info(f"Connecting to Realtime API: {self.url}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }

            self.websocket = await websockets.connect(
                self.url,
                extra_headers=headers,
                max_size=10 * 1024 * 1024  # 10MB max message size
            )

            self.connected = True
            self.reconnect_attempts = 0
            self.reconnect_delay = 1.0

            self.logger.info("✓ Connected to Realtime API")

            # Start receiving messages
            asyncio.create_task(self._receive_loop())

        except Exception as e:
            self.logger.error(f"Failed to connect to Realtime API: {e}")
            self.connected = False

            # Schedule reconnection
            if self.reconnect_enabled:
                await self._schedule_reconnect()


    async def _disconnect(self):
        """Close WebSocket connection"""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self.connected = False
            self.logger.info("Disconnected from Realtime API")

        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")


    async def _schedule_reconnect(self):
        """Schedule reconnection attempt with exponential backoff"""
        if not self.reconnect_enabled or self.shutdown_event.is_set():
            return

        self.reconnect_attempts += 1
        delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)),
                   self.max_reconnect_delay)

        self.logger.info(f"Reconnecting in {delay:.1f}s (attempt {self.reconnect_attempts})...")

        await asyncio.sleep(delay)
        await self._connect()


    async def _receive_loop(self):
        """Receive and dispatch events from WebSocket"""
        try:
            while self.connected and not self.shutdown_event.is_set():
                try:
                    # Receive message from WebSocket
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)

                    # Parse event
                    event = json.loads(message)
                    event_type = event.get('type')

                    self.events_received += 1
                    self.logger.debug(f"Received event: {event_type}")

                    # Dispatch to handlers
                    self._dispatch_event(event_type, event)

                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    self.connected = False

                    # Schedule reconnection
                    if self.reconnect_enabled:
                        await self._schedule_reconnect()
                    break

                except Exception as e:
                    self.logger.error(f"Error in receive loop: {e}")
                    self.errors += 1

        except Exception as e:
            self.logger.error(f"Fatal error in receive loop: {e}")
            self.connected = False


    def send_event(self, event: dict):
        """Send event to Realtime API (thread-safe)"""
        if not self.connected:
            self.logger.warning("Cannot send event - not connected")
            return False

        try:
            # Schedule send in event loop
            future = asyncio.run_coroutine_threadsafe(
                self._send_event_async(event),
                self.event_loop
            )

            # Wait for completion with timeout
            future.result(timeout=5.0)

            self.events_sent += 1
            return True

        except Exception as e:
            self.logger.error(f"Error sending event: {e}")
            self.errors += 1
            return False


    async def _send_event_async(self, event: dict):
        """Send event to WebSocket (async)"""
        try:
            message = json.dumps(event)
            await self.websocket.send(message)
            self.logger.debug(f"Sent event: {event.get('type')}")

        except Exception as e:
            self.logger.error(f"Error sending event: {e}")
            raise


    def register_event_handler(self, event_type: str, handler: Callable):
        """Register handler for specific event type"""
        with self.handler_lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []

            self.event_handlers[event_type].append(handler)
            self.logger.debug(f"Registered handler for event: {event_type}")


    def unregister_event_handler(self, event_type: str, handler: Callable = None):
        """Unregister handler(s) for specific event type"""
        with self.handler_lock:
            if event_type in self.event_handlers:
                if handler:
                    self.event_handlers[event_type].remove(handler)
                else:
                    del self.event_handlers[event_type]

                self.logger.debug(f"Unregistered handler for event: {event_type}")


    def _dispatch_event(self, event_type: str, event: dict):
        """Dispatch event to registered handlers"""
        with self.handler_lock:
            handlers = self.event_handlers.get(event_type, [])

            for handler in handlers:
                try:
                    # Call handler in separate thread to avoid blocking receive loop
                    threading.Thread(
                        target=handler,
                        args=(event,),
                        daemon=True
                    ).start()

                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_type}: {e}")


    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "connected": self.connected,
            "events_sent": self.events_sent,
            "events_received": self.events_received,
            "errors": self.errors,
            "reconnect_attempts": self.reconnect_attempts
        }
```

### Helper Components

#### AudioStreamer

```python
# realtime_api/audio_streamer.py

import base64
import logging


class AudioStreamer:
    """Helper for streaming audio to Realtime API"""

    def __init__(self, sample_rate: int = 24000, chunk_size: int = 4800, logger=None):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.logger = logger or logging.getLogger("AudioStreamer")


    def stream_audio(self, audio_bytes: bytes, connection_manager):
        """Stream audio chunk to Realtime API"""
        try:
            # Encode audio as base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Send input_audio_buffer.append event
            connection_manager.send_event({
                "type": "input_audio_buffer.append",
                "audio": audio_b64
            })

        except Exception as e:
            self.logger.error(f"Error streaming audio: {e}")
```

#### AudioPlayer

```python
# realtime_api/audio_player.py

import logging


class AudioPlayer:
    """Helper for playing audio from Realtime API"""

    def __init__(self, sample_rate: int = 24000, logger=None):
        self.sample_rate = sample_rate
        self.logger = logger or logging.getLogger("AudioPlayer")


    def play_chunk(self, audio_bytes: bytes, audio_stream):
        """Play audio chunk to output stream"""
        try:
            if audio_stream:
                audio_stream.write(audio_bytes)

        except Exception as e:
            self.logger.error(f"Error playing audio chunk: {e}")
```

---

## Integration Strategy

### Phase 1: Shared Infrastructure

1. Implement `RealtimeConnectionManager` in `realtime_api/connection_manager.py`
2. Implement helper components (`AudioStreamer`, `AudioPlayer`)
3. Add environment variable for Realtime API model selection: `NEVIL_REALTIME_MODEL`
4. Update launcher to create and inject connection manager into nodes

### Phase 2: Node Implementation

1. Implement `speech_recognition_node22` with audio streaming
2. Implement `ai_node22` with function calling
3. Implement `speech_synthesis_node22` with audio playback
4. Create `.messages` configuration files for all three nodes

### Phase 3: Testing and Validation

1. Unit tests for each node
2. Integration tests for full voice input → response cycle
3. Stress tests for connection reliability and reconnection
4. Performance benchmarking (latency, bandwidth, CPU, memory)

### Phase 4: Documentation and Deployment

1. Update main README with Realtime API setup instructions
2. Create migration guide from discrete nodes to Realtime nodes
3. Add configuration examples and troubleshooting guide
4. Deploy to production and monitor performance

---

## Migration Path

### Backward Compatibility

The new Realtime API nodes are designed to be **drop-in replacements** for the existing nodes:

| Old Node | New Node | Compatibility |
|----------|----------|---------------|
| `speech_recognition_node` | `speech_recognition_node22` | ✓ Publishes same `voice_command` messages |
| `ai_cognition_node` | `ai_node22` | ✓ Publishes same `text_response`, `robot_action` messages |
| `speech_synthesis_node` | `speech_synthesis_node22` | ✓ Publishes same `speaking_status` messages |

### Configuration Changes

**Environment Variables**:
```bash
# Enable Realtime API nodes
export NEVIL_REALTIME_MODEL="gpt-4o-realtime-preview-2024-10-01"

# OpenAI API key (required)
export OPENAI_API_KEY="sk-..."
```

**Launcher Configuration** (`nevil_launch.yaml`):
```yaml
nodes:
  # Realtime API nodes (new)
  - speech_recognition22
  - ai_cognition22
  - speech_synthesis22

  # OR traditional nodes (old)
  # - speech_recognition
  # - ai_cognition
  # - speech_synthesis
```

### Testing Procedure

1. **Side-by-side Testing**: Run both old and new nodes simultaneously (different topics)
2. **A/B Testing**: Switch between old and new nodes, compare latency and accuracy
3. **Load Testing**: Stress test with rapid voice commands
4. **Reliability Testing**: Test reconnection, error recovery, network interruptions

---

## Performance Benchmarks

### Expected Latencies

| Metric | Discrete Nodes | Realtime Nodes | Improvement |
|--------|---------------|----------------|-------------|
| Voice input → Transcription | 2-5s | 200-500ms | **4-10x faster** |
| Transcription → AI Response | 1-3s | 500-1500ms | **2-3x faster** |
| AI Response → Audio Output | 2-5s | 100-300ms | **10-20x faster** |
| **Total Latency** | **5-13s** | **800-2300ms** | **6-10x faster** |

### Resource Usage

| Resource | Discrete Nodes | Realtime Nodes | Change |
|----------|---------------|----------------|--------|
| CPU (avg) | 15-25% | 10-15% | **-33% to -50%** |
| Memory | 150MB | 200MB | **+33%** |
| Bandwidth | ~10 KB/s | ~100 KB/s | **+10x** |
| Disk I/O | High (temp audio files) | Minimal (streaming) | **-90%** |

---

## Error Handling and Recovery

### Connection Errors

1. **Initial Connection Failure**:
   - Log error with details
   - Retry with exponential backoff (1s, 2s, 4s, ..., max 30s)
   - Publish `system_mode: error` to message bus
   - Fall back to discrete nodes if available

2. **Mid-Session Disconnect**:
   - Detect connection loss via WebSocket close event
   - Attempt automatic reconnection
   - Buffer audio/events during reconnection
   - Resume session after reconnection

3. **Timeout Errors**:
   - Implement 30s timeout for WebSocket sends
   - Log timeout and attempt retry
   - If persistent, trigger reconnection

### API Errors

1. **Rate Limiting (429)**:
   - Respect `Retry-After` header
   - Implement exponential backoff
   - Queue pending requests

2. **Invalid Request (400)**:
   - Log error with request details
   - Skip invalid request
   - Continue processing

3. **Server Errors (500)**:
   - Log error
   - Retry request up to 3 times
   - If persistent, trigger reconnection

### Resource Errors

1. **Audio Buffer Overflow**:
   - Drop oldest chunks
   - Log warning
   - Continue streaming

2. **Audio Buffer Underrun**:
   - Pause playback
   - Wait for minimum buffer threshold
   - Resume playback

3. **PyAudio Errors**:
   - Log error with device details
   - Attempt device reinitialization
   - Fall back to alternative device if available

---

## Security Considerations

1. **API Key Protection**:
   - Store in environment variable only
   - Never log or expose API key
   - Use `.env` file for local development (excluded from git)

2. **WebSocket Security**:
   - Use WSS (WebSocket Secure) only
   - Validate server certificate
   - Implement connection timeout limits

3. **Audio Privacy**:
   - Audio is streamed to OpenAI servers
   - No local audio storage by default
   - Comply with privacy regulations

4. **Function Calling Security**:
   - Validate function arguments
   - Implement whitelist of allowed functions
   - Rate limit function executions

---

## Future Enhancements

1. **Multi-language Support**: Add language detection and switching
2. **Voice Cloning**: Use custom voice models for Nevil's personality
3. **Emotion Detection**: Analyze audio for emotional cues
4. **Conversation Summarization**: Periodic conversation summaries
5. **Local Fallback**: Use local Whisper/TTS when Realtime API unavailable
6. **Advanced Function Calling**: Complex multi-step robot actions
7. **Vision Integration**: Send camera frames for real-time vision analysis
8. **Performance Tuning**: Optimize buffer sizes, chunk sizes for lowest latency

---

## Conclusion

These technical specifications provide a comprehensive blueprint for implementing three new Nevil v3.0 nodes that integrate the OpenAI Realtime API. The design:

- **Maintains Compatibility**: Drop-in replacement for existing nodes
- **Reduces Latency**: 6-10x faster response times
- **Improves Efficiency**: Lower CPU usage, no disk I/O for temp files
- **Enhances Robustness**: Automatic reconnection, error recovery
- **Enables New Features**: Real-time function calling, streaming responses

The shared `RealtimeConnectionManager` ensures efficient resource usage while the event-driven architecture integrates seamlessly with Nevil's existing message bus and threading model.

Implementation can proceed in phases, with thorough testing at each stage to ensure reliability and performance meet production requirements.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Status**: Ready for Implementation
