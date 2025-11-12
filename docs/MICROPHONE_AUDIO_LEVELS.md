# Microphone Audio Level Diagnostics

## Test Results (2025-11-11 23:51)

### Hardware Detection
- ✅ Microphone detected: `USB PnP Sound Device (card 3, hw:3,0)`
- ✅ PyAudio default device: Index 5 (ALSA default routing)
- ✅ Recording functional: 3-second test successful (141KB WAV file)

### Audio Levels
- **Max level detected: 0.0085** (normalized 0.0-1.0 scale)
- **Typical range: 0.0055 - 0.0085**
- **VAD threshold default: 0.02**
- **Result: Audio too quiet for default VAD threshold**

## Issue Analysis

The microphone hardware is working correctly, but audio levels are approximately **2.4x too low** for the default Voice Activity Detection threshold.

### Why This Matters

While the OpenAI Realtime API **doesn't require VAD** (it streams all audio continuously), low audio levels can affect:
1. Realtime API transcription accuracy
2. Background noise discrimination
3. Overall signal quality

## Solutions

### Option 1: Increase Microphone Gain (Hardware)
```bash
# Check current microphone capture volume
amixer -c 3 sget Mic

# Increase to 100% (if adjustable)
amixer -c 3 sset Mic 100%
```

### Option 2: Disable VAD (Already Default)
The `AudioCaptureManager` has `vad_enabled=False` by default, so all audio is streamed regardless of volume levels.

### Option 3: Lower VAD Threshold (If Enabling VAD)
In `nodes/speech_recognition_realtime/.messages`:
```yaml
audio:
  sample_rate: 24000
  channel_count: 1
  buffer_size: 4096
  chunk_size: 4800
  vad_enabled: false  # Keep disabled for Realtime API
  vad_threshold: 0.005  # If enabling, use lower threshold
```

## Current Status

- ✅ Microphone hardware functional
- ✅ Audio capture working (24kHz PCM16 mono)
- ⚠️ Audio levels low but acceptable for streaming
- ✅ VAD disabled (correct for Realtime API)
- ❌ speech_recognition_realtime node crashed (fixed, needs restart)

## Next Steps

1. **Restart Nevil** to load the fixed speech_recognition_node22.py
2. **Test with voice input** - Realtime API should transcribe despite low levels
3. **If transcription poor**: Increase microphone gain via ALSA

## Technical Details

- **Sample Rate**: 24000 Hz (Realtime API requirement)
- **Format**: PCM16 (16-bit signed integers)
- **Channels**: 1 (mono)
- **Chunk Size**: 4800 samples (200ms)
- **Audio Range**: -32768 to 32767 (int16)
- **Normalized Range**: 0.0 to 1.0 (absolute mean / 32768)
