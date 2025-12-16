# YouTube Music Library - Quick Reference

## Adding YouTube URLs

Edit `youtube_music.json` and add entries like this:

```json
{
  "name": "YOUR_NAME",
  "description": "What this music is (AI reads this)",
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "category": "music",
  "mood": "calm"
}
```

## Categories
- `music` - Songs, playlists, music videos
- `ambient` - Nature sounds, white noise, rain

## Moods
- `calm` - Relaxing, peaceful
- `energetic` - Upbeat, motivating
- `peaceful` - Very calming
- `meditative` - Meditation
- `elegant` - Classical, sophisticated
- `relaxed` - Casual, easy listening

## How AI Uses This

AI reads the **description** and **mood**, then picks based on context:

- User: "I'm stressed" → AI picks `ocean_sounds` (peaceful)
- User: "I need to focus" → AI picks `lofi_study` (calm)
- User: "Play something upbeat" → AI picks `upbeat_pop` (energetic)

## Current Library (8 entries)

1. `lofi_study` - Lo-fi hip hop (calm)
2. `jazz_cafe` - Smooth jazz (relaxed)
3. `classical_piano` - Classical (elegant)
4. `ocean_sounds` - Ocean waves (peaceful)
5. `rain_sounds` - Rain sounds (calm)
6. `upbeat_pop` - Pop music (energetic)
7. `meditation_music` - Meditation (meditative)
8. `nature_sounds` - Forest birds (peaceful)

## After Adding URLs

Restart Nevil to reload:
```bash
sudo systemctl restart nevil
```

Or reload manually in Python:
```python
library.load_library()
```
