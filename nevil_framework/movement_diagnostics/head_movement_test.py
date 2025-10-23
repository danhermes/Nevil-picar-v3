#!/usr/bin/env python3
"""
Head Movement Diagnostic Tool
Tests pan/tilt servo actions from action_helper
"""

import sys
import os
import subprocess
from time import sleep

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../nodes/navigation'))

from nodes.navigation import action_helper
from nodes.navigation.picarx import Picarx

# Head movement actions to test (primarily pan/tilt focused)
HEAD_ACTIONS = [
    ("shake_head", action_helper.shake_head),
    ("nod", action_helper.nod),
    ("wave_hands", action_helper.wave_hands),
    ("resist", action_helper.resist),
    ("act_cute", action_helper.act_cute),
    ("rub_hands", action_helper.rub_hands),
    ("think", action_helper.think),
    ("keep_think", action_helper.keep_think),
    ("celebrate", action_helper.celebrate),
    ("depressed", action_helper.depressed),
]

def speak_quick(text):
    """Quick TTS announcement using espeak"""
    try:
        subprocess.run(
            ["espeak", "-v", "en-us", "-s", "180", text],
            timeout=3,
            capture_output=True
        )
    except Exception as e:
        print(f"TTS error: {e}")

def main():
    print("=" * 50)
    print("Head Movement Diagnostic Test")
    print("=" * 50)
    print()

    # Initialize car
    print("Initializing PiCar-X...")
    car = Picarx()
    car.reset()
    sleep(1)
    print("Ready!\n")

    # Test each action
    for action_name, action_func in HEAD_ACTIONS:
        print("-" * 50)
        print(f"Testing: {action_name}")
        print("-" * 50)

        # Announce the action
        speak_quick(action_name.replace("_", " "))

        # Reset before starting this action
        car.reset()
        sleep(0.3)

        # Run the action 3 times
        for i in range(3):
            print(f"  Iteration {i+1}/3...")
            action_func(car)
            sleep(0.5)  # Brief pause between iterations

        print(f"Completed: {action_name}\n")
        sleep(1)  # Pause before next action

    # Reset to neutral position
    print("-" * 50)
    print("Diagnostic complete! Resetting to neutral position...")
    car.reset()
    print("Done!")
    print("=" * 50)

if __name__ == "__main__":
    main()
