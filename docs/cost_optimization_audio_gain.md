# Audio Gain Cost Optimization

## Problem
Currently applying 3x software gain to ALL audio (audio_capture_manager.py:868):
```python
audio_data = audio_data * 3.0  # Amplifies silence and noise!
```

**Issues**:
1. Amplifies ambient noise 3x
2. Triggers VAD on background sounds
3. Sends more audio chunks to API than necessary
4. Increases clipping risk

## Solution: Dynamic Compression + Hardware Gain

### Option 1: Use ALSA Hardware Gain (Recommended)
```bash
# Set microphone capture level to 80% (instead of software gain)
amixer -c 3 sset 'Mic' 80%

# Or for specific device
amixer -D hw:3 sset 'Mic' 80%
```

Then in `audio_capture_manager.py`:
```python
def _float32_to_pcm16(self, audio_data: np.ndarray) -> bytes:
    """Convert float32 audio to PCM16 bytes."""
    # NO software gain - use hardware gain instead
    # audio_data = audio_data * 3.0  # ← REMOVE THIS LINE

    # Clamp to valid range
    audio_data = np.clip(audio_data, -1.0, 1.0)

    # Convert to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)

    return audio_int16.tobytes()
```

### Option 2: Dynamic Compression (Voice-Only Gain)
```python
def _apply_dynamic_compression(self, audio_data: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    """Apply compression only to speech, not silence"""
    # Calculate RMS volume
    rms = np.sqrt(np.mean(audio_data ** 2))

    # Only amplify if above speech threshold
    if rms > threshold:
        # Apply compression (boost weak signals, limit strong)
        ratio = 2.0  # Compression ratio
        makeup_gain = 1.5  # Post-compression gain

        # Compress
        compressed = np.sign(audio_data) * np.power(np.abs(audio_data), 1.0 / ratio)

        # Apply makeup gain
        return compressed * makeup_gain
    else:
        # Below threshold - return original (don't amplify silence)
        return audio_data
```

Then modify `_float32_to_pcm16`:
```python
def _float32_to_pcm16(self, audio_data: np.ndarray) -> bytes:
    """Convert float32 audio to PCM16 bytes."""
    # Apply dynamic compression instead of flat 3x gain
    audio_data = self._apply_dynamic_compression(audio_data, threshold=0.08)

    # Clamp to valid range
    audio_data = np.clip(audio_data, -1.0, 1.0)

    # Convert to int16
    audio_int16 = (audio_data * 32767).astype(np.int16)

    return audio_int16.tobytes()
```

### Option 3: Noise Gate + Gain
```python
def _apply_noise_gate_and_gain(self, audio_data: np.ndarray, gate_threshold: float = 0.02) -> np.ndarray:
    """Silence audio below threshold, then apply gain"""
    # Calculate RMS
    rms = np.sqrt(np.mean(audio_data ** 2))

    # Noise gate
    if rms < gate_threshold:
        return audio_data * 0.0  # Silence

    # Above threshold - apply gain
    return audio_data * 2.5  # Reduced from 3.0
```

## Hardware Gain Setup (Raspberry Pi)

### Check Current Levels
```bash
# List audio devices
arecord -l

# Check current mixer settings for device 3 (your USB mic)
amixer -c 3 contents

# Check capture volume
amixer -c 3 sget 'Mic'
```

### Set Optimal Gain
```bash
# Set capture volume to 80% (prevents clipping)
amixer -c 3 sset 'Mic' 80%

# Enable auto gain control if available
amixer -c 3 sset 'Auto Gain Control' on

# Test capture level
arecord -D hw:3,0 -f S16_LE -r 24000 -c 1 -d 5 test.wav
aplay test.wav
```

### Persist Settings
Add to `/etc/asound.conf` or create init script:
```bash
#!/bin/bash
# /home/dan/Nevil-picar-v3/scripts/setup_microphone.sh

# Set mic gain to 80%
amixer -c 3 sset 'Mic' 80%

# Enable AGC if available
amixer -c 3 sset 'Auto Gain Control' on 2>/dev/null || true

echo "Microphone configured"
```

## Testing

### Before (3x software gain)
```bash
# Record 10 seconds of silence
arecord -D hw:3,0 -f S16_LE -r 24000 -c 1 -d 10 silence_test.wav

# Check if silence triggers VAD (it shouldn't!)
```

### After (hardware gain)
```bash
# Test speech detection sensitivity
# Speak at normal volume and verify VAD triggers correctly
```

## Expected Savings
- **VAD false positives**: 60-80% reduction
- **Unnecessary audio chunks**: 15-20% reduction
- **API audio costs**: 15-20% savings
- **Audio quality**: Improved (less clipping, cleaner silence)

## Migration Checklist
- [ ] Backup current audio settings: `amixer -c 3 contents > mixer_backup.txt`
- [ ] Test hardware gain levels (50%, 70%, 80%, 90%)
- [ ] Remove software gain from audio_capture_manager.py:868
- [ ] Test VAD sensitivity with new gain
- [ ] Create startup script to set gain on boot
- [ ] Monitor audio levels for 24 hours
- [ ] Adjust threshold if needed
