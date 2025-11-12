# Instructions for Claude on Raspberry Pi

Copy and paste this to Claude on the Pi:

---

## Context

I'm continuing work on Nevil 2.2 (OpenAI Realtime API integration) on the Raspberry Pi. The initial setup was done on Windows and code has been committed to git.

## What Was Done on Windows

- ✅ Hive Mind designed Nevil 2.2 architecture
- ✅ Setup script created directory structure
- ✅ Generated RealtimeConnectionManager scaffolding (70% complete, 19 TODOs)
- ✅ Created comprehensive documentation with CRITICAL warnings
- ✅ Committed changes to git

## Critical Information

**⚠️ MAKE OR BREAK**: We MUST preserve the existing audio playback method (`robot_hat.Music()`). See `docs/CRITICAL_AUDIO_PLAYBACK_WARNING.md`

**Architecture**:
```
Realtime API streaming → Buffer in memory → Save to WAV → robot_hat.Music() plays
                                                          ^^^^^^^^^^^^^^^^^^^
                                                          CANNOT CHANGE
```

## Tasks for Pi

### 1. Pull Latest Code
```bash
cd ~/Nevil-picar-v3
git pull origin main
```

### 2. Read Critical Documentation (REQUIRED)
```bash
cat READ_THIS_FIRST.md
cat docs/CRITICAL_AUDIO_PLAYBACK_WARNING.md
cat docs/NEVIL_2.2_CORRECTED_ARCHITECTURE.md
```

### 3. Run Setup Script on Pi
```bash
./scripts/setup_nevil_2.2.sh
```

This will:
- Install Python dependencies (websockets, aiohttp, etc.)
- Install pyaudio (works on Linux/Pi)
- Validate environment
- Check robot_hat is available

### 4. Configure API Key
```bash
cp .env.realtime .env
nano .env
# Add: OPENAI_API_KEY=sk-your-key-here
```

### 5. Generate Node Implementations

I need you to:

**A. Generate speech_recognition_node22.py**
- Continuous audio streaming from microphone
- WebSocket to Realtime API
- Server-side VAD
- Publishes: `voice_command`
- Must use existing microphone setup (same hardware as v3.0)

**B. Generate ai_node22.py**
- Streaming conversation processing
- Function calling for 106 gestures
- Camera integration (multimodal)
- Publishes: `text_response`, `robot_action`

**C. Generate speech_synthesis_node22.py** ⚠️ CRITICAL
- Buffer streaming audio from Realtime API
- Save complete audio to WAV file
- **MUST USE**: `AudioOutput` from `audio/audio_output.py`
- **MUST USE**: `robot_hat.Music()` for playback
- **NEVER USE**: PyAudio for playback
- Publishes: `speaking_status`

### 6. Key Constraints

#### Hardware Compatibility (CRITICAL)
- ✅ MUST use `audio/audio_output.py` (contains `robot_hat.Music()`)
- ✅ MUST save streaming audio to WAV before playback
- ✅ MUST preserve GPIO pin 20 speaker switch
- ❌ NEVER replace `robot_hat.Music()` with PyAudio
- ❌ NEVER modify `audio/audio_output.py`

#### Message Bus Compatibility
- Use existing `NevilNode` base class
- Use `.messages` configuration files
- Follow declarative messaging pattern
- Maintain compatibility with v3.0 nodes

#### Audio Hardware
- Microphone: Same as v3.0 (USB or onboard)
- Speaker: HiFiBerry DAC via `robot_hat.Music()`
- Sample rate: 24kHz for Realtime API, but hardware stays same

### 7. Testing Checklist

Before running on robot:
- [ ] Imports `AudioOutput` from `audio/audio_output.py`
- [ ] Calls `play_loaded_speech()` or `play_audio_file()`
- [ ] Does NOT import PyAudio for playback
- [ ] Saves to WAV file before playback
- [ ] Uses existing microphone setup

### 8. What You Need to Build

Generate these files with full implementations:

1. `nodes/speech_recognition_realtime/speech_recognition_node22.py`
2. `nodes/ai_cognition_realtime/ai_node22.py`
3. `nodes/speech_synthesis_realtime/speech_synthesis_node22.py`
4. `.messages` files for each node
5. Test files in `tests/realtime/`

### 9. Reference Documentation

All docs are in the repo:
- `READ_THIS_FIRST.md` - Entry point
- `docs/CRITICAL_AUDIO_PLAYBACK_WARNING.md` - Make or break rules
- `docs/NEVIL_2.2_CORRECTED_ARCHITECTURE.md` - Architecture summary
- `docs/NEVIL_2.2_ZERO_TOUCH_PLAN.md` - Full implementation plan
- `HIVE_MIND_REPORT.md` - Design analysis

### 10. Expected Timeline

- Setup on Pi: 10 minutes
- Generate 3 nodes: 2-3 hours (with your help)
- Testing: 1-2 hours
- Total: Half day of work

### 11. Success Criteria

- ✅ All nodes follow `NevilNode` pattern
- ✅ speech_synthesis_node22 uses `robot_hat.Music()` playback
- ✅ Message bus topics match v3.0
- ✅ Audio hardware compatibility preserved
- ✅ WebSocket connection to Realtime API works
- ✅ Can speak → STT → AI → TTS → speak (full cycle)
- ✅ Latency < 2 seconds (vs 5-8s in v3.0)

## Questions?

Ask me to:
- Show you existing v3.0 node code for reference
- Explain specific parts of the architecture
- Review generated code before testing
- Help debug any issues

**Most Important**: Read `docs/CRITICAL_AUDIO_PLAYBACK_WARNING.md` FIRST before generating any code.
