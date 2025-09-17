#!/usr/bin/env python3

import pygame
import time
import sys

def test_audio_loop():
    pygame.mixer.init()

    sound_file = "v1.0/sounds/car-double-horn.wav"

    try:
        sound = pygame.mixer.Sound(sound_file)

        print(f"Playing {sound_file} in a loop...")
        print("Press Ctrl+C to stop")

        sound.play(loops=-1)

        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping audio loop...")
        pygame.mixer.stop()
        pygame.mixer.quit()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        pygame.mixer.quit()
        sys.exit(1)

if __name__ == "__main__":
    test_audio_loop()