# Audio Output Issue - Root Cause & Fix

**Date**: 2025-11-20
**Issue**: TTS audio not audible through speakers despite successful playback

## Problem Analysis

### Symptoms
- STT working fine
- AI cognition working fine
- TTS generating audio successfully
- Audio files being created
- `Music().play()` returning True
- Playback timing correct (27s audio plays for 27s)
- BUT: No sound from speakers

### Root Cause

**GPIO 20 amplifier enable pin was not set to output high**

The HifiBerry DAC amplifier requires GPIO 20 to be HIGH to enable audio output. Without this, the audio signal is generated but the amplifier is disabled, so no sound reaches the speakers.

## Fix Applied

### 1. Code Fix (audio/audio_output.py)

**Problem**: Original code used `os.popen("pinctrl set 20 op dh")` which is deprecated and doesn't wait for command completion.

**Solution**: Changed to `subprocess.run()` to ensure GPIO 20 is properly set before Music() initialization:

```python
# BEFORE (line 60):
os.popen("pinctrl set 20 op dh")  # enable robot_hat speaker switch

# AFTER (lines 60-73):
import subprocess
try:
    result = subprocess.run(
        ["pinctrl", "set", "20", "op", "dh"],
        capture_output=True,
        text=True,
        timeout=2
    )
    if result.returncode == 0:
        print("[AudioOutput] Amplifier enabled (GPIO 20 HIGH)")
    else:
        print(f"[AudioOutput] Warning: GPIO 20 enable failed: {result.stderr}")
except Exception as e:
    print(f"[AudioOutput] Warning: Could not enable GPIO 20: {e}")
```

This ensures the amplifier is enabled when running `./nevil start` manually.

### 2. Systemd Service Fix (Redundant but Safe)

Also modified `/etc/systemd/system/nevil.service` to enable amplifier before Nevil starts:

```ini
[Service]
ExecStartPre=/usr/bin/pinctrl set 20 op dh
ExecStart=/home/dan/Nevil-picar-v3/nevil start
```

This provides redundancy when running via systemd, but the primary fix is in the code itself.

## Verification

After fix was applied:
- Audio immediately started playing all queued messages
- Restart cleared the queue
- Audio output now working correctly

## Hardware Configuration

**Audio Devices:**
- Card 0: vc4hdmi0 (HDMI)
- Card 1: vc4hdmi1 (HDMI)
- **Card 2: sndrpihifiberry (HifiBerry DAC)** ← Speaker output
- Card 3: USB PnP Sound Device (Microphone)

**ALSA Configuration** (`/etc/asound.conf`):
- Default output: Card 2 (HifiBerry DAC)
- Mixer: dmix with softvol
- Volume: 100% (PCM control)

**Amplifier Enable:**
- GPIO 20: Must be HIGH for audio output
- Automatically set by systemd service at startup

## Files Modified

1. **audio/audio_output.py** (PRIMARY FIX)
   - Lines 60-73: Changed `os.popen()` to `subprocess.run()` for GPIO 20 enable
   - Ensures command completes before Music() initialization
   - Works for both manual (`./nevil start`) and systemd execution

2. **/etc/systemd/system/nevil.service** (REDUNDANT FIX)
   - Added `ExecStartPre=/usr/bin/pinctrl set 20 op dh` on line 14
   - Provides additional safety when running via systemd

## Testing

To verify audio is working:

```bash
# Test speaker directly
speaker-test -t sine -f 1000 -c 2 -D default -l 1

# Play a saved TTS file
aplay -D default audio/nevil_wavs/FILENAME.wav

# Check GPIO 20 status
pinctrl get 20  # Should show: "20: op dh pn | hi // GPIO20 = output"

# Check volume
amixer -c 2 get PCM  # Should show: 255 [100%]
```

## Related Scripts

The i2samp.sh setup script (in nodes/speech_synthesis_realtime/) includes:
- Line 676: `pinctrl set 20 op dh` - Amp enable
- Lines 477-640: auto_sound_card script for device configuration
- Volume management via amixer

## Prevention

With the systemd service modification, this issue should not recur. The amplifier will be automatically enabled on every boot before Nevil starts.

## Troubleshooting

If audio stops working again:

1. **Check GPIO 20:**
   ```bash
   pinctrl get 20
   # Should be: "20: op dh pn | hi"
   # If not, run: pinctrl set 20 op dh
   ```

2. **Check volume:**
   ```bash
   amixer -c 2 get PCM
   # Should be at 100%
   ```

3. **Check audio device:**
   ```bash
   cat /etc/asound.conf
   # Should reference card 2
   ```

4. **Test directly:**
   ```bash
   speaker-test -D default -t sine -f 1000 -l 1
   ```

## References

- HifiBerry DAC documentation
- Adafruit i2samp setup script
- GPIO pinout for Raspberry Pi
- ALSA dmix/softvol configuration
