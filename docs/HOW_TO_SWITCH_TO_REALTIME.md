# How to Switch Nevil to Realtime API (v2.2)

## Quick Switch

To switch from v3.0 (batch API) to v2.2 (Realtime API), simply run:

```bash
cd ~/Nevil-picar-v3
./scripts/switch_to_realtime.sh
```

This script will:
1. ✅ Backup your current v3.0 configuration
2. ✅ Copy Realtime nodes to proper directories
3. ✅ Create v2.2 configuration
4. ✅ Activate Realtime API nodes
5. ✅ Verify environment setup

## What Gets Switched?

### v3.0 (Current - Batch API)
```
Nodes running:
- speech_recognition      → Whisper API (1-3s latency)
- speech_synthesis        → OpenAI TTS API (1-2s latency)
- ai_cognition            → GPT-4o batch (2-4s latency)

Total latency: 5-8 seconds
```

### v2.2 (New - Realtime API)
```
Nodes running:
- speech_recognition_realtime  → Realtime STT (200-400ms)
- speech_synthesis_realtime    → Realtime TTS (200-400ms)
- ai_cognition_realtime        → Realtime AI (100-300ms)

Total latency: 1.5-2.1 seconds (75-80% faster!)
```

## Manual Switch Instructions

If you prefer to switch manually:

### 1. Backup Current Config
```bash
cp .nodes .nodes.v3.0.backup
```

### 2. Copy Realtime Nodes
```bash
# Copy node files
cp nevil_framework/realtime/speech_recognition_node22.py nodes/speech_recognition_realtime/
cp nevil_framework/realtime/ai_node22.py nodes/ai_cognition_realtime/
cp nevil_framework/realtime/speech_synthesis_node22.py nodes/speech_synthesis_realtime/

# Copy configurations
cp nevil_framework/realtime/.messages nodes/speech_recognition_realtime/
cp nevil_framework/realtime/ai_node22.messages nodes/ai_cognition_realtime/.messages
```

### 3. Create Node Entry Points

Each node directory needs an `__init__.py` that exports the node class:

**nodes/speech_recognition_realtime/__init__.py:**
```python
from .speech_recognition_node22 import SpeechRecognitionNode22
SpeechRecognitionNode = SpeechRecognitionNode22
```

**nodes/ai_cognition_realtime/__init__.py:**
```python
from .ai_node22 import AINode22
AINode = AINode22
```

**nodes/speech_synthesis_realtime/__init__.py:**
```python
from .speech_synthesis_node22 import SpeechSynthesisNode22
SpeechSynthesisNode = SpeechSynthesisNode22
```

### 4. Update .nodes Configuration

Create/update `.nodes` file:

```yaml
# Nevil v2.2 Root Configuration
version: "2.2"
description: "Nevil v2.2 with OpenAI Realtime API"

system:
  framework_version: "2.2.0"
  log_level: "INFO"
  health_check_interval: 5.0
  shutdown_timeout: 10.0
  startup_delay: 2.0

environment:
  NEVIL_VERSION: "2.2"
  LOG_LEVEL: "INFO"
  NEVIL_REALTIME_ENABLED: "true"

launch:
  startup_order: ["led_indicator", "speech_recognition_realtime", "speech_synthesis_realtime", "ai_cognition_realtime", "navigation", "visual"]
  parallel_launch: false
  wait_for_healthy: true
  ready_timeout: 30.0
```

### 5. Verify Environment

Make sure your `.env` file has:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

## Starting Nevil with Realtime API

After switching:

```bash
./nevil
```

You should see in the logs:
```
[Launcher] Starting node: speech_recognition_realtime
[Launcher] Starting node: speech_synthesis_realtime
[Launcher] Starting node: ai_cognition_realtime
```

## Testing

1. **Say something to Nevil**
   - Nevil should respond 75-80% faster
   - Response time: ~1.5-2 seconds instead of 5-8 seconds

2. **Check WebSocket connection**
   ```bash
   tail -f logs/system.log | grep -i "websocket\|realtime"
   ```

3. **Monitor audio streaming**
   ```bash
   tail -f logs/system.log | grep -i "audio\|pcm16\|24000"
   ```

## Switching Back to v3.0

If you need to switch back to the original v3.0:

```bash
./scripts/switch_to_v30.sh
```

Or manually:
```bash
cp .nodes.v3.0.backup .nodes
./nevil
```

## Troubleshooting

### Issue: Nodes not starting
**Check:** Are the node files in the right place?
```bash
ls -la nodes/speech_recognition_realtime/
ls -la nodes/ai_cognition_realtime/
ls -la nodes/speech_synthesis_realtime/
```

### Issue: WebSocket connection fails
**Check:** Is your API key valid?
```bash
grep OPENAI_API_KEY .env
```

**Test connection:**
```bash
python3 examples/realtime_connection_example.py
```

### Issue: Audio not working
**Check:** Is robot_hat.Music() available?
```bash
python3 -c "from robot_hat import Music; print('✓ robot_hat available')"
```

### Issue: Import errors
**Check:** Are dependencies installed?
```bash
pip3 install websockets aiohttp numpy pyaudio openai python-dotenv
```

## Configuration Comparison

| Aspect | v3.0 | v2.2 |
|--------|------|------|
| **STT** | Whisper API (batch) | Realtime API (streaming) |
| **AI** | GPT-4o (batch) | Realtime API (streaming) |
| **TTS** | OpenAI TTS (batch) | Realtime API (streaming) |
| **Playback** | robot_hat.Music() | robot_hat.Music() ✅ SAME |
| **Latency** | 5-8 seconds | 1.5-2.1 seconds |
| **Connection** | REST API | WebSocket |
| **Audio Format** | Various | 24kHz PCM16 mono |

## Important Notes

⚠️ **Hardware Compatibility Preserved**
- Both v3.0 and v2.2 use the SAME audio playback method
- robot_hat.Music() is used for all audio output
- HiFiBerry DAC compatibility maintained
- GPIO pin 20 speaker switch unchanged

✅ **What Changed**
- Audio GENERATION is faster (streaming vs batch)
- AI processing is faster (streaming conversation)
- WebSocket connection instead of REST API

✅ **What Stayed the Same**
- Audio PLAYBACK method (robot_hat.Music())
- Message bus architecture
- Node lifecycle management
- Hardware compatibility

## Expected Performance

### Latency Breakdown

**v3.0:**
- STT: 1-3 seconds (Whisper API)
- AI: 2-4 seconds (GPT-4o batch)
- TTS: 1-2 seconds (OpenAI TTS)
- Total: 5-8 seconds

**v2.2:**
- STT: 200-400ms (Realtime streaming)
- AI: 100-300ms (Realtime streaming)
- TTS Generation: 200-400ms (Realtime streaming)
- TTS Playback: ~1s (robot_hat.Music() - same)
- Total: 1.5-2.1 seconds

**Improvement: 75-80% latency reduction**

## Validation

After switching, run validation:

```bash
./scripts/validate_nevil_22.sh
```

This checks:
- ✓ Python environment
- ✓ Dependencies installed
- ✓ File structure correct
- ✓ API key configured
- ✓ Hardware compatibility
- ✓ Test suites passing

## Support

If you have issues:

1. Check logs: `tail -f logs/system.log`
2. Run validation: `./scripts/validate_nevil_22.sh`
3. Test examples: `python3 examples/realtime_connection_example.py`
4. Read docs: `docs/NEVIL_22_DEPLOYMENT_GUIDE.md`

## Quick Reference

```bash
# Switch to Realtime API (v2.2)
./scripts/switch_to_realtime.sh

# Switch back to v3.0
./scripts/switch_to_v30.sh

# Start Nevil
./nevil

# Validate setup
./scripts/validate_nevil_22.sh

# Run tests
./tests/realtime/run_tests.sh

# View logs
tail -f logs/system.log
```
