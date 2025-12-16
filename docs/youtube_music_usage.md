# YouTube Music Streaming

Stream audio from YouTube videos without displaying the video.

## Features

- Downloads audio-only from YouTube videos
- Plays through the existing audio system (HiFiBerry DAC)
- Automatic cleanup of temporary files
- No video display - audio only

## Installation

Dependencies are already installed:
- `yt-dlp` - YouTube audio downloader
- `ffmpeg` - Audio format conversion
- `pygame` - Audio playback (via robot_hat.Music)

## Usage

### Command Line

```bash
python3 scripts/youtube_music.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Python API

```python
from scripts.youtube_music import YouTubeMusicStreamer

# Create streamer instance
streamer = YouTubeMusicStreamer()

# Stream a YouTube video (audio only)
streamer.stream_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Cleanup when done
streamer.cleanup()
```

## Examples

Play a single song:
```bash
python3 scripts/youtube_music.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## How It Works

1. **Download**: Uses `yt-dlp` to extract audio-only stream from YouTube
2. **Convert**: Automatically converts to WAV format for pygame compatibility
3. **Play**: Uses the same `robot_hat.Music()` system as TTS
4. **Cleanup**: Removes temporary files after playback

## Technical Details

- Audio format: WAV (24kHz, mono)
- Output device: Same as TTS (HiFiBerry DAC via ALSA)
- Temporary files: Stored in `/tmp/youtube_music_*` and auto-deleted
- GPIO: Uses GPIO 20 to enable amplifier (same as AudioOutput)

## Troubleshooting

### No sound
- Verify audio system: `aplay -l`
- Check volume: `amixer sget 'Digital'`
- Test TTS first to ensure audio works

### Download fails
- Check internet connection
- Verify YouTube URL is valid
- Update yt-dlp: `sudo apt-get update && sudo apt-get upgrade yt-dlp`

### Quality issues
- The script uses best available audio quality (`--audio-quality 0`)
- Audio is converted to WAV for compatibility with pygame

## Integration with Nevil

You can integrate this into your robot's conversation system to play music on request:

```python
from scripts.youtube_music import YouTubeMusicStreamer

# In your conversation handler
if "play music" in user_message:
    streamer = YouTubeMusicStreamer()
    streamer.stream_audio(youtube_url)
    streamer.cleanup()
```
