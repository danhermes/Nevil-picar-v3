# YouTube Music - Category-Based Token Optimization

## Overview

**Category/mood-based selection** minimizes tokens regardless of library size.

## Token Comparison

### ❌ Name-Based (OLD - scales poorly)

```python
# Function definition grows with every song:
{
  "name": "stream_youtube_music",
  "parameters": {
    "name": {
      "enum": [
        "lofi_study", "jazz_cafe", "classical_piano", "ocean_sounds",
        "rain_sounds", "upbeat_pop", "meditation_music", "nature_sounds",
        "holly_jolly_christmas", "snow_heat_miser",
        // ... 100 more songs = 100 more entries
      ]
    }
  }
}
```

**Token cost**: ~25 tokens per song × number of songs
- 10 songs = 250 tokens
- 100 songs = 2,500 tokens
- 1000 songs = 25,000 tokens ❌

### ✅ Category-Based (NEW - constant size)

```python
# Function definition stays small:
{
  "name": "stream_youtube_music",
  "description": "Library: 10 songs. Categories: music, ambient. Moods: calm, energetic, festive, peaceful, elegant, relaxed, meditative.",
  "parameters": {
    "category": {
      "enum": ["music", "ambient"]
    },
    "mood": {
      "enum": ["calm", "energetic", "festive", "peaceful", "elegant", "relaxed", "meditative"]
    }
  }
}
```

**Token cost**: ~150 tokens (constant regardless of library size)
- 10 songs = 150 tokens
- 100 songs = 150 tokens ✅
- 1000 songs = 150 tokens ✅

## How It Works

### AI Calls

```python
# User: "Play some Christmas music"
stream_youtube_music(mood="festive")
# System randomly picks: holly_jolly_christmas OR snow_heat_miser

# User: "I need to relax"
stream_youtube_music(mood="calm")
# System randomly picks: lofi_study OR rain_sounds

# User: "Play ambient sounds"
stream_youtube_music(category="ambient")
# System randomly picks from all ambient entries

# User: "Play peaceful ambient music"
stream_youtube_music(category="ambient", mood="peaceful")
# System picks from ambient + peaceful: ocean_sounds OR nature_sounds
```

### Local Selection

```python
# In youtube_library.py (happens locally - 0 tokens to AI):
def stream_audio(self, category=None, mood=None):
    candidates = self.library

    # Filter by category
    if category:
        candidates = [e for e in candidates if e['category'] == category]

    # Filter by mood
    if mood:
        candidates = [e for e in candidates if e['mood'] == mood]

    # Randomly pick one
    entry = random.choice(candidates)

    # Stream the URL (AI never sees this)
    return streamer.stream_audio(entry['url'])
```

## Scaling Example

### Library Growth

```
Start: 10 songs
Categories: music, ambient
Moods: calm, festive, peaceful, energetic, elegant, relaxed, meditative
Token cost: ~150 tokens

Add 90 more songs (total 100):
Categories: music, ambient, educational (added 1 category)
Moods: calm, festive, peaceful, energetic, elegant, relaxed, meditative, focused (added 1 mood)
Token cost: ~160 tokens (only +10 tokens!)

Add 900 more songs (total 1000):
Categories: music, ambient, educational, entertainment (added 2 more categories)
Moods: calm, festive, peaceful, energetic, elegant, relaxed, meditative, focused, happy, sad (added 2 more moods)
Token cost: ~180 tokens (only +30 tokens from original!)
```

**Scaling**: ~0.03 tokens per song (vs 25 tokens per song with name-based)

## AI Intelligence Preserved

AI still makes smart choices based on context:

**User**: "I'm stressed"
```python
AI thinks: stressed = needs calm
AI calls: stream_youtube_music(mood="calm")
System picks: rain_sounds (perfect!)
```

**User**: "It's Christmas!"
```python
AI thinks: Christmas = festive
AI calls: stream_youtube_music(mood="festive")
System picks: holly_jolly_christmas or snow_heat_miser (both appropriate!)
```

**User**: "I need to focus on work"
```python
AI thinks: focus = calm music
AI calls: stream_youtube_music(category="music", mood="calm")
System picks: lofi_study (perfect!)
```

## Categories and Moods

### Current Categories
- `music` - Songs, playlists
- `ambient` - Nature sounds, white noise

### Current Moods
- `calm` - Relaxing
- `energetic` - Upbeat
- `festive` - Holiday/celebration
- `peaceful` - Very calming
- `elegant` - Sophisticated
- `relaxed` - Casual
- `meditative` - Deep relaxation

### Adding New Categories/Moods

Just add to your JSON entries - function definition auto-updates:

```json
{
  "name": "workout_music",
  "url": "https://...",
  "category": "music",
  "mood": "intense"  // ← New mood, automatically added to enum
}
```

## Integration Code

```python
# In ai_cognition_realtime_node.py:

from nevil_framework.youtube_library import YouTubeLibrary

class AICognitionRealtimeNode:
    def __init__(self):
        # Initialize YouTube library
        self.youtube_library = YouTubeLibrary()

        # Add to AI functions
        self.gesture_definitions.append(
            self.youtube_library.get_ai_function_definition()
        )

    def _execute_function(self, function_name, args):
        if function_name == "stream_youtube_music":
            return self.youtube_library.stream_audio(
                category=args.get("category"),
                mood=args.get("mood")
            )
```

## Summary

| Metric | Name-Based | Category-Based |
|--------|------------|----------------|
| 10 songs | 250 tokens | 150 tokens |
| 100 songs | 2,500 tokens | 160 tokens |
| 1000 songs | 25,000 tokens | 180 tokens |
| **Scaling** | **Linear** | **Constant** |

**Winner**: Category-based for scalability! 🎉

The AI is still intelligent (picks mood/category based on context), but tokens stay constant regardless of library size.
