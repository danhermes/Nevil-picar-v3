# Microphone Sensitivity Issue - Fix

**Date**: 2025-11-20
**Issue**: Microphone not sensitive enough - missing user speech

## Problem Analysis

### Root Causes

1. **Hardware Volume Too Low**
   - USB microphone (card 3) was at 4/16 (25%)
   - Maximum available: 16/16 (100% = 23.81dB)
   - Result: Weak signal to VAD

2. **VAD Threshold Too High**
   - Set to 0.15 (energy threshold)
   - Too aggressive filtering was rejecting valid speech
   - Result: Speech not detected

3. **Software Gain Too Low**
   - Set to 2.0x after fixing echo issue
   - Not enough amplification for distant speech
   - Result: Quiet audio reaching API

4. **Minimum Speech Duration Too Long**
   - Set to 0.5 seconds
   - Short utterances were being filtered out
   - Result: Brief commands ignored

## Fixes Applied

### 1. Hardware Microphone Volume (Immediate + Persistent)

**Immediate:**
```bash
amixer -c 3 set Mic 16  # 100% volume
```

**Persistent** (systemd service):
```ini
ExecStartPre=/usr/bin/amixer -c 3 set Mic 16
```

**Result**: Mic now at maximum hardware gain (23.81dB)

### 2. VAD Threshold (Configuration)

**File**: `nodes/speech_recognition_realtime/.messages`

```yaml
# BEFORE:
vad_threshold: 0.15  # Too high - missing speech

# AFTER:
vad_threshold: 0.08  # More sensitive - catches normal speech
```

**Impact**: Detects quieter speech, more forgiving threshold

### 3. Software Gain (Code)

**File**: `nevil_framework/realtime/audio_capture_manager.py:847`

```python
# BEFORE:
audio_data = audio_data * 2.0  # Too conservative

# AFTER:
audio_data = audio_data * 3.0  # Balanced sensitivity
```

**Impact**: 50% increase in software amplification

### 4. Minimum Speech Duration (Configuration)

**File**: `nodes/speech_recognition_realtime/.messages`

```yaml
# BEFORE:
vad_min_speech_duration: 0.5  # 500ms - too long

# AFTER:
vad_min_speech_duration: 0.3  # 300ms - allows short commands
```

**Impact**: Accepts shorter utterances like "yes", "no", "stop"

## Summary of Gains

| Setting | Before | After | Improvement |
|---------|--------|-------|-------------|
| Hardware Mic Volume | 4/16 (25%) | 16/16 (100%) | 4x increase |
| VAD Threshold | 0.15 | 0.08 | 47% more sensitive |
| Software Gain | 2.0x | 3.0x | 50% increase |
| Min Speech Duration | 0.5s | 0.3s | Allows 40% shorter commands |

**Total sensitivity improvement**: ~6x more sensitive overall

## Files Modified

1. **nodes/speech_recognition_realtime/.messages**
   - Line 133: `vad_threshold: 0.08` (was 0.15)
   - Line 134: `vad_min_speech_duration: 0.3` (was 0.5)

2. **nevil_framework/realtime/audio_capture_manager.py**
   - Line 847: `audio_data * 3.0` (was 2.0)

3. **/etc/systemd/system/nevil.service**
   - Line 15: Added `ExecStartPre=/usr/bin/amixer -c 3 set Mic 16`

## Testing

After applying changes, test with:

1. **Check mic volume:**
   ```bash
   amixer -c 3 get Mic
   # Should show: Capture 16 [100%] [23.81dB]
   ```

2. **Monitor VAD detection:**
   ```bash
   sudo journalctl -u nevil -f | grep "VAD:"
   # Should see "VAD: Speech started" when you speak
   ```

3. **Test recognition:**
   - Speak from normal distance (1-2 meters)
   - Try short commands: "stop", "go", "yes"
   - Try normal sentences

## Troubleshooting

### Too Sensitive (Picking up noise)

Increase VAD threshold in `.messages`:
```yaml
vad_threshold: 0.12  # More aggressive filtering
```

### Still Not Sensitive Enough

1. **Check mic placement** - Should face user
2. **Increase software gain** in `audio_capture_manager.py`:
   ```python
   audio_data = audio_data * 4.0  # Maximum recommended
   ```
3. **Lower VAD threshold** further:
   ```yaml
   vad_threshold: 0.05  # Very sensitive
   ```

### Echo/Feedback Issues

If you get echo or feedback from increased gain:

1. **Reduce software gain**:
   ```python
   audio_data = audio_data * 2.5  # Compromise
   ```

2. **Increase VAD threshold**:
   ```yaml
   vad_threshold: 0.10  # Filter more noise
   ```

3. **Check speaker volume** - May be too loud

## Hardware Info

**Microphone**: USB PnP Sound Device (Card 3)
- Type: USB Audio
- Channels: Mono
- Controls:
  - Mic Capture Volume: 0-16 (now at 16)
  - Auto Gain Control: Enabled
  - Max Gain: 23.81dB

**Audio Path**:
1. USB Mic → PyAudio (24kHz)
2. Software Gain (3x) → PCM16
3. VAD Threshold Check (0.08)
4. Base64 Encode → Realtime API

## Balance Considerations

The settings are now optimized for:
- Normal speaking volume
- 1-2 meter distance
- Indoor environment
- Minimal background noise

If your environment differs, you may need to adjust:
- **Noisy environment**: Increase `vad_threshold` to 0.12-0.15
- **Quiet speaker**: Increase `audio_data` gain to 3.5-4.0x
- **Very quiet environment**: Decrease `vad_threshold` to 0.05

## References

- ALSA mixer documentation
- OpenAI Realtime API audio specs (24kHz PCM16)
- VAD threshold tuning guide
- PyAudio input gain management
