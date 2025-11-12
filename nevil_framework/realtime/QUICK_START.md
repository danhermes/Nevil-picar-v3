# Quick Start Guide - RealtimeConnectionManager

## 5-Minute Setup

### 1. Get Your Token

```bash
# Get ephemeral token from OpenAI
export OPENAI_EPHEMERAL_TOKEN="eph-your-token-here"
```

### 2. Basic Connection

```python
from nevil_framework.realtime import create_realtime_connection

# Create and start
manager = create_realtime_connection(
    ephemeral_token="eph-...",
    debug=True
)

# Add handler
manager.on('connect', lambda: print("✅ Connected!"))

# Start connection
manager.start()
```

### 3. Send a Message

```python
# Text message
manager.send_sync({
    'type': 'conversation.item.create',
    'item': {
        'type': 'message',
        'role': 'user',
        'content': [{'type': 'input_text', 'text': 'Hello!'}]
    }
})

# Request response
manager.send_sync({'type': 'response.create'})
```

### 4. Handle Responses

```python
def on_transcript(event):
    print(f"AI: {event.get('transcript', '')}")

def on_audio(event):
    audio_data = base64.b64decode(event.get('delta', ''))
    # Play audio...

manager.on('response.audio_transcript.delta', on_transcript)
manager.on('response.audio.delta', on_audio)
```

### 5. Cleanup

```python
# When done
manager.destroy()
```

## Common Patterns

### Pattern 1: Voice Conversation

```python
import base64

# Send audio
audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
manager.send_sync({
    'type': 'input_audio_buffer.append',
    'audio': audio_base64
})
manager.send_sync({'type': 'input_audio_buffer.commit'})
manager.send_sync({'type': 'response.create'})

# Receive audio
def handle_audio(event):
    audio = base64.b64decode(event['delta'])
    play_audio(audio)

manager.on('response.audio.delta', handle_audio)
```

### Pattern 2: Text Chat

```python
def ask(question):
    manager.send_sync({
        'type': 'conversation.item.create',
        'item': {
            'type': 'message',
            'role': 'user',
            'content': [{'type': 'input_text', 'text': question}]
        }
    })
    manager.send_sync({'type': 'response.create'})

# Usage
ask("What is the capital of France?")
```

### Pattern 3: Monitor Status

```python
import time

while True:
    metrics = manager.get_metrics()
    print(f"State: {metrics['current_state']}")
    print(f"Messages: {metrics['messages_sent']}/{metrics['messages_received']}")
    time.sleep(5)
```

### Pattern 4: Error Handling

```python
def on_error(error):
    print(f"❌ Error: {error}")

def on_reconnecting(opts):
    print(f"🔄 Reconnecting... attempt {opts.attempt}")

manager.on('error', on_error)
manager.on('reconnecting', on_reconnecting)
```

### Pattern 5: Integration with Nevil Node

```python
from nevil_framework.base_node import NevilNode

class VoiceNode(NevilNode):
    def __init__(self):
        super().__init__("voice_node")
        self.realtime = create_realtime_connection(
            ephemeral_token=os.getenv('OPENAI_EPHEMERAL_TOKEN')
        )
        self.realtime.on('response.audio.delta', self.on_audio)
        self.realtime.start()

    def on_audio(self, event):
        self.publish('audio/output', {'data': event['delta']})

    def cleanup(self):
        self.realtime.destroy()
```

## Event Quick Reference

### Connection Events
- `connect` - Connected successfully
- `disconnect` - Connection closed
- `reconnecting` - Attempting reconnection
- `error` - Error occurred

### Common OpenAI Events
- `session.created` - Session ready
- `response.created` - Response started
- `response.audio.delta` - Audio chunk
- `response.audio_transcript.delta` - Transcript chunk
- `response.done` - Response complete

## Configuration Cheat Sheet

```python
from nevil_framework.realtime import (
    ConnectionConfig,
    SessionConfig,
    RealtimeConnectionManager
)

# Full configuration
config = ConnectionConfig(
    ephemeral_token="eph-...",
    max_reconnect_attempts=5,
    reconnect_base_delay=1.0,
    connection_timeout=30.0
)

session = SessionConfig(
    model="gpt-4o-realtime-preview-2024-12-17",
    voice="alloy",  # alloy, echo, shimmer
    temperature=0.8,
    modalities=["text", "audio"]
)

manager = RealtimeConnectionManager(
    config=config,
    session_config=session,
    debug=True
)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Won't connect | Check token, enable `debug=True` |
| Messages not sending | Check `manager.is_connected()` |
| High memory | Check queue: `len(manager.message_queue)` |
| Frequent disconnects | Monitor `get_metrics()['reconnect_attempts']` |

## Full Example

```python
#!/usr/bin/env python3
import os
import time
from nevil_framework.realtime import create_realtime_connection

# Setup
manager = create_realtime_connection(
    ephemeral_token=os.getenv('OPENAI_EPHEMERAL_TOKEN'),
    debug=True
)

# Handlers
manager.on('connect', lambda: print("✅ Connected"))
manager.on('disconnect', lambda r: print(f"❌ Disconnected: {r}"))
manager.on('response.audio_transcript.delta',
    lambda e: print(f"AI: {e.get('delta', '')}"))

# Start
manager.start()

# Wait for connection
time.sleep(2)

# Send message
if manager.is_connected():
    manager.send_sync({
        'type': 'conversation.item.create',
        'item': {
            'type': 'message',
            'role': 'user',
            'content': [{'type': 'input_text', 'text': 'Hello!'}]
        }
    })
    manager.send_sync({'type': 'response.create'})

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    manager.destroy()
```

## Learn More

- **Full Docs**: `/home/dan/Nevil-picar-v3/docs/realtime_connection_manager.md`
- **Module README**: `/home/dan/Nevil-picar-v3/nevil_framework/realtime/README.md`
- **Complete Example**: `/home/dan/Nevil-picar-v3/examples/realtime_connection_example.py`
- **Tests**: `/home/dan/Nevil-picar-v3/tests/realtime/test_connection_manager.py`
