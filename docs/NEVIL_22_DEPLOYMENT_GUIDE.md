# Nevil 2.2 Deployment Guide

Complete guide for deploying Nevil 2.2 with OpenAI Realtime API integration.

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Testing Procedures](#testing-procedures)
5. [Rollback Procedures](#rollback-procedures)
6. [Troubleshooting](#troubleshooting)
7. [Performance Tuning](#performance-tuning)

---

## Overview

### What is Nevil 2.2?

Nevil 2.2 introduces OpenAI's Realtime API integration, providing:
- **90-93% latency reduction** (5-8s → 500ms response time)
- **Native voice-to-voice conversation** (no intermediate text)
- **Streaming audio** for natural interactions
- **Hybrid mode** supporting both v3.0 and v2.2 systems

### Architecture Changes

```
Nevil v3.0                          Nevil 2.2
┌─────────────────┐                ┌─────────────────┐
│ Speech Recognition│               │ Speech Recognition│
│  (Google STT)    │               │  (Realtime API)  │
└────────┬─────────┘               └────────┬─────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐
│  AI Cognition   │                │  AI Cognition   │
│  (GPT-4 Text)   │◄──────────────►│ (Realtime API)  │
└────────┬─────────┘                └────────┬─────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────┐                ┌─────────────────┐
│ Speech Synthesis│                │ Speech Synthesis│
│  (OpenAI TTS)   │                │  (Realtime API) │
└─────────────────┘                └─────────────────┘

Total: 5-8s latency                Total: 300-500ms latency
```

### Deployment Strategy

- **Incremental**: Deploy alongside v3.0 (hybrid mode)
- **Reversible**: Complete rollback capability
- **Validated**: Comprehensive testing at each step
- **Safe**: Automatic backups before changes

---

## Pre-Deployment Checklist

### System Requirements

- [ ] **Python**: 3.9 or higher
- [ ] **Operating System**: Linux (Raspberry Pi OS recommended)
- [ ] **Memory**: 2GB+ RAM available
- [ ] **Storage**: 500MB+ free space
- [ ] **Network**: Stable internet connection (for API calls)

### Software Dependencies

- [ ] **Core Python packages**:
  - PyYAML >= 6.0
  - python-dateutil >= 2.8.0

- [ ] **Audio packages**:
  - SpeechRecognition >= 3.10.0
  - openai >= 1.0.0
  - pygame >= 2.5.0
  - pyaudio >= 0.2.11 (Linux only)

- [ ] **Realtime API packages**:
  - websockets >= 10.0
  - aiohttp >= 3.9.0
  - numpy >= 1.24.0
  - python-dotenv >= 1.0.0

### Hardware Requirements (Raspberry Pi)

- [ ] **Microphone**: USB or HAT-connected, 24kHz capable
- [ ] **Speaker**: Audio output device
- [ ] **Robot HAT**: If using navigation/motor features
- [ ] **Camera**: If using visual features (optional)

### Configuration

- [ ] **OpenAI API Key**: Active subscription with Realtime API access
- [ ] **Environment File**: `.env` with proper configuration
- [ ] **Node Configuration**: `.nodes` file properly set up
- [ ] **Backup Space**: Room for system backups

### Verification Commands

```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check dependencies
python3 -c "import websockets, aiohttp, numpy, openai"

# Check audio hardware (Linux)
arecord -l  # Should show input devices
aplay -l    # Should show output devices

# Check API key format
echo $OPENAI_API_KEY  # Should start with sk-

# Check disk space
df -h .  # Should have 500MB+ available
```

---

## Step-by-Step Deployment

### Phase 1: Setup (10 minutes)

#### 1.1 Run Setup Script

```bash
cd /home/dan/Nevil-picar-v3

# Run setup script
./scripts/setup_nevil_2.2.sh
```

**What it does:**
- Creates directory structure
- Generates RealtimeConnectionManager scaffold
- Creates environment template
- Backs up existing system
- Updates requirements.txt

**Expected output:**
```
✅ Nevil 2.2 Setup Complete!
📁 Files Created:
   • nevil_framework/realtime/realtime_connection_manager.py
   • .env.realtime (configuration template)
   ...
```

#### 1.2 Configure Environment

```bash
# Copy template
cp .env.realtime .env

# Edit configuration
nano .env
```

**Required settings:**
```bash
# Set your API key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Verify other settings (defaults usually work)
NEVIL_REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01
NEVIL_REALTIME_VOICE=alloy
NEVIL_AUDIO_SAMPLE_RATE=24000
```

**Voice options:**
- `alloy` - Neutral, balanced
- `echo` - Male, clear
- `fable` - British accent
- `onyx` - Deep, authoritative
- `nova` - Female, energetic
- `shimmer` - Soft, warm

#### 1.3 Install Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Verify installation
python3 -c "import websockets, aiohttp, numpy; print('✓ Dependencies OK')"
```

### Phase 2: Validation (5 minutes)

#### 2.1 Run Validation Script

```bash
./scripts/validate_nevil_22.sh --verbose
```

**What it checks:**
- Python environment
- Package dependencies
- File structure
- Configuration files
- API key validity
- Audio hardware (if on Pi)
- Import tests

**Success criteria:**
```
✓ All critical checks passed!

Next steps:
  1. Review any warnings above
  2. Configure API key in .env if not already done
  3. Run deployment script: ./scripts/deploy_nevil_22.sh
```

#### 2.2 Review Validation Report

```bash
# Find latest report
ls -t validation_report_*.txt | head -1

# Review report
cat validation_report_*.txt
```

**Fix any errors before proceeding.**

### Phase 3: Implementation (Development Phase)

This phase is where you implement the actual node logic. The setup script created scaffolds, but nodes need implementation.

#### 3.1 Implement RealtimeConnectionManager

Location: `nevil_framework/realtime/realtime_connection_manager.py`

**TODO items to complete:**
- Add timeout configuration
- Add connection validation
- Add SSL/TLS verification options
- Add event validation
- Add error event handling
- Add metrics collection
- Add async handler support
- Add send queue for offline messages
- And more (see file for complete list)

**Estimated time**: 8-10 hours

#### 3.2 Implement Speech Recognition Node

Location: `nodes/speech_recognition_realtime/speech_recognition_node.py`

**Key features needed:**
- Audio capture (24kHz PCM16)
- WebSocket integration
- VAD (Voice Activity Detection)
- Event handling
- Error recovery

**Reference**: `docs/speech_recognition_node22_implementation.md`

**Estimated time**: 6-8 hours

#### 3.3 Implement AI Cognition Node

Location: `nodes/ai_cognition_realtime/ai_cognition_node.py`

**Key features needed:**
- Conversation management
- Response streaming
- Function calling integration
- Context preservation
- Audio response handling

**Reference**: `docs/ai_node22_realtime_api.md`

**Estimated time**: 8-10 hours

#### 3.4 Implement Speech Synthesis Node

Location: `nodes/speech_synthesis_realtime/speech_synthesis_node.py`

**Key features needed:**
- Audio playback (24kHz PCM16)
- Buffer management
- Interruption handling
- Queue management

**Estimated time**: 4-6 hours

### Phase 4: Deployment (5 minutes)

#### 4.1 Pre-deployment Check

```bash
# Verify all implementations are in place
ls -l nodes/speech_recognition_realtime/speech_recognition_node.py
ls -l nodes/ai_cognition_realtime/ai_cognition_node.py
ls -l nodes/speech_synthesis_realtime/speech_synthesis_node.py

# Run validation again
./scripts/validate_nevil_22.sh
```

#### 4.2 Dry Run Deployment

```bash
# See what will happen without making changes
./scripts/deploy_nevil_22.sh --dry-run
```

Review the output to ensure it matches expectations.

#### 4.3 Execute Deployment

```bash
# Deploy with automatic backup
./scripts/deploy_nevil_22.sh

# Or skip confirmation prompts
./scripts/deploy_nevil_22.sh --force
```

**What it does:**
1. Validates pre-conditions
2. Backs up current v3.0 system
3. Deploys realtime nodes
4. Updates configuration
5. Creates symbolic links
6. Validates deployment
7. Generates deployment report

**Expected output:**
```
✓ Deployment completed successfully!

Backup: backups/nevil_v3_YYYYMMDD_HHMMSS
Report: deployment_report_YYYYMMDD_HHMMSS.txt

Next steps:
  1. Configure OPENAI_API_KEY in .env
  2. Review deployment report
  3. Run validation
  4. Test: ./nevil start
```

#### 4.4 Update .nodes Configuration

Edit `.nodes` to include realtime nodes:

```yaml
launch:
  # Hybrid mode: v3.0 + v2.2 nodes
  startup_order: [
    "led_indicator",
    "speech_recognition",           # v3.0 fallback
    "speech_recognition_realtime",  # v2.2 primary
    "speech_synthesis",             # v3.0 fallback
    "speech_synthesis_realtime",    # v2.2 primary
    "ai_cognition",                 # v3.0 fallback
    "ai_cognition_realtime",        # v2.2 primary
    "navigation",
    "visual"
  ]
  parallel_launch: false
  wait_for_healthy: true
  ready_timeout: 30.0
```

For **v2.2 only mode** (after testing):
```yaml
launch:
  startup_order: [
    "led_indicator",
    "speech_recognition_realtime",
    "ai_cognition_realtime",
    "speech_synthesis_realtime",
    "navigation",
    "visual"
  ]
```

---

## Testing Procedures

### Unit Testing

#### Test RealtimeConnectionManager

```bash
# Create test file
cat > tests/realtime/test_connection_manager.py << 'EOF'
import unittest
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

class TestRealtimeConnectionManager(unittest.TestCase):
    def test_initialization(self):
        manager = RealtimeConnectionManager(api_key="test-key")
        self.assertIsNotNone(manager)
        self.assertEqual(manager.model, "gpt-4o-realtime-preview-2024-10-01")

    def test_event_handler_registration(self):
        manager = RealtimeConnectionManager(api_key="test-key")
        handler = lambda x: None
        manager.register_event_handler("test.event", handler)
        self.assertIn("test.event", manager.event_handlers)

if __name__ == "__main__":
    unittest.main()
EOF

# Run test
python3 -m pytest tests/realtime/test_connection_manager.py -v
```

#### Test Node Imports

```bash
# Test all nodes can be imported
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from nodes.speech_recognition_realtime import speech_recognition_node
    print("✓ Speech recognition node imports OK")
except Exception as e:
    print(f"✗ Speech recognition import failed: {e}")

try:
    from nodes.ai_cognition_realtime import ai_cognition_node
    print("✓ AI cognition node imports OK")
except Exception as e:
    print(f"✗ AI cognition import failed: {e}")

try:
    from nodes.speech_synthesis_realtime import speech_synthesis_node
    print("✓ Speech synthesis node imports OK")
except Exception as e:
    print(f"✗ Speech synthesis import failed: {e}")
EOF
```

### Integration Testing

#### Test Basic Connectivity

```bash
# Test WebSocket connection
python3 << 'EOF'
import os
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("✗ OPENAI_API_KEY not set")
    exit(1)

manager = RealtimeConnectionManager(api_key=api_key)
manager.start()

import time
time.sleep(5)  # Wait for connection

stats = manager.get_stats()
if stats['connected']:
    print("✓ Successfully connected to Realtime API")
else:
    print("✗ Failed to connect to Realtime API")

manager.stop()
EOF
```

#### Test Audio Pipeline

```bash
# Test audio capture (Linux only)
python3 << 'EOF'
import pyaudio

p = pyaudio.PyAudio()
try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=24000,
        input=True,
        frames_per_buffer=4800
    )
    print("✓ Audio capture working")
    stream.close()
except Exception as e:
    print(f"✗ Audio capture failed: {e}")
finally:
    p.terminate()
EOF
```

### System Testing

#### Test Nevil Startup

```bash
# Start Nevil in test mode
./nevil start

# Check logs
tail -f logs/nevil.log

# Look for:
# - "RealtimeConnectionManager initialized"
# - "WebSocket connected successfully"
# - All nodes showing "Ready"
```

#### Test Voice Interaction

1. **Start Nevil**: `./nevil start`
2. **Speak to robot**: Say "Hello Nevil"
3. **Observe latency**: Should respond in < 1 second
4. **Check audio quality**: Voice should be clear
5. **Test interruption**: Try speaking while it responds
6. **Check logs**: Review for errors

Expected behavior:
- Fast response (300-500ms)
- Natural voice
- Proper interruption handling
- No stuttering or audio glitches

### Performance Testing

#### Measure Latency

```bash
# Create latency test script
cat > tests/realtime/test_latency.py << 'EOF'
import time
import os
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

def test_response_latency():
    """Measure end-to-end response latency"""
    api_key = os.getenv("OPENAI_API_KEY")
    manager = RealtimeConnectionManager(api_key=api_key)
    manager.start()

    # Wait for connection
    time.sleep(2)

    # Measure response time
    start = time.time()

    # Send text input event
    manager.send_event({
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello"}]
        }
    })

    # Trigger response
    manager.send_event({"type": "response.create"})

    # Wait for response (simplified - needs event handler)
    time.sleep(1)

    latency = time.time() - start
    print(f"Response latency: {latency*1000:.0f}ms")

    manager.stop()

    assert latency < 1.0, "Latency too high"

if __name__ == "__main__":
    test_response_latency()
EOF

# Run latency test
python3 tests/realtime/test_latency.py
```

Expected results:
- **v3.0 baseline**: 5000-8000ms
- **v2.2 target**: 300-500ms
- **Improvement**: 90-93% reduction

---

## Rollback Procedures

### Automatic Rollback (Recommended)

If deployment fails or issues arise:

```bash
# Find latest backup
ls -lt backups/ | head -5

# Identify backup timestamp
BACKUP_ID=YYYYMMDD_HHMMSS

# Stop Nevil
./nevil stop

# Restore from backup
cp -r backups/nevil_v3_$BACKUP_ID/nodes/* nodes/
cp backups/nevil_v3_$BACKUP_ID/.nodes.backup .nodes
cp backups/nevil_v3_$BACKUP_ID/.env.backup .env

# Restart
./nevil start
```

### Manual Rollback

If automatic rollback isn't available:

#### 1. Stop System

```bash
./nevil stop
```

#### 2. Remove Realtime Nodes

```bash
rm -rf nodes/speech_recognition_realtime
rm -rf nodes/ai_cognition_realtime
rm -rf nodes/speech_synthesis_realtime
```

#### 3. Restore v3.0 Configuration

Edit `.nodes` to remove realtime nodes:

```yaml
launch:
  startup_order: [
    "led_indicator",
    "speech_recognition",
    "speech_synthesis",
    "ai_cognition",
    "navigation",
    "visual"
  ]
```

#### 4. Restore Environment

```bash
# If you have old .env
cp .env.v3_backup .env

# Or set manually
export OPENAI_API_KEY=your-key-here
```

#### 5. Reinstall v3.0 Dependencies

```bash
# Remove v2.2 specific packages (optional)
pip3 uninstall websockets aiohttp

# Verify v3.0 packages
pip3 install -r requirements.txt
```

#### 6. Restart System

```bash
./nevil start
```

#### 7. Verify Operation

```bash
# Check logs
tail -f logs/nevil.log

# Test basic operation
# Speak to robot and verify response
```

### Verification After Rollback

- [ ] All v3.0 nodes start successfully
- [ ] Speech recognition works
- [ ] AI responses are correct
- [ ] Speech synthesis works
- [ ] Navigation functions (if applicable)
- [ ] No errors in logs

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Fails

**Symptoms:**
```
ERROR: WebSocket connection failed
ERROR: Cannot connect to wss://api.openai.com/v1/realtime
```

**Solutions:**

```bash
# Check API key
echo $OPENAI_API_KEY  # Should start with sk-

# Test connection manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check firewall
sudo iptables -L | grep 443

# Check network
ping api.openai.com
```

#### 2. Audio Capture Not Working

**Symptoms:**
```
ERROR: Could not open audio stream
ERROR: pyaudio.PyAudioError
```

**Solutions:**

```bash
# List audio devices
arecord -l

# Test microphone
arecord -D hw:1,0 -f S16_LE -r 24000 -c 1 -d 5 test.wav
aplay test.wav

# Check permissions
groups $USER  # Should include 'audio'
sudo usermod -a -G audio $USER

# Restart ALSA
sudo systemctl restart alsa-restore
```

#### 3. Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'websockets'
ImportError: cannot import name 'RealtimeConnectionManager'
```

**Solutions:**

```bash
# Reinstall dependencies
pip3 install --upgrade websockets aiohttp numpy openai

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Verify installation
pip3 list | grep websockets

# Try alternative Python
python --version
python -m pip install websockets
```

#### 4. High Latency

**Symptoms:**
- Responses take > 1 second
- Audio stuttering
- Delays between speech and response

**Solutions:**

```bash
# Check network latency
ping -c 10 api.openai.com

# Check system load
top
free -h

# Reduce buffer size in .env
NEVIL_AUDIO_CHUNK_SIZE=2400  # Reduce from 4800
NEVIL_AUDIO_BUFFER_SIZE=50   # Reduce from 100

# Check for CPU throttling (Raspberry Pi)
vcgencmd measure_temp
vcgencmd get_throttled
```

#### 5. API Rate Limiting

**Symptoms:**
```
ERROR: Rate limit exceeded
ERROR: 429 Too Many Requests
```

**Solutions:**

```bash
# Check API usage
# Visit: https://platform.openai.com/usage

# Add retry logic
# Edit connection manager to handle 429

# Reduce request frequency
# Add delays between requests

# Upgrade API tier
# Visit: https://platform.openai.com/account/billing
```

#### 6. Node Won't Start

**Symptoms:**
```
ERROR: Node failed to start
ERROR: speech_recognition_realtime not responding
```

**Solutions:**

```bash
# Check logs
cat logs/speech_recognition_realtime.log

# Test node manually
python3 nodes/speech_recognition_realtime/speech_recognition_node.py

# Verify dependencies
python3 -c "from nodes.speech_recognition_realtime import speech_recognition_node"

# Check .nodes configuration
cat .nodes | grep speech_recognition_realtime

# Increase timeout
# Edit .nodes: ready_timeout: 60.0
```

### Debugging Tools

#### Enable Verbose Logging

Edit `.env`:
```bash
LOG_LEVEL=DEBUG
NEVIL_REALTIME_DEBUG=true
```

#### Monitor WebSocket Traffic

```bash
# Install websocket debugging tool
pip3 install websocket-client

# Create debug script
cat > debug_ws.py << 'EOF'
import os
import websocket

def on_message(ws, message):
    print(f"<<< {message}")

def on_error(ws, error):
    print(f"!!! {error}")

def on_open(ws):
    print(">>> Connected")

api_key = os.getenv("OPENAI_API_KEY")
ws = websocket.WebSocketApp(
    f"wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
    header={"Authorization": f"Bearer {api_key}", "OpenAI-Beta": "realtime=v1"},
    on_message=on_message,
    on_error=on_error,
    on_open=on_open
)
ws.run_forever()
EOF

# Run debug
python3 debug_ws.py
```

#### Audio Pipeline Testing

```bash
# Test full audio pipeline
cat > test_audio_pipeline.sh << 'EOF'
#!/bin/bash

echo "Testing audio capture..."
arecord -D hw:1,0 -f S16_LE -r 24000 -c 1 -d 3 test_input.wav
echo "✓ Captured 3s of audio"

echo "Testing audio playback..."
aplay test_input.wav
echo "✓ Played back audio"

echo "Testing format conversion..."
python3 << 'PYEOF'
import wave
import numpy as np

# Read WAV
with wave.open("test_input.wav", "rb") as wf:
    frames = wf.readframes(wf.getnframes())
    audio = np.frombuffer(frames, dtype=np.int16)
    print(f"✓ Audio shape: {audio.shape}")
    print(f"✓ Sample rate: {wf.getframerate()}Hz")
    print(f"✓ Channels: {wf.getnchannels()}")
PYEOF

rm test_input.wav
echo "✓ Audio pipeline test complete"
EOF

chmod +x test_audio_pipeline.sh
./test_audio_pipeline.sh
```

### Getting Help

#### Log Files

```bash
# Main log
tail -f logs/nevil.log

# Node-specific logs
tail -f logs/speech_recognition_realtime.log
tail -f logs/ai_cognition_realtime.log
tail -f logs/speech_synthesis_realtime.log

# System logs (Raspberry Pi)
sudo journalctl -u nevil.service -f
```

#### Diagnostic Report

```bash
# Generate diagnostic report
cat > generate_diagnostic.sh << 'EOF'
#!/bin/bash

REPORT="diagnostic_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "Nevil 2.2 Diagnostic Report"
    echo "Generated: $(date)"
    echo ""

    echo "=== System Info ==="
    uname -a
    echo ""

    echo "=== Python Info ==="
    python3 --version
    pip3 --version
    echo ""

    echo "=== Packages ==="
    pip3 list | grep -E "(websockets|aiohttp|numpy|openai|pyaudio)"
    echo ""

    echo "=== Audio Devices ==="
    arecord -l 2>/dev/null || echo "N/A"
    echo ""

    echo "=== File Structure ==="
    find nodes/*/realtime -type f 2>/dev/null
    echo ""

    echo "=== Configuration ==="
    cat .nodes | grep -A 10 "launch:"
    echo ""

    echo "=== Recent Logs ==="
    tail -50 logs/nevil.log 2>/dev/null || echo "No log file"
    echo ""

    echo "=== Environment ==="
    env | grep -E "(OPENAI|NEVIL)" | sed 's/\(API_KEY=\).*/\1***REDACTED***/'

} > "$REPORT"

echo "Diagnostic report saved: $REPORT"
EOF

chmod +x generate_diagnostic.sh
./generate_diagnostic.sh
```

#### Community Resources

- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory (if available)
- **OpenAI Docs**: https://platform.openai.com/docs/guides/realtime
- **Issues**: GitHub issues or project-specific tracker

---

## Performance Tuning

### Optimize Latency

#### 1. Reduce Buffer Sizes

Edit `.env`:
```bash
# Smaller chunks = lower latency, higher CPU
NEVIL_AUDIO_CHUNK_SIZE=2400  # Default: 4800
NEVIL_AUDIO_BUFFER_SIZE=50   # Default: 100
NEVIL_AUDIO_PLAYBACK_THRESHOLD=3  # Default: 5
```

#### 2. Adjust Voice Activity Detection

```python
# In speech_recognition_node.py
VAD_CONFIG = {
    'threshold': 0.5,      # Lower = more sensitive
    'min_silence': 0.3,    # Shorter = faster cutoff
    'min_speech': 0.5,     # Shorter = quicker response
}
```

#### 3. Enable Parallel Processing

Edit `.nodes`:
```yaml
launch:
  parallel_launch: true  # Start nodes in parallel
  ready_timeout: 15.0    # Reduce timeout
```

#### 4. Optimize Network

```bash
# Increase network priority (Linux)
sudo sysctl -w net.ipv4.tcp_low_latency=1

# Use faster DNS
echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
```

### Optimize Audio Quality

#### 1. Use Better Codec

Edit `.env`:
```bash
# Higher quality audio
NEVIL_AUDIO_FORMAT=pcm24  # Default: pcm16
NEVIL_AUDIO_SAMPLE_RATE=48000  # Default: 24000

# Note: May increase latency and bandwidth
```

#### 2. Adjust Voice Settings

Edit `.env`:
```bash
# Different voices have different qualities
NEVIL_REALTIME_VOICE=nova    # Clear, energetic
NEVIL_REALTIME_VOICE=shimmer # Soft, warm
```

#### 3. Enable Audio Processing

```python
# In audio capture manager
import numpy as np

def process_audio(audio_data):
    # Noise reduction
    audio_data = reduce_noise(audio_data)

    # Normalization
    audio_data = audio_data / np.max(np.abs(audio_data))

    # High-pass filter (remove rumble)
    audio_data = high_pass_filter(audio_data, cutoff=80)

    return audio_data
```

### Optimize Resource Usage

#### 1. Monitor Resources

```bash
# Install monitoring
sudo apt-get install htop iotop

# Real-time monitoring
htop

# Check I/O
sudo iotop
```

#### 2. Limit CPU Usage

```python
# In node initialization
import os
os.nice(10)  # Lower priority for background tasks
```

#### 3. Manage Memory

Edit `.env`:
```bash
# Limit buffer memory
NEVIL_MAX_BUFFER_SIZE=50  # MB
NEVIL_CLEANUP_INTERVAL=60  # seconds
```

### Benchmarking

#### Create Benchmark Script

```bash
cat > benchmark_nevil.py << 'EOF'
import time
import statistics
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager

def benchmark_latency(iterations=10):
    """Measure average response latency"""
    latencies = []

    # Setup
    manager = RealtimeConnectionManager(api_key=os.getenv("OPENAI_API_KEY"))
    manager.start()
    time.sleep(2)

    for i in range(iterations):
        start = time.time()

        # Send request
        manager.send_event({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}]
            }
        })
        manager.send_event({"type": "response.create"})

        # Wait for response (simplified)
        time.sleep(1)

        latency = time.time() - start
        latencies.append(latency * 1000)  # Convert to ms

        print(f"Iteration {i+1}: {latency*1000:.0f}ms")
        time.sleep(1)  # Cool down

    manager.stop()

    # Statistics
    print(f"\nResults ({iterations} iterations):")
    print(f"  Mean: {statistics.mean(latencies):.0f}ms")
    print(f"  Median: {statistics.median(latencies):.0f}ms")
    print(f"  Min: {min(latencies):.0f}ms")
    print(f"  Max: {max(latencies):.0f}ms")
    print(f"  StdDev: {statistics.stdev(latencies):.0f}ms")

if __name__ == "__main__":
    benchmark_latency()
EOF

python3 benchmark_nevil.py
```

---

## Appendix

### A. File Checklist

After deployment, verify these files exist:

#### Framework Files
- [ ] `nevil_framework/realtime/__init__.py`
- [ ] `nevil_framework/realtime/realtime_connection_manager.py`

#### Node Files
- [ ] `nodes/speech_recognition_realtime/__init__.py`
- [ ] `nodes/speech_recognition_realtime/speech_recognition_node.py`
- [ ] `nodes/ai_cognition_realtime/__init__.py`
- [ ] `nodes/ai_cognition_realtime/ai_cognition_node.py`
- [ ] `nodes/speech_synthesis_realtime/__init__.py`
- [ ] `nodes/speech_synthesis_realtime/speech_synthesis_node.py`

#### Configuration Files
- [ ] `.env` (with OPENAI_API_KEY)
- [ ] `.nodes` (with realtime nodes)
- [ ] `requirements.txt` (with realtime packages)

#### Documentation Files
- [ ] `docs/NEVIL_2.2_QUICK_START.md`
- [ ] `docs/NEVIL_2.2_DEPLOYMENT_GUIDE.md`
- [ ] `docs/realtime_api_node_specifications.md`

### B. Environment Variables Reference

```bash
# Required
OPENAI_API_KEY=sk-...

# Realtime API
NEVIL_REALTIME_MODEL=gpt-4o-realtime-preview-2024-10-01
NEVIL_REALTIME_VOICE=alloy
NEVIL_REALTIME_TEMPERATURE=0.8
NEVIL_REALTIME_MAX_TOKENS=4096

# Audio
NEVIL_AUDIO_SAMPLE_RATE=24000
NEVIL_AUDIO_CHANNELS=1
NEVIL_AUDIO_FORMAT=pcm16
NEVIL_AUDIO_CHUNK_SIZE=4800

# Performance
NEVIL_REALTIME_RECONNECT_DELAY=1.0
NEVIL_REALTIME_MAX_RECONNECTS=5
NEVIL_AUDIO_BUFFER_SIZE=100
NEVIL_AUDIO_PLAYBACK_THRESHOLD=5

# Features
NEVIL_REALTIME_ENABLED=true
NEVIL_HYBRID_MODE=true
NEVIL_REALTIME_PERCENTAGE=10
```

### C. Quick Command Reference

```bash
# Setup
./scripts/setup_nevil_2.2.sh

# Validation
./scripts/validate_nevil_22.sh
./scripts/validate_nevil_22.sh --verbose
./scripts/validate_nevil_22.sh --skip-tests

# Deployment
./scripts/deploy_nevil_22.sh
./scripts/deploy_nevil_22.sh --dry-run
./scripts/deploy_nevil_22.sh --force
./scripts/deploy_nevil_22.sh --no-backup

# Operation
./nevil start
./nevil stop
./nevil status
./nevil logs

# Testing
python3 -m pytest tests/realtime/ -v
python3 benchmark_nevil.py

# Debugging
tail -f logs/nevil.log
./generate_diagnostic.sh
```

---

## Conclusion

This deployment guide covers the complete process of deploying Nevil 2.2. Follow each phase carefully, validate at every step, and don't hesitate to rollback if issues arise.

**Key Success Factors:**
- Thorough pre-deployment validation
- Careful implementation of TODO items
- Comprehensive testing at each phase
- Having rollback plan ready
- Monitoring performance metrics

**Expected Results:**
- 90-93% latency reduction
- Natural voice interactions
- Robust error handling
- Easy rollback capability

For additional support, refer to:
- `docs/NEVIL_2.2_ZERO_TOUCH_PLAN.md`
- `docs/realtime_api_node_specifications.md`
- OpenAI Realtime API documentation
