# Audio Capture Manager - Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
# System dependencies (Raspberry Pi)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio

# Python dependencies
pip install -r requirements.txt
```

### 2. Basic Test

```python
from nevil_framework.realtime.audio_capture_manager import create_audio_capture
import time

# Create and initialize
manager = create_audio_capture()

# Record for 5 seconds
manager.start_recording()
time.sleep(5)
manager.stop_recording()

# Print stats
print(manager.get_stats())

# Cleanup
manager.dispose()
```

### 3. With Realtime API

```python
from nevil_framework.realtime.audio_capture_manager import create_audio_capture
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager
import os

# Setup connection
connection = RealtimeConnectionManager(api_key=os.getenv('OPENAI_API_KEY'))
connection.start()

# Setup audio capture (automatically streams to API)
manager = create_audio_capture(connection_manager=connection, vad_enabled=True)

# Record
manager.start_recording()
time.sleep(30)
manager.stop_recording()

# Cleanup
manager.dispose()
connection.stop()
```

## Common Patterns

### Voice Activity Detection

```python
config = AudioCaptureConfig(
    vad_enabled=True,
    vad_threshold=0.02  # Adjust for environment
)

callbacks = AudioCaptureCallbacks(
    on_vad_speech_start=lambda: print("Speech!"),
    on_vad_speech_end=lambda: print("Silence")
)

manager = AudioCaptureManager(config=config, callbacks=callbacks)
```

### Volume Monitoring

```python
def show_volume(volume):
    bar = "█" * int(volume * 50)
    print(f"\rVolume: {bar} {volume:.2f}", end="", flush=True)

callbacks = AudioCaptureCallbacks(on_volume_change=show_volume)
manager = AudioCaptureManager(callbacks=callbacks)
```

### Error Handling

```python
def handle_error(error):
    logging.error(f"Audio error: {error}")
    # Implement recovery logic

callbacks = AudioCaptureCallbacks(on_error=handle_error)
manager = AudioCaptureManager(callbacks=callbacks)
```

## Configuration Cheat Sheet

| Parameter | Default | Description |
|-----------|---------|-------------|
| sample_rate | 24000 | Hz (Realtime API requirement) |
| channel_count | 1 | Mono (1) or Stereo (2) |
| chunk_size | 4800 | Samples per chunk (200ms) |
| buffer_size | 4096 | PyAudio internal buffer |
| vad_enabled | False | Voice Activity Detection |
| vad_threshold | 0.02 | VAD trigger level (0.0-1.0) |
| auto_flush_ms | 200 | Auto-flush interval |

## Troubleshooting

### No audio device
```bash
# List devices
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'[{i}] {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count()) if p.get_device_info_by_index(i)['maxInputChannels']>0]"
```

### High CPU usage
- Increase `buffer_size` to 8192
- Enable `vad_enabled=True`

### High latency
- Decrease `buffer_size` to 2048
- Decrease `chunk_size` to 2400

### VAD not working
- Lower `vad_threshold` to 0.01
- Check microphone sensitivity

## Examples

See `/home/dan/Nevil-picar-v3/examples/realtime_audio_capture_example.py` for complete examples:

1. Basic audio capture
2. VAD-enabled capture
3. Realtime API integration
4. Device selection

Run with:
```bash
python examples/realtime_audio_capture_example.py
```

## Resources

- Full Documentation: `docs/audio_capture_manager.md`
- Test Suite: `tests/realtime/test_audio_capture_manager.py`
- Connection Manager: `nevil_framework/realtime/realtime_connection_manager.py`
