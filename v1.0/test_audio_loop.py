#!/usr/bin/env python3

import os
import sys
import time

# Enable robot_hat speaker switch
os.popen("pinctrl set 20 op dh")
time.sleep(0.5)

from robot_hat import Music

def test_audio_loop():
    music = Music()

    # Initialize mixer with proper settings
    music.pygame.mixer.init(frequency=44100, size=-16, channels=2)

    sound_file = 'sounds/car-double-horn.wav'

    print(f"Testing audio loop with: {sound_file}")
    print("Press Ctrl+C to stop")

    try:
        # Load and play sound on loop
        music.pygame.mixer.music.load(sound_file)
        music.pygame.mixer.music.play(loops=-1)  # -1 means infinite loop

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping audio loop...")
        music.music_stop()
        print("Audio test complete")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_audio_loop()