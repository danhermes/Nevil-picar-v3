# Media Library Quick Reference

## AI Function Calls

### Sounds (15 total)

```python
# Background Music
play_sound(sound_name="calm_music", volume=0.3)
play_sound(sound_name="upbeat_music", volume=0.4)
play_sound(sound_name="dramatic_music", volume=0.5)

# Sound Effects
play_sound(sound_name="beep", volume=0.5)
play_sound(sound_name="chime", volume=0.6)
play_sound(sound_name="alert", volume=0.7)
play_sound(sound_name="success", volume=0.6)

# Ambient
play_sound(sound_name="rain", volume=0.2)
play_sound(sound_name="ocean", volume=0.2)
play_sound(sound_name="nature", volume=0.2)

# YouTube Streaming
play_sound(sound_name="youtube_lofi", volume=0.3)
play_sound(sound_name="youtube_jazz", volume=0.3)
play_sound(sound_name="youtube_classical", volume=0.3)

# Control
stop_sound()
```

### Videos (10 total)

```python
# Educational
play_video(video_name="how_robots_work")    # 5:30
play_video(video_name="ai_explained")       # 6:12

# Music
play_video(video_name="relaxing_nature")    # 3:00:00
play_video(video_name="lofi_study")         # LIVE
play_video(video_name="classical_piano")    # 2:00:00

# Entertainment
play_video(video_name="funny_robots")       # 10:15
play_video(video_name="robot_dance")        # 2:45

# Nature
play_video(video_name="ocean_waves")        # 3:00:00
play_video(video_name="forest_sounds")      # 3:00:00

# Inspiration
play_video(video_name="robot_inspiration")  # 5:42

# Search
search_videos(query="relaxing")
```

## Integration Code

```python
from nevil_framework.sound_library_manager import SoundLibraryManager
from nevil_framework.video_library_manager import VideoLibraryManager

# Initialize
sound_library = SoundLibraryManager(audio_output_callback=audio_output.music)
video_library = VideoLibraryManager()

# Add to AI functions
ai_functions.extend(sound_library.get_ai_function_definitions())
ai_functions.extend(video_library.get_ai_function_definitions())

# Handle in function executor
def _execute_function(self, function_name, args):
    if function_name == "play_sound":
        return self.sound_library.play_sound(
            sound_name=args["sound_name"],
            volume=args.get("volume")
        )
    elif function_name == "stop_sound":
        return self.sound_library.stop_sound()
    elif function_name == "play_video":
        return self.video_library.play_video(video_name=args["video_name"])
    elif function_name == "search_videos":
        return self.video_library.search_videos(query=args["query"])
```

## Cost Comparison

| Action | Old (Streaming) | New (Name-based) | Savings |
|--------|----------------|------------------|---------|
| Play music (10 min) | $0.60 | $0.0003 | 99.95% |
| Play video | $0.01-0.05 | $0.0003 | 99% |
| Background sound | $0.06/min | $0.0003 once | 99.95% |

## Files Created

```
nevil_framework/
├── sound_library_manager.py    # Sound library system
└── video_library_manager.py    # Video library system

docs/
├── MEDIA_LIBRARY_GUIDE.md            # Full documentation
└── MEDIA_LIBRARY_QUICK_REFERENCE.md  # This file

examples/
└── media_library_example.py    # Integration examples

sounds/                         # Sound files directory
├── music/
├── effects/
└── ambient/
```

## Adding Custom Content

### Add Sound
```python
# In sound_library_manager.py SOUND_LIBRARY:
"my_sound": {
    "type": "effect",
    "description": "My custom sound",
    "file_path": "sounds/effects/my_sound.wav",
    "default_volume": 0.5,
    "duration": 2.0
}
```

### Add Video
```python
# In video_library_manager.py VIDEO_LIBRARY:
"my_video": {
    "category": "educational",
    "description": "My video",
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "duration": "10:00",
    "topics": ["topic1", "topic2"]
}
```

## Testing

```bash
# Run examples
python3 examples/media_library_example.py

# Test sound library
python3 -c "from nevil_framework.sound_library_manager import SoundLibraryManager; s = SoundLibraryManager(); print(s.get_stats())"

# Test video library
python3 -c "from nevil_framework.video_library_manager import VideoLibraryManager; v = VideoLibraryManager(); print(v.get_stats())"
```
