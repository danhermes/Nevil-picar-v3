# YouTube Music Library - Simple Guide

## Overview

Add YouTube URLs to a config file → AI chooses and streams them automatically.

**Similar to gesture library**: AI picks from curated list instead of searching/generating.

---

## Quick Start

### 1. Add YouTube URLs

Edit `config/youtube_music.json`:

```json
{
  "library": [
    {
      "name": "lofi_study",
      "description": "Lo-fi hip hop beats for studying",
      "url": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
      "category": "music",
      "mood": "calm"
    },
    {
      "name": "my_favorite_song",
      "description": "My favorite relaxing song",
      "url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
      "category": "music",
      "mood": "peaceful"
    }
  ]
}
```

### 2. AI Automatically Uses Them

User: "Play some relaxing music"
```python
AI chooses: stream_youtube_music(mood="calm")
# System randomly picks: lofi_study or rain_sounds
```

User: "I'm stressed"
```python
AI chooses: stream_youtube_music(mood="peaceful")
# System randomly picks: ocean_sounds or nature_sounds
```

User: "It's Christmas time!"
```python
AI chooses: stream_youtube_music(mood="festive")
# System randomly picks: holly_jolly_christmas or snow_heat_miser
```

---

## File Format

Each entry needs:
- **name**: Unique identifier (AI uses this)
- **description**: What it is (AI reads this to choose)
- **url**: YouTube URL
- **category**: music, ambient, educational, etc.
- **mood**: calm, energetic, peaceful, etc.

---

## How AI Chooses

AI reads the descriptions and moods, then picks based on context:

**Example 1: User needs focus**
- AI sees: "lofi_study" - calm mood
- AI chooses: `stream_youtube_music(name="lofi_study")`

**Example 2: User wants energy**
- AI sees: "upbeat_pop" - energetic mood
- AI chooses: `stream_youtube_music(name="upbeat_pop")`

**Example 3: User needs relaxation**
- AI sees: "ocean_sounds" - peaceful mood
- AI chooses: `stream_youtube_music(name="ocean_sounds")`

---

## Integration with AI Node

```python
from nevil_framework.youtube_library import YouTubeLibrary

class AICognitionNode:
    def __init__(self):
        # Initialize YouTube library
        self.youtube_library = YouTubeLibrary()

        # Add to AI functions
        self.ai_functions.append(
            self.youtube_library.get_ai_function_definition()
        )

    def _execute_function(self, function_name, args):
        # ... existing gesture handling ...

        # Handle YouTube streaming
        if function_name == "stream_youtube_music":
            return self.youtube_library.stream_audio(
                category=args.get("category"),
                mood=args.get("mood")
            )
```

---

## Categories and Moods

### Categories
- **music**: Songs, playlists, music videos
- **ambient**: Nature sounds, white noise, rain
- **educational**: How-to videos, documentaries
- **entertainment**: Fun content, performances

### Moods
- **calm**: Relaxing, peaceful content
- **energetic**: Upbeat, motivating content
- **peaceful**: Very calming, meditative
- **meditative**: Deep relaxation, meditation
- **focused**: Good for concentration

AI uses these to match user's emotional state!

---

## Adding New URLs

### Method 1: Edit JSON directly

```bash
nano config/youtube_music.json
```

Add entry:
```json
{
  "name": "YOUR_NAME",
  "description": "What this is for",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "category": "music",
  "mood": "calm"
}
```

### Method 2: Use Python (future feature)

```python
from nevil_framework.youtube_library import YouTubeLibrary

library = YouTubeLibrary()
library.add_entry(
    name="new_song",
    description="Peaceful guitar music",
    url="https://www.youtube.com/watch?v=...",
    category="music",
    mood="peaceful"
)
```

---

## Examples in Config

```json
{
  "library": [
    {
      "name": "lofi_study",
      "description": "Lo-fi hip hop beats for studying and relaxing",
      "url": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
      "category": "music",
      "mood": "calm"
    },
    {
      "name": "ocean_sounds",
      "description": "Peaceful ocean waves for relaxation",
      "url": "https://www.youtube.com/watch?v=V1bFr2SWP1I",
      "category": "ambient",
      "mood": "peaceful"
    },
    {
      "name": "upbeat_pop",
      "description": "Upbeat pop music for energy",
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "category": "music",
      "mood": "energetic"
    }
  ]
}
```

---

## Cost Savings

**OLD (streaming all audio to AI)**:
- Continuous audio stream to OpenAI
- ~$0.06/minute
- 10-minute conversation with music = $0.60

**NEW (AI picks from list)**:
- Just function call: `stream_youtube_music(name="lofi_study")`
- ~50 tokens = $0.0003
- 10-minute conversation with music = $0.0003

**Savings: 99.95%** 🎉

---

## Testing

```bash
# Test library loading
python3 nevil_framework/youtube_library.py

# Expected output:
# Loaded 8 YouTube music entries
# Library Stats: {...}
```

---

## Current Library (8 entries)

1. **lofi_study** - Lo-fi hip hop beats (calm)
2. **jazz_cafe** - Smooth jazz music (relaxed)
3. **classical_piano** - Classical piano (elegant)
4. **ocean_sounds** - Ocean waves (peaceful)
5. **rain_sounds** - Rain sounds (calm)
6. **upbeat_pop** - Pop music (energetic)
7. **meditation_music** - Meditation (meditative)
8. **nature_sounds** - Forest birds (peaceful)

---

## Files

```
config/
└── youtube_music.json          # Add URLs here!

nevil_framework/
└── youtube_library.py          # Loader (don't edit)

scripts/
└── youtube_music.py            # Streamer (don't edit)
```

---

## Summary

✅ Edit `config/youtube_music.json` to add URLs
✅ AI reads descriptions and moods
✅ AI chooses based on context
✅ 99.95% cost savings vs streaming audio
✅ Same pattern as gesture library

Just add YouTube URLs and let AI choose! 🎵
