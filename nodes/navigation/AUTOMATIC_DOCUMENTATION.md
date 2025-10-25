# Automatic Mode Documentation (v3.0)

## Overview
The `automatic.py` module provides Nevil with **100% GPT-driven autonomous behavior**. Unlike traditional autonomous systems with hardcoded sequences, Nevil's AI makes ALL decisions about movement, speech, and silence based on mood-driven behavioral guidelines. Every autonomous cycle is unique and environment-responsive.

## Quick Start Examples

```python
# Say to Nevil:
"Go play"              # Starts auto mode with current mood
"Seeya Nevil"          # Dismissive way to start auto mode
"Stop auto"            # Stops auto mode
"Come back"            # Recalls Nevil from auto mode
"Set mood playful"     # Changes to playful personality
"Set mood sleepy"      # Changes to sleepy personality
```

## Key Features

### 🤖 100% GPT-Driven Decision Making
- **No hardcoded behaviors** - All movement and speech controlled by AI
- **No pre-scripted vocalizations** - GPT generates all speech dynamically
- **Silence is valid** - GPT can choose inactivity, pauses, or quiet observation
- **Environment-responsive** - High vision usage (70% when speaking, 35% when silent)
- **Unique every time** - Each autonomous cycle produces different behavior

### 🎭 8 Distinct Mood Personalities

| Mood | Energy | Sociability | Speech Freq | Listen Window | Character |
|------|--------|-------------|-------------|---------------|-----------|
| **playful** | 90 | 90 | 60% | 12.5s | Energetic, social, whimsical |
| **brooding** | 30 | 10 | 20% | 11.0s | Quiet, introspective, withdrawn |
| **curious** | 60 | 50 | 50% | 14.0s | Investigative, observational |
| **melancholic** | 20 | 20 | 25% | 15.0s | Slow, gentle, wistful |
| **zippy** | 95 | 60 | 65% | **5.8s** | Fast, bouncy, **impatient!** |
| **lonely** | 50 | 80 | 55% | **16.7s** | Seeks interaction, patient |
| **mischievous** | 85 | 50 | 60% | 11.5s | Playful, sneaky, energetic |
| **sleepy** | 15 | 10 | 15% | 14.5s | Minimal activity, very patient |

### ⏱️ Mood-Based Listening Windows (5-20 seconds)
After each autonomous cycle, Nevil pauses to listen for user interruption. Duration depends on mood:

**Formula:** `(sociability × 0.15) + ((100-energy) × 0.15) + 5`

- **Zippy mood**: ~5.8s (impatient, wants to keep moving!)
- **Lonely mood**: ~16.7s (patiently waiting for company)
- **High energy moods**: Shorter windows (restless, can't wait)
- **Low energy moods**: Longer windows (patient, lingering)
- **High sociability moods**: Longer windows (hoping for interaction)

### 🎨 3-Speed Gesture System
All 120+ gestures support speed modifiers for expressive movement:
- **:slow** - 2x pause duration (languid, thoughtful, melancholic)
- **:med** - 1x pause duration (normal, default)
- **:fast** - 0.5x pause duration (zippy, excited, nervous)

GPT chooses speeds to match mood and create rhythmic variety.

**Examples:**
```json
{
  "actions": ["ponder:slow", "sigh:slow", "sad_turnaway:slow"],
  "answer": "Just thinking..."
}

{
  "actions": ["happy_spin:fast", "jump_excited:fast", "cheer_wave:fast"],
  "answer": "Wheee!"
}
```

### 👁️ High Vision Integration
- **70% vision usage** when Nevil will speak (responds to environment)
- **35% vision usage** when Nevil is silent (quiet observation)
- Enables context-aware comments about surroundings
- GPT sees and reacts to what's in front of Nevil

### 🔄 Reduced Mood Change Frequency
- Moods persist **15-30 cycles** for stable personality periods
- **30% chance** to change when threshold reached
- Creates consistent personality sessions instead of constant mood swings
- Previous system changed every cycle - now much more stable

### 🎤 Microphone Mutex Architecture
- **Speech synthesis ↔ Speech recognition**: MUTUAL EXCLUSION (prevents self-talk)
- **Navigation ↔ Speech recognition**: MUTUAL EXCLUSION (blocks during servo noise)
- **Speech synthesis ↔ Navigation**: PARALLEL (can talk and move simultaneously!)
- **0.5s delay** before navigation starts for better speech synchronization

## How to Start Autonomous Mode

### Voice Commands (Easiest)

**Start Auto Mode:**
- "Start auto" / "Auto mode" / "Automatic mode"
- "Go play" / "Go have fun" / "Go explore"
- "Seeya Nevil" / "See ya Nevil" (dismissive)
- "Entertain yourself" / "Do your thing"

**Stop Auto Mode:**
- "Stop auto" / "Stop automatic" / "Stop playing"
- "Come back" / "Manual mode"

**Mood Control:**
- "Set mood playful" / "Set mood curious" / "Set mood sleepy"
- Available: playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy

### From Terminal
```bash
# Launch Nevil normally, then use voice
python3 -m nevil_framework.launcher
# Then say "go play" to Nevil

# Or use the start script
./nevil start
# Then say "auto mode"
```

### Programmatically
```python
# Enable autonomous mode
navigation_node.start_auto_mode()

# Disable autonomous mode
navigation_node.stop_auto_mode()

# Change mood
navigation_node.automatic.set_mood("playful")
```

## What Happens in Auto Mode

### Autonomous Cycle Flow

```
┌─────────────────────────────────────────┐
│ 1. Check mood change threshold          │
│    (Every 15-30 cycles, 30% chance)     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 2. Determine vision usage                │
│    Speaking: 70%, Silent: 35%           │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 3. Generate autonomous prompt            │
│    "You are in [mood] mode..."          │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 4. Call GPT with prompt + vision        │
│    100% GPT decides actions & speech    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 5. Execute GPT's chosen actions         │
│    Parallel with speech (microphone     │
│    mutex prevents self-talk)            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 6. Speak GPT's message (if any)         │
│    Empty answer = silent cycle          │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 7. Increment cycle counter               │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 8. Mood-based listening window           │
│    5.8s (zippy) to 16.7s (lonely)       │
│    User can interrupt with voice        │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 9. Loop back (unless stopped)            │
└─────────────────────────────────────────┘
```

### GPT Behavioral Guidelines (in System Prompt)

The system prompt includes detailed guidelines for each mood:

**Playful** (energy:90, soc:90, speech:60%)
- Energetic movements, frequent speech, social gestures
- Uses fast/med speeds: `happy_spin:fast`, `playful_bounce:med`
- Talk 60% of cycles

**Zippy** (energy:95, soc:60, speech:65%)
- Fast, bouncy, energetic!
- Uses fast gestures: `charge_forward:fast`, `zigzag:fast`, `eager_start:fast`
- Very active speech - talk 65% of cycles

**Sleepy** (energy:15, soc:10, speech:15%)
- Low energy, minimal activity, long pauses
- Uses slow gestures: `yawn:slow`, `sleep_mode:slow`, `idle_breath:slow`
- Very sparse speech - talk only 15% of cycles

**Lonely** (energy:50, soc:80, speech:55%)
- Seeking interaction, gentle social gestures
- Uses slow/med speeds: `bashful_hide:slow`, `greet_wave:med`, `call_attention:med`
- Moderate speech - talk 55% of cycles

*And 4 more moods with detailed guidelines...*

## Architecture Details

### Class: Automatic

**Initialization:**
```python
automatic = Automatic(nevil_instance)
```

**Key Attributes:**
- `current_mood_name` - Current mood string (e.g., "playful")
- `current_mood` - Mood profile dict with traits
- `cycles_since_mood_change` - Counter for mood persistence
- `mood_change_threshold` - Random 15-30 cycle threshold
- `MOOD_PROFILES` - All 8 mood definitions

**Key Methods:**

#### `run_idle_loop(cycles=1)`
Main autonomous behavior loop. Runs specified number of GPT-driven cycles.

```python
def run_idle_loop(self, cycles=1):
    # Check mood change threshold
    if self.cycles_since_mood_change >= self.mood_change_threshold:
        self.maybe_change_mood()

    # Determine vision usage
    use_vision = self.should_use_vision()

    # Get GPT response
    prompt = self.get_autonomous_prompt(use_vision)
    actions, message = self.nevil.call_GPT(prompt, use_image=use_vision)

    # Execute
    if actions:
        self.do_actions(actions)
    if message:
        self.nevil.handle_TTS_generation(message)

    self.cycles_since_mood_change += 1
```

#### `should_use_vision()`
Probabilistic vision usage based on mood speech frequency:
- Likely speaking: 70% use vision
- Likely silent: 35% use vision

#### `maybe_change_mood()`
30% chance to change to random new mood when threshold reached.

#### `set_mood(mood_name)`
Manually change mood. Updates profile and resets cycle counter.

#### `get_autonomous_prompt(use_vision)`
Generates simple prompt referencing system guidelines:
```python
prompt = f"You are in autonomous mode with mood '{self.current_mood_name}'. "
prompt += "Respond according to your mood behavioral guidelines. "
prompt += "Remember: speech is optional, silence and pauses are valid responses."
```

### Thread Safety
- Uses `nevil.action_lock` for action queue coordination
- Uses `nevil.speech_lock` for TTS coordination
- Respects `nevil.auto_enabled` flag for clean shutdown
- Microphone mutex prevents speech recognition during TTS/navigation

## Integration with Navigation Node

### Message Flow
```
User: "Go play"
    ↓
Speech Recognition → AI Cognition → Navigation Node
    ↓
Detects auto trigger → Publishes auto_mode_command
    ↓
Navigation Node receives command
    ↓
Calls start_auto_mode()
    ↓
Creates auto thread → Runs Automatic.run_idle_loop()
    ↓
Each cycle: GPT call → Actions + Speech
    ↓
Actions queued to action_queue (priority 50)
    ↓
Speech published to speech_synthesis via TTS
    ↓
Mood-based listening window (5-20s)
    ↓
Repeat until "Stop auto" or user interrupts
```

### Mock Nevil Interface
Navigation node provides automatic module with:
- `call_GPT(prompt, use_image)` - AI cognition integration
- `handle_TTS_generation(message)` - Speech synthesis
- `action_lock` - Thread-safe action queueing
- `speech_lock` - TTS coordination
- `auto_enabled` - Control flag

## Mood Examples

### Zippy Mood Behavior
```
Cycle 1:
  Vision: Yes (responding to environment)
  GPT: {"actions": ["charge_forward:fast", "zigzag:fast", "happy_spin:fast"],
        "answer": "Wheee!"}
  Listen window: 5.8s (impatient!)

Cycle 2:
  Vision: No
  GPT: {"actions": ["eager_start:fast", "jump_excited:fast"],
        "answer": ""}
  Listen window: 5.8s (wants to keep moving)
```

### Sleepy Mood Behavior
```
Cycle 1:
  Vision: No
  GPT: {"actions": ["yawn:slow", "idle_breath:slow"],
        "answer": ""}
  Listen window: 14.5s (very patient)

Cycle 2:
  Vision: No
  GPT: {"actions": [],
        "answer": ""}  # Complete inactivity
  Listen window: 14.5s (just sitting quietly)

Cycle 3:
  Vision: Yes (rare for sleepy)
  GPT: {"actions": ["stretch:slow"],
        "answer": "Zzz..."}
  Listen window: 14.5s
```

### Lonely Mood Behavior
```
Cycle 1:
  Vision: Yes
  GPT: {"actions": ["call_attention:med", "greet_wave:med", "listen_close:slow"],
        "answer": "Anyone there?"}
  Listen window: 16.7s (patiently waiting for response)

Cycle 2:
  Vision: Yes
  GPT: {"actions": ["bashful_hide:slow", "hello_friend:med"],
        "answer": ""}
  Listen window: 16.7s (still hoping for interaction)
```

## Performance Considerations

- **Mood stability**: 15-30 cycle persistence prevents erratic behavior
- **Listening windows**: Mood-based timing allows natural interruption
- **Parallel execution**: Speech and movement happen simultaneously
- **Microphone mutex**: Prevents Nevil from hearing himself
- **Vision throttling**: Smart usage prevents excessive API calls
- **Thread safety**: Locks prevent action queue conflicts
- **Priority queueing**: Auto actions use priority 50 (medium)

## Troubleshooting

### Auto Mode Won't Start
- Check navigation node is running: `./nevil validate`
- Verify trigger phrase recognized (check logs for `[AUTO COMMAND]`)
- Ensure no blocking errors in navigation node

### Auto Mode Won't Stop
- Use clear stop command: "Stop auto" or "Come back"
- Check listening window hasn't expired (wait for next cycle)
- If stuck, restart: `pkill -f navigation` then `./nevil start`

### Mood Not Changing When Requested
- Use exact mood names (case-insensitive): playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy
- Say "Set mood [name]" clearly during listening window
- Check logs for `[AUTO] Mood changed to: [name]`

### Nevil Not Speaking Much
- Check current mood's speech frequency (zippy=65%, sleepy=15%)
- Sleepy/brooding moods are naturally quiet
- Try setting mood to playful/zippy for more speech

### Nevil Too Impatient/Patient
- Listening window varies by mood
- Zippy = 5.8s (very impatient)
- Lonely = 16.7s (very patient)
- Choose mood based on desired interaction timing

### Movement Stopped Working
- Check gesture speed system is working: `python3 -m py_compile nodes/navigation/extended_gestures.py`
- Verify microphone mutex not blocking: check logs for `[AUTO] Microphone unavailable`
- Ensure navigation thread is running: look for `[AUTO] Running autonomous behavior cycle`

## File Locations

- **Module**: `/home/dan/Nevil-picar-v3/nodes/navigation/automatic.py`
- **Navigation Integration**: `/home/dan/Nevil-picar-v3/nodes/navigation/navigation_node.py` (lines 703-760)
- **Microphone Mutex**: `/home/dan/Nevil-picar-v3/nevil_framework/microphone_mutex.py`
- **Gesture Library**: `/home/dan/Nevil-picar-v3/nodes/navigation/extended_gestures.py` (106 gestures)
- **System Prompt**: `/home/dan/Nevil-picar-v3/nodes/ai_cognition/.messages` (line 231)
- **Documentation**: `/home/dan/Nevil-picar-v3/nodes/navigation/AUTOMATIC_DOCUMENTATION.md`

## Version History

### v3.0 (Current) - GPT-Driven Rewrite
- **Complete rewrite**: 100% GPT-driven, no hardcoded behaviors
- **Removed**: All 11 behavior functions, vocalizations dictionary (~350 lines)
- **Added**: Mood-based listening windows (5.8s - 16.7s range)
- **Added**: 3-speed gesture system (:slow/:med/:fast)
- **Added**: Microphone mutex for parallel speech/movement
- **Added**: High vision integration (70%/35%)
- **Improved**: Mood persistence (15-30 cycles vs every cycle)
- **Enhanced**: System prompt with detailed mood behavioral guidelines

### v2.0 - Behavior System
- Hardcoded behavior patterns (explore, rest, sleep, etc.)
- Pre-scripted vocalizations
- 25% GPT / 75% behavior split
- Frequent mood changes

### v1.0 - Initial Implementation
- Basic autonomous loop
- Simple action sequences
