# Nevil Realtime System - Complete Architecture Analysis

## Executive Summary

Nevil's realtime system implements a sophisticated audio processing pipeline with mutex-based synchronization to prevent feedback loops. However, there is a **critical initialization bug** causing the infinite self-conversation loop.

### Root Cause
The `mutex_acquired` flag in `SpeechSynthesisNode22` is **never initialized**, causing undefined behavior and bypassing mutex protection during TTS playback.

### Impact
- Nevil hears his own speech during TTS playback
- Microphone mutex checks fail unpredictably
- Infinite feedback loop until manual intervention

---

## System Architecture Overview

### 1. Core Components

#### A. Audio Capture Pipeline
```
Microphone → PyAudio Stream → audio_capture_manager.py → Realtime API (WebSocket)
```

**File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/audio_capture_manager.py` (902 lines)

**Key classes:**
- `AudioCaptureManager` - Manages microphone input streaming
- `AudioCaptureConfig` - Configuration (24kHz mono PCM16)
- `AudioCaptureCallbacks` - Event hooks for audio data

**Critical features:**
- 24kHz mono PCM16 format (OpenAI Realtime API spec)
- 4800-sample chunks (200ms at 24kHz)
- Mutex protection at three critical points
- Voice Activity Detection (VAD) support
- Thread-safe buffer management with `threading.Lock()`

#### B. Audio Recognition Pipeline
```
Realtime API (WebSocket) → response.audio_transcript.delta events → speech_recognition_node22.py
→ voice_command topic → AI Cognition Node
```

**File:** `/home/dan/Nevil-picar-v3/nodes/speech_recognition_realtime/speech_recognition_node22.py` (648 lines)

**Key responsibilities:**
- Subscribes to Realtime API transcript events
- Accumulates streaming transcript deltas
- Publishes `voice_command` messages when transcription completes
- Manages microphone mutex (acquire/release on speaking status)
- Handles audio buffer clearing

#### C. AI Cognition Pipeline
```
voice_command → AI Node (Realtime API) → response.text.delta events
→ text_response topic → Speech Synthesis Node
```

**File:** `/home/dan/Nevil-picar-v3/nodes/ai_cognition_realtime/ai_node22.py` (685 lines)

**Key responsibilities:**
- Processes user voice commands via Realtime API
- Streams text responses via `response.text.delta` events
- Handles function calling for 106+ gestures
- Publishes `text_response` messages for TTS

#### D. Speech Synthesis Pipeline
```
text_response topic → Speech Synthesis Node
→ Request audio from Realtime API
→ Buffer response.audio.delta chunks
→ Save WAV file on response.audio.done
→ Play via robot_hat.Music()
```

**File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py` (586 lines)

**Key responsibilities:**
- Subscribes to `text_response` messages
- Requests TTS audio from Realtime API
- Buffers audio chunks
- Saves to WAV file
- Plays audio via AudioOutput class
- **CRITICAL:** Manages microphone mutex during playback

### 2. Conversation Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ USER SPEAKS                                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ audio_capture_manager.py                                         │
│ • _processing_loop() reads from microphone                      │
│ • Checks: is_microphone_available()?                            │
│ • If YES: Buffers audio (line 564)                              │
│ • If NO: Discards audio (line 559)                              │
│ • Calls VAD processing (line 548)                               │
│ • VAD detects speech end → calls _process_vad() (line 657)      │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ VAD Speech End Detection (line 681)                              │
│ • Checks cooldown (2 second limit) (line 689)                   │
│ • Checks mutex: is_microphone_available()? (line 698)           │
│ • If YES: Commits audio buffer to Realtime API                  │
│ • Sends input_audio_buffer.commit event (line 722)              │
│ • Sends response.create event (line 728)                        │
│ • Updates last_commit_time (line 724)                           │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ speech_recognition_node22.py (lines 209-259)                    │
│ • Receives response.audio_transcript.delta events               │
│ • Accumulates transcript (line 225)                             │
│ • On response.audio_transcript.done:                            │
│   - _process_transcript() (line 261)                            │
│   - Publishes voice_command message (line 315)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ ai_cognition_node.py (lines 543-584)                            │
│ • on_voice_command() receives voice_command (line 543)          │
│ • Sends conversation.item.create to Realtime API (line 561)     │
│ • Sends response.create to Realtime API (line 575)              │
│ • Sets system_mode to "thinking" (line 579)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Realtime API generates response                                  │
│ • Streams response.text.delta events                            │
│ • Builds complete text response                                 │
│ • On response.text.done: sends response text                    │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ ai_cognition_node.py (lines 298-326)                            │
│ • _on_response_text_done() receives complete text (line 298)    │
│ • Publishes text_response message (line 315)                    │
│ • Sets system_mode to "speaking" (line 317)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ speech_synthesis_node22.py (lines 476-536)                      │
│ • on_text_response() receives text_response message (line 476)  │
│ • ⚠️  CRITICAL BUG: mutex_acquired NOT INITIALIZED             │
│ • Checks: if not self.mutex_acquired (line 503)                 │
│   - undefined variable → AttributeError OR unpredictable        │
│   - If False (by accident): acquires mutex (line 504)           │
│   - If undefined: CRASH or fallback in _on_audio_delta()        │
│ • Clears Realtime API input buffer (line 510)                   │
│ • Publishes speaking_status=True (line 517)                     │
│ • Sends response.create to Realtime API (line 523)              │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Realtime API generates audio                                     │
│ • Streams response.audio.delta events                           │
│ • Buffers audio chunks in memory                                │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ speech_synthesis_node22.py (lines 205-237)                      │
│ • _on_audio_delta() receives audio chunk (line 205)             │
│ • Buffers chunk (line 225)                                      │
│ • Fallback: if not self.mutex_acquired (line 228)               │
│   - Try to acquire mutex NOW (line 230)                         │
│   - TOO LATE - audio generation already started!                │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ speech_synthesis_node22.py (lines 261-407)                      │
│ • _on_audio_done() all audio received (line 261)                │
│ • Saves WAV file (line 299)                                     │
│ • Plays via robot_hat.Music() (line 346)                        │
│ • Publishes speaking_status=False (line 387) AFTER playback     │
│ • Releases mutex (line 392)                                     │
│   - PROBLEM: If mutex never acquired, release fails!            │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ ❌ PROBLEM: Nevil hears his own speech during TTS playback      │
│                                                                  │
│ Why?                                                             │
│ 1. mutex_acquired never initialized → unpredictable state       │
│ 2. on_text_response() may fail to acquire mutex                 │
│ 3. Microphone still active (not blocked by mutex)               │
│ 4. Audio capture continues → buffering Nevil's own speech       │
│ 5. VAD detects "new user speech" (Nevil's TTS)                  │
│ 6. Commits buffer → sends to Realtime API                       │
│ 7. Realtime API generates response to Nevil's own speech        │
│ 8. Loop repeats infinitely ❌                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Mutex Usage Patterns

### 1. MicrophoneMutex Implementation
**File:** `/home/dan/Nevil-picar-v3/nevil_framework/microphone_mutex.py` (100 lines)

```python
class MicrophoneMutex:
    """Reference-counted lock for microphone access"""
    
    def acquire_noisy_activity(self, activity_name="unknown"):
        """Acquire lock (speech synthesis or navigation)"""
        with self.mutex_lock:
            self.noisy_activity_count += 1
            self.active_activities.add(activity_name)
    
    def release_noisy_activity(self, activity_name="unknown"):
        """Release lock"""
        with self.mutex_lock:
            if self.noisy_activity_count > 0:
                self.noisy_activity_count -= 1
                self.active_activities.discard(activity_name)
    
    def is_microphone_available(self):
        """Check if microphone can be used"""
        with self.mutex_lock:
            return self.noisy_activity_count == 0
```

**Key characteristics:**
- Singleton pattern with thread-safe access
- Reference counting (allows multiple activities)
- Protects microphone during TTS and navigation
- **Not** a traditional mutex - it's a resource availability check

### 2. Mutex Usage Points in Audio Capture

#### Point 1: Processing Loop (audio_capture_manager.py:550-560)
```python
# Lines 550-560: Check mutex BEFORE buffering audio
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Microphone is muted - discard audio and clear buffer
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
            self.logger.debug("🚫 Audio discarded - mutex blocked (TTS/navigation active)")
    continue  # Don't buffer this audio
```

**Purpose:** Prevent NEW audio from being buffered during TTS

#### Point 2: Chunk Processing (audio_capture_manager.py:601-611)
```python
# Lines 601-611: Check mutex BEFORE processing buffered chunks
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Mutex blocked - clear buffer and return without sending
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
            self.logger.debug("🚫 Buffered audio discarded - mutex blocked during chunk processing")
    return
```

**Purpose:** Prevent BUFFERED audio from being processed/sent during TTS

#### Point 3: Flush (audio_capture_manager.py:367-377)
```python
# Lines 367-377: Check mutex BEFORE flushing
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    # Mutex blocked - clear buffer and return without sending
    with self.buffer_lock:
        if self.audio_buffer:
            self.audio_buffer.clear()
            self.buffer_length = 0
            self.logger.debug("🚫 Flush cancelled - mutex blocked, buffer cleared")
    return
```

**Purpose:** Prevent auto-flush from sending buffered audio during TTS

#### Point 4: VAD Speech End (audio_capture_manager.py:695-702)
```python
# Lines 695-702: Check mutex BEFORE committing audio for transcription
from nevil_framework.microphone_mutex import microphone_mutex
if not microphone_mutex.is_microphone_available():
    self.logger.info("VAD: Speech ended but mutex blocked - NOT committing (preventing feedback loop)")
    if self.callbacks.on_vad_speech_end:
        self.callbacks.on_vad_speech_end()
    return
```

**Purpose:** Prevent transcription of Nevil's own speech (detected as "user speech" by VAD)

---

## Critical Bug Analysis

### The Uninitialized `mutex_acquired` Flag

**Location:** `speech_synthesis_node22.py` - Lines 228, 231, 314, 318, 390, 393, 403, 406, 503, 505

**Problem:**
The flag `self.mutex_acquired` is **referenced 10 times** but **never initialized** in `__init__()`.

**Impact Timeline:**

1. **Line 503: on_text_response() - First check**
   ```python
   if not self.mutex_acquired:
       microphone_mutex.acquire_noisy_activity("speaking")
       self.mutex_acquired = True
   ```
   - Raises `AttributeError: 'SpeechSynthesisNode22' object has no attribute 'mutex_acquired'`
   - OR: If Python somehow doesn't crash, behavior is undefined

2. **Line 228: _on_audio_delta() - Fallback check**
   ```python
   if not self.mutex_acquired:
       microphone_mutex.acquire_noisy_activity("speaking")
       self.mutex_acquired = True
       self.logger.warning("⚠️  Mutex not acquired - fallback activation")
   ```
   - Never executes properly due to uninitialized state
   - Comment says "this shouldn't happen" but it WILL because line 503 failed

3. **Line 314: _on_audio_done() - Fallback check (again)**
   ```python
   if not self.mutex_acquired:
       from nevil_framework.microphone_mutex import microphone_mutex
       microphone_mutex.acquire_noisy_activity("speaking")
       self.mutex_acquired = True
   ```
   - Same uninitialized state problem

4. **Line 390: _on_audio_done() - Release attempt**
   ```python
   if self.mutex_acquired:
       from nevil_framework.microphone_mutex import microphone_mutex
       microphone_mutex.release_noisy_activity("speaking")
       self.mutex_acquired = False
   ```
   - If mutex was never acquired (due to initialization bug), this doesn't release
   - **Result:** Microphone remains muted forever!

### Symptoms of Bug

**Observed behavior:**
1. First TTS attempt may crash (AttributeError)
2. If it doesn't crash, subsequent attempts have unpredictable behavior
3. Microphone mutex state becomes out of sync with actual activity
4. Audio capture detects "speech" (which is actually Nevil's TTS)
5. Loop triggers again → infinite feedback

**Why the feedback loop happens:**
```
T=0:   on_text_response() tries to check mutex_acquired → CRASH or undefined
T=10:  If survives, mutex may not be acquired properly
T=100: TTS playing, microphone NOT muted
T=150: VAD detects TTS audio as "user speech"
T=200: Commits buffer to Realtime API
T=250: Realtime API generates response to Nevil's own speech
T=300: GOTO T=0 (loop)
```

---

## Data Flow Analysis

### 1. Message Bus Architecture

**Topics and Flow:**

```
voice_command (from speech_recognition_node22)
    ↓
ai_cognition_node ← processes, generates response
    ↓
text_response (published by ai_cognition_node)
    ↓
speech_synthesis_node22 ← generates TTS
    ↓
Realtime API ← requests audio
    ↓
response.audio.delta events ← buffers chunks
    ↓
response.audio.done ← saves WAV, plays
    ↓
playing_status (published by speech_synthesis_node22)
    ↓
speech_recognition_node22 ← receives, mutes microphone
```

### 2. Realtime API Event Handlers

#### AI Cognition Node Handlers (ai_node22.py:236-261)
- `response.text.delta` → _on_response_text_delta() (line 285)
- `response.text.done` → _on_response_text_done() (line 298)
- `response.audio.delta` → _on_response_audio_delta() (line 327)
- `response.audio.done` → _on_response_audio_done() (line 337)
- `response.function_call_arguments.delta` → _on_function_args_delta() (line 345)
- `response.function_call_arguments.done` → _on_function_args_done() (line 361)
- `conversation.item.created` → _on_conversation_item_created() (line 509)
- `response.done` → _on_response_done() (line 520)
- `input_audio_buffer.speech_started` → _on_speech_started() (line 529)
- `input_audio_buffer.speech_stopped` → _on_speech_stopped() (line 534)

#### Speech Recognition Node Handlers (speech_recognition_node22.py:176-188)
- `response.audio_transcript.delta` → _on_transcript_delta() (line 177)
- `response.audio_transcript.done` → _on_transcript_done() (line 182)
- `error` → _on_error_event() (line 186)

#### Speech Synthesis Node Handlers (speech_synthesis_node22.py:163-183)
- `response.audio.delta` → _on_audio_delta() (line 172)
- `response.audio.done` → _on_audio_done() (line 173)
- `response.audio_transcript.delta` → _on_transcript_delta() (line 176)
- `response.audio_transcript.done` → _on_transcript_done() (line 177)
- `response.output_item.added` → _on_output_item_added() (line 180)
- `response.done` → _on_response_done() (line 181)

### 3. Mutex State Transitions

**Expected sequence:**
```
IDLE
  ↓
User speaks
  ↓ audio_capture_manager: microphone available (mutex = 0)
  ↓ audio buffered and committed
  ↓
speech_recognition: transcribes audio
  ↓
AI Node: generates response
  ↓
Text Response Published
  ↓
speech_synthesis_node22.on_text_response()
  ↓ Acquire mutex (mutex = 1)
  ↓ Clear API buffer
  ↓ Request TTS from Realtime API
  ↓
Realtime API: generates audio
  ↓
Response Audio Done
  ↓ Play audio via robot_hat.Music()
  ↓ Release mutex (mutex = 0)
  ↓
IDLE - Ready for next user command
```

**Actual sequence (with bug):**
```
IDLE
  ↓
User speaks
  ↓ audio_capture_manager: microphone available (mutex = 0)
  ↓ audio buffered and committed
  ↓
speech_recognition: transcribes audio
  ↓
AI Node: generates response
  ↓
Text Response Published
  ↓
speech_synthesis_node22.on_text_response()
  ↓ AttributeError: 'mutex_acquired' not defined ❌
  ↓ Exception caught somewhere (maybe), execution continues
  ↓ Mutex NOT acquired (mutex = 0) ❌
  ↓ TTS audio generation starts
  ↓
audio_capture_manager: STILL ACTIVE (mutex still 0)
  ↓ Microphone captures Nevil's own TTS audio
  ↓ VAD detects it as "new user speech" ❌
  ↓ Buffer committed to Realtime API
  ↓
speech_recognition: Nevil's TTS transcribed as user input ❌
  ↓
AI Node: Generates response to Nevil's own speech ❌
  ↓
LOOP REPEATS INFINITELY ❌
```

---

## Configuration Issues

### Audio Configuration Mismatch

**speech_recognition_realtime/.messages (line 132):**
```yaml
chunk_size: 9600  # 200ms at 48kHz
sample_rate: 48000
```

**But audio_capture_manager.py defaults (lines 45-56):**
```python
sample_rate: int = 24000,  # DEFAULT 24kHz
chunk_size: int = 4800,     # DEFAULT 4800 samples
```

**Impact:** Configuration specifies 48kHz but code may use 24kHz
- Causes audio quality issues
- Chunk timing mismatches
- VAD detection may fail

---

## Specific Issues Found

### Issue 1: Uninitialized mutex_acquired Flag (CRITICAL)
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
- **Lines:** 228, 231, 314, 318, 390, 393, 403, 406, 503, 505
- **Severity:** CRITICAL
- **Cause:** Flag never initialized in `__init__()`
- **Fix:** Add `self.mutex_acquired = False` in `__init__()` (line ~115)

### Issue 2: Race Condition in on_text_response()
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
- **Lines:** 503-533
- **Severity:** HIGH
- **Cause:** Mutex acquired AFTER publishing speaking_status; should be BEFORE
- **Fix:** Reorder operations:
  1. Acquire mutex
  2. Clear API buffer
  3. Publish speaking_status
  4. Request audio

### Issue 3: Missing Initialization of mutex_acquired in __init__()
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
- **Location:** After line 114
- **Severity:** CRITICAL
- **Current code:** No initialization
- **Missing:** `self.mutex_acquired = False`

### Issue 4: Fallback Mutex Acquisition Too Late
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
- **Lines:** 227-232, 314-319
- **Severity:** MEDIUM
- **Cause:** Fallback acquisition in _on_audio_delta() is after Realtime API already generated audio
- **Fix:** Rely on on_text_response() to acquire upfront, remove fallback

### Issue 5: Error Handling for Release Without Acquire
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py`
- **Lines:** 390-394
- **Severity:** MEDIUM
- **Cause:** May try to release mutex that was never acquired
- **Fix:** Add error logging if release attempted but not acquired

### Issue 6: VAD Cooldown Prevents Multiple Responses
- **File:** `/home/dan/Nevil-picar-v3/nevil_framework/realtime/audio_capture_manager.py`
- **Lines:** 168-171, 686-693
- **Severity:** LOW-MEDIUM
- **Cause:** 2-second cooldown between commits prevents rapid back-and-forth
- **Context:** Designed to prevent API buffer errors but may cause missed user input

### Issue 7: No Session Management Between Nodes
- **File:** AI Node, Speech Recognition Node, Speech Synthesis Node
- **Severity:** MEDIUM
- **Cause:** Nodes don't share session state, possible duplicate connections
- **Impact:** Multiple Realtime API connections could be created
- **Fix:** Implement shared connection manager

---

## Conversation Flow Issues

### Issue A: Premature Speaking Status Publishing
- **When:** before mutex is acquired, before audio request sent
- **Result:** Other nodes think system is speaking before TTS actually starts
- **Fix:** Publish status AFTER mutex acquired and buffer cleared

### Issue B: No Response Cancellation on TTS Start
- **Current:** speech_synthesis_node22 requests audio while Realtime API may have in-progress responses
- **Result:** Multiple responses can be generated in parallel
- **Fix:** Send `response.cancel` before `response.create`

### Issue C: Audio Buffer Timing Issues
- **Problem:** 200ms delay added at line 718 for API to process chunks
- **Result:** May cause lag in transcription
- **Alternative:** Use proper event-based synchronization instead of sleep

---

## Recommended Fixes (Priority Order)

### Priority 1 (CRITICAL - Prevents infinite loop)
```python
# In speech_synthesis_node22.py __init__() after line 114:
self.mutex_acquired = False
```

### Priority 2 (HIGH - Ensures proper synchronization)
In `on_text_response()` (lines 503-533), reorder to:
1. Acquire mutex FIRST
2. Clear API buffer
3. Publish speaking status
4. Request audio

### Priority 3 (MEDIUM - Cleanup on error)
In `_on_audio_done()` cleanup section, add error handling for release attempts.

### Priority 4 (MEDIUM - Architecture improvement)
Implement shared Realtime connection manager to prevent duplicate connections.

### Priority 5 (LOW - Performance tuning)
Review VAD cooldown timeout (currently 2 seconds) and audio buffer timing.

---

## Testing Checklist

- [ ] Initialize `mutex_acquired = False` in `__init__()`
- [ ] Verify on_text_response() acquires mutex BEFORE audio request
- [ ] Verify audio capture discards audio when mutex is unavailable
- [ ] Test: User speaks → gets one response only (no loop)
- [ ] Test: Back-to-back questions (verify no dropped input)
- [ ] Test: TTS overlapping with user speech (verify no echo)
- [ ] Check mutex state transitions with `/tmp/nevil_mic_status.txt`
- [ ] Verify all mutex_acquired references after initialization exist
- [ ] Review error logs for AttributeError mentions

---

## Files Summary

### Core Realtime Framework
- `/home/dan/Nevil-picar-v3/nevil_framework/realtime/audio_capture_manager.py` - Microphone input (902 lines)
- `/home/dan/Nevil-picar-v3/nevil_framework/realtime/realtime_connection_manager.py` - WebSocket client
- `/home/dan/Nevil-picar-v3/nevil_framework/realtime/speech_synthesis_node22.py` - TTS node (586 lines) ⚠️ BUG HERE

### Node Implementations
- `/home/dan/Nevil-picar-v3/nodes/speech_recognition_realtime/speech_recognition_node22.py` - STT node (648 lines)
- `/home/dan/Nevil-picar-v3/nodes/ai_cognition_realtime/ai_node22.py` - AI cognition (685 lines)

### Synchronization
- `/home/dan/Nevil-picar-v3/nevil_framework/microphone_mutex.py` - Mutex implementation (100 lines)

### Configuration
- `/home/dan/Nevil-picar-v3/nevil_framework/realtime/.messages` - Framework config
- `/home/dan/Nevil-picar-v3/nodes/speech_recognition_realtime/.messages` - STT config
- `/home/dan/Nevil-picar-v3/nodes/speech_synthesis_realtime/.messages` - TTS config
- `/home/dan/Nevil-picar-v3/nodes/ai_cognition_realtime/.messages` - AI config

