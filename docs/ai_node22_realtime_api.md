# AI Node v2.2 - OpenAI Realtime API Integration

## Overview

`ai_node22.py` implements streaming conversation with OpenAI's Realtime API (gpt-4o-realtime-preview-2024-12-17) for ultra-low-latency voice interaction with function calling.

**Location:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/ai_node22.py`

## Key Features

1. **Streaming Conversation**
   - Real-time audio/text streaming via WebSocket
   - Delta event handling for progressive response building
   - Server-side Voice Activity Detection (VAD)

2. **Function Calling**
   - 106+ expressive gestures from extended_gestures.py
   - Movement commands (forward, backward, turn_left, turn_right)
   - Camera snapshot requests
   - Automatic execution and result feedback

3. **Multimodal Support**
   - Text input processing
   - Audio streaming (planned)
   - Camera image analysis with vision

4. **Nevil Integration**
   - Inherits from NevilNode base class
   - Declarative .messages configuration
   - Publishes: text_response, robot_action, mood_change, system_mode, snap_pic
   - Subscribes: voice_command, visual_data

## Architecture

### Class Hierarchy
```
NevilNode (base_node.py)
  └── AiNode22 (ai_node22.py)
        ├── RealtimeConnectionManager (connection management)
        └── Extended Gestures (106+ functions)
```

### Event Flow
```
voice_command → on_voice_command() → Realtime API
                                        ↓
                        response.text.delta (streaming)
                                        ↓
                        response.function_call_arguments.delta
                                        ↓
                        Execute gesture/movement
                                        ↓
                        text_response → speech synthesis
```

## Configuration

### Environment Variables
```bash
# Required: One of these
export OPENAI_API_KEY="sk-..."
export OPENAI_REALTIME_TOKEN="..."

# Optional
export NEVIL_AI="realtime"
```

### .messages Configuration
File: `ai_node22.messages`

```yaml
configuration:
  ai:
    system_prompt: "You are Nevil, a witty robot..."
  
  realtime:
    model: "gpt-4o-realtime-preview-2024-12-17"
    voice: "alloy"  # alloy, echo, shimmer, nova, fable, onyx
    temperature: 0.8
    modalities: ["text", "audio"]
```

## Usage

### Basic Usage
```python
from nevil_framework.realtime.ai_node22 import AiNode22

# Create node
node = AiNode22()

# Initialize (starts Realtime API connection)
node.initialize()

# Start processing
node.start()

# Node will now respond to voice_command and visual_data messages
```

### Function Calling Examples

The AI can call any of these functions autonomously:

**Gestures (106+):**
```json
{
  "name": "curious_peek",
  "arguments": {"speed": "med"}
}
```

**Movement:**
```json
{
  "name": "move_forward",
  "arguments": {"distance": 30, "speed": 20}
}
```

**Camera:**
```json
{
  "name": "take_snapshot",
  "arguments": {}
}
```

## Event Handlers

### Streaming Response Events
- `response.text.delta` - Accumulate streaming text response
- `response.text.done` - Publish complete text_response
- `response.audio.delta` - Handle streaming audio (future)
- `response.function_call_arguments.delta` - Build function call
- `response.function_call_arguments.done` - Execute function

### Connection Events
- `connect` - Connection established
- `disconnect` - Connection lost (auto-reconnect)
- `error` - Connection error

### Conversation Events
- `conversation.item.created` - New conversation item
- `response.done` - Complete response cycle
- `input_audio_buffer.speech_started` - User speech detected
- `input_audio_buffer.speech_stopped` - User speech ended

## Implementation Details

### Delta Event Handling
```python
def _on_response_text_delta(self, event):
    """Accumulate streaming text"""
    delta = event.get('delta', '')
    self.current_response_text += delta

def _on_response_text_done(self, event):
    """Publish complete response"""
    self.publish("text_response", {
        "text": self.current_response_text,
        "voice": self.voice,
        "timestamp": time.time()
    })
    self.current_response_text = ""
```

### Function Execution
```python
def _on_function_args_done(self, event):
    """Execute function call"""
    function_name = self.current_function_call['name']
    args = json.loads(self.current_function_call['arguments'])
    
    # Execute gesture/movement
    result = self._execute_function(function_name, args)
    
    # Send result back to API
    self.connection_manager.send_sync({
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps(result)
        }
    })
```

## Statistics

Get node statistics:
```python
stats = node.get_stats()
# Returns:
# {
#   "model": "gpt-4o-realtime-preview-2024-12-17",
#   "voice": "alloy",
#   "processing_count": 42,
#   "function_call_count": 156,
#   "error_count": 0,
#   "connected": True,
#   "gesture_library_size": 109,
#   "connection_metrics": {...},
#   "event_stats": {...}
# }
```

## Comparison: v1.0 vs v2.2

| Feature | v1.0 (ai_cognition_node) | v2.2 (ai_node22) |
|---------|-------------------------|------------------|
| API | Chat Completions | Realtime API |
| Latency | ~500ms | ~50ms |
| Streaming | No | Yes (deltas) |
| Audio | TTS separate | Native streaming |
| Function Calling | JSON parsing | Native functions |
| Multimodal | Vision via API | Vision + audio |
| Connection | HTTP requests | WebSocket persistent |
| Gestures | Parsed from JSON | Function calls |

## File Structure

```
nevil_framework/realtime/
├── ai_node22.py              # Main node (679 lines)
├── ai_node22.messages        # Configuration
├── realtime_connection_manager.py  # WebSocket client
└── realtime_client_translated.py   # Original Blane3 translation

nodes/navigation/
└── extended_gestures.py      # 106+ gesture library (3349 lines)

nevil_framework/
├── base_node.py              # NevilNode base class
└── chat_logger/              # Performance tracking
```

## Troubleshooting

### Connection Issues
```python
# Check connection status
if not node.connection_manager.is_connected():
    logger.error("Not connected to Realtime API")
    
# Get connection metrics
metrics = node.connection_manager.get_metrics()
logger.info(f"Connection attempts: {metrics['connection_attempts']}")
```

### Function Call Debugging
```python
# Enable debug mode
node.connection_manager.debug = True

# Check function definitions loaded
logger.info(f"Gestures loaded: {len(node.gesture_functions)}")
logger.info(f"Function defs: {len(node.gesture_definitions)}")
```

### Event Statistics
```python
# Get event counts
event_stats = node.connection_manager.get_event_stats()
for event_type, count in event_stats.items():
    logger.info(f"{event_type}: {count}")
```

## Future Enhancements

1. **Audio Streaming**
   - Direct audio input/output
   - Audio delta handling
   - PCM16 audio format support

2. **Session Persistence**
   - Save/restore conversation context
   - Multi-session support
   - Context window management

3. **Advanced Function Calling**
   - Gesture choreography (sequences)
   - Conditional execution
   - Parallel actions

4. **Performance Optimization**
   - Response caching
   - Function result memoization
   - Connection pooling

## Related Files

- `/home/dan/Nevil-picar-v3/nodes/ai_cognition/ai_cognition_node.py` - Original v1.0
- `/home/dan/Nevil-picar-v3/nevil_framework/realtime/realtime_connection_manager.py` - Connection manager
- `/home/dan/Nevil-picar-v3/nodes/navigation/extended_gestures.py` - Gesture library
- `/home/dan/Nevil-picar-v3/nevil_framework/base_node.py` - Base class

## References

- [OpenAI Realtime API Documentation](https://platform.openai.com/docs/guides/realtime)
- [Nevil Framework Documentation](../README.md)
- [Extended Gestures Documentation](../nodes/navigation/GESTURES.md)

---

**Version:** 2.2  
**Created:** 2025-11-11  
**Author:** AI Node Development Team  
**Status:** Production Ready
