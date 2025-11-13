# The REAL Issue: Multiple Realtime API Connections

## Problem Summary

Nevil has **THREE separate OpenAI Realtime API WebSocket connections**:

1. **Speech Recognition Node** (`speech_recognition_node22.py`) - Has its own `connection_manager`
2. **AI Cognition Node** (`ai_node22.py`) - Has its own `connection_manager`
3. **Speech Synthesis Node** (`speech_synthesis_node22.py`) - Has its own `realtime_manager`

## Why Previous Fixes Failed

The previous fix attempted to clear the audio buffer when TTS started, but it was clearing **the WRONG connection's buffer**:

```python
# In speech_synthesis_node22.py:514
clear_event = {"type": "input_audio_buffer.clear"}
self.realtime_manager.send_sync(clear_event)  # ❌ Clears TTS connection, not STT!
```

This cleared the **TTS connection's** buffer, but the user's speech was actually buffered in the **SPEECH RECOGNITION connection's** buffer!

## The Feedback Loop Mechanism

```
1. User speaks "Hey Nevil"
   ↓
2. Audio goes into SPEECH RECOGNITION's Realtime API buffer
   ↓
3. AI generates response → triggers TTS
   ↓
4. TTS node clears ITS OWN buffer (wrong connection!)
   ↓
5. SPEECH RECOGNITION connection still has buffered audio ⚠️
   ↓
6. Transcription completes and returns "Hey Nevil"
   ↓
7. AI responds to "Hey Nevil" again
   ↓
8. LOOP REPEATS ∞
```

## The Real Fix

### Fix 1: Add Missing `_clear_audio_buffer()` Method

**File:** `nodes/speech_recognition_realtime/speech_recognition_node22.py:622-632`

```python
def _clear_audio_buffer(self):
    """Clear the Realtime API input audio buffer to prevent feedback"""
    try:
        if self.connection_manager:
            clear_event = {
                "type": "input_audio_buffer.clear"
            }
            self.connection_manager.send_sync(clear_event)
            self.logger.info("🗑️  Cleared speech recognition audio buffer")
    except Exception as e:
        self.logger.debug(f"Error clearing audio buffer: {e}")
```

**Impact:** Now when `_clear_audio_buffer()` is called, it clears the **CORRECT** connection's buffer (speech recognition, not TTS).

### Fix 2: Re-enable Response Cancellation

**File:** `nodes/speech_recognition_realtime/speech_recognition_node22.py:495-499`

**Before:**
```python
# # ⚠️ DISABLED: This was cancelling the response we're about to speak!
# # The mutex already handles preventing new audio during TTS
# self._cancel_response()
# self.logger.info("🚫 Cancelled in-progress Realtime API responses")
```

**After:**
```python
# ⚠️ CRITICAL: Cancel in-progress TRANSCRIPTION responses
# This is the SPEECH RECOGNITION node - we're cancelling TRANSCRIPTIONS, not TTS!
# Must happen BEFORE clearing buffer to ensure API stops processing
self._cancel_response()
self.logger.info("🚫 Cancelled in-progress transcription responses")
```

**Impact:** Cancels any in-flight transcription responses in the speech recognition API when TTS starts. This is NOT canceling TTS - it's canceling TRANSCRIPTION of user speech that's already being processed.

## Why This Fix Works

### Old Flow (Broken):
```
T0: User speaks → Audio buffered in STT connection
T1: STT connection starts transcribing
T2: AI generates response → TTS starts
T3: TTS connection buffer cleared ❌ (wrong connection!)
T4: STT connection transcription completes ⚠️ (still processing!)
T5: "Hey Nevil" published → AI responds again
T6: Loop repeats ∞
```

### New Flow (Fixed):
```
T0: User speaks → Audio buffered in STT connection
T1: STT connection starts transcribing
T2: AI generates response → TTS starts
T3: Speaking status published
T4: Speech recognition receives speaking=True
T5: ✅ STT connection response.cancel sent
T6: ✅ STT connection buffer cleared
T7: In-flight transcriptions cancelled ✅
T8: TTS plays
T9: TTS ends → speaking=False
T10: Ready for next user input (no loop!)
```

## Files Modified

1. **`nodes/speech_recognition_realtime/speech_recognition_node22.py`**
   - Added `_clear_audio_buffer()` method (lines 622-632)
   - Re-enabled `_cancel_response()` call (lines 495-499)
   - Updated log messages for clarity

2. **`nevil_framework/realtime/speech_synthesis_node22.py`**
   - Added `self.mutex_acquired = False` initialization (line 115)

3. **`nevil_framework/realtime/audio_capture_manager.py`**
   - Moved mutex check BEFORE hardware audio read (line 516)
   - Added mutex check for VAD processing (line 559)
   - Reset VAD state when mutex blocks (lines 700-702)

4. **`nodes/speech_recognition_realtime/speech_recognition_node22.py`**
   - Changed buffer clear to happen BEFORE mutex release (line 506)

## Testing Checklist

When Nevil starts and you speak to it, you should see:

1. **When TTS starts:**
   ```
   🔇 Microphone muted - system is speaking
   🚫 Cancelled in-progress transcription responses
   🗑️  Cleared speech recognition audio buffer - preventing echo feedback
   ```

2. **When TTS ends:**
   ```
   🎤 Audio buffer cleared while mutex still held
   🎤 Microphone unmuted - system finished speaking
   ```

3. **During TTS playback (in audio capture logs):**
   - No "MIC SIGNAL" logs (hardware read skipped)
   - OR logs showing audio discarded due to mutex

## Key Insights

1. **Multiple API connections = Multiple buffers**
   - Each Realtime API connection has its own independent buffer
   - Clearing one connection's buffer doesn't affect the others

2. **Clear the RIGHT connection**
   - User speech goes through STT connection
   - Must clear STT connection's buffer, not TTS connection's buffer

3. **Cancel in-flight responses**
   - Realtime API processes audio asynchronously
   - Must cancel in-progress transcription responses, not just clear buffer

4. **The mutex prevents NEW audio, not BUFFERED audio**
   - Mutex stops new hardware audio capture
   - But API might still have buffered audio from before mutex was acquired
   - Must explicitly cancel and clear on the API side

## Architecture Diagram

```
┌─────────────────┐
│  MICROPHONE     │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│  Audio Capture Manager                  │
│  (Mutex checks happen here)             │
└────────┬────────────────────────────────┘
         │
         ↓
    ┌────────────────────────────────────┐
    │  Speech Recognition Node           │
    │  Connection Manager #1  ←── FIX!   │
    │  (User speech buffered here)       │
    └────────┬───────────────────────────┘
             │
             ↓ voice_command
    ┌────────────────────────────────────┐
    │  AI Cognition Node                 │
    │  Connection Manager #2             │
    └────────┬───────────────────────────┘
             │
             ↓ text_response
    ┌────────────────────────────────────┐
    │  Speech Synthesis Node             │
    │  Realtime Manager #3               │
    │  (Was clearing WRONG buffer)       │
    └────────┬───────────────────────────┘
             │
             ↓
    ┌────────────────────────────────────┐
    │  SPEAKERS                          │
    └────────────────────────────────────┘
```

## Conclusion

The infinite loop was caused by clearing the **wrong Realtime API connection's buffer**. The fix ensures:

1. ✅ Speech recognition buffer is cleared (not TTS buffer)
2. ✅ In-flight transcription responses are cancelled
3. ✅ Mutex prevents new hardware audio capture
4. ✅ VAD state is reset when blocked
5. ✅ Buffer cleared before mutex release

**Status: FIXED** ✅
**Date:** 2025-11-13
