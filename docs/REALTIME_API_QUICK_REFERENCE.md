# OpenAI Realtime API Integration - Quick Reference
**Swarm ID**: swarm-1762909553486-yd1fw3wqi

## Overview

This quick reference provides essential information for implementing the three new Realtime API nodes for Nevil v3.0.

**Full Specifications**: See `realtime_api_node_specifications.md` for complete technical details.

---

## Architecture Summary

```
OpenAI Realtime API (WebSocket)
          ↓
RealtimeConnectionManager (shared)
          ↓
   ┌──────┴──────┐
   ↓             ↓             ↓
Speech Rec 22   AI 22    Speech Synth 22
   ↓             ↓             ↓
    Nevil Message Bus
```

### Key Benefits

- **6-10x faster** response times (5-13s → 800-2300ms)
- **Lower CPU** usage (15-25% → 10-15%)
- **No disk I/O** for temporary audio files
- **Real-time** audio streaming in both directions
- **Function calling** for robot actions
- **Auto-reconnection** on connection loss

---

## Component Overview

### 1. speech_recognition_node22

**Purpose**: Stream microphone audio to Realtime API for transcription

**Key Features**:
- Continuous audio streaming (24kHz PCM16)
- Real-time speech detection events
- Server-side VAD (Voice Activity Detection)
- Automatic start/stop on speaking status

**Main Events**:
- `input_audio_buffer.speech_started` → Speech detected
- `input_audio_buffer.speech_stopped` → Speech ended
- `conversation.item.input_audio_transcription.completed` → Publish `voice_command`

**Publishes**:
- `voice_command` - Transcribed speech
- `speech_detected` - Speech start/stop events
- `listening_status` - Streaming status

**Subscribes**:
- `speaking_status` - Pause/resume streaming
- `system_mode` - Mode-based streaming control

---

### 2. ai_node22

**Purpose**: Manage AI conversation and function calling

**Key Features**:
- Conversation context management
- Function calling for robot actions
- Multi-modal responses (text + audio)
- Automatic response generation

**Main Events**:
- `response.created` → AI started thinking
- `response.done` → AI finished, publish `text_response`
- `response.function_call_arguments.done` → Execute robot function

**Registered Functions**:
- `move_forward(distance, speed)` → Publish `robot_action`
- `turn(direction, angle)` → Publish `robot_action`
- `take_snapshot()` → Publish `snap_pic`
- `play_sound(sound_name)` → Publish `sound_effect`

**Publishes**:
- `text_response` - AI text responses
- `robot_action` - Function call → robot commands
- `snap_pic` - Camera requests
- `sound_effect` - Sound playback requests
- `system_mode` - Mode changes

**Subscribes**:
- `voice_command` - Voice input (compatibility)
- `visual_data` - Camera images for analysis

---

### 3. speech_synthesis_node22

**Purpose**: Play streaming audio from Realtime API

**Key Features**:
- Real-time audio chunk buffering
- Concurrent playback while receiving
- Transcript streaming for UI
- Auto-start on first chunk

**Main Events**:
- `response.audio.delta` → Buffer and play audio chunk
- `response.audio.done` → Audio generation complete
- `response.audio_transcript.delta` → Partial transcript
- `response.audio_transcript.done` → Complete transcript

**Publishes**:
- `speaking_status` - Playback status + transcript

**Subscribes**:
- `text_response` - Text responses (compatibility)
- `system_mode` - Mode-based playback control

---

## RealtimeConnectionManager

**Purpose**: Shared WebSocket connection manager

**Key Responsibilities**:
1. Establish and maintain WebSocket connection
2. Handle reconnection with exponential backoff
3. Route events to registered handlers
4. Send events from nodes to API
5. Provide connection statistics

**API**:
```python
# Registration
manager.register_event_handler('event_type', handler_function)
manager.unregister_event_handler('event_type')

# Sending events
manager.send_event({
    "type": "event_type",
    # ... event data
})

# Connection management
manager.start()  # Start connection
manager.stop()   # Stop connection
manager.get_stats()  # Get connection stats
```

**Reconnection Strategy**:
- Initial retry: 1 second
- Exponential backoff: 2x each attempt
- Max delay: 30 seconds
- Unlimited attempts while `reconnect_enabled=True`

---

## Configuration

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional (defaults shown)
export NEVIL_REALTIME_MODEL="gpt-4o-realtime-preview-2024-10-01"
```

### .messages Files

**speech_recognition22/.messages**:
```yaml
configuration:
  audio:
    sample_rate: 24000  # Required by API
    chunk_size: 4800    # 200ms chunks
    channels: 1
    format: "pcm16"
  realtime:
    enable_vad: true
    vad_threshold: 0.5
    vad_prefix_padding_ms: 300
    vad_silence_duration_ms: 500
```

**ai_cognition22/.messages**:
```yaml
configuration:
  ai:
    system_prompt: "You are Nevil..."
    voice: "alloy"
    temperature: 0.7
    max_tokens: 4096
    max_conversation_items: 50
  functions:
    enable_movement: true
    enable_camera: true
    enable_sounds: true
```

**speech_synthesis22/.messages**:
```yaml
configuration:
  audio:
    sample_rate: 24000
    channels: 1
    format: "pcm16"
    buffer_size: 100
  playback:
    start_threshold: 5  # Start after N chunks
    underrun_recovery: true
```

---

## Implementation Checklist

### Phase 1: Shared Infrastructure
- [ ] Implement `RealtimeConnectionManager`
- [ ] Implement `AudioStreamer` helper
- [ ] Implement `AudioPlayer` helper
- [ ] Add environment variable support
- [ ] Update launcher to create/inject manager

### Phase 2: Node Implementation
- [ ] Implement `speech_recognition_node22`
- [ ] Implement `ai_node22`
- [ ] Implement `speech_synthesis_node22`
- [ ] Create `.messages` configuration files
- [ ] Add to launcher node discovery

### Phase 3: Testing
- [ ] Unit tests for each node
- [ ] Integration test: voice → response cycle
- [ ] Stress test: connection reliability
- [ ] Performance benchmarking
- [ ] Load testing: rapid commands

### Phase 4: Deployment
- [ ] Update README with setup instructions
- [ ] Create migration guide
- [ ] Add troubleshooting guide
- [ ] Deploy and monitor

---

## Code Snippets

### Basic Event Handler Pattern

```python
def _on_event_name(self, event):
    """Handle event from Realtime API"""
    try:
        # Extract data from event
        data = event.get('data_field')

        # Process data
        result = self._process_data(data)

        # Publish to message bus
        self.publish("topic_name", {
            "field": result,
            "timestamp": time.time()
        })

    except Exception as e:
        self.logger.error(f"Error handling event: {e}")
        self.error_count += 1
```

### Registering Event Handlers

```python
def initialize(self):
    # Define handlers
    self.event_handlers = {
        'event.type.one': self._on_event_one,
        'event.type.two': self._on_event_two,
    }

    # Register with connection manager
    for event_type, handler in self.event_handlers.items():
        self.connection_manager.register_event_handler(event_type, handler)
```

### Sending Events to API

```python
# Update session configuration
self.connection_manager.send_event({
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "instructions": "System prompt...",
        "voice": "alloy"
    }
})

# Send audio buffer
self.connection_manager.send_event({
    "type": "input_audio_buffer.append",
    "audio": audio_base64
})

# Trigger response generation
self.connection_manager.send_event({
    "type": "response.create"
})
```

### Function Registration

```python
self.function_registry['function_name'] = {
    'description': 'What this function does',
    'parameters': {
        'type': 'object',
        'properties': {
            'param1': {
                'type': 'string',
                'description': 'Parameter description'
            }
        },
        'required': ['param1']
    },
    'handler': self._handle_function_name
}
```

### Function Handler

```python
def _handle_function_name(self, args):
    """Handle function call from AI"""
    param1 = args.get('param1')

    # Execute action
    self.publish("topic_name", {
        "data": param1,
        "timestamp": time.time()
    })

    # Return result to API
    return {
        "status": "success",
        "result": f"Executed with {param1}"
    }
```

---

## Common Patterns

### Audio Streaming Pattern

```python
def _audio_callback(self, in_data, frame_count, time_info, status):
    """PyAudio callback for continuous audio capture"""
    try:
        # Convert to base64
        audio_b64 = base64.b64encode(in_data).decode('utf-8')

        # Send to API
        self.connection_manager.send_event({
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        })

    except Exception as e:
        self.logger.error(f"Error in audio callback: {e}")

    return (in_data, pyaudio.paContinue)
```

### Audio Playback Pattern

```python
def _on_audio_delta(self, event):
    """Handle streaming audio chunk"""
    try:
        delta = event.get('delta', '')

        if not delta:
            return

        # Decode base64 audio
        audio_bytes = base64.b64decode(delta)

        # Add to playback buffer
        self.audio_buffer.put_nowait(audio_bytes)

    except queue.Full:
        self.logger.warning("Buffer full, dropping chunk")
    except Exception as e:
        self.logger.error(f"Error handling audio delta: {e}")
```

---

## Error Handling

### Connection Errors

```python
# In RealtimeConnectionManager
try:
    self.websocket = await websockets.connect(self.url, extra_headers=headers)
    self.connected = True
except Exception as e:
    self.logger.error(f"Connection failed: {e}")
    # Schedule reconnection
    await self._schedule_reconnect()
```

### Event Processing Errors

```python
try:
    # Process event
    result = self._process_event(event)
except Exception as e:
    self.logger.error(f"Event processing failed: {e}")
    self.error_count += 1
    # Continue processing other events
```

### Audio Errors

```python
try:
    self.audio_stream.write(audio_data)
except Exception as e:
    self.logger.error(f"Audio playback error: {e}")
    # Attempt stream recovery
    self._reinitialize_audio_stream()
```

---

## Performance Tuning

### Buffer Sizes

- **Audio Capture**: 4800 samples (200ms at 24kHz)
- **Audio Playback**: 100 chunks max in buffer
- **Playback Threshold**: Start after 5 chunks buffered

### Reconnection Settings

- **Initial Delay**: 1 second
- **Max Delay**: 30 seconds
- **Backoff Multiplier**: 2x per attempt

### WebSocket Settings

- **Max Message Size**: 10MB
- **Receive Timeout**: 1 second
- **Send Timeout**: 5 seconds

---

## Troubleshooting

### Issue: High latency

**Causes**:
- Network latency to OpenAI servers
- Audio buffer too large
- PyAudio buffer misconfigured

**Solutions**:
- Reduce `chunk_size` to 2400 (100ms)
- Reduce `buffer_size` to 50
- Lower `start_threshold` to 3

### Issue: Audio choppy/stuttering

**Causes**:
- Buffer underrun (not enough chunks buffered)
- CPU overload
- Network jitter

**Solutions**:
- Increase `start_threshold` to 10
- Increase `buffer_size` to 200
- Enable `underrun_recovery`

### Issue: Connection keeps dropping

**Causes**:
- Network instability
- API rate limiting
- Invalid API key

**Solutions**:
- Check network connectivity
- Verify API key
- Check OpenAI status page
- Review reconnection logs

### Issue: Transcription missing words

**Causes**:
- VAD too aggressive
- Low microphone volume
- Background noise

**Solutions**:
- Increase `vad_threshold` to 0.7
- Increase `vad_prefix_padding_ms` to 500
- Increase `vad_silence_duration_ms` to 1000

---

## Migration from Discrete Nodes

### Compatibility

All three Realtime nodes are **backward compatible** with existing message topics:

| Message Topic | Old Node | New Node | Compatible? |
|---------------|----------|----------|-------------|
| `voice_command` | speech_recognition | speech_recognition22 | ✓ |
| `text_response` | ai_cognition | ai_node22 | ✓ |
| `robot_action` | ai_cognition | ai_node22 | ✓ |
| `speaking_status` | speech_synthesis | speech_synthesis22 | ✓ |

### Migration Steps

1. **Backup existing configuration**:
   ```bash
   cp -r nodes/speech_recognition nodes/speech_recognition.backup
   cp -r nodes/ai_cognition nodes/ai_cognition.backup
   cp -r nodes/speech_synthesis nodes/speech_synthesis.backup
   ```

2. **Create new node directories**:
   ```bash
   mkdir -p nodes/speech_recognition22
   mkdir -p nodes/ai_cognition22
   mkdir -p nodes/speech_synthesis22
   ```

3. **Copy .messages templates** from specifications

4. **Update launcher configuration**:
   ```yaml
   # Comment out old nodes
   # - speech_recognition
   # - ai_cognition
   # - speech_synthesis

   # Add new nodes
   - speech_recognition22
   - ai_cognition22
   - speech_synthesis22
   ```

5. **Test with both sets of nodes** (different topics) before full migration

---

## Additional Resources

- **Full Specifications**: `realtime_api_node_specifications.md`
- **OpenAI Realtime API Docs**: https://platform.openai.com/docs/guides/realtime
- **WebSocket Docs**: https://websockets.readthedocs.io/
- **PyAudio Docs**: https://people.csail.mit.edu/hubert/pyaudio/docs/

---

**Last Updated**: 2025-11-11
**Version**: 1.0
