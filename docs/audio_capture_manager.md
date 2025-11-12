# AudioCaptureManager Documentation

## Overview

The `AudioCaptureManager` is a production-ready Python module for capturing audio from microphones on Raspberry Pi hardware and streaming it to the OpenAI Realtime API. It provides thread-safe operation, voice activity detection (VAD), and comprehensive error handling.

## Features

- **Realtime API Compliance**: Configured for 24kHz mono PCM16 format
- **PyAudio Integration**: Native support for Raspberry Pi Linux audio
- **Thread-Safe Operation**: Proper synchronization for concurrent access
- **Voice Activity Detection**: Optional VAD to reduce bandwidth
- **Streaming Support**: Direct integration with WebSocket connection
- **Comprehensive Callbacks**: Monitor audio data, volume, state changes, and errors
- **Auto-Flush Buffer**: Prevents audio buffer overflow
- **Statistics Tracking**: Monitor samples processed, chunks sent, and more

## Installation

### Requirements

```bash
# Install system dependencies (Raspberry Pi)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Install Python dependencies
pip install -r requirements.txt
```

### Required Packages

- `pyaudio>=0.2.11` - Audio capture interface
- `numpy>=1.24.0` - Audio processing
- `websockets>=10.0` - WebSocket communication (for Realtime API)

## Quick Start

### Basic Usage

```python
from nevil_framework.realtime.audio_capture_manager import (
    AudioCaptureManager,
    AudioCaptureConfig,
    AudioCaptureCallbacks
)

# Define callbacks
def on_audio_data(base64_audio: str, volume: float):
    print(f"Audio: {len(base64_audio)} bytes, Volume: {volume:.3f}")

callbacks = AudioCaptureCallbacks(on_audio_data=on_audio_data)

# Create and initialize manager
config = AudioCaptureConfig()
manager = AudioCaptureManager(config=config, callbacks=callbacks)
manager.initialize()

# Start recording
manager.start_recording()
time.sleep(10)  # Record for 10 seconds
manager.stop_recording()

# Cleanup
manager.dispose()
```

### With Connection Manager

```python
from nevil_framework.realtime.audio_capture_manager import create_audio_capture
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

# Create connection
connection = RealtimeConnectionManager(api_key="your-api-key")
connection.start()

# Create audio capture with automatic integration
manager = create_audio_capture(
    connection_manager=connection,
    vad_enabled=True
)

# Start recording (audio automatically streams to API)
manager.start_recording()
```

## Configuration

### AudioCaptureConfig

Configuration class for audio capture settings.

```python
config = AudioCaptureConfig(
    sample_rate=24000,        # Hz (24kHz for Realtime API)
    channel_count=1,          # Mono (1) or Stereo (2)
    chunk_size=4800,          # Samples per chunk (200ms at 24kHz)
    buffer_size=4096,         # PyAudio buffer size
    device_index=None,        # Audio device (None = default)
    vad_enabled=False,        # Enable Voice Activity Detection
    vad_threshold=0.02,       # VAD volume threshold (0.0-1.0)
    auto_flush_ms=200         # Auto-flush interval (ms)
)
```

#### Parameters

- **sample_rate** (int): Audio sample rate in Hz
  - Default: 24000 (required for OpenAI Realtime API)
  - Other options: 16000, 22050, 44100, 48000

- **channel_count** (int): Number of audio channels
  - Default: 1 (mono, required for Realtime API)
  - Other: 2 (stereo, not supported by Realtime API)

- **chunk_size** (int): Number of samples per processing chunk
  - Default: 4800 (200ms at 24kHz)
  - Formula: `sample_rate * duration_seconds`
  - Example: 4800 = 24000 * 0.2 (200ms)

- **buffer_size** (int): PyAudio internal buffer size
  - Default: 4096
  - Larger = more latency, less CPU usage
  - Smaller = less latency, more CPU usage

- **device_index** (Optional[int]): Specific audio device index
  - Default: None (use system default device)
  - Use `list_audio_devices()` to find available devices

- **vad_enabled** (bool): Enable Voice Activity Detection
  - Default: False
  - When enabled, only sends audio when speech detected

- **vad_threshold** (float): Volume threshold for VAD
  - Default: 0.02 (2% of max volume)
  - Range: 0.0 to 1.0
  - Lower = more sensitive (triggers on quieter sounds)
  - Higher = less sensitive (only triggers on louder sounds)

- **auto_flush_ms** (int): Automatic buffer flush interval
  - Default: 200 (milliseconds)
  - Prevents buffer from growing indefinitely
  - Flushes buffered audio if not sent within this time

### AudioCaptureCallbacks

Callback functions for audio events.

```python
callbacks = AudioCaptureCallbacks(
    on_audio_data=audio_data_handler,
    on_volume_change=volume_change_handler,
    on_error=error_handler,
    on_state_change=state_change_handler,
    on_vad_speech_start=speech_start_handler,
    on_vad_speech_end=speech_end_handler
)
```

#### Callback Functions

**on_audio_data(base64_audio: str, volume: float)**
- Called when audio chunk is ready to send
- `base64_audio`: Base64-encoded PCM16 audio data
- `volume`: Volume level (0.0 to 1.0, RMS)

**on_volume_change(volume: float)**
- Called on volume level changes
- `volume`: Current volume level (0.0 to 1.0)
- Useful for volume meters

**on_error(error: Exception)**
- Called when error occurs
- `error`: Exception object with error details

**on_state_change(state: CaptureState)**
- Called when capture state changes
- `state`: New state (INACTIVE, RECORDING, PAUSED)

**on_vad_speech_start()**
- Called when speech detected (VAD enabled)
- Signals start of speech activity

**on_vad_speech_end()**
- Called when speech ends (VAD enabled)
- Signals end of speech activity

## API Reference

### AudioCaptureManager

Main class for managing audio capture.

#### Methods

##### `__init__(config, callbacks, connection_manager)`

Initialize audio capture manager.

```python
manager = AudioCaptureManager(
    config=config,
    callbacks=callbacks,
    connection_manager=connection_manager
)
```

##### `initialize()`

Initialize PyAudio and prepare for capture. Must be called before recording.

```python
manager.initialize()
```

**Raises:**
- `Exception`: If initialization fails (no audio device, etc.)

##### `start_recording()`

Start recording audio from microphone.

```python
manager.start_recording()
```

**Raises:**
- `RuntimeError`: If not initialized or already recording

##### `stop_recording()`

Stop recording and flush remaining audio.

```python
manager.stop_recording()
```

##### `pause()`

Pause recording (audio still captured but not processed).

```python
manager.pause()
```

##### `resume()`

Resume recording after pause.

```python
manager.resume()
```

##### `flush()`

Manually flush buffered audio.

```python
manager.flush()
```

##### `get_current_volume()`

Get current volume level.

```python
volume = manager.get_current_volume()  # Returns 0.0 to 1.0
```

##### `get_state()`

Get current capture state.

```python
state = manager.get_state()  # Returns CaptureState enum
```

##### `get_stats()`

Get capture statistics.

```python
stats = manager.get_stats()
# Returns:
# {
#     "state": "recording",
#     "is_recording": True,
#     "is_paused": False,
#     "total_samples": 48000,
#     "total_chunks": 10,
#     "buffer_samples": 1200,
#     "buffer_ms": 50.0,
#     "vad_enabled": True,
#     "vad_speech_active": True,
#     "sample_rate": 24000,
#     "channels": 1
# }
```

##### `set_callbacks(callbacks)`

Update callbacks.

```python
manager.set_callbacks(new_callbacks)
```

##### `dispose()`

Clean up all resources.

```python
manager.dispose()
```

### Convenience Functions

#### `create_audio_capture()`

Create and initialize AudioCaptureManager with common defaults.

```python
manager = create_audio_capture(
    connection_manager=connection_manager,
    sample_rate=24000,
    vad_enabled=False,
    **kwargs  # Additional config parameters
)
```

**Parameters:**
- `connection_manager`: RealtimeConnectionManager instance
- `sample_rate`: Audio sample rate (default: 24000)
- `vad_enabled`: Enable VAD (default: False)
- `**kwargs`: Additional AudioCaptureConfig parameters

**Returns:**
- Initialized AudioCaptureManager instance

## Usage Examples

### Example 1: Basic Audio Capture

```python
from nevil_framework.realtime.audio_capture_manager import (
    AudioCaptureManager,
    AudioCaptureConfig,
    AudioCaptureCallbacks
)

def on_audio(base64_audio, volume):
    print(f"Audio: {len(base64_audio)} bytes, Volume: {volume:.3f}")

config = AudioCaptureConfig()
callbacks = AudioCaptureCallbacks(on_audio_data=on_audio)
manager = AudioCaptureManager(config=config, callbacks=callbacks)

manager.initialize()
manager.start_recording()
time.sleep(10)
manager.stop_recording()
manager.dispose()
```

### Example 2: Voice Activity Detection

```python
config = AudioCaptureConfig(
    vad_enabled=True,
    vad_threshold=0.02
)

def on_speech_start():
    print("Speech detected!")

def on_speech_end():
    print("Silence detected")

callbacks = AudioCaptureCallbacks(
    on_vad_speech_start=on_speech_start,
    on_vad_speech_end=on_speech_end
)

manager = AudioCaptureManager(config=config, callbacks=callbacks)
manager.initialize()
manager.start_recording()
```

### Example 3: Volume Meter

```python
def on_volume_change(volume):
    # Create visual volume meter
    bar_length = int(volume * 50)
    bar = "█" * bar_length + "░" * (50 - bar_length)
    print(f"\rVolume: {bar} {volume:.3f}", end="", flush=True)

callbacks = AudioCaptureCallbacks(on_volume_change=on_volume_change)
manager = AudioCaptureManager(callbacks=callbacks)
manager.initialize()
manager.start_recording()
```

### Example 4: Full Realtime API Integration

```python
from nevil_framework.realtime.audio_capture_manager import create_audio_capture
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

# Create connection
connection = RealtimeConnectionManager(api_key=os.getenv('OPENAI_API_KEY'))
connection.start()

# Configure session
connection.send_event({
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "input_audio_format": "pcm16",
        "voice": "alloy"
    }
})

# Create audio capture
manager = create_audio_capture(
    connection_manager=connection,
    vad_enabled=True
)

# Start recording (automatically streams to API)
manager.start_recording()
time.sleep(30)
manager.stop_recording()

# Cleanup
manager.dispose()
connection.stop()
```

### Example 5: Device Selection

```python
import pyaudio

# List available devices
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"[{i}] {info['name']}")
audio.terminate()

# Use specific device
config = AudioCaptureConfig(device_index=2)  # Use device 2
manager = AudioCaptureManager(config=config)
```

## Audio Format Specifications

### OpenAI Realtime API Requirements

The AudioCaptureManager is configured to meet OpenAI Realtime API specifications:

- **Sample Rate**: 24000 Hz (24 kHz)
- **Channels**: 1 (mono)
- **Format**: PCM16 (16-bit signed integers)
- **Encoding**: Base64-encoded
- **Chunk Size**: 4800 samples (200ms at 24kHz)

### Audio Processing Pipeline

1. **Capture**: PyAudio reads audio from microphone
2. **Convert**: Int16 → Float32 (-1.0 to 1.0)
3. **Process**: Calculate volume, run VAD
4. **Buffer**: Accumulate samples until chunk size reached
5. **Encode**: Float32 → PCM16 → Base64
6. **Send**: Stream to WebSocket or callback

### Data Flow

```
Microphone → PyAudio → NumPy Array → Buffer
                                         ↓
                                      Chunk Ready?
                                         ↓
                                    PCM16 Encoding
                                         ↓
                                   Base64 Encoding
                                         ↓
                              Callback / WebSocket
```

## Threading Model

The AudioCaptureManager uses a dedicated processing thread:

- **Main Thread**: Application logic, control methods
- **Processing Thread**: Continuous audio capture and processing
- **Thread-Safe**: All methods use locks for synchronization

### Thread Safety

All public methods are thread-safe:

```python
# Safe to call from any thread
manager.start_recording()
manager.pause()
manager.get_stats()
manager.flush()
```

## Performance Considerations

### CPU Usage

- **Typical**: 5-10% on Raspberry Pi 4
- **With VAD**: +2-3% overhead
- **Buffer Size**: Larger = less CPU, more latency

### Memory Usage

- **Base**: ~10 MB
- **Buffer**: ~1 MB per second of buffered audio
- **Auto-Flush**: Prevents memory growth

### Latency

- **Capture Latency**: ~100ms (buffer_size=4096)
- **Processing Latency**: <10ms
- **Total Latency**: ~110-150ms

### Optimization Tips

1. **Adjust buffer_size**: Larger for lower CPU, smaller for lower latency
2. **Use VAD**: Reduces bandwidth and API costs
3. **Tune chunk_size**: Larger chunks = more efficient, more latency
4. **Monitor stats**: Use `get_stats()` to track performance

## Troubleshooting

### No Audio Device Found

```python
# List available devices
import pyaudio
audio = pyaudio.PyAudio()
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"[{i}] {info['name']}")
audio.terminate()
```

### Buffer Overflow Errors

- Increase `buffer_size` in config
- Reduce `chunk_size` for faster processing
- Enable `vad_enabled` to skip silence

### High Latency

- Decrease `buffer_size` (e.g., 2048)
- Decrease `chunk_size` (e.g., 2400 = 100ms)
- Ensure system is not under heavy load

### VAD Not Triggering

- Lower `vad_threshold` (e.g., 0.01)
- Check microphone sensitivity
- Verify ambient noise levels

### Audio Quality Issues

- Verify sample rate matches hardware capabilities
- Check for buffer overflows in logs
- Test with different `buffer_size` values

## Best Practices

1. **Always call initialize()** before start_recording()
2. **Always call dispose()** when done (use try/finally)
3. **Use VAD** to reduce bandwidth and costs
4. **Monitor statistics** for performance tuning
5. **Handle errors** in callbacks appropriately
6. **Test audio levels** before production use
7. **Use connection_manager** for seamless integration

## Error Handling

```python
try:
    manager = create_audio_capture()
    manager.start_recording()
    time.sleep(10)
except RuntimeError as e:
    print(f"Initialization error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    manager.stop_recording()
    manager.dispose()
```

## License

Part of the Nevil v3.0 Framework
