# YouTube Music Integration - COMPLETE ✅

Nevil can now play music! The integration is complete and ready to use.

---

## What Was Changed

### 1. System Prompt Updated (`nodes/ai_cognition_realtime/.messages`)

Added music capability section at the beginning of system prompt:

```
## MUSIC CAPABILITY
YOU CAN PLAY MUSIC! Use stream_youtube_music function when users ask for music, sounds, or audio.
Examples: User: 'play music' → stream_youtube_music(category='music').
User: 'play Christmas music' → stream_youtube_music(mood='festive').
User: 'I need to relax' → stream_youtube_music(mood='calm').
User: 'play nature sounds' → stream_youtube_music(category='ambient').
NEVER say 'I can't play music' - you CAN play music using this function!
```

### 2. AI Node Updated (`nodes/ai_cognition_realtime/ai_cognition_realtime_node.py`)

#### Added Import:
```python
from nevil_framework.youtube_library import YouTubeLibrary
```

#### Added Initialization (line 99-101):
```python
# Initialize YouTube music library
self.youtube_library = YouTubeLibrary()
self.logger.info(f"YouTube library initialized with {len(self.youtube_library.library)} songs")
```

#### Added Function to AI Tools (line 210):
```python
# Add YouTube music function
self.gesture_definitions.append(self.youtube_library.get_ai_function_definition())
```

#### Added Function Handler (line 672-674):
```python
# Handle YouTube music streaming
elif function_name == "stream_youtube_music":
    self.logger.info("🎵 Handling YouTube music streaming")
    return self._handle_stream_youtube_music(args)
```

#### Added Handler Method (line 926-944):
```python
def _handle_stream_youtube_music(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle YouTube music streaming"""
    try:
        category = args.get('category')
        mood = args.get('mood')

        self.logger.info(f"🎵 Streaming YouTube music: category={category}, mood={mood}")

        # Stream audio via youtube library
        result = self.youtube_library.stream_audio(
            category=category,
            mood=mood
        )

        return result

    except Exception as e:
        self.logger.error(f"Error in _handle_stream_youtube_music: {e}")
        return {"status": "error", "message": str(e)}
```

---

## How It Works

### User Says: "Play music"

1. **AI receives**: "Play music"
2. **AI reads system prompt**: Sees "YOU CAN PLAY MUSIC! Use stream_youtube_music..."
3. **AI calls**: `stream_youtube_music(category="music")`
4. **_handle_stream_youtube_music()**: Receives the call
5. **youtube_library.stream_audio()**: Picks random music from "music" category
6. **YouTubeMusicStreamer**: Downloads and plays audio via yt-dlp + pygame
7. **User hears**: Music playing!

### User Says: "Play Christmas music"

1. **AI calls**: `stream_youtube_music(mood="festive")`
2. **System picks**: Random from festive songs (holly_jolly_christmas or snow_heat_miser)
3. **Plays**: Christmas music!

---

## Available Music (10 songs)

### Categories
- `music` - 6 songs
- `ambient` - 4 songs

### Moods
- `calm` - lofi_study, rain_sounds
- `energetic` - upbeat_pop
- `festive` - holly_jolly_christmas, snow_heat_miser
- `peaceful` - ocean_sounds, nature_sounds
- `elegant` - classical_piano
- `relaxed` - jazz_cafe
- `meditative` - meditation_music

---

## AI Function Definition Sent

```python
{
  "name": "stream_youtube_music",
  "description": "**THIS IS HOW YOU PLAY MUSIC/SOUNDS.** You CAN play music - use this function!
                  Library: 10 songs. Categories: ambient, music.
                  Moods: peaceful, energetic, calm, elegant, meditative, relaxed, festive.

                  When user asks for music, sounds, songs, or audio - use this function.
                  Choose by category (music/ambient) or mood (calm/energetic/festive/peaceful/etc).
                  System will pick appropriate song from that category/mood.

                  Examples:
                  - User: 'play music' → stream_youtube_music(category='music')
                  - User: 'play Christmas music' → stream_youtube_music(mood='festive')
                  - User: 'I need to relax' → stream_youtube_music(mood='calm')
                  - User: 'play sounds' → stream_youtube_music(category='ambient')",
  "parameters": {
    "category": {"enum": ["music", "ambient"]},
    "mood": {"enum": ["peaceful", "energetic", "calm", "elegant", "meditative", "relaxed", "festive"]}
  }
}
```

---

## Token Cost

- **Function definition**: ~250 tokens (sent once per session)
- **Per function call**: ~15 tokens
- **Streaming audio**: 0 tokens (happens locally)

**Total cost per song**: ~15 tokens = $0.0003

---

## Testing

### Restart Nevil:
```bash
sudo systemctl restart nevil
```

### Test Phrases:
- "Play some music"
- "Play Christmas music"
- "I need to relax" (should play calm music)
- "Play nature sounds"
- "Play something festive"

### Expected Behavior:
Nevil should:
1. **NOT say** "I can't play music"
2. **Call** `stream_youtube_music(category/mood)`
3. **Play** audio from YouTube
4. **Respond** with something like "Sure! Playing some relaxing music for you"

---

## Adding More Songs

Edit `config/youtube_music.json`:

```json
{
  "name": "new_song",
  "description": "Description here",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "category": "music",
  "mood": "calm"
}
```

Then restart Nevil.

---

## Summary

✅ System prompt updated - Nevil knows he can play music
✅ YouTube library integrated into AI node
✅ Function added to AI's tool list
✅ Handler implemented for music streaming
✅ 10 curated songs ready to play
✅ Category/mood-based selection (constant token cost)
✅ Ready to use!

**Nevil will now play music when asked!** 🎵
