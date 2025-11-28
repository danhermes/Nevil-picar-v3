# Dynamic Audio Threshold Configuration

## Overview

Nevil supports **automatic dynamic threshold adjustment** that continuously adapts to ambient noise levels without manual tuning. This is ideal for environments with varying background noise like coffee shops, conferences, and parties.

---

## Quick Start

**Status**: ✅ ENABLED (as of latest configuration)

**Location**: `audio/audio_input.py:51-54`

No manual tuning required - the system automatically adjusts to your environment!

---

## How Dynamic Thresholds Work

### Automatic Adaptation Process

1. **Initial Threshold**: Starts at 1500 energy units
2. **Background Monitoring**: Continuously tracks ambient noise floor
3. **Auto-Adjustment**:
   - **Noisy environment** → Raises threshold (filters more noise)
   - **Quiet environment** → Lowers threshold (more sensitive)
4. **Speech Detection**: Triggers when audio exceeds `threshold × ratio`
5. **Continuous Learning**: Updates threshold based on non-speech audio

### Benefits Over Static Thresholds

- **No manual tuning** for different rooms
- **Adapts to changing conditions** (HVAC cycles, crowd noise)
- **Handles transitions** (moving from quiet to noisy areas)
- **Prevents false triggers** from sustained background noise
- **Maintains sensitivity** to legitimate speech

---

## Configuration Parameters

### Current Settings (Optimized for Variable Environments)

```python
# File: audio/audio_input.py:51-54

self.recognizer.dynamic_energy_threshold = True     # ✅ ENABLED
self.recognizer.energy_threshold = 1500            # Initial baseline
self.recognizer.dynamic_energy_adjustment_damping = 0.15  # Adaptation speed
self.recognizer.dynamic_energy_ratio = 1.5         # Sensitivity multiplier
```

---

## Parameter Reference

### 1. `dynamic_energy_threshold` (Boolean)

**Purpose**: Master enable/disable for automatic adaptation

- `True`: Auto-adjusts to ambient noise (recommended)
- `False`: Uses static `energy_threshold` value

**Recommendation**: Always `True` unless debugging

---

### 2. `energy_threshold` (Integer: 50-4000)

**Purpose**: Initial threshold when dynamic mode starts

- **Lower values (300-800)**: More sensitive, picks up quieter speech
- **Medium values (1000-2000)**: Balanced for normal environments (current: 1500)
- **Higher values (2500-4000)**: Less sensitive, filters aggressive noise

**Note**: When `dynamic_energy_threshold = True`, this is the **starting point** only. The system will adjust it automatically.

**Recommendation**: Keep at 1500 unless you have specific environment constraints

---

### 3. `dynamic_energy_adjustment_damping` (Float: 0.0-1.0)

**Purpose**: Controls how quickly the threshold adapts to changes

**Formula**:
```
new_threshold = old_threshold + (measured_noise - old_threshold) × damping
```

**Values**:
- **0.05-0.10**: Very slow adaptation (stable, long-term environments)
- **0.10-0.15**: Moderate adaptation (normal use, current: 0.15)
- **0.15-0.25**: Fast adaptation (changing environments)
- **0.25-0.50**: Very fast adaptation (highly variable noise)

**Current Setting**: `0.15` (balanced)

**Use Cases**:
- **0.10**: Quiet home office with stable HVAC
- **0.15**: Normal office with moderate activity (current)
- **0.20**: Coffee shop with varying customer volume
- **0.25**: Conference with people moving around
- **0.30**: Party or outdoor with rapid noise changes

---

### 4. `dynamic_energy_ratio` (Float: 1.0-3.0)

**Purpose**: Multiplier for speech detection sensitivity

**How It Works**:
```
speech_detected = current_energy > (dynamic_threshold × ratio)
```

**Values**:
- **1.0-1.2**: Very conservative, only loud/clear speech
- **1.2-1.5**: Moderate sensitivity (current: 1.5)
- **1.5-2.0**: High sensitivity, picks up quieter speech
- **2.0-3.0**: Maximum sensitivity, may increase false positives

**Current Setting**: `1.5` (moderately sensitive)

**Use Cases**:
- **1.2**: Very loud environment, close-talking mic
- **1.5**: Normal distance, moderate noise (current)
- **1.7**: Coffee shop, need to hear over ambient chatter
- **2.0**: Party/conference, distant speaker
- **2.5**: Outdoor or very noisy environment

---

## Environment-Specific Tuning

### Quiet Home/Office
```python
dynamic_energy_adjustment_damping = 0.10  # Slow, stable
dynamic_energy_ratio = 1.3               # Conservative
```

**Why**: Stable environment doesn't need fast adaptation

---

### Normal Office (Current Default)
```python
dynamic_energy_adjustment_damping = 0.15  # Balanced ✅
dynamic_energy_ratio = 1.5               # Moderate ✅
```

**Why**: Handles typical office noise variations

---

### Coffee Shop
```python
dynamic_energy_adjustment_damping = 0.20  # Faster adaptation
dynamic_energy_ratio = 1.7               # More sensitive
```

**Why**: Customer volume varies, espresso machine cycles, music

---

### Party/Conference
```python
dynamic_energy_adjustment_damping = 0.25  # Fast adaptation
dynamic_energy_ratio = 2.0               # High sensitivity
```

**Why**: Crowd noise fluctuates rapidly, need to catch speech over chatter

---

### Outdoor (Wind/Traffic)
```python
dynamic_energy_adjustment_damping = 0.30  # Very fast
dynamic_energy_ratio = 2.2               # Maximum sensitivity
energy_threshold = 2000                  # Higher baseline
```

**Why**: Wind gusts and traffic create sudden noise spikes

**Note**: Also recommend physical windscreen on microphone

---

## Complementary Audio Settings

Dynamic thresholds work with other audio parameters:

### Pause Detection
```python
self.recognizer.pause_threshold = 0.5  # Seconds of silence to end phrase
```

- **Shorter (0.3-0.4s)**: More responsive, may cut off slow speakers
- **Longer (0.6-0.8s)**: Waits for complete thoughts, may feel sluggish

---

### Phrase Filtering
```python
self.phrase_threshold = 0.5  # Minimum speaking duration
```

- **Shorter (0.3s)**: Catches brief commands, more false positives
- **Longer (0.7s)**: Filters coughs/clicks, may miss quick phrases

---

### Timeout
```python
self.recognizer.operation_timeout = 18  # Max seconds waiting for speech
```

- Adjust if users speak slowly or take long pauses

---

## Hardware Settings

### Microphone Volume (Current: 100% / +23.81dB)

```bash
# Check current volume
amixer -c 3 get Mic

# Adjust (0-16, current: 16)
amixer -c 3 set Mic 16  # Maximum
amixer -c 3 set Mic 12  # 75% (for very loud environments)
```

### Auto Gain Control (Current: ENABLED)

```bash
# Check status
amixer -c 3 get 'Auto Gain Control'

# Enable (recommended for dynamic thresholds)
amixer -c 3 set 'Auto Gain Control' on

# Disable (if AGC conflicts with dynamic threshold)
amixer -c 3 set 'Auto Gain Control' off
```

**Recommendation**: Keep AGC **enabled** with dynamic thresholds for best adaptation

---

## Testing Dynamic Thresholds

### Verify It's Working

1. **Start Nevil** in a quiet environment
2. **Speak normally** - should respond reliably
3. **Increase noise** (music, fan, conversation)
4. **Wait 5-10 seconds** - dynamic threshold adapts
5. **Speak again** - should still respond (may need slightly louder voice)
6. **Return to quiet** - threshold lowers again within 10-20 seconds

### Signs It's Adapting Properly

✅ **Good**:
- Responds in both quiet and noisy environments
- Fewer false triggers when HVAC kicks on
- Doesn't miss speech when background music starts
- Adjusts smoothly when moving between rooms

❌ **Needs Tuning**:
- Constantly missing speech in noisy areas → Increase `ratio` or `damping`
- Too many false triggers from background noise → Decrease `ratio`
- Slow to adapt when environment changes → Increase `damping`
- Adapts too aggressively, threshold "hunting" → Decrease `damping`

---

## Troubleshooting

### Problem: Missing Speech in Noisy Environments

**Symptoms**: Works in quiet room, fails in coffee shop

**Solutions**:
1. Increase sensitivity ratio:
   ```python
   dynamic_energy_ratio = 2.0  # Was 1.5
   ```

2. Speed up adaptation:
   ```python
   dynamic_energy_adjustment_damping = 0.25  # Was 0.15
   ```

3. Check microphone volume:
   ```bash
   amixer -c 3 set Mic 16  # Ensure at maximum
   ```

---

### Problem: False Triggers from Background Noise

**Symptoms**: Responds to HVAC, music, or ambient sounds

**Solutions**:
1. Decrease sensitivity ratio:
   ```python
   dynamic_energy_ratio = 1.3  # Was 1.5
   ```

2. Increase minimum speech duration:
   ```python
   phrase_threshold = 0.7  # Was 0.5
   ```

3. Ensure dynamic threshold is enabled:
   ```python
   dynamic_energy_threshold = True
   ```

---

### Problem: Threshold "Hunting" (Unstable)

**Symptoms**: Works sporadically, seems to constantly adjust

**Solutions**:
1. Slow down adaptation:
   ```python
   dynamic_energy_adjustment_damping = 0.10  # Was 0.15
   ```

2. Check for intermittent noise sources (fans cycling, etc.)

3. Verify AGC isn't conflicting:
   ```bash
   amixer -c 3 set 'Auto Gain Control' off
   ```

---

### Problem: Too Slow to Adapt

**Symptoms**: Takes 30+ seconds to adjust to new environment

**Solutions**:
1. Increase damping rate:
   ```python
   dynamic_energy_adjustment_damping = 0.25  # Was 0.15
   ```

2. Lower initial threshold:
   ```python
   energy_threshold = 1000  # Was 1500
   ```

---

## Advanced: Combining with Realtime API Mode

**Note**: Dynamic thresholds currently apply to **legacy mode** (`audio_input.py`). The realtime API mode (`audio_capture_manager.py`) uses static VAD thresholds.

### If Using Realtime Mode

Edit: `nodes/speech_recognition_realtime/.messages`

```yaml
audio:
  vad_threshold: 0.08  # Static threshold (no auto-adaptation)
  vad_min_speech_duration: 0.3
```

**Manual environment adjustment required**:
- Coffee shop: `vad_threshold: 0.12`
- Party/conference: `vad_threshold: 0.15`

### Future Enhancement

Dynamic thresholds could be implemented in realtime mode by:
1. Tracking rolling average of non-speech audio energy
2. Auto-adjusting `vad_threshold` based on measured noise floor
3. Using similar damping/ratio parameters

---

## File Reference

### Primary Configuration
- **File**: `/home/dan/Nevil-picar-v3/audio/audio_input.py`
- **Lines**: 51-54
- **Component**: SpeechRecognition library recognizer settings

### Related Files
- **Audio Manager**: `nevil_framework/realtime/audio_capture_manager.py` (static VAD)
- **Realtime Config**: `nodes/speech_recognition_realtime/.messages` (static thresholds)
- **Microphone Mutex**: `nevil_framework/microphone_mutex.py` (echo prevention)

---

## Best Practices

1. ✅ **Enable dynamic thresholds** for real-world deployments
2. ✅ **Keep AGC enabled** for best hardware-software coordination
3. ✅ **Start with default settings** (damping: 0.15, ratio: 1.5)
4. ✅ **Test in target environment** before adjusting
5. ✅ **Make small incremental changes** (0.05-0.1 at a time)
6. ✅ **Document environment-specific tuning** for reproducibility
7. ❌ **Avoid disabling dynamic mode** unless debugging
8. ❌ **Don't set damping > 0.5** (causes instability)
9. ❌ **Don't set ratio < 1.0** (prevents speech detection)

---

## Summary

**Dynamic thresholds are ENABLED** with optimized settings for variable environments:

```python
dynamic_energy_threshold = True          # Auto-adaptation ON
energy_threshold = 1500                 # Starting baseline
dynamic_energy_adjustment_damping = 0.15 # Balanced adaptation speed
dynamic_energy_ratio = 1.5              # Moderate sensitivity
```

**No manual tuning needed** for most environments. The system automatically adapts to:
- Quiet → Noisy transitions (entering coffee shop)
- Noisy → Quiet transitions (leaving party)
- Cyclic noise (HVAC, traffic patterns)
- Crowd volume changes (conference sessions)

**For extreme environments** (outdoor, very loud parties), adjust `ratio` (1.5 → 2.0) and `damping` (0.15 → 0.25).

---

**Last Updated**: 2025-11-23
**Version**: Nevil-picar-v3 with dynamic threshold optimization
**Status**: Production-ready
