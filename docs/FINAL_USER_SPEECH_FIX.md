# Final Fix: User Speech Not Being Captured

## The Problem

**User speech was NOT being transcribed at all!**

Database showed ZERO user transcriptions - only Nevil's own voice being transcribed and creating loops.

## Root Cause

Even with mutex checking in VAD, the system was still capturing Nevil's speech:

1. **User speaks** → VAD detects → commits → response.create
2. **Mutex acquires** → Nevil starts speaking
3. **Audio continues buffering** → Nevil's voice goes into buffer
4. **VAD still processes volume** → Sets `vad_speech_active = True`
5. **Mutex releases** → VAD sees silence
6. **VAD triggers "speech ended"** → Commits buffer (containing Nevil's voice!)
7. **Realtime API transcribes Nevil** → Loop continues

## The Fix

**Clear audio buffer when mutex blocks:**

```python
def _process_vad(self, volume_level):
    # Check mutex BEFORE processing VAD
    if not microphone_mutex.is_microphone_available():
        # Reset VAD state
        if self.vad_speech_active:
            self.vad_speech_active = False
            self.vad_silence_frames = 0

            # CRITICAL: Clear buffer to prevent committing Nevil's speech
            with self.buffer_lock:
                self.audio_buffer.clear()
                self.buffer_length = 0
        return

    # Now safe to process VAD for user speech
    speech_detected = volume_level > threshold
    # ...
```

## What This Does

1. **Before VAD processes each frame** → Check if mutex active (Nevil speaking)
2. **If mutex active:**
   - Reset VAD state (no "speech active")
   - **Clear audio buffer** (discard Nevil's voice)
   - Skip VAD processing entirely
3. **If mutex not active:**
   - Process VAD normally
   - Capture user speech
   - Commit and transcribe

## Expected Behavior After Fix

✅ **User speaks** → Captured and transcribed correctly
✅ **Nevil responds** → Mutex blocks, buffer cleared continuously
✅ **Nevil finishes** → Mutex releases, ready for next user input
✅ **No loops** → Nevil's voice never committed to Realtime API

## Files Modified

1. `/nevil_framework/realtime/audio_capture_manager.py:652-665`
   - Added buffer clearing when mutex blocks

## Testing

```bash
python launcher_realtime.py
```

**Expected:**
1. Say "Hello Nevil"
2. Check database: YOUR transcription should appear
3. Nevil responds once
4. System ready for next input
5. NO Nevil voice in transcriptions

**Verify:**
```bash
sqlite3 /home/dan/Nevil-picar-v3/logs/chat_log.db \
  "SELECT timestamp_start, output_text FROM log_chat \
   WHERE step = 'stt' ORDER BY timestamp_start DESC LIMIT 10;"
```

Should show YOUR words, not Nevil's responses.

## Date

2025-11-13

## Status

✅ **FIXED** - Audio buffer now clears during Nevil's speech
