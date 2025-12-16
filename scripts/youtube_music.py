#!/usr/bin/env python3
"""
YouTube Music Streamer
Stream audio from YouTube videos without displaying video
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add parent directory to path to import audio modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from robot_hat import Music


class YouTubeMusicStreamer:
    """Stream audio from YouTube videos using yt-dlp and pygame"""

    def __init__(self):
        """Initialize the music streamer"""
        # Enable amplifier GPIO (same as AudioOutput)
        try:
            result = subprocess.run(
                ["pinctrl", "set", "20", "op", "dh"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                print("[YouTubeMusic] Amplifier enabled (GPIO 20 HIGH)")
            else:
                print(f"[YouTubeMusic] Warning: GPIO 20 enable failed: {result.stderr}")
        except Exception as e:
            print(f"[YouTubeMusic] Warning: Could not enable GPIO 20: {e}")

        # Initialize Music() player
        self.music = Music()
        self.temp_dir = tempfile.mkdtemp(prefix="youtube_music_")
        print(f"[YouTubeMusic] Temporary directory: {self.temp_dir}")

    def stream_audio(self, url, blocking=True):
        """
        Stream audio from a YouTube URL

        Args:
            url: YouTube video URL
            blocking: If True, wait for playback to complete. If False, return immediately.

        Returns:
            True if successful, False otherwise
        """
        print(f"[YouTubeMusic] Fetching audio from: {url}")

        # Output file path
        output_file = os.path.join(self.temp_dir, "audio.wav")

        try:
            # Download audio using yt-dlp
            # -x: extract audio
            # --audio-format wav: convert to WAV for pygame compatibility
            # --audio-quality 0: best quality
            # -o: output template
            cmd = [
                "yt-dlp",
                "-x",  # Extract audio
                "--audio-format", "wav",  # Convert to WAV
                "--audio-quality", "0",  # Best quality
                "-o", output_file.replace('.wav', '.%(ext)s'),  # Output template
                url
            ]

            print(f"[YouTubeMusic] Downloading audio...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"[YouTubeMusic] Error downloading: {result.stderr}")
                return False

            # Play the audio file
            if os.path.exists(output_file):
                print(f"[YouTubeMusic] Playing audio...")
                self.music.music_play(output_file)

                if blocking:
                    # Wait for playback to complete
                    while self.music.pygame.mixer.music.get_busy():
                        self.music.pygame.time.Clock().tick(10)

                    print(f"[YouTubeMusic] Playback complete")

                    # Cleanup
                    os.remove(output_file)
                else:
                    print(f"[YouTubeMusic] Playback started (non-blocking)")

                return True
            else:
                print(f"[YouTubeMusic] Error: Audio file not found")
                return False

        except Exception as e:
            print(f"[YouTubeMusic] Error: {e}")
            return False

    def cleanup(self):
        """Cleanup temporary files and resources"""
        try:
            # Stop playback
            self.music.music_stop()

            # Remove temp directory
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"[YouTubeMusic] Cleaned up temporary files")
        except Exception as e:
            print(f"[YouTubeMusic] Cleanup error: {e}")

    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()


def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python3 youtube_music.py <youtube_url>")
        print("Example: python3 youtube_music.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
        sys.exit(1)

    url = sys.argv[1]

    streamer = YouTubeMusicStreamer()
    try:
        streamer.stream_audio(url)
    finally:
        streamer.cleanup()


if __name__ == "__main__":
    main()
