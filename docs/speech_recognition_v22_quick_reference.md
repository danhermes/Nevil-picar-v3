# Speech Recognition Node v2.2 - Quick Reference

## File Locations

```
nevil_framework/realtime/
├── speech_recognition_node22.py       # Main node (543 lines) ✅
├── .messages                          # Configuration ✅
├── audio_capture_manager.py           # Audio capture (739 lines) ✅
├── realtime_connection_manager.py     # WebSocket (204 lines) ✅
└── __init__.py                        # Package init ✅

docs/
├── speech_recognition_node22_implementation.md  # Full docs ✅
└── speech_recognition_v22_quick_reference.md    # This file ✅
```

## Quick Start

### 1. Import and Initialize

```python
from nevil_framework.realtime.speech_recognition_node22 import SpeechRecognitionNode22

# Create node
node = SpeechRecognitionNode22()

# Set message bus (done by launcher)
node.set_message_bus(message_bus)

# Initialize
node.initialize()

# Start
node.start()
```

### 2. Key Methods

```python
# Lifecycle
node.initialize()           # Setup WebSocket and audio
node.start()                # Start threads
node.stop()                 # Graceful shutdown
node.cleanup()              # Release resources

# State control
node._start_listening()     # Begin audio capture
node._stop_listening()      # Stop audio capture

# Statistics
stats = node.get_speech_stats()
```

### 3. Event Handlers (Auto-configured)

```python
# These are automatically routed from .messages configuration
on_system_mode_change(message)      # System mode transitions
on_speaking_status_change(message)   # TTS playback state
on_navigation_status_change(message) # Robot movement state
```

## Message Flow

### Input Topics (Subscribed)

```python
# system_mode
{
    "mode": "listening" | "speaking" | "thinking" | "idle" | "error",
    "timestamp": 1234567890.123
}

# speaking_status
{
    "speaking": true | false,
    "text": "optional text being spoken"
}

# navigation_status
{
    "status": "idle" | "executing" | "completed" | "error",
    "current_action": "optional action name",
    "timestamp": 1234567890.123
}
```

### Output Topics (Published)

```python
# voice_command
{
    "text": "recognized speech text",
    "confidence": 0.95,
    "timestamp": 1234567890.123,
    "language": "en-US",
    "duration": 2.5,
    "conversation_id": "unique-id-123",
    "mode": "realtime_streaming"
}

# listening_status
{
    "listening": true | false,
    "reason": "started" | "stopped" | "paused"
}
```

## Configuration (.messages)

### Realtime API Settings

```yaml
realtime:
  model: "gpt-4o-realtime-preview-2024-10-01"
  url: "wss://api.openai.com/v1/realtime"
  max_reconnects: 5
  reconnect_delay: 1.0
  connection_timeout: 30.0
```

### Audio Settings

```yaml
audio:
  sample_rate: 24000      # Required by Realtime API
  channel_count: 1        # Mono
  echo_cancellation: true
  noise_suppression: true
  auto_gain_control: true
  buffer_size: 4096
  chunk_size: 4800        # 200ms at 24kHz
```

### Recognition Settings

```yaml
recognition:
  language: "en-US"
  confidence_threshold: 0.5
  transcript_timeout: 2.0   # Process after 2s silence
```

## Key Differences from v1.0

| Feature | v1.0 | v2.2 |
|---------|------|------|
| API | Whisper REST | Realtime WebSocket |
| Latency | 2-5s | <500ms |
| Audio | Discrete recordings | Continuous streaming |
| Format | WAV files | Base64 PCM16 |
| Transcript | Single result | Streaming deltas |
| Sample Rate | 16kHz | 24kHz |
| Connection | Per-request | Persistent |

## Event Flow

```
Microphone
    ↓
AudioCaptureManager (24kHz PCM16)
    ↓
Base64 Encoding
    ↓
WebSocket → input_audio_buffer.append
    ↓
OpenAI Realtime API
    ↓
response.audio_transcript.delta (streaming)
    ↓
Transcript Accumulation
    ↓
response.audio_transcript.done (final)
    ↓
Process & Publish → voice_command topic
    ↓
AI Cognition Node (processes command)
```

## State Management

### Listening States

```python
# Active listening
is_listening = True          # Captures and streams audio
speaking_active = False      # TTS not playing
navigation_active = False    # Robot not moving

# Paused (during TTS)
is_listening = False         # Audio capture stopped
speaking_active = True       # TTS playing

# Paused (during movement)
is_listening = False         # Audio capture stopped
navigation_active = True     # Robot executing actions
```

### Thread Safety

```python
# Locks
transcript_lock = threading.Lock()    # Protects transcript accumulation
stream_lock = threading.Lock()        # Protects streaming state

# Events
stop_event = threading.Event()        # Signals shutdown

# Threads
transcript_thread                     # Monitors transcript timeout
```

## WebSocket Events

### Sent to API

```python
{
    "type": "input_audio_buffer.append",
    "audio": "base64_encoded_pcm16_data"
}
```

### Received from API

```python
# Streaming transcript chunk
{
    "type": "response.audio_transcript.delta",
    "delta": "partial text..."
}

# Final transcript
{
    "type": "response.audio_transcript.done",
    "transcript": "complete final text"
}

# Error event
{
    "type": "error",
    "error": {
        "message": "error description"
    }
}
```

## Debugging

### Enable Debug Logging

```python
import logging

# Set logger level
logging.getLogger('speech_recognition_realtime').setLevel(logging.DEBUG)
logging.getLogger('nevil_framework.realtime').setLevel(logging.DEBUG)
```

### Check Connection Status

```python
# Get connection stats
stats = node.connection_manager.get_stats()
print(f"Connected: {stats['connected']}")
print(f"Messages sent: {stats['messages_sent']}")
print(f"Messages received: {stats['messages_received']}")
print(f"Reconnect count: {stats['reconnect_count']}")
```

### Monitor Transcript Flow

```python
# Check current accumulation
with node.transcript_lock:
    print(f"Current: '{node.current_transcript}'")
    print(f"Last update: {time.time() - node.last_transcript_time:.1f}s ago")
```

### Verify Audio Capture

```python
# Check audio state
if node.audio_capture:
    state = node.audio_capture.get_state()
    print(f"Audio state: {state}")
```

## Common Issues

### Issue: No audio detected

```bash
# Check microphone
arecord -l

# Test PyAudio
python3 -c "import pyaudio; p = pyaudio.PyAudio(); print(f'Devices: {p.get_device_count()}')"
```

### Issue: WebSocket disconnects

```python
# Check reconnection settings
node.connection_manager.max_reconnects = 10  # Increase limit
node.connection_manager.reconnect_delay = 2.0  # Slower backoff
```

### Issue: Transcripts incomplete

```python
# Increase timeout
node.recognition_config['transcript_timeout'] = 3.0

# Check for early processing
# Look for: "Transcript timeout" in logs
```

## Performance Tuning

### Audio Chunk Size

```python
# Smaller chunks = lower latency, more overhead
chunk_size: 2400  # 100ms at 24kHz

# Larger chunks = higher latency, less overhead
chunk_size: 9600  # 400ms at 24kHz

# Recommended (balance)
chunk_size: 4800  # 200ms at 24kHz
```

### Buffer Size

```python
# Smaller buffer = more responsive, more CPU
buffer_size: 2048

# Larger buffer = less responsive, less CPU
buffer_size: 8192

# Recommended (balance)
buffer_size: 4096
```

### Reconnection Strategy

```python
# Aggressive (fast recovery, more API calls)
max_reconnects: 10
reconnect_delay: 0.5

# Conservative (slow recovery, fewer API calls)
max_reconnects: 3
reconnect_delay: 2.0

# Recommended (balance)
max_reconnects: 5
reconnect_delay: 1.0
```

## Testing Checklist

```
[ ] Import and initialize node
[ ] WebSocket connects successfully
[ ] Audio capture starts
[ ] Speak into microphone
[ ] See transcript.delta events in logs
[ ] See transcript.done event
[ ] voice_command published to message bus
[ ] AI cognition receives command
[ ] TTS starts (speaking_status = true)
[ ] Audio capture pauses
[ ] TTS ends (speaking_status = false)
[ ] Audio capture resumes
[ ] Graceful shutdown works
```

## Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional (for debugging)
export REALTIME_DEBUG=1
export REALTIME_LOG_LEVEL=DEBUG
```

## Statistics

```python
stats = node.get_speech_stats()

# Returns:
{
    "recognition_count": 42,
    "error_count": 0,
    "is_listening": true,
    "system_mode": "idle",
    "speaking_active": false,
    "last_recognition_time": 1234567890.123,
    "mode": "realtime_streaming",
    "connection_stats": {
        "connected": true,
        "messages_sent": 156,
        "messages_received": 312,
        "reconnect_count": 0,
        "uptime_seconds": 3600.5,
        "registered_handlers": 3
    }
}
```

## Integration Example

```python
# In your application
from nevil_framework.realtime.speech_recognition_node22 import SpeechRecognitionNode22
from nevil_framework.message_bus import MessageBus

# Create message bus
bus = MessageBus()

# Create and start node
stt_node = SpeechRecognitionNode22()
stt_node.set_message_bus(bus)
stt_node.initialize()
stt_node.start()

# Subscribe to voice commands
def on_voice_command(message):
    text = message.data['text']
    confidence = message.data['confidence']
    print(f"Heard: '{text}' (confidence: {confidence:.2f})")

bus.subscribe("app", "voice_command", on_voice_command)

# Run your application...
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    stt_node.stop()
```

---

**Quick Reference Version:** 1.0
**Implementation Date:** 2025-11-11
**Status:** ✅ Production Ready
