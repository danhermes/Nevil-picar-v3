# Media Library System - AI-Driven Sound & Video Playback

## Overview

Similar to the curated gesture system, Nevil now has **curated sound and video libraries** that the AI can call by name. This approach:

✅ **Reduces costs** - No audio streaming to AI, just names
✅ **Reduces latency** - Instant playback, no generation
✅ **Increases control** - Curated, appropriate content
✅ **Preserves AI intelligence** - AI chooses what to play and when

---

## Architecture

### The Pattern (Same as Gestures)

**❌ OLD (Expensive)**:
- Stream all audio to AI continuously
- AI generates or searches for content
- High latency, high cost

**✅ NEW (Economical)**:
- AI calls: `play_sound(name="calm_music", volume=0.3)`
- AI calls: `play_video(name="relaxing_nature")`
- Local playback, instant, cheap

---

## Sound Library

### Available Sounds (15 total)

#### Background Music (3 sounds)
```python
"calm_music"     - Calm, peaceful background music for relaxation
"upbeat_music"   - Upbeat, energetic music for excitement
"dramatic_music" - Dramatic, intense music for important moments
```

#### Sound Effects (4 sounds)
```python
"beep"    - Simple beep sound for notifications
"chime"   - Pleasant chime for positive feedback
"alert"   - Alert sound for important notifications
"success" - Success sound for achievements
```

#### Ambient Sounds (3 sounds)
```python
"rain"   - Rain sounds for calming atmosphere
"ocean"  - Ocean waves for peaceful atmosphere
"nature" - Nature sounds (birds, forest) for relaxation
```

#### YouTube Streaming (3 sounds)
```python
"youtube_lofi"      - Lo-fi hip hop music from YouTube
"youtube_jazz"      - Smooth jazz music from YouTube
"youtube_classical" - Classical music from YouTube
```

### AI Function Calls

```python
# Play a sound
play_sound(sound_name="calm_music", volume=0.3)

# Stop current sound
stop_sound()
```

### AI Usage Examples

**User: "I'm stressed"**
```python
AI: "Let me help you relax."
AI calls: play_sound(sound_name="rain", volume=0.2)
```

**User: "Play some music"**
```python
AI: "Sure! How about some lo-fi beats?"
AI calls: play_sound(sound_name="youtube_lofi", volume=0.3)
```

**User: "Stop the music"**
```python
AI calls: stop_sound()
```

---

## Video Library

### Available Videos (10 total)

#### Educational (2 videos)
```python
"how_robots_work" - Educational video about how robots work (5:30)
"ai_explained"    - Simple explanation of artificial intelligence (6:12)
```

#### Music (3 videos)
```python
"relaxing_nature" - Relaxing music with nature sounds (3:00:00)
"lofi_study"      - Lo-fi hip hop music for studying/relaxing (LIVE)
"classical_piano" - Beautiful classical piano music (2:00:00)
```

#### Entertainment (2 videos)
```python
"funny_robots" - Compilation of funny robot moments (10:15)
"robot_dance"  - Amazing robot dance performance (2:45)
```

#### Nature/Scenery (2 videos)
```python
"ocean_waves"  - Peaceful ocean waves for relaxation (3:00:00)
"forest_sounds" - Peaceful forest with bird sounds (3:00:00)
```

#### Inspiration (1 video)
```python
"robot_inspiration" - Inspiring video about robotics future (5:42)
```

### AI Function Calls

```python
# Play a video
play_video(video_name="relaxing_nature")

# Search for videos
search_videos(query="relaxing")
# Returns: ["relaxing_nature", "ocean_waves", "forest_sounds"]
```

### AI Usage Examples

**User: "Show me something about robots"**
```python
AI: "Here's an interesting video about how robots work!"
AI calls: play_video(video_name="how_robots_work")
```

**User: "I need to focus"**
```python
AI: "Let me put on some study music for you."
AI calls: play_video(video_name="lofi_study")
```

**User: "Find relaxing videos"**
```python
AI calls: search_videos(query="relaxing")
AI: "I found 3 relaxing videos: nature sounds, ocean waves, and forest sounds. Which would you like?"
```

---

## Implementation

### 1. File Structure

```
nevil_framework/
├── sound_library_manager.py  # Sound library system
├── video_library_manager.py  # Video library system

sounds/                        # Sound files directory
├── music/
│   ├── calm.wav
│   ├── upbeat.wav
│   └── dramatic.wav
├── effects/
│   ├── beep.wav
│   ├── chime.wav
│   ├── alert.wav
│   └── success.wav
└── ambient/
    ├── rain.wav
    ├── ocean.wav
    └── nature.wav
```

### 2. Integration with AI Node

```python
from nevil_framework.sound_library_manager import SoundLibraryManager
from nevil_framework.video_library_manager import VideoLibraryManager

class AICognitionRealtimeNode:
    def __init__(self):
        # ... existing code ...

        # Initialize media libraries
        self.sound_library = SoundLibraryManager(
            audio_output_callback=self.audio_output.music
        )
        self.video_library = VideoLibraryManager()

        # Add to AI functions
        self.ai_functions.extend(self.sound_library.get_ai_function_definitions())
        self.ai_functions.extend(self.video_library.get_ai_function_definitions())

    def _execute_function(self, function_name: str, args: dict):
        # ... existing gesture handling ...

        # Handle sound functions
        if function_name == "play_sound":
            return self.sound_library.play_sound(
                sound_name=args["sound_name"],
                volume=args.get("volume")
            )

        elif function_name == "stop_sound":
            return self.sound_library.stop_sound()

        # Handle video functions
        elif function_name == "play_video":
            return self.video_library.play_video(
                video_name=args["video_name"]
            )

        elif function_name == "search_videos":
            results = self.video_library.search_videos(
                query=args["query"]
            )
            return {
                "status": "success",
                "results": list(results.keys()),
                "count": len(results)
            }
```

### 3. Adding Custom Sounds

```python
# In sound_library_manager.py, add to SOUND_LIBRARY:

"my_custom_sound": {
    "type": "effect",
    "description": "My custom sound effect",
    "file_path": "sounds/effects/custom.wav",
    "default_volume": 0.5,
    "duration": 2.0
}
```

### 4. Adding Custom Videos

```python
# In video_library_manager.py, add to VIDEO_LIBRARY:

"my_custom_video": {
    "category": "educational",
    "description": "My educational video",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "duration": "10:00",
    "topics": ["education", "learning"]
}
```

---

## Cost Comparison

### Audio Approach

**OLD (Streaming to AI)**:
- Continuous audio streaming to OpenAI Realtime API
- ~200ms chunks × 300 chunks/minute = 60,000 samples/minute
- Cost: ~$0.06/minute of audio
- **10-minute conversation with background music**: $0.60

**NEW (Name-based)**:
- AI calls: `play_sound(name="calm_music")`
- Just function call (~50 tokens)
- Cost: ~$0.0003/call
- **10-minute conversation with background music**: $0.0003

**Savings: 99.95%** 🎉

### Video Approach

**OLD (AI searching YouTube)**:
- AI searches YouTube via API
- Filters results, picks video
- Multiple API calls, tokens for processing
- Cost: ~$0.01-0.05 per video search

**NEW (Name-based)**:
- AI calls: `play_video(name="relaxing_nature")`
- Just function call (~50 tokens)
- Cost: ~$0.0003/call

**Savings: 99%** 🎉

---

## AI Intelligence Preserved

### Example: User Wants Relaxation

**AI Reasoning:**
```
User: "I'm stressed and need to relax"

AI thinks:
  - User is stressed (emotion detected)
  - Needs calming intervention
  - Multiple options available:
    * Sound: rain, ocean, nature, calm_music
    * Video: relaxing_nature, ocean_waves, forest_sounds
  - Best choice: Start with ambient sound (less intrusive)
  - Then offer video if user wants

AI calls: play_sound(sound_name="rain", volume=0.2)
AI says: "I've started some gentle rain sounds. Would you like me to show you a relaxing nature video too?"
```

**AI made ALL decisions:**
- WHAT to play (rain not music)
- WHICH media type (sound first, not video)
- WHEN to play it (immediately)
- HOW loud (quiet 0.2 volume)
- WHETHER to offer more (yes, suggest video)

---

## Benefits

### 🎯 Same as Gesture System

1. **AI-Driven** - AI chooses specific sounds/videos, not random
2. **Economical** - 99% cost reduction vs streaming
3. **Low Latency** - Instant playback, no generation
4. **Curated** - Only appropriate, tested content
5. **Extensible** - Easy to add more sounds/videos

### 🆕 Unique to Media

1. **YouTube Integration** - Stream music directly
2. **Multi-Modal** - Audio AND video
3. **Ambient Capability** - Background sounds during conversation
4. **Search Function** - AI can discover content dynamically

---

## Directory Setup

Create sound files directory:
```bash
mkdir -p sounds/{music,effects,ambient}
```

You can:
1. Record your own sounds
2. Download royalty-free sounds
3. Use text-to-speech for voice effects
4. Convert YouTube audio to WAV files

For YouTube videos, just add URLs to the library - no files needed!

---

## Summary

**Sound Library**: 15 curated sounds (music, effects, ambient, YouTube)
**Video Library**: 10 curated videos (educational, music, nature, inspiration)
**Cost**: ~$0.0003 per function call (99% savings)
**Integration**: Identical pattern to gestures
**AI Control**: Full - AI chooses what, when, how

The AI now has expressive media capabilities without the cost of continuous audio streaming!
