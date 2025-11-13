# Mutex Feedback Loop Fix - 2025-11-12

## Problem: Infinite Feedback Loop ("Won't Stop Talking")

Nevil would hear his own speech and respond to it in an endless loop:
1. User: "Hey Nevil, what's the weather?"
2. Nevil responds with TTS
3. **Nevil hears his own TTS** and transcribes it
4. Nevil responds to what he "heard" (his own speech)
5. **Realtime API continues generating responses from buffered audio**
6. Loop repeats infinitely ❌

## Root Cause: Race Condition

**Old (BROKEN) timing:**
```
T=0ms:   AI generates text response
T=10ms:  on_text_response() sends response.create to Realtime API
         ^ Realtime API ALREADY has audio buffered from microphone!
T=50ms:  First audio chunk arrives
T=51ms:  Mutex acquired, buffer cleared
         ^ TOO LATE - response already generated from buffered audio
```

**The problem:** Mutex and buffer clear happened AFTER the audio generation request was sent, so the Realtime API was already processing audio that included Nevil's own speech.

## Solution: Preemptive Muting

**New (FIXED) timing:**
```
T=0ms:   AI generates text response
T=10ms:  on_text_response() called
         1. ✅ Acquire mutex (mute mic)
         2. ✅ Clear Realtime API input buffer
         3. ✅ Publish speaking_status=True
         4. ✅ Send response.create to Realtime API
T=50ms:  First audio chunk arrives → just buffer it
         ^ Mutex already acquired, no echo possible!
```

## Root Causes Found

### 1. Race condition in audio buffering
Audio was buffered BEFORE mutex check → already-buffered audio sent even when muted

### 2. Missing mutex checks in processing pipeline
`_process_audio_chunk()` and `flush()` didn't check mutex → buffered audio sent anyway

### 3. Missing response cancellation
Realtime API responses in-progress when TTS started were never cancelled → continued generating

## Changes Made

### 1. audio_capture_manager.py - Processing Loop (lines 532-542)
**Before:** Audio was buffered first, then mutex checked in callback
**After:** Mutex checked BEFORE buffering - audio discarded if mutex blocked

```python
# Check mutex BEFORE buffering to prevent race condition
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Microphone is muted - discard audio and clear buffer
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
    continue  # Don't buffer this audio
```

### 2. audio_capture_manager.py - _process_audio_chunk() (lines 575-585)
**NEW:** Check mutex BEFORE processing buffered chunks

```python
# Check mutex BEFORE processing buffered audio
# This prevents sending already-buffered audio when TTS starts mid-buffer
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Mutex blocked - clear buffer and return without sending
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
    return
```

### 3. audio_capture_manager.py - flush() (lines 361-371)
**NEW:** Check mutex BEFORE flushing

```python
# Check mutex BEFORE flushing
# Don't send buffered audio if TTS is active
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Mutex blocked - clear buffer and return without sending
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
    return
```

### 4. speech_synthesis_node22.py - on_text_response() (lines 511-531)
**Before:** Sent audio request first, mutex acquired when audio arrived
**After:** Acquire mutex and clear buffer BEFORE sending audio request

```python
# 1. Acquire mutex immediately to prevent new audio from being processed
if not self.mutex_acquired:
    microphone_mutex.acquire_noisy_activity("speaking")
    self.mutex_acquired = True

# 2. Clear Realtime API input buffer to discard any accumulated audio
if self.realtime_manager:
    clear_event = {"type": "input_audio_buffer.clear"}
    self.realtime_manager.send_event(clear_event)

# 3. Publish speaking status to notify other nodes
self._publish_speaking_status(True, text, voice)

# 4. NOW send to Realtime API for audio generation
self.realtime_manager.send_event({"type": "response.create", ...})
```

### 5. speech_synthesis_node22.py - _on_audio_delta() (simplified)
**Before:** Acquired mutex on first audio chunk
**After:** Mutex already acquired, just buffer the audio (with fallback check)

### 6. speech_synthesis_node22.py - _on_audio_done() (simplified)
**Before:** Acquired mutex before playback
**After:** Mutex already acquired, just release it after playback

### 7. speech_recognition_node22.py - on_speaking_status_change() (lines 503-510)
**NEW:** Cancel in-progress Realtime API responses when TTS starts

```python
if speaking:
    microphone_mutex.acquire_noisy_activity("speaking")

    # ⚠️ CRITICAL: Cancel any in-progress Realtime API responses
    # This prevents the API from generating responses based on audio captured before muting
    self._cancel_response()

    # Clear the audio buffer to discard any captured audio
    self._clear_audio_buffer()
```

## Files Updated

1. `/home/dan/Nevil-picar-v3/nevil_framework/realtime/audio_capture_manager.py`
   - Mutex check in processing loop (line 534)
   - Mutex check in `_process_audio_chunk()` (line 578)
   - Mutex check in `flush()` (line 364)

2. `/home/dan/Nevil-picar-v3/nodes/speech_synthesis_realtime/speech_synthesis_node22.py`
   - Preemptive muting in `on_text_response()` (lines 516-531)
   - Simplified `_on_audio_delta()` (line 232)
   - Simplified `_on_audio_done()` (line 314)

3. `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
   - Same changes as #2

4. `/home/dan/Nevil-picar-v3/nodes/speech_recognition_realtime/speech_recognition_node22.py`
   - Response cancellation in `on_speaking_status_change()` (line 505)

## Expected Behavior After Fix

✅ **User speaks** → Transcribed correctly
✅ **Nevil responds** → Mutex acquired BEFORE audio generation
✅ **Realtime API input buffer cleared** → No accumulated user speech
✅ **TTS plays** → Microphone blocked, audio discarded
✅ **TTS ends** → Mutex released, microphone available again
✅ **User speaks again** → Cycle repeats correctly (no feedback loop)

## Testing

To verify the fix works:
1. Start Nevil
2. Say "Hey Nevil, tell me a story"
3. Observe: Nevil should respond **ONCE** and stop (not loop)
4. Check logs for:
   - `🔇 Microphone muted PREEMPTIVELY before TTS request`
   - `🗑️  Cleared Realtime API input buffer BEFORE TTS request`
   - `🚫 Cancelled in-progress Realtime API responses`
   - `🚫 Audio discarded - mutex blocked` (during TTS)
   - `🚫 Buffered audio discarded - mutex blocked during chunk processing`
   - `🚫 Flush cancelled - mutex blocked, buffer cleared`
   - `🎤 Microphone unmuted - TTS complete`

## Debug Commands

Monitor mutex status:
```bash
tail -f /tmp/nevil_mic_status.txt | grep -E "(MUTEX|mutex|🔇|🔓|🎤)"
```

Check audio processing:
```bash
tail -f /tmp/nevil_mic_status.txt | grep "MIC SIGNAL"
```

## Key Insights

**1. Preemptive > Reactive:**
- **OLD:** React to audio arrival → too late
- **NEW:** Mute before requesting audio → prevents echo at source

**2. Multi-layer protection required:**
- Layer 1: Prevent NEW audio from being buffered
- Layer 2: Prevent BUFFERED audio from being processed
- Layer 3: Prevent BUFFERED audio from being flushed
- Layer 4: Cancel IN-PROGRESS API responses

**3. All exit paths must be protected:**
Audio can escape through:
- Processing loop → **FIXED** with mutex check before buffering
- Chunk processing → **FIXED** with mutex check in `_process_audio_chunk()`
- Auto-flush → **FIXED** with mutex check in `flush()`
- API in-progress responses → **FIXED** with `response.cancel` event
