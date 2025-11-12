# ⚠️ CRITICAL: AUDIO PLAYBACK PRESERVATION WARNING

## THIS IS MAKE-OR-BREAK CRITICAL

**DO NOT CHANGE THE AUDIO PLAYBACK METHOD UNDER ANY CIRCUMSTANCES**

---

## What MUST Stay EXACTLY The Same

### Hardware-Specific Playback (UNTOUCHABLE)

```python
# File: audio/audio_output.py
# Lines 44-48, 127-147

from robot_hat import Music

class AudioOutput:
    def __init__(self):
        # CRITICAL: Hardware-specific initialization
        os.popen("pinctrl set 20 op dh")  # Enable robot_hat speaker switch
        self.music = Music()  # robot_hat.Music() - DO NOT REPLACE

    def play_loaded_speech(self):
        # CRITICAL: Uses robot_hat.Music() for HiFiBerry DAC
        play_audio_file(self.music, self.tts_file)
```

**This code is:**
- Hardware-specific for HiFiBerry DAC on Raspberry Pi
- Tested and working in production
- Required for proper audio output on the robot
- **CANNOT BE CHANGED WITHOUT BREAKING THE ROBOT**

---

## Why This Cannot Be Changed

1. **Hardware Dependency**: robot_hat.Music() is specifically designed for:
   - HiFiBerry DAC
   - Raspberry Pi GPIO pin 20 (speaker switch)
   - Specific audio routing on the robot hardware

2. **Production Stability**: Current system works perfectly with:
   - Correct volume levels
   - No audio glitches
   - Reliable playback
   - Proper hardware initialization

3. **No Alternative Works**: PyAudio, pygame.mixer, or other libraries:
   - Don't handle GPIO pin 20 speaker switch
   - Don't route audio correctly to HiFiBerry DAC
   - Would require extensive hardware testing
   - Risk breaking working audio

---

## What CAN Change (Audio Generation)

### Current v3.0 Pipeline
```
User speaks → STT → AI response → OpenAI TTS API (batch) → WAV file → robot_hat.Music() plays
                                  ^^^^^^^^^^^^^^^^^^^^^^^^
                                  SLOW (1-2 seconds)
```

### New v2.2 Pipeline (CORRECT)
```
User speaks → STT → AI response → OpenAI Realtime API (stream) → buffer → WAV file → robot_hat.Music() plays
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^       ^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
                                  FASTER (200-400ms)                      Same WAV    EXACT SAME PLAYBACK
```

**Key Point**: We change HOW we generate the audio bytes, but NOT how we play them.

---

## Correct speech_synthesis_node22 Implementation

```python
class SpeechSynthesisNode22(NevilNode):
    """
    ⚠️ CRITICAL: This node uses EXACT same playback as v3.0

    Changes:
    - Audio generation: Realtime API streaming (FASTER)

    Preserved:
    - Audio playback: robot_hat.Music() (UNCHANGED)
    """

    def __init__(self):
        super().__init__("speech_synthesis_realtime")

        # ⚠️ CRITICAL: Use EXACT same audio output class
        # This contains robot_hat.Music() - DO NOT REPLACE
        from audio.audio_output import AudioOutput
        self.audio_output = AudioOutput()

        # NEW: Buffer for streaming audio chunks from Realtime API
        self.audio_buffer = []
        self.realtime_manager = None  # WebSocket connection

    def initialize(self):
        # Register Realtime API event handlers
        self.realtime_manager.register_event_handler(
            "response.audio.delta",
            self._on_audio_delta
        )
        self.realtime_manager.register_event_handler(
            "response.audio.done",
            self._on_audio_done
        )

    def _on_audio_delta(self, event):
        """
        Receive streaming audio chunk from Realtime API.
        Buffer it in memory - do NOT play yet.
        """
        audio_chunk = base64.b64decode(event['delta'])
        self.audio_buffer.append(audio_chunk)

    def _on_audio_done(self, event):
        """
        All audio received. Now save to WAV and play.

        ⚠️ CRITICAL: Playback uses EXACT v3.0 method
        """
        # 1. Concatenate all buffered chunks
        complete_audio = b''.join(self.audio_buffer)

        # 2. Save to WAV file (REQUIRED for robot_hat.Music())
        from audio.audio_utils import generate_tts_filename
        wav_file, _ = generate_tts_filename(volume_db=-10)

        # Convert PCM16 bytes to WAV format
        self._save_pcm16_to_wav(complete_audio, wav_file, sample_rate=24000)

        # 3. ⚠️ CRITICAL: Use EXACT existing playback method
        # DO NOT CHANGE - uses robot_hat.Music()
        self.audio_output.tts_file = wav_file
        with self.audio_output.speech_lock:
            self.audio_output.speech_loaded = True

        # This calls play_audio_file(self.music, wav_file) internally
        self.audio_output.play_loaded_speech()

        # 4. Clear buffer for next response
        self.audio_buffer.clear()

    def _save_pcm16_to_wav(self, pcm_data, output_file, sample_rate=24000):
        """Save raw PCM16 bytes to WAV file."""
        import wave
        import struct

        with wave.open(output_file, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(pcm_data)
```

---

## What's Different in v2.2

| Aspect | v3.0 | v2.2 | Same? |
|--------|------|------|-------|
| **Audio Generation** | OpenAI TTS API (batch) | Realtime API (streaming) | ❌ Changed |
| **Generation Time** | 1-2 seconds | 200-400ms | ❌ Faster |
| **Audio Format** | PCM16 WAV file | PCM16 WAV file | ✅ Same |
| **Playback Method** | robot_hat.Music() | robot_hat.Music() | ✅ **IDENTICAL** |
| **Playback Code** | audio/audio_output.py | audio/audio_output.py | ✅ **UNCHANGED** |
| **Hardware Support** | HiFiBerry DAC | HiFiBerry DAC | ✅ Same |
| **GPIO Pin 20** | Enabled | Enabled | ✅ Same |

---

## Testing Checklist

Before deploying speech_synthesis_node22:

- [ ] Verify it imports `AudioOutput` from `audio/audio_output.py`
- [ ] Verify it uses `self.audio_output.music` (robot_hat.Music())
- [ ] Verify it calls `play_audio_file()` or `play_loaded_speech()`
- [ ] Verify it does NOT import PyAudio
- [ ] Verify it does NOT create alternative playback methods
- [ ] Verify WAV files are saved before playback
- [ ] Test on actual robot hardware (not laptop!)
- [ ] Confirm GPIO pin 20 is enabled
- [ ] Confirm HiFiBerry DAC receives audio
- [ ] Confirm volume levels are correct

---

## Common Mistakes to Avoid

### ❌ WRONG: Using PyAudio for Playback
```python
# DO NOT DO THIS
import pyaudio
p = pyaudio.PyAudio()
stream = p.open(...)
stream.write(audio_data)  # ❌ Wrong! Doesn't work with HiFiBerry
```

### ❌ WRONG: Direct Audio Streaming
```python
# DO NOT DO THIS
def play_audio_stream(self, audio_data):
    # Some custom playback code
    pass  # ❌ Wrong! robot_hat.Music() required
```

### ❌ WRONG: Replacing AudioOutput Class
```python
# DO NOT DO THIS
class NewAudioOutput:
    def play(self, audio):
        # Custom implementation
        pass  # ❌ Wrong! Must use existing AudioOutput
```

### ✅ CORRECT: Using Existing AudioOutput
```python
# DO THIS
from audio.audio_output import AudioOutput
self.audio_output = AudioOutput()  # ✅ Contains robot_hat.Music()

# Save streaming audio to WAV
wav_file = "/tmp/tts_realtime.wav"
save_pcm16_to_wav(audio_data, wav_file)

# Use EXACT existing playback
self.audio_output.tts_file = wav_file
self.audio_output.play_loaded_speech()  # ✅ Uses robot_hat.Music()
```

---

## Summary

### The Rule
**Generate audio however you want (streaming, batch, etc.), but ALWAYS play through robot_hat.Music()**

### The Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ Audio Generation (CAN CHANGE)                                │
│ - OpenAI Realtime API streaming                              │
│ - Buffer chunks in memory                                    │
│ - Save complete audio to WAV file                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Audio Playback (CANNOT CHANGE)                               │
│ - robot_hat.Music()                                          │
│ - play_audio_file()                                          │
│ - HiFiBerry DAC routing                                      │
│ - GPIO pin 20 speaker switch                                 │
└─────────────────────────────────────────────────────────────┘
```

### The Files
- **CAN MODIFY**: `nodes/speech_synthesis_realtime/` (new code)
- **CANNOT TOUCH**: `audio/audio_output.py` (existing playback)
- **CANNOT REPLACE**: robot_hat.Music() usage

---

## Contact for Questions

If you have ANY doubt about whether something breaks this requirement:
1. Check: Does it use `robot_hat.Music()`?
2. Check: Does it call functions from `audio/audio_output.py`?
3. Check: Does it save to WAV file first?

If answer to any is "no" → **DON'T DO IT**

**THIS IS MAKE-OR-BREAK CRITICAL FOR ROBOT FUNCTIONALITY**
