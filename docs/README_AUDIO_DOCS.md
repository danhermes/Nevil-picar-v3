# Audio System Documentation - Index

This directory contains comprehensive documentation about Nevil's audio pipeline, specifically covering the integration between OpenAI's Realtime API (24kHz output) and the HiFiBerry DAC with PCM5102A chip (44.1kHz input).

## Documentation Files

### 1. [AUDIO_COMPATIBILITY_SUMMARY.md](AUDIO_COMPATIBILITY_SUMMARY.md)
**Start here!** Executive summary for quick reference.

**Contents:**
- Quick facts table
- How the conversion works (simple explanation)
- Evidence that it's working correctly
- Troubleshooting checklist
- Recommendations

**Audience:** Developers, maintainers, anyone wanting a quick answer to "Does this work?"

**Reading time:** 3-5 minutes

---

### 2. [HIFIBERRY_REALTIME_COMPATIBILITY.md](HIFIBERRY_REALTIME_COMPATIBILITY.md)
**Deep technical analysis** of hardware and software compatibility.

**Contents:**
- Executive summary
- Hardware specifications (HiFiBerry, PCM5102A DAC)
- PCM5102A supported sample rates (from TI datasheet)
- Complete audio pipeline analysis
- Sample rate conversion details
- Performance characteristics
- Configuration files
- Potential issues and mitigations
- Alternative approaches (and why we don't use them)
- Technical references

**Audience:** Engineers, system architects, technical troubleshooting

**Reading time:** 15-20 minutes

---

### 3. [AUDIO_PIPELINE_DIAGRAM.md](AUDIO_PIPELINE_DIAGRAM.md)
**Visual walkthrough** of the entire audio path with ASCII diagrams.

**Contents:**
- Complete signal flow diagram (OpenAI → Speaker)
- Resampling algorithm details with examples
- Latency breakdown and timeline
- Sample rate conversion quality comparison
- Troubleshooting guide with commands
- Performance metrics (CPU, memory, disk I/O)

**Audience:** Visual learners, debugging sessions, presentations

**Reading time:** 10-15 minutes

---

## Quick Reference

### Is it compatible?
✅ **Yes.** See [AUDIO_COMPATIBILITY_SUMMARY.md](AUDIO_COMPATIBILITY_SUMMARY.md)

### How does sample rate conversion work?
See [AUDIO_PIPELINE_DIAGRAM.md](AUDIO_PIPELINE_DIAGRAM.md) → "Resampling Algorithm Detail"

### What if audio doesn't work?
See [AUDIO_COMPATIBILITY_SUMMARY.md](AUDIO_COMPATIBILITY_SUMMARY.md) → "Troubleshooting" section

### What are the hardware specs?
See [HIFIBERRY_REALTIME_COMPATIBILITY.md](HIFIBERRY_REALTIME_COMPATIBILITY.md) → "Hardware Configuration"

### Can I use a different sample rate?
No. OpenAI Realtime API only outputs 24kHz PCM16. See [HIFIBERRY_REALTIME_COMPATIBILITY.md](HIFIBERRY_REALTIME_COMPATIBILITY.md) → "Alternative Approaches"

---

## Related Code Files

### Audio Output
- **[audio/audio_output.py](../audio/audio_output.py)** - Wraps robot_hat.Music() (pygame)
- **[audio/audio_utils.py](../audio/audio_utils.py)** - play_audio_file() function

### Speech Synthesis
- **[nodes/speech_synthesis_realtime/speech_synthesis_realtime_node.py](../nodes/speech_synthesis_realtime/speech_synthesis_realtime_node.py)** - Receives audio from Realtime API

### Configuration
- **[.env](../.env)** - NEVIL_REALTIME_VOICE, NEVIL_REALTIME_MODEL
- **`/etc/asound.conf`** - ALSA default card (card 2 = HiFiBerry)
- **`/boot/firmware/config.txt`** - dtoverlay=hifiberry-dac

---

## Testing Commands

### Verify HiFiBerry is active
```bash
lsof /dev/snd/pcmC2D0p
# Should show: python3 process
```

### Check hardware parameters
```bash
cat /proc/asound/card2/pcm0p/sub0/hw_params
# Should show: rate: 44100
```

### Verify pygame mixer initialization
```bash
python3 -c "from robot_hat import Music; print(Music().pygame.mixer.get_init())"
# Should show: (44100, -16, 2)
```

### Check WAV file format
```bash
file audio/nevil_wavs/*.wav
# Should show: 24000 Hz
```

### Verify GPIO speaker enable
```bash
sudo pinctrl get 20
# Should show: op dh | hi
```

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ OpenAI Realtime API                                         │
│   ↓ 24 kHz PCM16 mono (WebSocket stream)                   │
├─────────────────────────────────────────────────────────────┤
│ speech_synthesis_realtime_node.py                           │
│   ↓ Save to WAV file (24kHz, 16-bit, mono)                 │
├─────────────────────────────────────────────────────────────┤
│ audio/audio_output.py (robot_hat.Music)                     │
│   ↓ pygame.mixer.music.play()                               │
├─────────────────────────────────────────────────────────────┤
│ pygame/SDL2                                                  │
│   ↓ Automatic resample: 24kHz → 44.1kHz                    │
│   ↓ Automatic conversion: mono → stereo                     │
├─────────────────────────────────────────────────────────────┤
│ ALSA (hw:2,0)                                               │
│   ↓ 44.1 kHz, S16_LE, stereo                               │
├─────────────────────────────────────────────────────────────┤
│ HiFiBerry DAC (PCM5102A)                                    │
│   ↓ I2S digital input @ 44.1kHz                             │
│   ↓ Delta-sigma modulation                                  │
│   ↓ Analog output                                            │
├─────────────────────────────────────────────────────────────┤
│ 🔊 Speaker (GPIO 20 enabled)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Findings

1. **PCM5102A DAC does NOT natively support 24kHz**
   - Officially supported: 8k, 16k, 32k, 44.1k, 48k, 88.2k, 96k, 176.4k, 192k, 384k
   - Source: Texas Instruments datasheet + TI E2E forums

2. **pygame automatically resamples 24kHz → 44.1kHz**
   - Uses SDL2's linear interpolation
   - Transparent to application
   - Excellent quality for speech

3. **HiFiBerry receives 44.1kHz (fully supported)**
   - DAC auto-detects sample rate correctly
   - Digital filter configured for 44.1kHz
   - No issues or artifacts

4. **Current implementation is optimal**
   - No code changes needed
   - Maintains v1.0/v3.0 compatibility
   - Low CPU overhead (<1%)
   - Acceptable latency (~10-20ms for resampling)

---

## Support

For questions or issues:
1. Check [AUDIO_COMPATIBILITY_SUMMARY.md](AUDIO_COMPATIBILITY_SUMMARY.md) → Troubleshooting
2. Review [AUDIO_PIPELINE_DIAGRAM.md](AUDIO_PIPELINE_DIAGRAM.md) → Troubleshooting Guide
3. Verify hardware with commands listed above
4. Check logs in `/var/log/auto_sound_card.log`

---

**Documentation Version:** 1.0  
**Last Updated:** 2025-11-17  
**System:** Nevil v2.2 (Realtime API)  
**Hardware:** Raspberry Pi 5 + HiFiBerry DAC  
**Author:** Claude Code
