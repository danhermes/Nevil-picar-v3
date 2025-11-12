# Nevil 2.2 - CORRECTED Architecture Summary

## ⚠️ CRITICAL CORRECTION: Audio Playback Preservation

**Original Design Error**: Proposed using PyAudio for direct audio streaming
**Corrected Design**: Uses robot_hat.Music() playback (EXACT same as v3.0)

---

## What Changed vs Original Design

### ❌ REMOVED: PyAudio Direct Streaming
```python
# ORIGINAL (WRONG):
import pyaudio
stream = pyaudio.PyAudio().open(...)
stream.write(audio_chunks)  # ❌ Breaks hardware compatibility
```

### ✅ CORRECTED: robot_hat.Music() Playback
```python
# CORRECTED (RIGHT):
from audio.audio_output import AudioOutput
audio_output = AudioOutput()  # Contains robot_hat.Music()
audio_output.play_loaded_speech()  # ✅ Hardware-compatible
```

---

## Corrected Node Architectures

### speech_recognition_node22 (No Change)
✅ **Status**: Original design is correct

- Continuous audio streaming INPUT via Realtime API
- WebSocket connection for bidirectional audio
- Server-side Voice Activity Detection
- Publishes voice_command to message bus

**This node is UNCHANGED from original design.**

### ai_node22 (No Change)
✅ **Status**: Original design is correct

- Streaming conversation processing
- Function calling for 106 gestures
- Camera integration (multimodal)
- Publishes text_response and robot_action

**This node is UNCHANGED from original design.**

### speech_synthesis_node22 (CRITICAL CORRECTION)
⚠️ **Status**: CORRECTED to preserve robot_hat.Music()

#### Original Design (WRONG)
```python
class SpeechSynthesisNode22(NevilNode):
    def __init__(self):
        # ❌ WRONG: Used PyAudio for direct streaming
        import pyaudio
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(...)

    def _on_audio_delta(self, event):
        # ❌ WRONG: Direct streaming to speakers
        audio_chunk = base64.b64decode(event['delta'])
        self.stream.write(audio_chunk)  # Breaks hardware!
```

#### Corrected Design (RIGHT)
```python
class SpeechSynthesisNode22(NevilNode):
    """
    ⚠️ CRITICAL: Uses EXACT same playback as v3.0 (robot_hat.Music())

    What Changed:
    - Audio generation: Realtime API streaming (FASTER)

    What Stayed Same:
    - Audio playback: robot_hat.Music() (UNCHANGED)
    - File: audio/audio_output.py (UNTOUCHED)
    """

    def __init__(self):
        super().__init__("speech_synthesis_realtime")

        # ✅ CORRECT: Use existing AudioOutput with robot_hat.Music()
        from audio.audio_output import AudioOutput
        self.audio_output = AudioOutput()

        # Buffer for streaming audio from Realtime API
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()

        # WebSocket connection manager
        self.realtime_manager = None

    def initialize(self):
        """Initialize and register Realtime API event handlers."""
        # Register for streaming audio events
        self.realtime_manager.register_event_handler(
            "response.audio.delta",
            self._on_audio_delta
        )
        self.realtime_manager.register_event_handler(
            "response.audio.done",
            self._on_audio_done
        )
        self.realtime_manager.register_event_handler(
            "response.audio_transcript.delta",
            self._on_transcript_delta
        )

    def _on_audio_delta(self, event):
        """
        Buffer streaming audio chunks (do NOT play yet).

        ⚠️ CRITICAL: Only buffers - does NOT do playback
        """
        audio_chunk = base64.b64decode(event['delta'])
        with self.buffer_lock:
            self.audio_buffer.append(audio_chunk)

        self.logger.debug(f"Buffered audio chunk: {len(audio_chunk)} bytes")

    def _on_audio_done(self, event):
        """
        Audio complete. Save to WAV and play via robot_hat.Music().

        ⚠️ CRITICAL: This is where we use EXISTING playback method
        """
        # 1. Concatenate all buffered chunks
        with self.buffer_lock:
            complete_audio = b''.join(self.audio_buffer)
            self.audio_buffer.clear()

        self.logger.info(f"Audio generation complete: {len(complete_audio)} bytes")

        # 2. Save to WAV file (REQUIRED for robot_hat.Music())
        from audio.audio_utils import generate_tts_filename
        wav_file, _ = generate_tts_filename(volume_db=-10)

        # Convert PCM16 to WAV format
        self._save_pcm16_to_wav(complete_audio, wav_file, sample_rate=24000)
        self.logger.info(f"Saved audio to: {wav_file}")

        # 3. ⚠️ CRITICAL: Use EXACT existing playback method
        # This is the same code path as v3.0 speech_synthesis_node
        self.audio_output.tts_file = wav_file
        with self.audio_output.speech_lock:
            self.audio_output.speech_loaded = True

        # Publish speaking status
        self._publish_speaking_status(True, "", "alloy")

        # This internally calls play_audio_file(self.music, wav_file)
        # which uses robot_hat.Music() - DO NOT CHANGE
        success = self.audio_output.play_loaded_speech()

        # Publish completion
        self._publish_speaking_status(False, "", "alloy")

        if success:
            self.logger.info("✅ Playback complete (robot_hat.Music())")
        else:
            self.logger.error("❌ Playback failed")

    def _save_pcm16_to_wav(self, pcm_data, output_file, sample_rate=24000):
        """Save raw PCM16 bytes to WAV file."""
        import wave

        with wave.open(output_file, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit PCM
            wav.setframerate(sample_rate)
            wav.writeframes(pcm_data)

    def _publish_speaking_status(self, speaking, text, voice):
        """Publish speaking status (same as v3.0)."""
        status_data = {
            "speaking": speaking,
            "text": text,
            "voice": voice,
            "progress": 1.0 if not speaking else 0.0,
            "timestamp": time.time()
        }
        self.publish("speaking_status", status_data)

    def on_text_response(self, message):
        """
        Handle text response (trigger TTS via Realtime API).

        ⚠️ CRITICAL: This requests audio from Realtime API,
        but playback still uses robot_hat.Music()
        """
        text = message.data.get("text", "")
        if not text.strip():
            return

        # Send to Realtime API for audio generation
        self.realtime_manager.send_event({
            "type": "response.create",
            "response": {
                "modalities": ["audio", "text"],
                "instructions": text,
                "voice": "alloy"
            }
        })

        self.logger.info(f"Requested TTS from Realtime API: '{text[:50]}'")

    def cleanup(self):
        """Cleanup (same as v3.0)."""
        if self.audio_output:
            self.audio_output.stop_playback()
            self.audio_output.cleanup()
```

---

## Architecture Comparison

### v3.0 (Current - Batch API)
```
Text → OpenAI TTS API (1-2s) → WAV file → robot_hat.Music() plays
       ^^^^^^^^^^^^^^^^^^^^^               ^^^^^^^^^^^^^^^^^^^^^^^^
       Batch generation                    Hardware playback
```

### v2.2 ORIGINAL (WRONG - PyAudio)
```
Text → Realtime API stream → PyAudio direct play ❌ BREAKS HARDWARE
       ^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^
       Streaming generation    Wrong playback method
```

### v2.2 CORRECTED (RIGHT - robot_hat.Music())
```
Text → Realtime API stream → Buffer → WAV file → robot_hat.Music() plays
       ^^^^^^^^^^^^^^^^^^^^                       ^^^^^^^^^^^^^^^^^^^^^^^^
       Streaming generation                       SAME hardware playback
       (200-400ms faster)                         (UNCHANGED from v3.0)
```

---

## File Changes Summary

### Files That Change
| File | Status | Purpose |
|------|--------|---------|
| `nodes/speech_recognition_realtime/speech_recognition_node22.py` | NEW | Streaming STT |
| `nodes/ai_cognition_realtime/ai_node22.py` | NEW | Streaming AI |
| `nodes/speech_synthesis_realtime/speech_synthesis_node22.py` | NEW | Buffer streaming TTS |
| `nevil_framework/realtime/realtime_connection_manager.py` | NEW | WebSocket manager |
| `nevil_framework/realtime/audio_capture_manager.py` | NEW | Mic input streaming |
| `nevil_framework/realtime/audio_buffer_manager.py` | NEW | Buffer audio chunks |

### Files That NEVER Change
| File | Status | Purpose |
|------|--------|---------|
| `audio/audio_output.py` | **UNTOUCHABLE** | robot_hat.Music() playback |
| `audio/audio_utils.py` | **UNTOUCHABLE** | play_audio_file() function |
| Hardware GPIO pin 20 | **UNTOUCHABLE** | Speaker switch enable |
| robot_hat library | **UNTOUCHABLE** | Hardware abstraction |

---

## Performance Comparison (Corrected)

### v3.0 (Batch API)
- STT: 1-3 seconds (Whisper API)
- AI: 2-4 seconds (GPT-4o)
- TTS: 1-2 seconds (OpenAI TTS API)
- **Total**: 5-8 seconds

### v2.2 (Streaming - Corrected Architecture)
- STT: 200-400ms (Realtime API streaming)
- AI: 100-300ms (Realtime API streaming)
- TTS Generation: 200-400ms (Realtime API streaming)
- TTS Playback: ~1 second (robot_hat.Music() - SAME as v3.0)
- **Total**: 1.5-2.1 seconds

**Improvement**: 3-4x faster (not 10x, because playback time stays same)

---

## Latency Breakdown

### What Gets Faster (Realtime API)
- ✅ Speech recognition: 1-3s → 200-400ms (75-87% reduction)
- ✅ AI processing: 2-4s → 100-300ms (92-95% reduction)
- ✅ TTS generation: 1-2s → 200-400ms (80-90% reduction)

### What Stays Same (Hardware Playback)
- ❌ TTS playback: ~1s → ~1s (NO CHANGE)
  - This is robot_hat.Music() playing WAV file
  - Hardware-dependent, cannot be sped up
  - MUST preserve for hardware compatibility

**Total Improvement**: 75-80% latency reduction (realistic)

---

## Testing Requirements

### Before Deployment Checklist

- [ ] speech_synthesis_node22 imports `AudioOutput` from `audio/audio_output.py`
- [ ] speech_synthesis_node22 uses `self.audio_output.music` (robot_hat.Music())
- [ ] speech_synthesis_node22 calls `play_loaded_speech()` for playback
- [ ] speech_synthesis_node22 does NOT import PyAudio
- [ ] speech_synthesis_node22 does NOT create alternative playback
- [ ] speech_synthesis_node22 saves to WAV file before playback
- [ ] Test on actual robot hardware (Raspberry Pi + HiFiBerry DAC)
- [ ] Verify GPIO pin 20 is enabled
- [ ] Verify audio routes to correct hardware
- [ ] Verify volume levels match v3.0

---

## Summary of Correction

### What Was Wrong
- Original design used PyAudio for direct audio streaming
- Would break hardware compatibility with HiFiBerry DAC
- Would bypass GPIO pin 20 speaker switch
- Would not work on actual robot

### What's Corrected
- ✅ Use Realtime API for GENERATION (faster)
- ✅ Buffer streaming audio in memory
- ✅ Save complete audio to WAV file
- ✅ Use EXACT v3.0 playback (robot_hat.Music())
- ✅ Preserve hardware compatibility

### The Rule
**Generate audio however you want, but ALWAYS play through robot_hat.Music()**

---

## Files to Read

1. **CRITICAL WARNING**: `docs/CRITICAL_AUDIO_PLAYBACK_WARNING.md`
2. **Corrected Plan**: `docs/NEVIL_2.2_ZERO_TOUCH_PLAN.md` (updated)
3. **This Summary**: `docs/NEVIL_2.2_CORRECTED_ARCHITECTURE.md`

**READ THE CRITICAL WARNING FIRST BEFORE ANY IMPLEMENTATION**
