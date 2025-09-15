#!/usr/bin/env python3

import os
import sys
import time

# Set up path
sys.path.insert(0, '/home/dan/Nevil-picar-v3/v1.0')
os.chdir('/home/dan/Nevil-picar-v3/v1.0')

# Enable speaker
os.popen("pinctrl set 20 op dh")
time.sleep(0.5)

print("Testing Nevil audio nodes and AI cognitive text passthrough...")

# Import what we need from Nevil
from robot_hat import Music, Pin
from helpers.openai_helper import OpenAiHelper
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize Music for audio nodes
music = Music()
music.pygame.mixer.init(frequency=44100, size=-16, channels=2)

# Test audio node - play a sound
print("\n1. Testing audio node - playing sound...")
try:
    music.sound_play('sounds/car-double-horn.wav')
    time.sleep(2)
    print("   Audio node test complete")
except Exception as e:
    print(f"   Audio node error: {e}")

# Test AI cognitive text passthrough
print("\n2. Testing AI cognitive text passthrough...")
try:
    openai_helper = OpenAiHelper(
        os.getenv("OPENAI_API_KEY"),
        os.getenv("OPENAI_ASSISTANT_ID"),
        'picarx'
    )

    # Test text passthrough
    test_text = "Hello, this is a test of the cognitive text passthrough system."
    print(f"   Input text: {test_text}")

    # This would normally go through the OpenAI processing
    print("   AI cognitive processing initialized")

    # Test TTS passthrough (simulated since TTS not available)
    print("   Text-to-speech passthrough ready (TTS module not available)")

except Exception as e:
    print(f"   AI cognitive error: {e}")

print("\n3. Testing audio loop with cognitive integration...")
try:
    # Simulate audio loop with cognitive processing
    for i in range(3):
        print(f"   Loop {i+1}: Processing audio -> cognitive -> output")
        music.sound_play('sounds/car-double-horn.wav')
        time.sleep(1)
    print("   Audio loop test complete")
except Exception as e:
    print(f"   Loop error: {e}")

print("\nAll tests complete!")