# Automatic Module Documentation

## Overview
The `automatic.py` module (`/home/dan/Nevil-picar-v3/nodes/navigation/automatic.py`) provides Nevil PiCar with autonomous behavior capabilities, enabling the robot to act independently with personality-driven behaviors and dynamic responses.

## Quick Start Examples

```python
# Say to Nevil:
"Go play"           # Starts auto mode with current mood
"Seeya Nevil"       # Dismissive way to start auto mode
"Stop playing"      # Stops auto mode
"Set mood playful"  # Changes to playful personality
```

## How to Start Autonomous Mode

### Voice Commands (Easiest)
Simply say to Nevil:

**Start Auto Mode:**
- **"Start auto"** - starts autonomous behavior
- **"Auto mode"** / **"Automatic mode"** - also works
- **"Go play"** - friendly way to start auto mode
- **"Seeya Nevil"** / **"See ya Nevil"** - dismissive trigger
- **"Go have fun"** / **"Go explore"** - exploratory triggers
- **"Entertain yourself"** / **"Do your thing"** - independent triggers

**Stop Auto Mode:**
- **"Stop auto"** / **"Stop automatic"** - disables autonomous behavior
- **"Stop playing"** / **"Stop exploring"** - activity-specific stops
- **"Come back"** - recall command
- **"Manual mode"** - switch to manual control

**Mood Control:**
- **"Set mood [mood_name]"** - changes personality
- Available moods: playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy

### From Terminal
```bash
# Launch Nevil with auto mode enabled from start
python3 -m nevil_framework.launcher --auto

# Or launch normally and use voice command
python3 -m nevil_framework.launcher
# Then say "auto mode" to Nevil
```

### Programmatically
```python
# Enable autonomous mode
self.auto_enabled = True
self.auto_thread = threading.Thread(target=self.run_auto)
self.auto_thread.start()

# Disable autonomous mode
self.auto_enabled = False

# Change mood
self.auto.set_mood("playful")  # or curious, sleepy, mischievous, etc.
```

### What Happens in Auto Mode
Once enabled, Nevil will:
1. Wait 5 seconds between interaction cycles
2. Each cycle, randomly choose:
   - **25% chance**: Make a GPT-powered comment (may use camera)
   - **75% chance**: Perform a mood-based behavior with possible vocalization
3. Continue until you say "Stop auto" or disable programmatically

The robot exhibits behaviors like exploring, dancing, singing, and making contextual comments based on its current mood.

## What Happens in Auto Mode

When enabled, Nevil exhibits autonomous behaviors based on its current mood:

1. **Movement patterns** - Exploring, circling, dancing based on energy level
2. **Vocalizations** - Context-appropriate comments like "What's that?", "Wheee!", "Hmm..."
3. **Expressions** - Head movements, body twists, celebrations
4. **Sound effects** - Honks and engine sounds based on mood
5. **GPT responses** - 25% chance of AI-generated contextual comments

The robot continues these behaviors until you tell it to stop or it runs out of energy (based on mood).

## Architecture

### Mood System
The module defines 8 distinct personality profiles that influence behavior selection:

| Mood | Volume | Curiosity | Sociability | Whimsy | Energy | Character |
|------|--------|-----------|-------------|--------|---------|-----------|
| **playful** | 85 | 70 | 90 | 95 | 90 | High energy, very social and whimsical |
| **brooding** | 25 | 40 | 10 | 15 | 30 | Quiet, antisocial, low energy |
| **curious** | 40 | 85 | 50 | 35 | 60 | Investigation-focused, moderate energy |
| **melancholic** | 30 | 30 | 20 | 20 | 20 | Low across all traits |
| **zippy** | 70 | 60 | 60 | 50 | 95 | Maximum energy, balanced other traits |
| **lonely** | 60 | 40 | 80 | 20 | 50 | High sociability, seeks interaction |
| **mischievous** | 90 | 75 | 50 | 95 | 85 | Loud, whimsical, high energy |
| **sleepy** | 10 | 20 | 10 | 5 | 15 | Minimal activity across all traits |

### Behavior System

#### Available Behaviors
1. **explore** - Forward movement with head turns based on curiosity
2. **rest** - Act cute animation with duration based on energy
3. **sleep** - Depressed animation followed by long pause
4. **fidget** - Twist body or shake head based on energy level
5. **address** - Wave hands or resist based on sociability
6. **play** - Engine sounds, turning, waving with optional honks
7. **panic** - Quick backward movement with alarm sounds
8. **circle** - Spinning in place, more rotations with higher energy
9. **sing** - Celebratory movements with honking sounds
10. **mutter** - Thinking animations with hand rubbing
11. **dance** - Complex movement sequences with celebrations

#### Behavior Selection Algorithm
```python
# Base weights define default probability
BEHAVIOR_BASE_WEIGHTS = {
    "explore": 0.3,    # 30% base chance
    "rest": 0.1,       # 10% base chance
    "sleep": 0.2,      # 20% base chance
    # ... etc
}

# Trait biases modify weights based on mood
BEHAVIOR_TRAIT_BIASES = {
    "explore": {"curiosity": 1.2, "energy": 1.1},
    # Higher curiosity/energy increases explore chance
}
```

The system computes final weights by:
1. Starting with base weight
2. Applying mood trait modifiers
3. Using weighted random selection

### Vocalization System
Each behavior has associated vocal phrases that may trigger based on mood traits:

```python
vocalization_chance = (energy + whimsy + sociability + curiosity + volume) / 500
```

Examples:
- **explore**: "What's that?", "Interesting...", "Let's see..."
- **panic**: "AAAHHHHH!", "Look out!", "Emergency!"
- **play**: "Wheee!", "Watch this!", "Fun fun fun!"

### Autonomous Loop

The main control flow (`run_idle_loop`):

```
┌─────────────────────────────┐
│  Check 5-second cooldown    │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Random choice (0-1)        │
└──────────┬──────────────────┘
           │
     ┌─────┴─────┐
     │ < 0.25?   │
     └─────┬─────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌─────────┐
│   GPT   │  │Behavior │
│Response │  │ System  │
└─────────┘  └─────────┘
    │             │
    └──────┬──────┘
           │
           ▼
┌─────────────────────────────┐
│   Execute Actions/Speech    │
└─────────────────────────────┘
```

- **25% chance**: GPT-powered response
  - May use vision based on curiosity level
  - Generates 1-5 word comments
  - Examples: "Hey Dan", "What's that?", "Cool room!"

- **75% chance**: Pre-programmed behavior
  - Selects behavior based on weighted mood traits
  - May include vocalization
  - Executes action sequence

## Class Interface

### Initialization
```python
automatic = Automatic(nevil_instance)
```

### Key Methods

#### `run_idle_loop(cycles=1)`
Main autonomous behavior loop. Runs specified number of behavior cycles.

#### `set_mood(mood_name)`
Changes current mood profile. Valid names: playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy

#### `do_actions(actions, mood=None)`
Queues action list for execution by main action thread. Thread-safe with locks.

#### `get_cycle_count()`
Determines number of autonomous cycles based on energy/whimsy (2-10 range).

### Thread Safety
- Uses `nevil.action_lock` for action queue management
- Uses `nevil.speech_lock` for TTS coordination
- Respects `nevil.auto_enabled` flag for clean shutdown

## Integration

The module integrates with the main Nevil system:
- Receives reference to main Nevil instance
- Queues actions to `nevil.actions_to_be_done`
- Uses `nevil.handle_TTS_generation()` for speech
- Calls `nevil.call_GPT()` for dynamic responses
- Monitors `nevil.auto_enabled` for control

## Configuration

### Adjusting Behavior Probability
Modify `BEHAVIOR_BASE_WEIGHTS` to change default behavior frequency.

### Adding New Moods
Add entries to `MOOD_PROFILES` dictionary with all 5 trait values (0-100 scale).

### Customizing Vocalizations
Edit `BEHAVIOR_VOCALIZATIONS` dictionary to add/modify phrases for each behavior.

### GPT Response Examples
Modify `AUTO_PROMPT_EXAMPLES` to influence GPT response style.

## Usage Example

```python
# In main Nevil system
from nodes.navigation.automatic import Automatic

# Initialize
self.auto = Automatic(self)

# Set mood
self.auto.set_mood("playful")

# Run autonomous behavior
if self.auto_enabled:
    cycles = self.auto.get_cycle_count()
    self.auto.run_idle_loop(cycles)
```

## Integration with Navigation Node (v3.0)

The Automatic module is now integrated directly into the Navigation Node, allowing seamless transitions between manual control and autonomous behavior.

### How It Works

1. **Voice Trigger Detection**: The navigation node monitors incoming messages for auto mode trigger phrases
2. **Mode Activation**: When triggered, creates an autonomous behavior thread
3. **Action Execution**: Autonomous actions are queued to the same action processing pipeline as manual commands
4. **Speech Integration**: TTS requests are published to the speech node for vocalization

### Implementation Details

The navigation node creates a mock Nevil interface that provides:
- Action queueing system
- TTS request publishing
- Thread-safe locks for coordination
- GPT integration hooks (for future enhancement)

### Message Flow

```
User speaks → Speech Recognition → AI Cognition → Navigation Node
                                                    ↓
                                        Detect auto trigger phrase
                                                    ↓
                                            Start auto thread
                                                    ↓
                                        Automatic.run_idle_loop()
                                                    ↓
                                        Queue actions & TTS
                                                    ↓
                                        Execute via action thread
```

## Performance Considerations

- 5-second cooldown prevents interaction overlap
- Actions execute synchronously to prevent conflicts
- Sleep operations allow for natural pacing
- Thread locks ensure safe multi-threaded operation
- Priority queue ensures auto actions don't block manual commands

## Detailed Behavior Examples

### Playful Mood (High Energy + Whimsy)
```
Actions: Quick forward movements, frequent honks, celebrations
Speech: "Wheee!", "Watch this!", "Fun fun fun!"
Likely behaviors: play (honking), dance (celebrations), explore (fast)
```

### Curious Mood (High Curiosity)
```
Actions: Explore with head turns, thinking gestures
Speech: "What's that?", "Interesting...", "Let me see..."
Likely behaviors: explore (with investigation), circle, think
```

### Sleepy Mood (Low Energy)
```
Actions: Slow movements, depressed pose, long rests
Speech: "Zzzz...", minimal vocalizations
Likely behaviors: sleep, rest, minimal activity
```

### Mischievous Mood (High Volume + Whimsy)
```
Actions: Loud honks, playful movements, celebrations
Speech: "Boogie!", "Chicken look at this!"
Likely behaviors: play (loud), dance, sing (noisy)
```

## Common Use Cases

### Entertainment Mode
```
User: "Go play"
Nevil: "Okay, I'll go play now!"
[Enters auto mode, performs autonomous behaviors]
```

### Demonstration Mode
```
User: "Set mood playful"
Nevil: "Feeling playful now!"
User: "Go have fun"
[Shows off playful behaviors for demonstration]
```

### Background Activity
```
User: "Seeya Nevil"
Nevil: [Autonomously explores while user does other tasks]
User: "Come back"
Nevil: "I'm back!"
```

## Debugging

Monitor console output prefixes:
- `[AUTO]` - Auto mode state changes and control
- `[auto]` - Autonomous mode decisions
- `[actions]` - Action queue activity
- `[vocal]` - Vocalization probability calculations
- `[auto speech]` - Generated speech content
- `[auto vocalization]` - Selected vocal phrase
- `[system]` - System-level information

## Troubleshooting

### Auto Mode Won't Start
- Check that navigation node is running
- Verify trigger phrase is recognized (check logs for `[AUTO]`)
- Ensure no other blocking actions in queue

### Auto Mode Won't Stop
- Use "Stop auto" or "Come back" commands
- Check if action queue is blocked
- Restart navigation node if necessary

### Mood Not Changing
- Use exact mood names: playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy
- Say "Set mood [name]" clearly
- Check logs for mood transition confirmation

## File Locations

- **Module**: `/home/dan/Nevil-picar-v3/nodes/navigation/automatic.py`
- **Integration**: `/home/dan/Nevil-picar-v3/nodes/navigation/navigation_node.py`
- **Documentation**: `/home/dan/Nevil-picar-v3/nodes/navigation/AUTOMATIC_DOCUMENTATION.md`