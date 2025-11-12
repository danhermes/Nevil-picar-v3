# RealtimeConnectionManager - Production-Ready Python Implementation

## Overview

The `RealtimeConnectionManager` is a production-ready Python WebSocket client for the OpenAI Realtime API, adapted from the battle-tested Blane3 TypeScript implementation. It provides robust connection management, auto-reconnection, and thread-safe operations fully integrated with Nevil's threading model.

## Key Features

### 1. Robust Connection Management
- **Async WebSocket**: Native Python asyncio with websockets library
- **Authentication**: Supports both API keys and ephemeral tokens
- **Auto-Reconnection**: Exponential backoff strategy (1s, 2s, 4s, 8s, 16s)
- **Connection States**: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED
- **Timeout Handling**: Configurable connection timeout with automatic recovery

### 2. Thread-Safe Operations
- **Background Event Loop**: Runs asyncio in dedicated thread
- **Thread-Safe Messaging**: Queue-based message sending from any thread
- **State Locking**: RLock protection for concurrent access
- **Nevil Integration**: Compatible with Nevil's NevilNode threading model

### 3. Event-Driven Architecture
- **Flexible Event Handlers**: Register callbacks for any event type
- **Async/Sync Support**: Handles both async and sync callbacks
- **Event Statistics**: Track event frequency and patterns
- **Multiple Handlers**: Support multiple callbacks per event

### 4. Message Queuing
- **Offline Queuing**: Messages queued when disconnected
- **Auto-Retry**: Queued messages sent on reconnection
- **Queue Management**: Configurable max size with overflow handling
- **Thread-Safe**: RLock protection for queue operations

### 5. Connection Metrics
- **Performance Tracking**: Connection attempts, messages sent/received
- **Uptime Monitoring**: Total uptime and connection timestamps
- **Reconnection Stats**: Track reconnection attempts and success rate
- **Real-Time Access**: Get metrics at any time

## Architecture

### Class Structure

```
RealtimeConnectionManager
├── Thread Management (Nevil Integration)
│   ├── start() - Start in background thread
│   ├── stop() - Clean shutdown
│   └── _run_event_loop() - Asyncio event loop
│
├── Connection Management
│   ├── connect() - Establish WebSocket connection
│   ├── _async_disconnect() - Clean disconnection
│   └── reconnect() - Auto-reconnection with backoff
│
├── WebSocket Event Handlers
│   ├── _handle_open() - Connection opened
│   ├── _receive_loop() - Message receiving
│   ├── _handle_message() - Message processing
│   ├── _handle_error() - Error handling
│   └── _handle_close() - Connection closed
│
├── Message Sending
│   ├── send() - Async message sending
│   ├── send_sync() - Thread-safe sync sending
│   ├── update_session() - Update session config
│   ├── append_input_audio() - Send audio data
│   ├── commit_input_audio() - Commit audio buffer
│   └── create_response() - Request AI response
│
└── Public API
    ├── on() - Subscribe to events
    ├── off() - Unsubscribe from events
    ├── once() - Subscribe once
    ├── get_metrics() - Connection metrics
    ├── get_event_stats() - Event statistics
    └── destroy() - Cleanup resources
```

### Supporting Classes

- **ConnectionState**: Enum for connection states
- **ConnectionConfig**: WebSocket connection settings
- **SessionConfig**: OpenAI session configuration
- **ConnectionMetrics**: Performance metrics dataclass
- **ReconnectOptions**: Reconnection attempt details
- **RealtimeEventHandler**: Event handling system

## Usage Examples

### Basic Usage

```python
from nevil_framework.realtime import (
    RealtimeConnectionManager,
    ConnectionConfig,
    SessionConfig
)

# Configure connection
config = ConnectionConfig(
    ephemeral_token="your_ephemeral_token",
    max_reconnect_attempts=5,
    reconnect_base_delay=1.0,
    connection_timeout=30.0
)

# Configure session
session_config = SessionConfig(
    model="gpt-4o-realtime-preview-2024-12-17",
    voice="alloy",
    modalities=["text", "audio"],
    temperature=0.8
)

# Create manager
manager = RealtimeConnectionManager(
    config=config,
    session_config=session_config,
    debug=True
)

# Register event handlers
manager.on('connect', lambda: print("Connected!"))
manager.on('disconnect', lambda reason: print(f"Disconnected: {reason}"))
manager.on('error', lambda error: print(f"Error: {error}"))

# Start connection in background thread
manager.start()

# Your application continues running...
# Manager handles connection automatically
```

### Factory Function (Simplified)

```python
from nevil_framework.realtime import create_realtime_connection

# Quick setup
manager = create_realtime_connection(
    ephemeral_token="your_token",
    model="gpt-4o-realtime-preview-2024-12-17",
    voice="alloy",
    debug=True
)

manager.start()
```

### Handling OpenAI Events

```python
# Audio response handler
def handle_audio_delta(event):
    audio_base64 = event.get('delta')
    if audio_base64:
        # Process audio chunk
        audio_data = base64.b64decode(audio_base64)
        play_audio(audio_data)

# Transcript handler
def handle_transcript(event):
    text = event.get('transcript')
    print(f"AI: {text}")

# Register handlers
manager.on('response.audio.delta', handle_audio_delta)
manager.on('response.audio_transcript.delta', handle_transcript)
manager.on('response.done', lambda e: print("Response complete"))

# Start connection
manager.start()
```

### Sending Messages (Thread-Safe)

```python
import base64

# Send audio (from any thread)
audio_data = record_audio()
audio_base64 = base64.b64encode(audio_data).decode('utf-8')

# Thread-safe sync send
manager.send_sync({
    'type': 'input_audio_buffer.append',
    'audio': audio_base64
})

# Commit audio and request response
manager.send_sync({'type': 'input_audio_buffer.commit'})
manager.send_sync({'type': 'response.create'})
```

### Async Usage

```python
import asyncio

async def send_audio_async():
    """Send audio using async methods"""
    audio_data = await record_audio_async()
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')

    await manager.append_input_audio(audio_base64)
    await manager.commit_input_audio()
    await manager.create_response()

# Schedule in manager's event loop
if manager.loop and manager.loop.is_running():
    asyncio.run_coroutine_threadsafe(send_audio_async(), manager.loop)
```

### Integration with Nevil Node

```python
from nevil_framework.base_node import NevilNode
from nevil_framework.realtime import create_realtime_connection

class RealtimeNode(NevilNode):
    """Nevil node with OpenAI Realtime integration"""

    def __init__(self):
        super().__init__("realtime_node")

        # Create connection manager
        self.realtime = create_realtime_connection(
            ephemeral_token=os.getenv('OPENAI_EPHEMERAL_TOKEN'),
            debug=True
        )

        # Setup event handlers
        self.realtime.on('connect', self.on_connect)
        self.realtime.on('response.audio.delta', self.on_audio)

        # Start connection
        self.realtime.start()

    def on_connect(self):
        """Handle connection established"""
        self.logger.info("Realtime API connected")

        # Publish to message bus
        self.publish('realtime/status', {'connected': True})

    def on_audio(self, event):
        """Handle audio response"""
        audio_base64 = event.get('delta')
        if audio_base64:
            # Publish audio to message bus
            self.publish('realtime/audio', {
                'audio': audio_base64,
                'timestamp': time.time()
            })

    def run(self):
        """Main node loop"""
        while not self.shutdown_event.is_set():
            # Check for audio input messages
            msg = self.get_message('audio/input', timeout=0.1)
            if msg:
                # Send to OpenAI Realtime API
                self.realtime.send_sync({
                    'type': 'input_audio_buffer.append',
                    'audio': msg.data['audio']
                })

    def cleanup(self):
        """Cleanup on shutdown"""
        self.realtime.destroy()
        super().cleanup()
```

### Monitoring Metrics

```python
import time

# Monitor connection status
while True:
    metrics = manager.get_metrics()

    print(f"State: {metrics['current_state']}")
    print(f"Connected: {metrics['is_connected']}")
    print(f"Uptime: {metrics['total_uptime']:.1f}s")
    print(f"Messages sent: {metrics['messages_sent']}")
    print(f"Messages received: {metrics['messages_received']}")
    print(f"Reconnect attempts: {metrics['reconnect_attempts']}")

    # Event statistics
    event_stats = manager.get_event_stats()
    print(f"Event stats: {event_stats}")

    time.sleep(5)
```

### Error Handling

```python
# Global error handler
def handle_error(error):
    logger.error(f"Realtime API error: {error}")

    # Check if we should alert
    metrics = manager.get_metrics()
    if metrics['reconnect_attempts'] > 3:
        send_alert("Realtime API struggling to connect")

manager.on('error', handle_error)

# Reconnection monitoring
def handle_reconnecting(options):
    logger.warning(
        f"Reconnecting... attempt {options.attempt}/{options.max_attempts}, "
        f"delay: {options.delay}s, reason: {options.reason}"
    )

manager.on('reconnecting', handle_reconnecting)

# State change monitoring
def handle_state_change(data):
    logger.info(f"State: {data['from'].value} -> {data['to'].value}")

    if data['to'].value == 'failed':
        logger.critical("Connection failed!")
        # Implement fallback strategy

manager.on('state_change', handle_state_change)
```

## Configuration

### ConnectionConfig

```python
@dataclass
class ConnectionConfig:
    api_key: Optional[str] = None              # OpenAI API key
    ephemeral_token: Optional[str] = None      # Ephemeral token (recommended)
    url: str = 'wss://api.openai.com/v1/realtime'
    max_reconnect_attempts: int = 5            # Max reconnection tries
    reconnect_base_delay: float = 1.0          # Base delay in seconds
    connection_timeout: float = 30.0           # Connection timeout
```

### SessionConfig

```python
@dataclass
class SessionConfig:
    model: str = "gpt-4o-realtime-preview-2024-12-17"
    modalities: List[str] = ["text", "audio"]
    instructions: Optional[str] = None         # System instructions
    voice: str = "alloy"                       # Voice: alloy, echo, shimmer
    input_audio_format: str = "pcm16"          # Audio format
    output_audio_format: str = "pcm16"
    temperature: float = 0.8
    max_response_output_tokens: Union[int, str] = "inf"
    turn_detection: Optional[Dict[str, Any]] = None
    tools: Optional[List[Dict[str, Any]]] = None
```

## Event Types

### Connection Events
- `connect` - Connection established
- `disconnect(reason)` - Connection closed
- `reconnecting(options)` - Reconnection attempt
- `state_change(data)` - State transition
- `error(error)` - Error occurred

### OpenAI Realtime API Events
- `session.created` - Session initialized
- `session.updated` - Session configuration updated
- `input_audio_buffer.committed` - Audio buffer committed
- `response.created` - Response generation started
- `response.audio.delta` - Audio chunk received
- `response.audio_transcript.delta` - Transcript chunk
- `response.done` - Response complete
- `conversation.item.created` - New conversation item
- And many more... (see OpenAI Realtime API docs)

## Best Practices

### 1. Use Ephemeral Tokens
```python
# ✅ GOOD: Use ephemeral tokens for security
config = ConnectionConfig(ephemeral_token="eph-...")

# ❌ AVOID: Direct API key usage (less secure)
config = ConnectionConfig(api_key="sk-...")
```

### 2. Monitor Connection Health
```python
# Check connection state before operations
if manager.is_connected():
    manager.send_sync(message)
else:
    logger.warning("Not connected, message queued")
```

### 3. Handle Reconnections Gracefully
```python
# Let auto-reconnection handle temporary failures
manager.on('reconnecting', lambda opts:
    logger.info(f"Reconnecting (attempt {opts.attempt})"))

# Only alert on permanent failure
manager.on('error', lambda e:
    alert_team(e) if "Max reconnection" in str(e) else None)
```

### 4. Clean Shutdown
```python
# Always cleanup on exit
try:
    manager.start()
    run_application()
finally:
    manager.destroy()  # Closes connection, removes handlers
```

### 5. Thread-Safe Messaging
```python
# Use send_sync() from synchronous code
def send_from_thread():
    manager.send_sync({'type': 'ping'})

# Use send() from async code
async def send_from_async():
    await manager.send({'type': 'ping'})
```

## Performance Considerations

### Message Queue Size
- Default: 100 messages
- Increase for high-volume applications
- Monitor queue depth via `len(manager.message_queue)`

### Reconnection Strategy
- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
- Adjust `reconnect_base_delay` for faster/slower retry
- Set `max_reconnect_attempts` based on criticality

### Event Loop Thread
- Dedicated thread prevents blocking main application
- All async operations run in this thread
- Use `send_sync()` for thread-safe access

## Troubleshooting

### Connection Fails Immediately
```python
# Check authentication
manager.on('error', lambda e: print(f"Auth error: {e}"))

# Verify token/key is valid
# Check network connectivity
# Ensure URL is correct
```

### Messages Not Sending
```python
# Check connection state
print(manager.get_state())

# Check message queue
print(f"Queued: {len(manager.message_queue)}")

# Enable debug mode
manager.debug = True
```

### Memory Leaks
```python
# Always remove handlers when done
manager.off('event', handler)

# Or destroy entire manager
manager.destroy()
```

### High Reconnection Rate
```python
# Monitor reconnection attempts
metrics = manager.get_metrics()
if metrics['reconnect_attempts'] > 10:
    # Possible network issues or API problems
    logger.critical("Excessive reconnections")
```

## Testing

Run the comprehensive test suite:

```bash
python -m pytest tests/realtime/test_connection_manager.py -v
```

Test coverage includes:
- ✅ Initialization and configuration
- ✅ Event subscription/unsubscription
- ✅ State management
- ✅ Message queuing and overflow
- ✅ Authentication validation
- ✅ URL construction
- ✅ Thread safety
- ✅ Metrics tracking
- ✅ Async operations
- ✅ Cleanup and resource management

## Migration from Blane3

The Python implementation maintains API compatibility with Blane3:

| Blane3 (TypeScript) | Nevil (Python) |
|---------------------|----------------|
| `new RealtimeClient(options)` | `RealtimeConnectionManager(config, session_config)` |
| `client.connect()` | `manager.start()` |
| `client.disconnect(reason)` | `manager.stop(reason)` |
| `client.send(message)` | `manager.send_sync(message)` |
| `client.on(event, handler)` | `manager.on(event, handler)` |
| `client.getMetrics()` | `manager.get_metrics()` |

## License

Part of the Nevil framework. Adapted from Blane3 with permission.

## Support

For issues or questions:
- Check logs with `debug=True`
- Review metrics with `get_metrics()`
- See test suite for examples
- Consult OpenAI Realtime API documentation
