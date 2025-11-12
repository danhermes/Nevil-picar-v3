# AudioCaptureManager Integration Guide

## Quick Integration with Nevil

This guide shows how to integrate the AudioCaptureManager into your Nevil robot project.

## Step 1: Basic Setup

```python
#!/usr/bin/env python3
"""
Nevil with Realtime API Audio Capture
"""

import os
import time
import logging
from dotenv import load_dotenv

from nevil_framework.realtime import (
    create_audio_capture,
    create_realtime_connection
)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env")

# Create connection
connection = create_realtime_connection(api_key=api_key)

# Create audio capture
audio = create_audio_capture(
    connection_manager=connection,
    vad_enabled=True
)

# Start conversation
connection.start()
time.sleep(1)  # Wait for connection

audio.start_recording()
logger.info("Listening... speak to Nevil!")

# Let it run
time.sleep(30)

# Cleanup
audio.stop_recording()
audio.dispose()
connection.stop()
```

## Step 2: Integration with Nevil Main Loop

### Option A: Simple Integration

Add to your existing Nevil main script:

```python
from nevil_framework.realtime import create_audio_capture, RealtimeConnectionManager

class NevilRobot:
    def __init__(self):
        # Existing Nevil initialization
        self.robot_hat = RobotHat()
        self.music = Music()

        # Add Realtime API
        self.connection = RealtimeConnectionManager(api_key=os.getenv('OPENAI_API_KEY'))
        self.audio_capture = create_audio_capture(
            connection_manager=self.connection,
            vad_enabled=True
        )

        # Register event handlers
        self.connection.register_event_handler('response.audio.delta', self.on_audio_response)
        self.connection.register_event_handler('response.text.delta', self.on_text_response)

    def start(self):
        """Start Nevil with Realtime API"""
        self.connection.start()
        self.audio_capture.start_recording()
        logger.info("Nevil listening with Realtime API")

    def stop(self):
        """Stop Nevil"""
        self.audio_capture.stop_recording()
        self.audio_capture.dispose()
        self.connection.stop()

    def on_audio_response(self, event):
        """Handle audio response from API"""
        audio_data = event.get('delta', '')
        # TODO: Play audio through robot_hat.Music()

    def on_text_response(self, event):
        """Handle text response from API"""
        text = event.get('delta', '')
        logger.info(f"Assistant: {text}")
```

### Option B: Advanced Integration with State Machine

```python
from enum import Enum
from nevil_framework.realtime import (
    create_audio_capture,
    RealtimeConnectionManager,
    CaptureState
)

class NevilState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"

class NevilWithRealtime:
    def __init__(self):
        self.state = NevilState.IDLE

        # Realtime API setup
        self.connection = RealtimeConnectionManager(api_key=os.getenv('OPENAI_API_KEY'))
        self.audio_capture = create_audio_capture(
            connection_manager=self.connection,
            vad_enabled=True
        )

        # Register callbacks
        self.audio_capture.set_callbacks(AudioCaptureCallbacks(
            on_vad_speech_start=self.on_speech_start,
            on_vad_speech_end=self.on_speech_end,
            on_error=self.on_audio_error
        ))

        self.connection.register_event_handler('response.audio.delta', self.on_assistant_audio)
        self.connection.register_event_handler('response.done', self.on_response_done)
        self.connection.register_event_handler('error', self.on_api_error)

    def on_speech_start(self):
        """User started speaking"""
        self.state = NevilState.LISTENING
        logger.info("User speaking...")

    def on_speech_end(self):
        """User stopped speaking"""
        logger.info("User finished")
        # Commit audio to API
        self.connection.send_event({
            "type": "input_audio_buffer.commit"
        })
        self.state = NevilState.PROCESSING

    def on_assistant_audio(self, event):
        """Assistant is speaking"""
        self.state = NevilState.SPEAKING
        audio_delta = event.get('delta', '')
        # TODO: Buffer and play audio

    def on_response_done(self, event):
        """Assistant finished response"""
        self.state = NevilState.IDLE
        logger.info("Response complete")

    def on_audio_error(self, error):
        """Handle audio capture errors"""
        logger.error(f"Audio error: {error}")
        self.state = NevilState.IDLE

    def on_api_error(self, event):
        """Handle API errors"""
        logger.error(f"API error: {event}")
        self.state = NevilState.IDLE

    def run(self):
        """Main loop"""
        try:
            self.connection.start()
            self.audio_capture.start_recording()

            logger.info("Nevil ready!")

            while True:
                # Monitor state and stats
                if self.state == NevilState.IDLE:
                    # Could show idle animation
                    pass
                elif self.state == NevilState.LISTENING:
                    # Show listening animation
                    pass
                elif self.state == NevilState.SPEAKING:
                    # Show speaking animation
                    pass

                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.audio_capture.stop_recording()
            self.audio_capture.dispose()
            self.connection.stop()
```

## Step 3: Configuration for Nevil Hardware

Create a configuration file:

```python
# nevil_config.py
from nevil_framework.realtime import AudioCaptureConfig

# Optimized for Raspberry Pi 4 with USB microphone
NEVIL_AUDIO_CONFIG = AudioCaptureConfig(
    sample_rate=24000,        # Required by Realtime API
    channel_count=1,          # Mono
    chunk_size=4800,          # 200ms chunks
    buffer_size=4096,         # Good balance for RPi
    device_index=None,        # Use default (or specify if multiple mics)
    vad_enabled=True,         # Enable to save bandwidth
    vad_threshold=0.02,       # May need tuning for environment
    auto_flush_ms=200         # Prevent buffer buildup
)

# Session configuration for Realtime API
NEVIL_SESSION_CONFIG = {
    "modalities": ["text", "audio"],
    "instructions": (
        "You are Nevil, a friendly robot assistant. "
        "You can see through your camera, move around, and interact with people. "
        "Be helpful, curious, and express personality."
    ),
    "voice": "alloy",
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
    }
}
```

Use in your code:

```python
from nevil_config import NEVIL_AUDIO_CONFIG, NEVIL_SESSION_CONFIG

# Create with custom config
audio = AudioCaptureManager(config=NEVIL_AUDIO_CONFIG)

# Configure session
connection.send_event({
    "type": "session.update",
    "session": NEVIL_SESSION_CONFIG
})
```

## Step 4: Testing on Raspberry Pi

### Test 1: Hardware Check

```bash
# Check audio devices
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'[{i}] {info[\"name\"]}')
"
```

### Test 2: Basic Capture

```bash
python examples/realtime_audio_capture_example.py
# Select option 1 (Basic capture)
```

### Test 3: VAD Testing

```bash
python examples/realtime_audio_capture_example.py
# Select option 2 (VAD capture)
```

### Test 4: Full Integration

```bash
python examples/realtime_audio_capture_example.py
# Select option 3 (Realtime API)
```

## Step 5: Troubleshooting

### No Audio Device

```bash
# List USB devices
lsusb

# Check ALSA devices
arecord -l

# Test recording
arecord -d 5 -f cd test.wav
aplay test.wav
```

### VAD Not Triggering

Lower the threshold:

```python
config = AudioCaptureConfig(
    vad_enabled=True,
    vad_threshold=0.01  # More sensitive
)
```

### High Latency

Reduce buffer sizes:

```python
config = AudioCaptureConfig(
    buffer_size=2048,  # Lower latency
    chunk_size=2400    # 100ms chunks
)
```

### CPU Usage Too High

Increase buffer size:

```python
config = AudioCaptureConfig(
    buffer_size=8192,  # Less CPU
    vad_enabled=True   # Skip silence
)
```

## Step 6: Production Deployment

### Systemd Service

Create `/etc/systemd/system/nevil-realtime.service`:

```ini
[Unit]
Description=Nevil Realtime Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Nevil-picar-v3
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /home/pi/Nevil-picar-v3/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable nevil-realtime
sudo systemctl start nevil-realtime
sudo systemctl status nevil-realtime
```

### Logging

Add to your script:

```python
import logging
from logging.handlers import RotatingFileHandler

# Setup logging
handler = RotatingFileHandler(
    'nevil_realtime.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Monitoring

Monitor performance:

```python
# In main loop
stats = audio_capture.get_stats()
conn_stats = connection.get_stats()

logger.info(f"Audio: {stats['total_chunks']} chunks, {stats['buffer_ms']:.1f}ms buffered")
logger.info(f"Connection: {conn_stats['messages_sent']} sent, {conn_stats['messages_received']} received")
```

## Best Practices

1. **Always initialize before use:**
   ```python
   audio.initialize()
   ```

2. **Always cleanup:**
   ```python
   try:
       audio.start_recording()
       # ... do work ...
   finally:
       audio.stop_recording()
       audio.dispose()
   ```

3. **Handle errors:**
   ```python
   callbacks = AudioCaptureCallbacks(
       on_error=lambda e: logger.error(f"Audio error: {e}")
   )
   ```

4. **Monitor statistics:**
   ```python
   stats = audio.get_stats()
   if stats['buffer_ms'] > 1000:
       logger.warning("Audio buffer growing too large!")
   ```

5. **Tune VAD for your environment:**
   ```python
   # Test different thresholds
   for threshold in [0.01, 0.02, 0.03]:
       config.vad_threshold = threshold
       # Test and observe
   ```

## Examples Repository

All examples are in: `/home/dan/Nevil-picar-v3/examples/`

- `realtime_audio_capture_example.py` - Interactive examples
- More examples coming soon!

## Support

- Documentation: `/home/dan/Nevil-picar-v3/docs/audio_capture_manager.md`
- Quick Start: `/home/dan/Nevil-picar-v3/docs/AUDIO_CAPTURE_QUICK_START.md`
- Tests: `/home/dan/Nevil-picar-v3/tests/realtime/test_audio_capture_manager.py`
