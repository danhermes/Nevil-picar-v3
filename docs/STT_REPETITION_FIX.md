# STT Repetition Issue - Root Cause & Fix

**Date**: 2025-11-20
**Issue**: Speech-to-text was repeating transcriptions and producing garbled output

## Problem Analysis

### Observed Symptoms
```
Transcription 1: "Can you hear me?" repeated 16 times
Transcription 2: Same phrase repeated 4 times
Transcription 3: Garbled "Respond bonded it. Are you are you you? Boy planes means..."
```

### Root Causes Identified

1. **Race Condition in Audio Commit**
   - Audio continuously streams to OpenAI Realtime API via `input_audio_buffer.append`
   - When VAD detected speech end, it waited 200ms before committing
   - During this 200ms delay, MORE audio chunks were being appended
   - Result: Committed buffer contained user speech + extra audio that arrived during delay

2. **Cooldown Mismatch**
   - Commit cooldown: 2.0 seconds
   - Speech timeout: 1.5 seconds
   - Result: Audio accumulated between speech detection events

3. **Local Buffer Not Cleared**
   - After committing to API, local buffer still contained audio
   - This stale audio could be re-sent in subsequent commits
   - Result: Repetitive transcriptions

4. **Excessive Software Gain**
   - 4x amplification on microphone input
   - Amplified echoes and feedback from speakers
   - VAD triggered on Nevil's own speech being picked up by mic

## Fixes Applied

### 1. Fix Race Condition (`audio_capture_manager.py:746-782`)
```python
# BEFORE:
time_module.sleep(0.2)  # 200ms delay
commit_event = {"type": "input_audio_buffer.commit"}
self.connection_manager.send_sync(commit_event)

# AFTER:
was_recording = self.is_recording
self.is_recording = False  # STOP processing new audio immediately
time_module.sleep(0.05)    # Reduced to 50ms

commit_event = {"type": "input_audio_buffer.commit"}
self.connection_manager.send_sync(commit_event)

# Clear local buffer after commit
with self.buffer_lock:
    self.audio_buffer.clear()
    self.buffer_length = 0

# Resume recording
if was_recording:
    self.is_recording = True
```

**Impact**: Prevents new audio from being added during commit, reduces delay from 200ms to 50ms

### 2. Reduce Commit Cooldown (`audio_capture_manager.py:174`)
```python
# BEFORE:
self.commit_cooldown = 2.0  # 2 seconds

# AFTER:
self.commit_cooldown = 0.5  # 500ms
```

**Impact**: Prevents audio accumulation, allows faster back-to-back speech

### 3. Reduce Software Gain (`audio_capture_manager.py:847`)
```python
# BEFORE:
audio_data = audio_data * 4.0  # 4x amplification

# AFTER:
audio_data = audio_data * 2.0  # 2x amplification
```

**Impact**: Reduces echo/feedback amplification

## Expected Results

1. **Clean transcriptions** - Only user's actual speech is transcribed
2. **No repetitions** - Each utterance transcribed exactly once
3. **Faster response** - 50ms delay instead of 200ms
4. **Better echo rejection** - Lower gain reduces feedback pickup

## Testing Recommendations

1. Test single utterances: "Hello Nevil"
2. Test back-to-back speech: "Move forward" ... "Turn left"
3. Test during robot speech: Verify mic properly muted during TTS
4. Monitor logs for:
   - `🛑 Paused audio streaming for clean commit`
   - `✅ Committed audio buffer to Realtime API`
   - `🗑️ Cleared local audio buffer after commit`
   - `▶️ Resumed audio streaming`

## Configuration Tuning

If issues persist, adjust these values in `nodes/speech_recognition_realtime/.messages`:

```yaml
audio:
  vad_threshold: 0.15              # INCREASE (e.g., 0.20) to filter more noise
  vad_min_speech_duration: 0.5    # INCREASE (e.g., 0.7) to ignore brief sounds
  speech_timeout_ms: 1500          # Time of silence before committing
```

## Files Modified

1. `nevil_framework/realtime/audio_capture_manager.py`
   - Line 174: Reduced commit cooldown from 2.0s to 0.5s
   - Lines 746-782: Added pause/resume logic around commit
   - Line 847: Reduced software gain from 4x to 2x

## References

- Issue logs: See user-provided logs showing 16x repetition
- VAD implementation: `_process_vad()` method in AudioCaptureManager
- Realtime API docs: https://platform.openai.com/docs/guides/realtime
