# Nevil 2.2 Migration and Testing Strategy
## Full Realtime API Integration with OpenAI

**Document Version:** 1.0
**Target Release:** Nevil v2.2
**Date:** 2025-11-11
**Status:** COMPREHENSIVE STRATEGY

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Migration Strategy](#migration-strategy)
4. [Testing Strategy](#testing-strategy)
5. [Quality Assurance](#quality-assurance)
6. [Risk Assessment & Mitigation](#risk-assessment--mitigation)
7. [Implementation Timeline](#implementation-timeline)
8. [Appendices](#appendices)

---

## Executive Summary

### Migration Scope

Nevil 2.2 represents a major architectural evolution from the current Blane3/v3.0 implementation to a fully integrated OpenAI Realtime API system. This migration replaces the existing modular audio pipeline (speech recognition → AI cognition → speech synthesis) with a unified bidirectional audio stream that provides:

- **Native speech-to-speech processing** with sub-300ms latency
- **Bidirectional audio streaming** for natural conversation flow
- **Function calling integration** for robot actions and camera control
- **Multimodal support** for vision-enabled interactions
- **Emotion and prosody detection** from voice input
- **Interruption handling** for more natural dialogue

### Key Benefits

1. **Dramatic Latency Reduction**: From 5-8 seconds (current) to <500ms total
2. **Natural Conversations**: Interruption support and overlapping speech
3. **Unified Architecture**: Single WebSocket connection replaces 3-node pipeline
4. **Enhanced Intelligence**: Function calling for seamless robot control
5. **Cost Efficiency**: Reduced API calls through streaming architecture
6. **Improved UX**: More human-like, responsive interactions

### Migration Approach

**Phased Migration with Parallel Operation**
- Phase 1: Create new Realtime API node alongside existing nodes
- Phase 2: Implement hybrid mode with feature flagging
- Phase 3: Full cutover with fallback capability
- Phase 4: Deprecate legacy nodes

---

## Current State Analysis

### Existing Architecture (Nevil v3.0 / Blane3)

#### Node Structure
```
┌─────────────────────┐
│ Speech Recognition  │ (speech_recognition_node.py)
│ - OpenAI Whisper    │
│ - USB Microphone    │
│ - energy_threshold  │
└──────────┬──────────┘
           │ publishes: voice_command
           ▼
┌─────────────────────┐
│   AI Cognition      │ (ai_cognition_node.py)
│ - OpenAI GPT-4o     │
│ - Chat Completions  │
│ - Context mgmt      │
└──────────┬──────────┘
           │ publishes: text_response, robot_action
           ▼
┌─────────────────────┐
│ Speech Synthesis    │ (speech_synthesis_node.py)
│ - OpenAI TTS        │
│ - HiFiBerry DAC     │
│ - robot_hat.Music   │
└─────────────────────┘
```

#### Current Dependencies
```yaml
Core Framework:
  - nevil_framework.base_node
  - nevil_framework.message_bus
  - nevil_framework.chat_logger

Audio Stack:
  - speech_recognition (SpeechRecognition library)
  - pyaudio (microphone access)
  - robot_hat.Music (speaker output)
  - pygame.mixer (audio playback)

AI Providers:
  - openai (GPT-4o chat completions)
  - openai (Whisper STT)
  - openai (TTS-1)

Hardware:
  - USB PnP Sound Device (device index 1)
  - HiFiBerry DAC (ALSA card 3)
  - GPIO pin 20 (speaker enable)
```

#### Current Performance Metrics
- **Speech Recognition Latency**: 1.5-2.5s (audio capture + Whisper API)
- **AI Processing Latency**: 2-4s (GPT-4o completion)
- **Speech Synthesis Latency**: 1.5-2s (TTS API + playback start)
- **Total Round-Trip**: 5-8 seconds user speech → robot response
- **Message Bus Overhead**: ~50-100ms per hop
- **Error Recovery**: Per-node restart (5-10s downtime)

#### Code Inventory
```
nodes/speech_recognition/
  - speech_recognition_node.py (28,322 bytes)
  - direct_commands.py (4,989 bytes)
  - .messages (4,878 bytes)

nodes/ai_cognition/
  - ai_cognition_node.py (24,510 bytes)
  - base_agent.py (8,077 bytes)
  - completion/ (factory pattern for providers)
  - .messages (17,820 bytes)

nodes/speech_synthesis/
  - speech_synthesis_node.py (22,773 bytes)
  - .messages (5,243 bytes)
  - i2samp.sh (HiFiBerry setup)

Total Code: ~92KB across 3 nodes
Configuration: ~28KB in .messages files
```

### Identified Migration Challenges

1. **Hardware Abstraction**: Current code tightly coupled to v1.0 audio hardware
2. **State Management**: Conversation history split across nodes
3. **Action Parsing**: Complex JSON parsing in AI cognition node
4. **Audio Quality**: Proven parameters (energy_threshold=300) must preserve
5. **Backward Compatibility**: v1.0 components must continue working
6. **Message Bus Integration**: Existing nodes expect pub/sub pattern

---

## Migration Strategy

### Phase 1: Foundation & New Node Development (Weeks 1-2)

#### 1.1 Create Realtime API Node

**File Structure**:
```
nodes/realtime_cognition/
├── __init__.py
├── realtime_cognition_node.py      # Main node implementation
├── realtime_client.py               # WebSocket client wrapper
├── audio_stream_manager.py          # Audio I/O abstraction
├── function_handler.py              # Robot action function calling
├── session_manager.py               # Connection lifecycle
├── .messages                        # Message configuration
└── config/
    ├── realtime_config.yaml         # API configuration
    ├── function_definitions.json    # OpenAI function schemas
    └── audio_config.yaml            # Hardware settings
```

**Key Components**:

```python
# realtime_cognition_node.py (skeleton)

from nevil_framework.base_node import NevilNode
from .realtime_client import RealtimeClient
from .audio_stream_manager import AudioStreamManager
from .function_handler import FunctionHandler

class RealtimeCognitionNode(NevilNode):
    """
    Unified speech-to-speech node using OpenAI Realtime API.
    Replaces speech_recognition + ai_cognition + speech_synthesis.
    """

    def __init__(self):
        super().__init__("realtime_cognition")

        # Core components
        self.realtime_client = None
        self.audio_manager = None
        self.function_handler = None

        # Configuration
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = 'gpt-4o-realtime-preview-2024-12-17'
        self.voice = 'alloy'  # or 'echo', 'shimmer'

        # State
        self.session_active = False
        self.conversation_id = None

    def initialize(self):
        """Initialize Realtime API components"""
        # Hardware setup (preserve v1.0 configuration)
        self.audio_manager = AudioStreamManager(
            input_device=1,      # USB microphone
            output_device=3,     # HiFiBerry DAC
            sample_rate=24000,   # Realtime API requirement
            channels=1           # Mono for Realtime API
        )

        # WebSocket client
        self.realtime_client = RealtimeClient(
            api_key=self.api_key,
            on_audio=self._on_audio_response,
            on_function_call=self._on_function_call,
            on_error=self._on_error
        )

        # Function calling
        self.function_handler = FunctionHandler(
            message_bus=self.message_bus,
            logger=self.logger
        )

        # Connect and configure session
        self._establish_session()

    def _establish_session(self):
        """Connect to Realtime API and configure session"""
        self.realtime_client.connect()

        # Configure session with system instructions
        self.realtime_client.send_config({
            "model": self.model,
            "voice": self.voice,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {"model": "whisper-1"},
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "instructions": self._load_system_prompt(),
            "tools": self._load_function_definitions(),
            "tool_choice": "auto"
        })

        self.session_active = True

    def main_loop(self):
        """Main processing loop - bidirectional audio streaming"""
        if not self.session_active:
            time.sleep(0.1)
            return

        # Read from microphone
        audio_chunk = self.audio_manager.read_input(chunk_size=4800)

        if audio_chunk:
            # Send to Realtime API
            self.realtime_client.send_audio(audio_chunk)

        # Process incoming events (non-blocking)
        self.realtime_client.process_events()

    def _on_audio_response(self, audio_data, transcript=None):
        """Handle audio response from Realtime API"""
        # Play through speakers
        self.audio_manager.write_output(audio_data)

        # Publish transcript if available
        if transcript:
            self.publish("text_response", {
                "text": transcript,
                "source": "realtime_api",
                "timestamp": time.time()
            })

    def _on_function_call(self, function_name, arguments):
        """Handle function calls from Realtime API"""
        result = self.function_handler.execute(function_name, arguments)

        # Send result back to Realtime API
        self.realtime_client.send_function_result(
            call_id=arguments.get('call_id'),
            result=result
        )
```

#### 1.2 Dependency Updates

**New Dependencies** (`requirements.txt`):
```txt
# Existing dependencies
PyYAML>=6.0
python-dateutil>=2.8.0
openai>=1.40.0  # Updated for Realtime API

# New for Realtime API
websockets>=12.0  # WebSocket client
sounddevice>=0.4.6  # Modern audio I/O
numpy>=1.24.0  # Audio processing

# Existing audio (kept for backward compatibility)
SpeechRecognition>=3.10.0
pygame>=2.5.0
pyaudio>=0.2.11
```

**Installation Strategy**:
```bash
# Create backup of current environment
pip freeze > requirements_backup_v3.0.txt

# Install new dependencies without breaking existing
pip install websockets>=12.0 sounddevice>=0.4.6 numpy>=1.24.0

# Verify openai library supports Realtime API
python -c "import openai; print(openai.__version__)"
# Expected: 1.40.0 or higher
```

#### 1.3 Configuration Migration

**New Configuration File**: `nodes/realtime_cognition/.messages`

```yaml
node_name: "realtime_cognition"
version: "2.2.0"
description: "Unified speech-to-speech cognition using OpenAI Realtime API"

# Topics this node publishes
publishes:
  - topic: "text_response"
    message_type: "TextResponse"
    description: "Transcribed AI responses from Realtime API"

  - topic: "robot_action"
    message_type: "RobotAction"
    description: "Movement commands from function calling"

  - topic: "mood_change"
    message_type: "MoodChange"
    description: "AI mood changes"

  - topic: "realtime_status"
    message_type: "RealtimeStatus"
    description: "Connection and session status"
    schema:
      connected: {type: boolean}
      session_id: {type: string}
      latency_ms: {type: integer}
      error: {type: string, required: false}

# Topics this node subscribes to
subscribes:
  - topic: "visual_data"
    message_type: "VisualData"
    callback: "on_visual_data"
    description: "Camera images for multimodal processing"

  - topic: "system_command"
    message_type: "SystemCommand"
    callback: "on_system_command"
    description: "System control commands (pause, resume, reset)"

# Configuration
configuration:
  realtime_api:
    model: "gpt-4o-realtime-preview-2024-12-17"
    voice: "alloy"  # alloy, echo, shimmer, cedar, marin
    input_audio_format: "pcm16"
    output_audio_format: "pcm16"
    sample_rate: 24000

  audio_hardware:
    # Preserve v1.0 working configuration
    input_device: 1          # USB PnP Sound Device
    output_device: 3         # HiFiBerry DAC
    chunk_size: 4800         # 200ms at 24kHz
    buffer_size: 2           # Double buffering

  turn_detection:
    type: "server_vad"       # Server-side voice activity detection
    threshold: 0.5
    prefix_padding_ms: 300
    silence_duration_ms: 500

  function_calling:
    enabled: true
    auto_execute: true       # Auto-execute robot actions
    confirmation_required: ["navigate", "shutdown"]

  session_management:
    auto_reconnect: true
    reconnect_delay_ms: 1000
    max_reconnect_attempts: 5
    heartbeat_interval_ms: 30000
```

#### 1.4 Backward Compatibility Layer

**Hybrid Mode Configuration**: `.nodes` file update

```yaml
nodes:
  # Legacy nodes (can be disabled via feature flag)
  speech_recognition:
    status: ${USE_LEGACY_AUDIO:-disabled}  # Default: disabled
    priority: high

  ai_cognition:
    status: ${USE_LEGACY_AUDIO:-disabled}
    priority: medium

  speech_synthesis:
    status: ${USE_LEGACY_AUDIO:-disabled}
    priority: high

  # NEW: Realtime API node
  realtime_cognition:
    status: ${USE_REALTIME_API:-live}  # Default: live
    priority: critical
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      REALTIME_API_MODEL: ${REALTIME_API_MODEL:-gpt-4o-realtime-preview}

  # Unchanged nodes
  navigation:
    status: live
    priority: high

  visual:
    status: live
    priority: medium

  led_indicator:
    status: live
    priority: low
```

**Environment-Based Switching**:
```bash
# Use new Realtime API (default)
./nevil start

# Fallback to legacy audio pipeline
USE_LEGACY_AUDIO=live USE_REALTIME_API=disabled ./nevil start

# Hybrid mode (both systems for A/B testing)
USE_LEGACY_AUDIO=live USE_REALTIME_API=live REALTIME_TEST_MODE=true ./nevil start
```

---

### Phase 2: Audio Pipeline Integration (Week 3)

#### 2.1 Audio Stream Manager

**Unified audio I/O preserving v1.0 hardware configuration**:

```python
# audio_stream_manager.py

import sounddevice as sd
import numpy as np
import queue
import threading

class AudioStreamManager:
    """
    Manages bidirectional audio streaming for Realtime API.
    Preserves v1.0 hardware configuration while providing
    modern audio I/O capabilities.
    """

    def __init__(self, input_device=1, output_device=3,
                 sample_rate=24000, channels=1):
        # Hardware configuration (v1.0 compatible)
        self.input_device = input_device
        self.output_device = output_device
        self.sample_rate = sample_rate
        self.channels = channels

        # Streaming state
        self.input_stream = None
        self.output_stream = None
        self.input_queue = queue.Queue(maxsize=100)
        self.output_queue = queue.Queue(maxsize=100)

        # Initialize hardware (preserve v1.0 setup)
        self._init_gpio()
        self._verify_devices()

    def _init_gpio(self):
        """Initialize GPIO for speaker (v1.0 approach)"""
        try:
            import os
            os.system("pinctrl set 20 op dh")  # Enable robot_hat speaker
        except Exception as e:
            logging.warning(f"GPIO initialization failed: {e}")

    def _verify_devices(self):
        """Verify audio devices match v1.0 configuration"""
        devices = sd.query_devices()

        # Check input device
        input_dev = devices[self.input_device]
        if 'USB' not in input_dev['name']:
            logging.warning(f"Input device {self.input_device} may not be USB microphone")

        # Check output device
        output_dev = devices[self.output_device]
        if 'hifiberry' not in output_dev['name'].lower():
            logging.warning(f"Output device {self.output_device} may not be HiFiBerry DAC")

    def start_streams(self):
        """Start bidirectional audio streaming"""
        # Input stream (microphone → queue)
        self.input_stream = sd.InputStream(
            device=self.input_device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.int16,
            blocksize=4800,  # 200ms chunks
            callback=self._input_callback
        )

        # Output stream (queue → speakers)
        self.output_stream = sd.OutputStream(
            device=self.output_device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.int16,
            blocksize=4800,
            callback=self._output_callback
        )

        self.input_stream.start()
        self.output_stream.start()

    def _input_callback(self, indata, frames, time_info, status):
        """Stream callback for microphone input"""
        if status:
            logging.warning(f"Input stream status: {status}")
        self.input_queue.put(indata.copy())

    def _output_callback(self, outdata, frames, time_info, status):
        """Stream callback for speaker output"""
        if status:
            logging.warning(f"Output stream status: {status}")

        try:
            data = self.output_queue.get_nowait()
            outdata[:] = data
        except queue.Empty:
            outdata.fill(0)  # Silence if no data

    def read_input(self, chunk_size=4800):
        """Read audio chunk from microphone"""
        try:
            audio_data = self.input_queue.get(timeout=0.01)
            return audio_data.tobytes()
        except queue.Empty:
            return None

    def write_output(self, audio_data):
        """Write audio chunk to speakers"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        self.output_queue.put(audio_array)

    def stop_streams(self):
        """Stop audio streaming"""
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()

        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
```

#### 2.2 Realtime Client WebSocket Wrapper

```python
# realtime_client.py

import websockets
import json
import asyncio
import threading
import base64
from typing import Callable

class RealtimeClient:
    """
    WebSocket client for OpenAI Realtime API.
    Handles bidirectional communication and event processing.
    """

    def __init__(self, api_key: str,
                 on_audio: Callable = None,
                 on_transcript: Callable = None,
                 on_function_call: Callable = None,
                 on_error: Callable = None):
        self.api_key = api_key
        self.websocket = None
        self.connected = False

        # Event callbacks
        self.on_audio = on_audio
        self.on_transcript = on_transcript
        self.on_function_call = on_function_call
        self.on_error = on_error

        # State
        self.session_id = None
        self.conversation_id = None

        # Event loop
        self.loop = None
        self.loop_thread = None

    def connect(self):
        """Establish WebSocket connection to Realtime API"""
        # Start event loop in separate thread
        self.loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.loop_thread.start()

        # Wait for connection
        while not self.connected:
            time.sleep(0.1)

    def _run_event_loop(self):
        """Run asyncio event loop in separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._connect_websocket())
        except Exception as e:
            if self.on_error:
                self.on_error(f"WebSocket error: {e}")

    async def _connect_websocket(self):
        """Async WebSocket connection"""
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }

        async with websockets.connect(url, extra_headers=headers) as ws:
            self.websocket = ws
            self.connected = True

            # Message processing loop
            async for message in ws:
                await self._process_message(message)

    async def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            event = json.loads(message)
            event_type = event.get('type')

            if event_type == 'session.created':
                self.session_id = event['session']['id']

            elif event_type == 'response.audio.delta':
                # Audio chunk from API
                audio_b64 = event['delta']
                audio_bytes = base64.b64decode(audio_b64)
                if self.on_audio:
                    self.on_audio(audio_bytes)

            elif event_type == 'response.audio_transcript.delta':
                # Transcript chunk
                transcript = event['delta']
                if self.on_transcript:
                    self.on_transcript(transcript)

            elif event_type == 'response.function_call_arguments.done':
                # Function call from API
                func_name = event['name']
                arguments = json.loads(event['arguments'])
                if self.on_function_call:
                    self.on_function_call(func_name, arguments)

            elif event_type == 'error':
                error_msg = event.get('error', {}).get('message', 'Unknown error')
                if self.on_error:
                    self.on_error(error_msg)

        except Exception as e:
            if self.on_error:
                self.on_error(f"Message processing error: {e}")

    def send_audio(self, audio_data: bytes):
        """Send audio chunk to Realtime API"""
        if not self.connected:
            return

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')

        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }

        # Send asynchronously
        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(event)),
            self.loop
        )

    def send_config(self, config: dict):
        """Configure session parameters"""
        event = {
            "type": "session.update",
            "session": config
        }

        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(event)),
            self.loop
        )

    def send_function_result(self, call_id: str, result: dict):
        """Send function execution result back to API"""
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result)
            }
        }

        asyncio.run_coroutine_threadsafe(
            self.websocket.send(json.dumps(event)),
            self.loop
        )

    def disconnect(self):
        """Close WebSocket connection"""
        if self.loop:
            self.loop.stop()
        self.connected = False
```

#### 2.3 Function Calling Handler

**Map Realtime API function calls to existing message bus topics**:

```python
# function_handler.py

import json
import time
from typing import Dict, Any

class FunctionHandler:
    """
    Handles OpenAI function calls from Realtime API.
    Translates function calls to Nevil message bus publications.
    """

    def __init__(self, message_bus, logger):
        self.message_bus = message_bus
        self.logger = logger

        # Function registry
        self.functions = {
            'execute_robot_actions': self._execute_robot_actions,
            'change_mood': self._change_mood,
            'take_snapshot': self._take_snapshot,
            'play_sound': self._play_sound,
            'navigate': self._navigate
        }

    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function call and return result"""
        self.logger.info(f"Function call: {function_name}({arguments})")

        if function_name not in self.functions:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }

        try:
            result = self.functions[function_name](arguments)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Function execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_robot_actions(self, args: Dict) -> Dict:
        """Execute robot movement/gesture actions"""
        actions = args.get('actions', [])

        # Publish to navigation node
        self.message_bus.publish({
            "topic": "robot_action",
            "data": {
                "actions": actions,
                "source_text": args.get('context', ''),
                "mood": args.get('mood', 'neutral'),
                "timestamp": time.time()
            }
        })

        return {"executed_actions": len(actions)}

    def _change_mood(self, args: Dict) -> Dict:
        """Change AI mood state"""
        mood = args.get('mood', 'neutral')

        self.message_bus.publish({
            "topic": "mood_change",
            "data": {
                "mood": mood,
                "source": "realtime_api",
                "timestamp": time.time()
            }
        })

        return {"new_mood": mood}

    def _take_snapshot(self, args: Dict) -> Dict:
        """Request camera snapshot"""
        self.message_bus.publish({
            "topic": "snap_pic",
            "data": {
                "requested_by": "realtime_cognition",
                "timestamp": time.time()
            }
        })

        return {"snapshot_requested": True}

    def _play_sound(self, args: Dict) -> Dict:
        """Play sound effect"""
        sound_name = args.get('sound', '')

        self.message_bus.publish({
            "topic": "robot_action",
            "data": {
                "actions": [f"play_sound {sound_name}"],
                "source_text": "sound_effect",
                "timestamp": time.time()
            }
        })

        return {"sound_played": sound_name}

    def _navigate(self, args: Dict) -> Dict:
        """Execute navigation command"""
        direction = args.get('direction', 'forward')
        distance = args.get('distance', 10)
        speed = args.get('speed', 30)

        action = f"{direction} {distance} {speed}"

        self.message_bus.publish({
            "topic": "robot_action",
            "data": {
                "actions": [action],
                "source_text": "navigation_command",
                "timestamp": time.time()
            }
        })

        return {
            "direction": direction,
            "distance": distance,
            "speed": speed
        }
```

**Function Definitions for Realtime API**:

```json
// function_definitions.json

[
  {
    "name": "execute_robot_actions",
    "description": "Execute robot movement, gestures, or expressions. Can string together multiple actions for elaborate performances.",
    "parameters": {
      "type": "object",
      "properties": {
        "actions": {
          "type": "array",
          "items": {"type": "string"},
          "description": "List of action commands (e.g., ['forward 30', 'nod', 'wave_hands', 'happy_spin:fast'])"
        },
        "mood": {
          "type": "string",
          "enum": ["playful", "brooding", "curious", "melancholic", "zippy", "lonely", "mischievous", "sleepy", "neutral"],
          "description": "Mood affecting action execution"
        },
        "context": {
          "type": "string",
          "description": "Context or reason for actions"
        }
      },
      "required": ["actions"]
    }
  },
  {
    "name": "change_mood",
    "description": "Change the AI's current mood state, affecting behavior and responses",
    "parameters": {
      "type": "object",
      "properties": {
        "mood": {
          "type": "string",
          "enum": ["playful", "brooding", "curious", "melancholic", "zippy", "lonely", "mischievous", "sleepy", "neutral"]
        },
        "reason": {
          "type": "string",
          "description": "Why the mood changed"
        }
      },
      "required": ["mood"]
    }
  },
  {
    "name": "take_snapshot",
    "description": "Capture an image with the robot's camera for visual inspection",
    "parameters": {
      "type": "object",
      "properties": {
        "purpose": {
          "type": "string",
          "description": "Why taking the snapshot (e.g., 'inspect object', 'look around')"
        }
      }
    }
  },
  {
    "name": "play_sound",
    "description": "Play a sound effect (vehicle sounds, musical effects, spooky sounds, alien sounds)",
    "parameters": {
      "type": "object",
      "properties": {
        "sound": {
          "type": "string",
          "enum": ["rev_engine", "airhorn", "machinegun", "shock", "dubstep", "dubstep_bass", "reggae", "agent_theme", "ghost_laugh", "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit", "inception_horn", "alien_voice", "alien_pitch", "alien_horn", "preacher"]
        }
      },
      "required": ["sound"]
    }
  },
  {
    "name": "navigate",
    "description": "Execute precise navigation command with direction, distance, and speed",
    "parameters": {
      "type": "object",
      "properties": {
        "direction": {
          "type": "string",
          "enum": ["forward", "backward", "left", "right"]
        },
        "distance": {
          "type": "number",
          "description": "Distance in cm (for forward/backward)"
        },
        "speed": {
          "type": "number",
          "minimum": 0,
          "maximum": 50,
          "description": "Speed level (0-50)"
        }
      },
      "required": ["direction"]
    }
  }
]
```

---

### Phase 3: Code Adaptation & Refactoring (Week 4)

#### 3.1 Preserve v1.0 Audio Quality

**Energy Threshold Mapping**:
```python
# The v1.0 proven energy_threshold=300 needs to map to
# Realtime API's turn_detection threshold

# v1.0 configuration
recognizer.energy_threshold = 300  # Proven working value

# Realtime API equivalent (approximate)
# Realtime uses 0-1 scale, need empirical testing
turn_detection_threshold = 0.5  # Starting point for testing

# Adaptive configuration based on environment
def calculate_threshold(v1_energy_threshold):
    """Map v1.0 energy threshold to Realtime API threshold"""
    # Empirical formula (to be calibrated during testing)
    # v1.0 range: 0-4000, Realtime range: 0-1
    normalized = v1_energy_threshold / 4000.0
    return max(0.1, min(0.9, normalized))

# Testing matrix
test_thresholds = [
    (300, 0.3),   # v1.0 proven → estimated Realtime
    (300, 0.4),
    (300, 0.5),
    (300, 0.6)
]
```

#### 3.2 Conversation History Migration

**Current AI Cognition History**:
```python
# ai_cognition_node.py (current)
self.conversation_history = []
self.max_history_length = 10

def _generate_response(self, user_text):
    self.conversation_history.append({
        "role": "user",
        "content": user_text
    })

    # Truncate history
    if len(self.conversation_history) > self.max_history_length:
        self.conversation_history = self.conversation_history[-self.max_history_length:]
```

**Realtime API Approach**:
```python
# Realtime API manages history server-side
# No client-side history management needed!
# Conversation context maintained in session state

# However, for logging/analytics, mirror history locally
class ConversationMirror:
    """Mirror Realtime API conversation for logging"""

    def __init__(self, max_length=50):
        self.history = []
        self.max_length = max_length

    def add_user_turn(self, transcript, audio_duration):
        self.history.append({
            "role": "user",
            "content": transcript,
            "duration_ms": audio_duration,
            "timestamp": time.time()
        })
        self._truncate()

    def add_assistant_turn(self, transcript, audio_duration, functions_called=[]):
        self.history.append({
            "role": "assistant",
            "content": transcript,
            "duration_ms": audio_duration,
            "functions": functions_called,
            "timestamp": time.time()
        })
        self._truncate()

    def _truncate(self):
        if len(self.history) > self.max_length:
            self.history = self.history[-self.max_length:]

    def export_for_logging(self):
        """Export for chat logger integration"""
        return {
            "total_turns": len(self.history),
            "history": self.history,
            "session_duration": self._calculate_session_duration()
        }
```

#### 3.3 System Prompt Preservation

**Current System Prompt** (from `.messages`):
- Location: `nodes/ai_cognition/.messages` → `configuration.ai.system_prompt`
- Size: ~3,200 characters (detailed personality definition)

**Migration to Realtime API**:
```python
def _load_system_prompt(self):
    """Load system instructions from configuration"""
    # Read from same location as current implementation
    system_prompt = self.ai_config.get('system_prompt')

    # Realtime API format (slightly different from chat completions)
    realtime_instructions = {
        "instructions": system_prompt,
        "modalities": ["text", "audio"],
        "temperature": 0.7,
        "max_response_output_tokens": "inf"  # Allow full responses
    }

    return realtime_instructions
```

**No Changes Needed**: System prompt content remains identical, only formatting changes for API compatibility.

---

### Phase 4: Rollout & Deployment (Week 5-6)

#### 4.1 Rollout Phases

**Week 5: Staged Rollout**

```
Day 1-2: Internal Testing
├── Developer environment testing
├── Unit test validation
└── Integration test suite

Day 3-4: Alpha Deployment
├── Feature flag: REALTIME_ALPHA=true
├── Single test device
├── Monitoring dashboard active
└── Daily performance reviews

Day 5-7: Beta Deployment
├── Feature flag: REALTIME_BETA=true
├── 3-5 test devices
├── A/B testing framework active
└── User feedback collection
```

**Week 6: Production Rollout**

```
Day 1-2: Canary Deployment (10%)
├── 10% of traffic to Realtime API
├── Automated rollback if error rate > 5%
├── Latency monitoring
└── Cost tracking

Day 3-4: Incremental Rollout (50%)
├── 50% traffic split
├── Performance comparison
├── Function calling accuracy
└── Audio quality assessment

Day 5-7: Full Rollout (100%)
├── 100% Realtime API
├── Legacy nodes on standby
├── Deprecation timeline announced
└── Success metrics review
```

#### 4.2 Rollback Procedures

**Automated Rollback Triggers**:
```python
# deployment/rollback_monitor.py

class RollbackMonitor:
    """Monitor Realtime API health and auto-rollback if needed"""

    def __init__(self):
        self.error_threshold = 0.05  # 5% error rate
        self.latency_threshold = 2000  # 2 seconds
        self.consecutive_failures = 0
        self.max_failures = 3

    def check_health(self):
        """Check system health metrics"""
        metrics = self._collect_metrics()

        # Error rate check
        if metrics['error_rate'] > self.error_threshold:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        # Latency check
        if metrics['avg_latency_ms'] > self.latency_threshold:
            self.consecutive_failures += 1

        # Rollback trigger
        if self.consecutive_failures >= self.max_failures:
            self._trigger_rollback("Health check failed")

    def _trigger_rollback(self, reason):
        """Switch back to legacy audio pipeline"""
        logging.critical(f"ROLLBACK TRIGGERED: {reason}")

        # Update environment
        os.environ['USE_LEGACY_AUDIO'] = 'live'
        os.environ['USE_REALTIME_API'] = 'disabled'

        # Restart system
        subprocess.run(['./nevil', 'restart'])

        # Alert developers
        self._send_alert(reason)
```

**Manual Rollback**:
```bash
# Emergency rollback command
./nevil rollback --reason "audio-quality-issues"

# This will:
# 1. Stop Realtime API node
# 2. Enable legacy nodes (speech_recognition, ai_cognition, speech_synthesis)
# 3. Restart system
# 4. Create rollback report
```

---

## Testing Strategy

### Unit Tests

#### Test Suite Structure

```
tests/
├── unit/
│   ├── test_realtime_client.py           # WebSocket client tests
│   ├── test_audio_stream_manager.py      # Audio I/O tests
│   ├── test_function_handler.py          # Function calling tests
│   ├── test_session_manager.py           # Connection lifecycle
│   └── test_realtime_cognition_node.py   # Main node tests
├── integration/
│   ├── test_audio_pipeline.py            # End-to-end audio
│   ├── test_message_bus_integration.py   # Inter-node messaging
│   ├── test_function_execution.py        # Function → action flow
│   └── test_multimodal.py                # Vision integration
├── performance/
│   ├── test_latency.py                   # Response time tests
│   ├── test_throughput.py                # Concurrent request handling
│   ├── test_memory.py                    # Memory leak detection
│   └── test_audio_quality.py             # Signal processing quality
└── regression/
    ├── test_legacy_compatibility.py      # v1.0 feature preservation
    ├── test_v3_parity.py                 # v3.0 feature parity
    └── test_edge_cases.py                # Known edge case handling
```

#### Unit Test Examples

**Test 1: WebSocket Connection**
```python
# tests/unit/test_realtime_client.py

import unittest
import os
from nodes.realtime_cognition.realtime_client import RealtimeClient

class TestRealtimeClient(unittest.TestCase):

    def setUp(self):
        self.api_key = os.getenv('OPENAI_API_KEY_TEST')  # Test API key
        self.client = None

    def test_connection_establishment(self):
        """Test WebSocket connection to Realtime API"""
        # Create client
        self.client = RealtimeClient(
            api_key=self.api_key,
            on_error=self._on_error
        )

        # Connect
        self.client.connect()

        # Assert connected
        self.assertTrue(self.client.connected)
        self.assertIsNotNone(self.client.session_id)

    def test_connection_failure_handling(self):
        """Test handling of connection failures"""
        # Invalid API key
        client = RealtimeClient(api_key="invalid_key")

        with self.assertRaises(ConnectionError):
            client.connect()

    def test_audio_transmission(self):
        """Test audio data transmission"""
        self.client = RealtimeClient(api_key=self.api_key)
        self.client.connect()

        # Send test audio chunk
        test_audio = b'\x00' * 4800  # Silence
        self.client.send_audio(test_audio)

        # Should not raise exception
        self.assertTrue(True)

    def tearDown(self):
        if self.client:
            self.client.disconnect()
```

**Test 2: Audio Stream Manager**
```python
# tests/unit/test_audio_stream_manager.py

import unittest
import numpy as np
from nodes.realtime_cognition.audio_stream_manager import AudioStreamManager

class TestAudioStreamManager(unittest.TestCase):

    def setUp(self):
        # Mock device indices for testing
        self.manager = AudioStreamManager(
            input_device=1,
            output_device=3,
            sample_rate=24000
        )

    def test_device_verification(self):
        """Test audio device availability"""
        # Should identify correct devices
        self.assertEqual(self.manager.input_device, 1)
        self.assertEqual(self.manager.output_device, 3)

    def test_stream_initialization(self):
        """Test audio stream start/stop"""
        # Start streams
        self.manager.start_streams()
        self.assertTrue(self.manager.input_stream.active)
        self.assertTrue(self.manager.output_stream.active)

        # Stop streams
        self.manager.stop_streams()
        self.assertFalse(self.manager.input_stream.active)

    def test_audio_read_write_cycle(self):
        """Test reading from input and writing to output"""
        self.manager.start_streams()

        # Read audio chunk (may be None if no sound)
        audio_chunk = self.manager.read_input()

        if audio_chunk:
            # Write chunk to output
            self.manager.write_output(audio_chunk)
            # Should not raise exception

        self.manager.stop_streams()

    def test_hardware_configuration_preservation(self):
        """Test v1.0 hardware settings preserved"""
        # Check sample rate
        self.assertEqual(self.manager.sample_rate, 24000)

        # Check device indices match v1.0
        self.assertEqual(self.manager.input_device, 1)  # USB mic
        self.assertEqual(self.manager.output_device, 3)  # HiFiBerry
```

**Test 3: Function Handler**
```python
# tests/unit/test_function_handler.py

import unittest
from unittest.mock import Mock
from nodes.realtime_cognition.function_handler import FunctionHandler

class TestFunctionHandler(unittest.TestCase):

    def setUp(self):
        self.message_bus = Mock()
        self.logger = Mock()
        self.handler = FunctionHandler(self.message_bus, self.logger)

    def test_execute_robot_actions(self):
        """Test robot action execution"""
        result = self.handler.execute('execute_robot_actions', {
            'actions': ['forward 30', 'nod', 'wave_hands'],
            'mood': 'playful'
        })

        # Assert success
        self.assertTrue(result['success'])
        self.assertEqual(result['result']['executed_actions'], 3)

        # Assert message bus called
        self.message_bus.publish.assert_called_once()

    def test_change_mood(self):
        """Test mood change function"""
        result = self.handler.execute('change_mood', {
            'mood': 'curious',
            'reason': 'user_interaction'
        })

        self.assertTrue(result['success'])
        self.assertEqual(result['result']['new_mood'], 'curious')

    def test_unknown_function_handling(self):
        """Test handling of unknown function calls"""
        result = self.handler.execute('invalid_function', {})

        self.assertFalse(result['success'])
        self.assertIn('Unknown function', result['error'])

    def test_function_error_handling(self):
        """Test error handling in function execution"""
        # Force error by passing invalid arguments
        result = self.handler.execute('execute_robot_actions', {
            'actions': None  # Invalid type
        })

        self.assertFalse(result['success'])
        self.assertIn('error', result)
```

### Integration Tests

#### Test 4: End-to-End Audio Pipeline
```python
# tests/integration/test_audio_pipeline.py

import unittest
import time
import wave
import os
from nodes.realtime_cognition.realtime_cognition_node import RealtimeCognitionNode

class TestAudioPipeline(unittest.TestCase):

    def setUp(self):
        self.node = RealtimeCognitionNode()
        self.node.initialize()
        self.response_received = False
        self.response_text = None

    def test_speech_to_speech_pipeline(self):
        """Test complete speech-to-speech flow"""
        # Load test audio file (pre-recorded "Hello Nevil")
        test_audio = self._load_test_audio('hello_nevil.wav')

        # Override audio manager to inject test audio
        original_read = self.node.audio_manager.read_input

        def mock_read():
            if hasattr(self, '_audio_sent'):
                return original_read()
            else:
                self._audio_sent = True
                return test_audio

        self.node.audio_manager.read_input = mock_read

        # Override audio callback to capture response
        original_on_audio = self.node._on_audio_response

        def mock_on_audio(audio_data, transcript=None):
            self.response_received = True
            self.response_text = transcript
            original_on_audio(audio_data, transcript)

        self.node._on_audio_response = mock_on_audio

        # Run main loop for up to 10 seconds
        start_time = time.time()
        while not self.response_received and time.time() - start_time < 10:
            self.node.main_loop()
            time.sleep(0.1)

        # Assert response received
        self.assertTrue(self.response_received)
        self.assertIsNotNone(self.response_text)
        self.assertGreater(len(self.response_text), 0)

    def _load_test_audio(self, filename):
        """Load test audio file as bytes"""
        path = os.path.join('tests', 'fixtures', filename)
        with wave.open(path, 'rb') as wav:
            return wav.readframes(wav.getnframes())

    def tearDown(self):
        self.node.cleanup()
```

#### Test 5: Function Calling Integration
```python
# tests/integration/test_function_execution.py

import unittest
import time
from nodes.realtime_cognition.realtime_cognition_node import RealtimeCognitionNode

class TestFunctionExecution(unittest.TestCase):

    def setUp(self):
        self.node = RealtimeCognitionNode()
        self.node.initialize()
        self.function_called = False
        self.function_name = None

    def test_action_function_calling(self):
        """Test that AI can call robot action functions"""
        # Inject function call event
        test_function_call = {
            'name': 'execute_robot_actions',
            'arguments': {
                'actions': ['nod', 'wave_hands'],
                'mood': 'playful'
            }
        }

        # Trigger function call handler
        result = self.node.function_handler.execute(
            test_function_call['name'],
            test_function_call['arguments']
        )

        # Assert function executed
        self.assertTrue(result['success'])

        # Check message bus was called
        # (Would need to mock message_bus in node initialization)

    def test_camera_function_calling(self):
        """Test snapshot function calling"""
        result = self.node.function_handler.execute('take_snapshot', {
            'purpose': 'inspect_object'
        })

        self.assertTrue(result['success'])
        self.assertTrue(result['result']['snapshot_requested'])
```

### Performance Tests

#### Test 6: Latency Measurement
```python
# tests/performance/test_latency.py

import unittest
import time
import statistics
from nodes.realtime_cognition.realtime_cognition_node import RealtimeCognitionNode

class TestLatency(unittest.TestCase):

    def setUp(self):
        self.node = RealtimeCognitionNode()
        self.node.initialize()
        self.latencies = []

    def test_average_response_latency(self):
        """Test average latency over multiple requests"""
        test_inputs = [
            "Hello",
            "What's the weather?",
            "Tell me a joke",
            "Move forward",
            "Take a picture"
        ]

        for input_text in test_inputs:
            start_time = time.time()

            # Simulate user speech (would inject audio)
            # For this test, directly trigger text processing

            # Wait for response
            response_received = False
            while not response_received and time.time() - start_time < 5:
                self.node.main_loop()
                # Check if response in output queue
                if not self.node.audio_manager.output_queue.empty():
                    response_received = True
                time.sleep(0.01)

            latency = time.time() - start_time
            self.latencies.append(latency)

        # Calculate statistics
        avg_latency = statistics.mean(self.latencies)
        p95_latency = statistics.quantiles(self.latencies, n=20)[18]  # 95th percentile

        # Assert performance targets
        self.assertLess(avg_latency, 0.5, "Average latency should be < 500ms")
        self.assertLess(p95_latency, 1.0, "P95 latency should be < 1s")

        print(f"\nLatency Results:")
        print(f"  Average: {avg_latency*1000:.0f}ms")
        print(f"  P95: {p95_latency*1000:.0f}ms")
        print(f"  Min: {min(self.latencies)*1000:.0f}ms")
        print(f"  Max: {max(self.latencies)*1000:.0f}ms")
```

#### Test 7: Audio Quality
```python
# tests/performance/test_audio_quality.py

import unittest
import numpy as np
from nodes.realtime_cognition.audio_stream_manager import AudioStreamManager

class TestAudioQuality(unittest.TestCase):

    def test_signal_to_noise_ratio(self):
        """Test audio quality via SNR measurement"""
        manager = AudioStreamManager()
        manager.start_streams()

        # Collect audio samples
        samples = []
        for _ in range(100):  # 2 seconds at 200ms chunks
            chunk = manager.read_input()
            if chunk:
                samples.append(np.frombuffer(chunk, dtype=np.int16))
            time.sleep(0.02)

        # Calculate SNR
        if samples:
            signal = np.concatenate(samples)
            signal_power = np.mean(signal ** 2)
            noise_power = np.var(signal - np.mean(signal))
            snr = 10 * np.log10(signal_power / noise_power)

            # Assert acceptable SNR (> 20 dB for voice)
            self.assertGreater(snr, 20, "SNR should be > 20 dB")

        manager.stop_streams()

    def test_latency_buffer_overflow(self):
        """Test that audio buffers don't overflow under load"""
        manager = AudioStreamManager()
        manager.start_streams()

        # Rapid read/write cycles
        overflow_count = 0
        for _ in range(1000):
            chunk = manager.read_input()
            if chunk:
                try:
                    manager.write_output(chunk)
                except queue.Full:
                    overflow_count += 1

        # Assert minimal overflows (< 1%)
        self.assertLess(overflow_count, 10, "Buffer overflow rate should be < 1%")

        manager.stop_streams()
```

### Regression Tests

#### Test 8: v1.0 Feature Preservation
```python
# tests/regression/test_legacy_compatibility.py

import unittest
from nodes.realtime_cognition.audio_stream_manager import AudioStreamManager

class TestLegacyCompatibility(unittest.TestCase):

    def test_v1_hardware_configuration(self):
        """Test v1.0 hardware settings preserved"""
        manager = AudioStreamManager()

        # Device indices must match v1.0
        self.assertEqual(manager.input_device, 1, "USB microphone must be device 1")
        self.assertEqual(manager.output_device, 3, "HiFiBerry DAC must be device 3")

    def test_v1_gpio_initialization(self):
        """Test GPIO pin 20 configured for speaker"""
        manager = AudioStreamManager()

        # Check GPIO command was executed
        # (Would need to mock os.system to verify)

    def test_v1_audio_quality_parameters(self):
        """Test audio parameters match v1.0 quality"""
        manager = AudioStreamManager(sample_rate=24000)

        # Sample rate for Realtime API
        self.assertEqual(manager.sample_rate, 24000)

        # Channels (mono for Realtime API, was stereo in v1.0)
        self.assertEqual(manager.channels, 1)
```

---

### Test Automation & CI/CD

#### GitHub Actions Workflow
```yaml
# .github/workflows/nevil-tests.yml

name: Nevil 2.2 Test Suite

on:
  push:
    branches: [main, develop, feature/realtime-api]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run unit tests
        env:
          OPENAI_API_KEY_TEST: ${{ secrets.OPENAI_API_KEY_TEST }}
        run: |
          pytest tests/unit/ -v --cov=nodes/realtime_cognition

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-timeout

      - name: Run integration tests
        env:
          OPENAI_API_KEY_TEST: ${{ secrets.OPENAI_API_KEY_TEST }}
        run: |
          pytest tests/integration/ -v --timeout=30

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-benchmark

      - name: Run performance tests
        env:
          OPENAI_API_KEY_TEST: ${{ secrets.OPENAI_API_KEY_TEST }}
        run: |
          pytest tests/performance/ -v --benchmark-only

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: .benchmarks/
```

---

## Quality Assurance

### Validation Criteria

#### Node-Level Validation

**Realtime Cognition Node**:
```yaml
Connection & Session:
  - ✓ WebSocket connects within 2 seconds
  - ✓ Session established with valid session_id
  - ✓ Auto-reconnect on disconnection (< 5s downtime)
  - ✓ Graceful handling of API rate limits

Audio Processing:
  - ✓ Input audio captured at 24kHz mono PCM16
  - ✓ Output audio plays through HiFiBerry DAC
  - ✓ No audio dropouts or glitches
  - ✓ Latency < 500ms (input → output)

Function Calling:
  - ✓ Function definitions loaded correctly
  - ✓ Function calls execute within 100ms
  - ✓ Robot actions publish to message bus
  - ✓ Function results sent back to API

Error Handling:
  - ✓ Network errors trigger reconnection
  - ✓ API errors logged and reported
  - ✓ Invalid function calls handled gracefully
  - ✓ Audio stream errors don't crash node
```

#### System-Level Validation

**End-to-End Flow**:
```yaml
Speech Recognition:
  - ✓ User speech detected via VAD
  - ✓ Transcription accuracy > 90%
  - ✓ Ambient noise filtering works
  - ✓ Multiple speakers distinguishable

AI Processing:
  - ✓ Context maintained across turns
  - ✓ Personality traits evident in responses
  - ✓ Mood changes reflected in behavior
  - ✓ Function calls match user intent

Speech Synthesis:
  - ✓ Voice quality matches expectations
  - ✓ Prosody and emotion conveyed
  - ✓ Speaking rate appropriate
  - ✓ Audio synchronization correct

Robot Actions:
  - ✓ Movement commands executed accurately
  - ✓ Gesture sequences smooth and natural
  - ✓ Camera snapshots captured on request
  - ✓ Sound effects play correctly
```

### Performance Benchmarks

#### Latency Targets

| Metric | Target | Method |
|--------|--------|--------|
| VAD Detection | < 100ms | Server-side turn detection |
| Speech Recognition | < 200ms | Realtime API transcription |
| AI Processing | < 100ms | Streaming function calls |
| Speech Synthesis | < 100ms | Audio chunk streaming |
| **Total Round-Trip** | **< 500ms** | User speech → robot response start |

#### Throughput Targets

| Metric | Target | Method |
|--------|--------|--------|
| Concurrent Conversations | 1 | Single WebSocket session |
| Audio Stream Rate | 24kHz | PCM16 mono |
| Function Call Rate | 10/sec | Message bus throughput |
| Message Bus Latency | < 50ms | Queue-based pub/sub |

#### Resource Targets

| Resource | Target | Monitoring |
|----------|--------|------------|
| CPU Usage | < 25% | Per-node monitoring |
| Memory Usage | < 300MB | Process memory tracking |
| Network Bandwidth | < 100KB/s | WebSocket data rate |
| Disk Usage | < 100MB | Conversation logs |

### Success Metrics

#### Primary Metrics

1. **Latency Reduction**: ≥ 85% reduction vs. v3.0 baseline
   - Baseline (v3.0): 5-8 seconds
   - Target (v2.2): < 500ms
   - Measurement: End-to-end timing tests

2. **Conversation Naturalness**: ≥ 4.0/5.0 user rating
   - Interruption handling
   - Overlapping speech support
   - Response coherence
   - Measurement: User surveys

3. **Function Calling Accuracy**: ≥ 95% correct execution
   - Intent recognition
   - Parameter extraction
   - Action execution
   - Measurement: Automated tests

4. **System Stability**: ≥ 99.5% uptime
   - Connection reliability
   - Error recovery
   - Resource utilization
   - Measurement: Production monitoring

#### Secondary Metrics

1. **Cost Efficiency**: ≤ $0.24/minute interaction cost
   - Audio input: $0.06/min
   - Audio output: $0.24/min
   - Measurement: API usage tracking

2. **User Engagement**: ≥ 30% increase in interaction duration
   - Session length
   - Turn count
   - Re-engagement rate
   - Measurement: Analytics dashboard

3. **Error Rate**: < 2% of interactions
   - API errors
   - Audio failures
   - Function call errors
   - Measurement: Error logging

---

## Risk Assessment & Mitigation

### Critical Risks

#### Risk 1: API Availability & Reliability

**Risk Level**: HIGH
**Impact**: Complete system failure
**Probability**: MEDIUM (30%)

**Description**:
- OpenAI Realtime API is in beta (gpt-4o-realtime-preview-2024-12-17)
- No SLA guarantees for beta services
- Potential for unexpected downtime or API changes

**Mitigation Strategy**:
```python
# 1. Fallback to Legacy Pipeline
class RealtimeCognitionNode:
    def __init__(self):
        self.fallback_mode = False
        self.legacy_nodes_available = True

    def _on_error(self, error_msg):
        """Handle Realtime API errors"""
        if self._is_critical_error(error_msg):
            self.logger.critical(f"Realtime API critical error: {error_msg}")
            self._activate_fallback()

    def _activate_fallback(self):
        """Switch to legacy audio pipeline"""
        self.fallback_mode = True

        # Re-enable legacy nodes
        self.message_bus.publish({
            "topic": "system_command",
            "data": {
                "command": "enable_legacy_audio",
                "reason": "realtime_api_failure"
            }
        })

        # Disable this node
        self.stop()

# 2. Health Monitoring
class HealthMonitor:
    def check_realtime_api_status(self):
        """Monitor API health"""
        if self.consecutive_failures > 5:
            self._trigger_fallback()

    def _trigger_fallback(self):
        """Automated fallback activation"""
        # Email alert to developers
        # Slack notification
        # Enable legacy nodes
        # Update monitoring dashboard
```

**Contingency Plan**:
- Maintain legacy nodes in codebase (no deletion)
- Regular failover drills
- 24-hour monitoring during initial rollout

---

#### Risk 2: Hardware Incompatibility

**Risk Level**: MEDIUM
**Impact**: Audio quality degradation
**Probability**: MEDIUM (40%)

**Description**:
- Realtime API requires 24kHz audio (v1.0 uses 44.1kHz)
- Sample rate conversion may introduce artifacts
- HiFiBerry DAC compatibility unknown

**Mitigation Strategy**:
```python
# Sample Rate Conversion Testing
def test_sample_rate_conversion():
    """Test 24kHz vs 44.1kHz audio quality"""

    # Record same audio at both rates
    audio_44k = record_audio(sample_rate=44100)
    audio_24k = record_audio(sample_rate=24000)

    # Compare quality metrics
    snr_44k = calculate_snr(audio_44k)
    snr_24k = calculate_snr(audio_24k)

    quality_difference = abs(snr_44k - snr_24k)

    assert quality_difference < 3, "Quality degradation > 3dB"

# Hardware Compatibility Matrix
hardware_tests = {
    'USB_PnP_Microphone_24kHz': 'PASS',
    'HiFiBerry_DAC_24kHz': 'TESTING',
    'Sample_Rate_Conversion': 'TESTING'
}
```

**Testing Plan**:
- Week 1: Hardware compatibility testing
- Week 2: Audio quality blind testing
- Week 3: A/B comparison with v1.0

---

#### Risk 3: Cost Overrun

**Risk Level**: MEDIUM
**Impact**: Budget exceeded
**Probability**: HIGH (60%)

**Description**:
- Realtime API pricing: $0.06/min input + $0.24/min output
- Expected usage: 5 hours/day = $45/day = $1,350/month
- Budget: $500/month (3.3x over)

**Mitigation Strategy**:
```python
# Cost Monitoring & Throttling
class CostMonitor:
    def __init__(self):
        self.daily_budget = 500 / 30  # $16.67/day
        self.hourly_budget = self.daily_budget / 24  # $0.69/hour
        self.current_cost = 0

    def track_usage(self, duration_seconds, input_output='both'):
        """Track API usage cost"""
        minutes = duration_seconds / 60

        if input_output == 'both':
            cost = minutes * (0.06 + 0.24)  # $0.30/min
        elif input_output == 'input':
            cost = minutes * 0.06
        else:
            cost = minutes * 0.24

        self.current_cost += cost

        # Check budget
        if self.current_cost > self.hourly_budget:
            self._throttle_usage()

    def _throttle_usage(self):
        """Reduce usage to stay within budget"""
        # Option 1: Reduce conversation frequency
        # Option 2: Shorter responses
        # Option 3: Switch to text-only mode
        # Option 4: Fallback to legacy (free after API costs)

        self.logger.warning("Budget exceeded, throttling enabled")
```

**Cost Reduction Strategies**:
1. **Optimize Turn Detection**: Reduce false activations
2. **Shorter System Prompt**: Reduce token usage (not applicable to audio pricing)
3. **Session Timeouts**: Close idle sessions
4. **Usage Limits**: Daily/monthly caps

---

#### Risk 4: Migration Regression

**Risk Level**: MEDIUM
**Impact**: Feature loss or quality degradation
**Probability**: MEDIUM (50%)

**Description**:
- 106 extended gestures must work identically
- Mood system integration
- Camera snapshot workflow
- Sound effect playback

**Mitigation Strategy**:
```python
# Comprehensive Regression Test Suite
class RegressionTests:
    def test_all_gestures_available(self):
        """Test all 106 gestures callable"""
        gestures = load_gesture_list()  # 106 gestures

        for gesture in gestures:
            result = self.handler.execute('execute_robot_actions', {
                'actions': [gesture]
            })
            assert result['success'], f"Gesture {gesture} failed"

    def test_mood_system_integration(self):
        """Test all 9 moods work correctly"""
        moods = ['playful', 'brooding', 'curious', 'melancholic',
                 'zippy', 'lonely', 'mischievous', 'sleepy', 'neutral']

        for mood in moods:
            result = self.handler.execute('change_mood', {'mood': mood})
            assert result['success']

    def test_camera_integration(self):
        """Test camera snapshot workflow"""
        result = self.handler.execute('take_snapshot', {})
        assert result['success']

        # Verify message published
        # Verify visual node responds

    def test_sound_effects(self):
        """Test all sound effects playable"""
        sounds = ['rev_engine', 'airhorn', 'dubstep', 'ghost_laugh', ...]

        for sound in sounds:
            result = self.handler.execute('play_sound', {'sound': sound})
            assert result['success']
```

**Regression Prevention**:
- Automated regression suite runs on every commit
- Manual testing of critical user journeys
- Beta testing period with rollback option

---

### Risk Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────┐
│ Nevil 2.2 Risk Monitoring Dashboard                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ API Availability:        ●●●●● 99.2%  [HEALTHY]       │
│ Audio Quality (SNR):     ●●●○○ 24.3dB [WARNING]       │
│ Daily Cost:              ●●●●○ $18.42 [OVER BUDGET]   │
│ Regression Tests:        ●●●●● 100%   [PASSING]       │
│ User Satisfaction:       ●●●●○ 4.2/5  [GOOD]          │
│                                                         │
│ Active Risks:                                           │
│  ⚠️  Cost trending 10% over budget                     │
│  ⚠️  Audio SNR below 25dB threshold                    │
│                                                         │
│ Mitigation Actions:                                     │
│  🔧 Optimize turn detection to reduce false triggers   │
│  🔧 Hardware audio settings calibration in progress    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Timeline

### 6-Week Detailed Schedule

#### Week 1: Foundation (Dec 16-22, 2024)

**Days 1-2: Environment Setup**
- [ ] Install new dependencies (websockets, sounddevice, numpy)
- [ ] Update `requirements.txt`
- [ ] Create `nodes/realtime_cognition/` directory structure
- [ ] Set up test fixtures and test data
- [ ] Configure CI/CD pipeline for new tests

**Days 3-4: Core Components**
- [ ] Implement `realtime_client.py` (WebSocket wrapper)
- [ ] Implement `audio_stream_manager.py` (Audio I/O)
- [ ] Write unit tests for both components
- [ ] Hardware compatibility testing

**Days 5-7: Node Skeleton**
- [ ] Implement `realtime_cognition_node.py` (main node)
- [ ] Implement `function_handler.py` (function calling)
- [ ] Create `.messages` configuration
- [ ] Basic integration testing

**Deliverables**:
- ✓ Realtime API connection working
- ✓ Audio I/O functional
- ✓ Unit tests passing (>80% coverage)

---

#### Week 2: Audio Integration (Dec 23-29, 2024)

**Days 1-2: Audio Pipeline**
- [ ] Bidirectional audio streaming implementation
- [ ] Sample rate conversion (44.1kHz → 24kHz)
- [ ] Buffer management and optimization
- [ ] Audio quality testing (SNR, latency)

**Days 3-4: VAD Configuration**
- [ ] Server-side VAD tuning (threshold calibration)
- [ ] v1.0 energy_threshold mapping
- [ ] False trigger rate testing
- [ ] Silence detection optimization

**Days 5-7: Hardware Integration**
- [ ] GPIO configuration preservation
- [ ] HiFiBerry DAC compatibility testing
- [ ] USB microphone integration
- [ ] ALSA configuration verification

**Deliverables**:
- ✓ Audio pipeline functional end-to-end
- ✓ Voice activity detection tuned
- ✓ Hardware compatibility verified

---

#### Week 3: Function Calling (Dec 30 - Jan 5, 2025)

**Days 1-2: Function Definitions**
- [ ] Create `function_definitions.json`
- [ ] Map all 106 gestures to function parameters
- [ ] Define mood change function
- [ ] Define camera/sound functions

**Days 3-4: Function Execution**
- [ ] Implement function call handlers
- [ ] Message bus integration
- [ ] Action execution testing
- [ ] Error handling for invalid calls

**Days 5-7: Testing & Refinement**
- [ ] Function calling accuracy tests
- [ ] Integration with navigation node
- [ ] Integration with visual node
- [ ] Performance benchmarking

**Deliverables**:
- ✓ All functions callable and executing
- ✓ Integration tests passing
- ✓ Function calling accuracy >95%

---

#### Week 4: System Integration (Jan 6-12, 2025)

**Days 1-2: Message Bus Integration**
- [ ] Realtime node publishes to existing topics
- [ ] Subscribe to visual_data for multimodal
- [ ] Inter-node communication testing
- [ ] Message format compatibility

**Days 3-4: Conversation Management**
- [ ] System prompt migration
- [ ] Conversation history mirroring
- [ ] Context preservation across sessions
- [ ] Chat logger integration

**Days 5-7: End-to-End Testing**
- [ ] Complete user journey testing
- [ ] Multi-turn conversation testing
- [ ] Edge case handling
- [ ] Performance regression testing

**Deliverables**:
- ✓ Full system integration complete
- ✓ E2E tests passing
- ✓ Latency targets met (<500ms)

---

#### Week 5: Testing & Validation (Jan 13-19, 2025)

**Days 1-3: Comprehensive Testing**
- [ ] Run full test suite (unit, integration, performance)
- [ ] Regression testing (v1.0 compatibility)
- [ ] Load testing and stress testing
- [ ] Audio quality blind testing

**Days 4-5: Alpha Deployment**
- [ ] Deploy to test device
- [ ] 24-hour continuous operation test
- [ ] Error monitoring and logging
- [ ] Performance metrics collection

**Days 6-7: Beta Deployment**
- [ ] Deploy to 3-5 beta devices
- [ ] User acceptance testing
- [ ] Collect feedback and telemetry
- [ ] Bug fixes and refinements

**Deliverables**:
- ✓ All tests passing (100% critical, >95% total)
- ✓ Alpha/Beta deployments successful
- ✓ User feedback collected

---

#### Week 6: Production Rollout (Jan 20-26, 2025)

**Days 1-2: Canary Deployment**
- [ ] 10% traffic to Realtime API
- [ ] Automated monitoring and alerting
- [ ] Rollback procedures tested
- [ ] Performance comparison (v3.0 vs v2.2)

**Days 3-4: Incremental Rollout**
- [ ] 50% traffic split
- [ ] A/B testing and metrics collection
- [ ] Cost monitoring and optimization
- [ ] User satisfaction surveys

**Days 5-7: Full Rollout**
- [ ] 100% traffic to Realtime API
- [ ] Legacy nodes on standby
- [ ] Success metrics review
- [ ] Documentation finalization
- [ ] Team training and handoff

**Deliverables**:
- ✓ Production deployment complete
- ✓ Success metrics met
- ✓ Legacy fallback ready
- ✓ Documentation complete

---

### Critical Path

```
Week 1: Foundation → Week 2: Audio → Week 3: Functions → Week 4: Integration → Week 5: Testing → Week 6: Rollout
   ↓                     ↓                 ↓                    ↓                  ↓                  ↓
Realtime Client → Audio Pipeline → Function Calling → Message Bus → Alpha Test → Canary Deploy → Production
(Cannot proceed to next stage without completing previous)
```

**Critical Dependencies**:
1. Realtime Client must work before Audio Pipeline
2. Audio Pipeline must work before Function Calling
3. Function Calling must work before Integration
4. Integration must work before Testing
5. Testing must pass before Rollout

---

## Appendices

### Appendix A: API Reference

#### OpenAI Realtime API Events

**Client → Server Events**:
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["text", "audio"],
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16"
  }
}

{
  "type": "input_audio_buffer.append",
  "audio": "base64_encoded_audio_data"
}

{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_abc123",
    "output": "{\"result\": \"success\"}"
  }
}
```

**Server → Client Events**:
```json
{
  "type": "session.created",
  "session": {
    "id": "sess_abc123",
    "modalities": ["text", "audio"]
  }
}

{
  "type": "response.audio.delta",
  "delta": "base64_audio_chunk"
}

{
  "type": "response.audio_transcript.delta",
  "delta": "transcribed text chunk"
}

{
  "type": "response.function_call_arguments.done",
  "name": "execute_robot_actions",
  "arguments": "{\"actions\": [\"nod\"]}"
}
```

---

### Appendix B: Configuration Templates

#### `.messages` Template
```yaml
node_name: "realtime_cognition"
version: "2.2.0"
description: "Unified speech-to-speech cognition using OpenAI Realtime API"

publishes:
  - topic: "text_response"
    message_type: "TextResponse"
  - topic: "robot_action"
    message_type: "RobotAction"
  - topic: "mood_change"
    message_type: "MoodChange"
  - topic: "realtime_status"
    message_type: "RealtimeStatus"

subscribes:
  - topic: "visual_data"
    message_type: "VisualData"
    callback: "on_visual_data"
  - topic: "system_command"
    message_type: "SystemCommand"
    callback: "on_system_command"

configuration:
  realtime_api:
    model: "gpt-4o-realtime-preview-2024-12-17"
    voice: "alloy"
    sample_rate: 24000
  audio_hardware:
    input_device: 1
    output_device: 3
  turn_detection:
    type: "server_vad"
    threshold: 0.5
```

#### Environment Variables
```bash
# .env

# Core API
OPENAI_API_KEY=sk-...
REALTIME_API_MODEL=gpt-4o-realtime-preview-2024-12-17

# Feature Flags
USE_REALTIME_API=live  # live | disabled
USE_LEGACY_AUDIO=disabled  # live | disabled
REALTIME_TEST_MODE=false  # true | false

# Audio Configuration
REALTIME_INPUT_DEVICE=1  # USB microphone
REALTIME_OUTPUT_DEVICE=3  # HiFiBerry DAC
REALTIME_SAMPLE_RATE=24000

# Cost Controls
REALTIME_DAILY_BUDGET=16.67  # dollars
REALTIME_THROTTLE_ENABLED=true

# Monitoring
REALTIME_METRICS_ENABLED=true
REALTIME_LOGGING_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
```

---

### Appendix C: Troubleshooting Guide

#### Common Issues

**Issue 1: WebSocket Connection Fails**
```
Error: Connection refused to wss://api.openai.com/v1/realtime
```

**Solution**:
1. Check API key: `echo $OPENAI_API_KEY`
2. Verify API key has Realtime API access
3. Check network connectivity: `curl https://api.openai.com`
4. Review firewall rules (port 443)

---

**Issue 2: Audio Not Playing**
```
Error: Output device not found (device 3)
```

**Solution**:
1. List audio devices: `python -c "import sounddevice; print(sounddevice.query_devices())"`
2. Verify HiFiBerry DAC: `aplay -l | grep hifiberry`
3. Check GPIO configuration: `pinctrl get 20`
4. Restart ALSA: `sudo systemctl restart alsa-utils`

---

**Issue 3: High Latency (>1s)**
```
Warning: Average latency 1523ms exceeds target 500ms
```

**Solution**:
1. Check network latency: `ping api.openai.com`
2. Reduce buffer size in `audio_stream_manager.py`
3. Optimize turn detection threshold
4. Enable debug logging to identify bottleneck

---

**Issue 4: Function Calls Not Executing**
```
Error: Function 'execute_robot_actions' not found
```

**Solution**:
1. Verify function definitions loaded: Check `function_definitions.json`
2. Check function handler registration
3. Verify message bus connection
4. Review function call logs

---

### Appendix D: Cost Analysis

#### Realtime API Pricing Breakdown

**Per-Minute Costs**:
- Audio Input: $0.06/min
- Audio Output: $0.24/min
- Total: $0.30/min for bidirectional audio

**Daily Usage Estimate**:
- Active Hours: 5 hours/day
- Minutes: 300 min/day
- Daily Cost: 300 × $0.30 = $90/day

**Monthly Projection**:
- Days: 30
- Monthly Cost: $90 × 30 = $2,700/month

**Budget Constraints**:
- Allocated Budget: $500/month
- Overage: $2,200/month (440% over budget)

**Cost Reduction Strategies**:
1. **Reduce Active Hours**: 5h → 2h/day = $900/month (still 80% over)
2. **Throttle Conversations**: Limit to 10 min/hour = $72/month (within budget!)
3. **Hybrid Approach**:
   - 80% legacy (free after API costs)
   - 20% Realtime API = $540/month (8% over, acceptable)

**Recommended Approach**: Hybrid with 20% Realtime API adoption for testing, gradually increase as budget allows.

---

### Appendix E: Glossary

- **Realtime API**: OpenAI's speech-to-speech API with low-latency bidirectional audio streaming
- **VAD**: Voice Activity Detection - automatic detection of speech vs. silence
- **Function Calling**: AI ability to call predefined functions (e.g., robot actions)
- **Multimodal**: Processing both audio and visual data (speech + camera)
- **Message Bus**: Pub/sub communication system between Nevil nodes
- **HiFiBerry DAC**: Digital-to-Analog Converter for high-quality audio output
- **PCM16**: 16-bit Pulse Code Modulation audio format
- **SNR**: Signal-to-Noise Ratio - measure of audio quality
- **Canary Deployment**: Gradual rollout starting with small percentage of traffic
- **Rollback**: Reverting to previous version if issues detected

---

## Document Control

**Version History**:
- v1.0 (2025-11-11): Initial comprehensive strategy document
- v1.1 (TBD): Post-alpha testing updates
- v2.0 (TBD): Production rollout learnings

**Reviewers**:
- [ ] Architecture Team
- [ ] Development Team
- [ ] QA Team
- [ ] Product Owner

**Approval**:
- [ ] Technical Lead
- [ ] Project Manager
- [ ] Budget Approver

**Next Review Date**: 2025-01-27 (post-rollout retrospective)

---

**END OF DOCUMENT**
