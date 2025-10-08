# Nevil Sound Architecture Documentation

## Quick Start: Adding a New Sound

### Complete Process (5 Steps)

#### Step 1: Add Audio File
```bash
# Copy your sound file to the audio directory
cp your_new_sound.mp3 /home/dan/Nevil-picar-v3/audio/sounds/

# Verify file was copied correctly
ls -la /home/dan/Nevil-picar-v3/audio/sounds/your_new_sound.mp3
```

#### Step 2: Update Sound Mapping
```python
# Edit: /home/dan/Nevil-picar-v3/nodes/navigation/action_helper.py
# Add to SOUND_MAPPINGS dictionary (around line 482):

SOUND_MAPPINGS = {
    # ... existing sounds ...

    # Add your new sound in appropriate category
    "your_sound_name": "your_new_sound.mp3"
}
```

#### Step 3: Update Navigation Messages
```yaml
# Edit: /home/dan/Nevil-picar-v3/nodes/navigation/.messages
# Add to allowed list (around line 84):

allowed: ["honk", "rev_engine", "horn", "airhorn", "machinegun", "shock",
          "dubstep", "dubstep_bass", "reggae", "agent_theme", "ghost_laugh",
          "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit",
          "inception_horn", "alien_voice", "alien_pitch", "alien_horn",
          "preacher", "your_sound_name"]
```

#### Step 4: Update Speech Synthesis Messages
```yaml
# Edit: /home/dan/Nevil-picar-v3/nodes/speech_synthesis/.messages
# Add to allowed list (around line 139):

allowed: ["honk", "rev_engine", "horn", "airhorn", "machinegun", "shock",
          "dubstep", "dubstep_bass", "reggae", "agent_theme", "ghost_laugh",
          "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit",
          "inception_horn", "alien_voice", "alien_pitch", "alien_horn",
          "preacher", "your_sound_name"]
```

#### Step 5: Update AI Prompt
```
# Edit: /home/dan/Nevil-picar-v3/nevil_framework/nevil_prompt.txt
# Add to appropriate category (around line 58-63):

## Sound Effects Available via play_sound action:
Vehicle: ["honk", "rev_engine", "horn", "airhorn"]
Action: ["machinegun", "shock"]
Musical: ["dubstep", "dubstep_bass", "reggae", "agent_theme"]
Spooky: ["ghost_laugh", "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit", "inception_horn"]
Alien: ["alien_voice", "alien_pitch", "alien_horn"]
Voice: ["preacher"]
YourCategory: ["your_sound_name"]  # Add to existing or create new category
```

### Test Your New Sound
```bash
# Start Nevil and test in automatic mode or through voice command:
# "play sound your_sound_name"

# Or test the action directly in the logs when Nevil uses:
# ["play_sound your_sound_name"]
```

### File Requirements
- **Supported Formats**: .mp3, .wav, .ogg
- **Recommended**: MP3 format for smaller file size
- **Max Size**: Keep under 5MB for responsive playback
- **Naming**: Use descriptive filenames with hyphens/underscores

### Common Sound Categories
- **Vehicle**: Car sounds, engines, horns
- **Action**: Weapon sounds, impact sounds, mechanical sounds
- **Musical**: Background music, musical stings
- **Spooky**: Halloween, horror, mysterious sounds
- **Alien**: Sci-fi, otherworldly sounds
- **Voice**: Speech clips, vocal samples
- **Nature**: Animal sounds, environmental audio
- **Electronic**: Beeps, digital sounds, notifications

---

## Overview

The Nevil sound system is designed to provide rich audio feedback through a scalable, conflict-free architecture that supports both text-to-speech (TTS) and sound effects playback. The system routes all audio through a single Music() instance to avoid multi-process conflicts while maintaining modularity and extensibility.

## Architecture Components

### 1. Sound Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Action Request │───▶│  Navigation Node │───▶│ Speech Synthesis    │
│  (User/Auto)    │    │                  │    │ Node                │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────────┐
                       │ Message Bus      │    │ Audio Output        │
                       │ (sound_effect)   │    │ (Music() Instance)  │
                       └──────────────────┘    └─────────────────────┘
```

### 2. Component Breakdown

#### A. Sound Mapping System (`action_helper.py`)
- **SOUND_MAPPINGS Dictionary**: Maps logical sound names to physical audio files
- **Generic Functions**: `play_sound(car, sound_name, volume)` for scalable audio
- **Legacy Wrappers**: `honk()`, `rev_engine()` for backward compatibility
- **Actions Integration**: Sound functions registered in `actions_dict`

#### B. Message Bus Configuration (`.messages` files)
- **Navigation Node**: Publishes sound effect requests
- **Speech Synthesis Node**: Subscribes to and processes sound requests
- **Schema Validation**: Ensures only valid sound names are processed

#### C. Audio Processing (`speech_synthesis_node.py`)
- **Single Music() Instance**: Centralized audio output to prevent conflicts
- **Sound Effect Handler**: `on_sound_effect()` callback processes requests
- **Busy State Management**: Coordinates between TTS and sound effects
- **File Path Resolution**: Maps sound names to actual file locations

## Detailed Component Analysis

### 1. Sound Mapping System

```python
# Location: /home/dan/Nevil-picar-v3/nodes/navigation/action_helper.py

SOUND_MAPPINGS = {
    # Vehicle sounds
    "honk": "car-double-horn.wav",
    "rev_engine": "engine-revving.wav",
    "horn": "train-horn-337875.mp3",
    "airhorn": "airhorn-fx-343682.mp3",

    # Action sounds
    "machinegun": "clean-machine-gun-burst-98224.mp3",
    "shock": "shock-gasp-female-383751.mp3",

    # Musical sounds
    "dubstep": "dubstep-75bpm-67136.mp3",
    "dubstep_bass": "dubstep-bassline-datsik-style-61181.mp3",
    "reggae": "reggae-loop-75237.mp3",
    "agent_theme": "agent-movie-music-inspired-by-james-bond-theme-30066.mp3",

    # Spooky/Halloween sounds
    "ghost_laugh": "scary-female-halloween-horror-laughter-vol-006-165223.mp3",
    "ghost_voice": "ghost-voice-halloween-moany-ghost-168411.mp3",
    "wolf_howl": "sound-effect-halloween-wolf-howling-253243.mp3",
    "creepy_bell": "creepy-halloween-bell-trap-melody-247720.mp3",
    "horror_hit": "horror-hit-logo-142395.mp3",
    "inception_horn": "inception-style-movie-horn-80358.mp3",

    # Alien sounds
    "alien_voice": "alien-voice-102709.mp3",
    "alien_pitch": "alien-high-pitch-312010.mp3",
    "alien_horn": "eerie-alien-horn-82052.mp3",

    # Voice clips
    "preacher": "old-school-preacher-clips-pastor-darryl-hussey-129622.mp3"
}
```

**Key Features:**
- **Categorized Organization**: Sounds grouped by theme for easy discovery
- **File Extension Agnostic**: Supports .wav, .mp3, and other formats
- **Descriptive Naming**: Logical names that map to AI prompt usage
- **Scalable Design**: Adding new sounds requires only dictionary updates

### 2. Generic Sound Function

```python
def play_sound(car, sound_name=None, volume=100):
    """Generic sound player - takes sound name as parameter"""
    if not sound_name:
        logger.warning("No sound name provided to play_sound")
        return

    logger.info(f"🔊 PLAY_SOUND action called: {sound_name} (volume: {volume})")

    try:
        # Check if we can publish sound effect message through navigation node
        if hasattr(car, 'nav_node') and car.nav_node:
            logger.info(f"Publishing sound effect request: {sound_name}")
            car.nav_node.publish("sound_effect", {
                "effect": sound_name,
                "volume": volume,
                "priority": 30
            })
            # Brief pause for sound to play
            time.sleep(1.0)
        else:
            logger.warning(f"Cannot play {sound_name} - no navigation node reference for messaging")
    except Exception as e:
        logger.error(f"Error playing sound {sound_name}: {e}")
```

**Architecture Benefits:**
- **Message-Based**: Avoids direct Music() access conflicts
- **Parameter-Driven**: Sound name passed as parameter, not hardcoded
- **Error Handling**: Graceful degradation when audio unavailable
- **Logging**: Comprehensive debug information

### 3. Message Schema Configuration

#### Navigation Node (Publisher)
```yaml
# Location: /home/dan/Nevil-picar-v3/nodes/navigation/.messages

- topic: "sound_effect"
  message_type: "SoundEffect"
  description: "Sound effect playback requests"
  frequency: "on_demand"
  schema:
    effect:
      type: "string"
      required: true
      description: "Sound effect to play"
      allowed: ["honk", "rev_engine", "horn", "airhorn", "machinegun", "shock",
                "dubstep", "dubstep_bass", "reggae", "agent_theme", "ghost_laugh",
                "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit",
                "inception_horn", "alien_voice", "alien_pitch", "alien_horn", "preacher"]
    volume:
      type: "integer"
      required: false
      description: "Playback volume (0-100)"
      default: 100
    priority:
      type: "integer"
      required: false
      description: "Request priority"
      default: 50
```

#### Speech Synthesis Node (Subscriber)
```yaml
# Location: /home/dan/Nevil-picar-v3/nodes/speech_synthesis/.messages

- topic: "sound_effect"
  message_type: "SoundEffect"
  callback: "on_sound_effect"
  description: "Sound effect playback requests"
  schema:
    effect:
      type: "string"
      required: true
      description: "Sound effect to play"
      allowed: ["honk", "rev_engine", "horn", "airhorn", "machinegun", "shock",
                "dubstep", "dubstep_bass", "reggae", "agent_theme", "ghost_laugh",
                "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit",
                "inception_horn", "alien_voice", "alien_pitch", "alien_horn", "preacher"]
    volume:
      type: "integer"
      required: false
      description: "Playback volume (0-100)"
      default: 100
    priority:
      type: "integer"
      required: false
      description: "Request priority"
      default: 50
```

### 4. Audio Processing Handler

```python
# Location: /home/dan/Nevil-picar-v3/nodes/speech_synthesis/speech_synthesis_node.py

def on_sound_effect(self, message):
    """Handle sound effect playback requests (declaratively configured callback)"""
    try:
        effect = message.data.get("effect", "")
        volume = message.data.get("volume", 100)
        priority = message.data.get("priority", 50)

        # Import sound mappings from action_helper
        from nodes.navigation.action_helper import SOUND_MAPPINGS

        # Map effect names to full sound file paths
        sound_files = {
            name: f"/home/dan/Nevil-picar-v3/audio/sounds/{filename}"
            for name, filename in SOUND_MAPPINGS.items()
        }

        sound_file = sound_files.get(effect)
        if not sound_file:
            self.logger.error(f"Unknown sound effect: {effect}")
            return

        # Check if file exists
        if not os.path.exists(sound_file):
            self.logger.error(f"Sound file not found: {sound_file}")
            return

        # Play the sound using the audio output's Music() instance
        if self.audio_output and self.audio_output.music:
            # Acquire busy state for sound playback
            if not busy_state.acquire("sound_effect"):
                self.logger.warning("Could not acquire busy state for sound effect")
                return

            try:
                self.audio_output.music.sound_play(sound_file, volume)
                # Wait for sound to finish
                while self.audio_output.music.pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                self.logger.info(f"✓ Sound effect completed: {effect}")
            finally:
                busy_state.release()
        else:
            self.logger.error("Audio output not available for sound effects")

    except Exception as e:
        self.logger.error(f"Error playing sound effect: {e}")
```

## File Organization

### Sound Files Location
```
/home/dan/Nevil-picar-v3/audio/sounds/
├── car-double-horn.wav                     # honk
├── engine-revving.wav                      # rev_engine
├── train-horn-337875.mp3                   # horn
├── airhorn-fx-343682.mp3                   # airhorn
├── clean-machine-gun-burst-98224.mp3       # machinegun
├── shock-gasp-female-383751.mp3            # shock
├── dubstep-75bpm-67136.mp3                 # dubstep
├── dubstep-bassline-datsik-style-61181.mp3 # dubstep_bass
├── reggae-loop-75237.mp3                   # reggae
├── agent-movie-music-inspired-by-james-bond-theme-30066.mp3 # agent_theme
├── scary-female-halloween-horror-laughter-vol-006-165223.mp3 # ghost_laugh
├── ghost-voice-halloween-moany-ghost-168411.mp3 # ghost_voice
├── sound-effect-halloween-wolf-howling-253243.mp3 # wolf_howl
├── creepy-halloween-bell-trap-melody-247720.mp3 # creepy_bell
├── horror-hit-logo-142395.mp3              # horror_hit
├── inception-style-movie-horn-80358.mp3    # inception_horn
├── alien-voice-102709.mp3                  # alien_voice
├── alien-high-pitch-312010.mp3             # alien_pitch
├── eerie-alien-horn-82052.mp3              # alien_horn
└── old-school-preacher-clips-pastor-darryl-hussey-129622.mp3 # preacher
```

### Code Organization
```
/home/dan/Nevil-picar-v3/
├── nodes/navigation/
│   ├── action_helper.py           # Sound mappings & functions
│   ├── navigation_node.py         # Sound effect publishing
│   └── .messages                  # Navigation message schema
├── nodes/speech_synthesis/
│   ├── speech_synthesis_node.py   # Sound processing handler
│   └── .messages                  # Speech synthesis message schema
├── audio/
│   ├── audio_output.py           # Music() wrapper
│   └── sounds/                   # Audio file storage
└── nevil_framework/
    └── nevil_prompt.txt          # AI prompt with sound documentation
```

## AI Integration

### Nevil Prompt Documentation
```
## Sounds:
["honk", "start_engine", "play_sound"]

## Sound Effects Available via play_sound action:
Vehicle: ["honk", "rev_engine", "horn", "airhorn"]
Action: ["machinegun", "shock"]
Musical: ["dubstep", "dubstep_bass", "reggae", "agent_theme"]
Spooky: ["ghost_laugh", "ghost_voice", "wolf_howl", "creepy_bell", "horror_hit", "inception_horn"]
Alien: ["alien_voice", "alien_pitch", "alien_horn"]
Voice: ["preacher"]

## Use play_sound with specific effect name:
["play_sound alien_voice"] - plays alien voice sound
["play_sound dubstep"] - plays dubstep music
["play_sound ghost_laugh"] - plays spooky laughter
```

### Usage Examples

#### Direct Sound Actions
```json
{"actions": ["honk", "forward 30"], "answer": "Beep beep, coming through!"}
{"actions": ["start_engine", "celebrate"], "answer": "Let's rev this up!"}
```

#### Generic Sound Actions
```json
{"actions": ["play_sound dubstep", "twist_body"], "answer": "Time to dance!", "mood": "zippy"}
{"actions": ["play_sound ghost_laugh", "shake_head"], "answer": "Spooky vibes!", "mood": "mischievous"}
{"actions": ["play_sound alien_voice", "think"], "answer": "Communications from beyond...", "mood": "curious"}
```

## Technical Benefits

### 1. Conflict Resolution
- **Single Music() Instance**: All audio routed through speech synthesis node
- **Busy State Management**: Prevents overlapping audio operations
- **Message-Based Communication**: Eliminates direct hardware access conflicts

### 2. Scalability
- **Mapping-Based**: New sounds require only dictionary updates
- **Schema Validation**: Automatic validation of sound names
- **Category Organization**: Logical grouping for easy discovery

### 3. Maintainability
- **Centralized Configuration**: All sound mappings in one location
- **Declarative Messages**: Schema-driven communication
- **Comprehensive Logging**: Full audit trail for debugging

### 4. Extensibility
- **Generic Functions**: Parameter-driven sound playback
- **Category System**: Organized sound library structure
- **AI Integration**: Rich prompt documentation for natural usage

## Adding New Sounds

### Step 1: Add Audio File
```bash
# Copy new sound file to audio directory
cp new_sound.mp3 /home/dan/Nevil-picar-v3/audio/sounds/
```

### Step 2: Update Sound Mapping
```python
# In action_helper.py, add to SOUND_MAPPINGS
SOUND_MAPPINGS = {
    # ... existing sounds ...
    "new_sound": "new_sound.mp3"
}
```

### Step 3: Update Message Schemas
```yaml
# In both .messages files, add to allowed list
allowed: ["honk", "rev_engine", ..., "new_sound"]
```

### Step 4: Update AI Prompt
```
# In nevil_prompt.txt, add to appropriate category
Category: ["existing_sounds", "new_sound"]
```

## Troubleshooting

### Common Issues

1. **Sound Not Playing**
   - Check file exists in `/home/dan/Nevil-picar-v3/audio/sounds/`
   - Verify sound name in SOUND_MAPPINGS
   - Check .messages file allows the sound name
   - Ensure navigation node has nav_node reference

2. **Music() Conflicts**
   - Verify all sounds route through speech synthesis node
   - Check busy_state acquisition/release
   - Avoid direct Music() instantiation in other nodes

3. **Schema Validation Errors**
   - Ensure sound name in both .messages files' allowed lists
   - Check message format matches schema requirements
   - Verify callback method names match .messages configuration

### Debug Commands
```bash
# Check sound files
ls -la /home/dan/Nevil-picar-v3/audio/sounds/

# Test sound mappings
python3 -c "from action_helper import SOUND_MAPPINGS; print(len(SOUND_MAPPINGS))"

# Verify message schemas
grep -A 20 "sound_effect" /home/dan/Nevil-picar-v3/nodes/*/. messages
```

## Performance Considerations

- **File Formats**: MP3 and WAV supported, MP3 recommended for size
- **File Sizes**: Keep under 5MB for responsive playback
- **Concurrent Playback**: Single Music() instance, sequential playback only
- **Memory Usage**: Sounds loaded on-demand, not cached
- **Network Impact**: No network dependencies, all files local

This architecture provides a robust, scalable foundation for Nevil's audio capabilities while maintaining clean separation of concerns and avoiding common multi-process audio conflicts.