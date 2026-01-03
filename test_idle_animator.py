#!/usr/bin/env python3
"""
Test script for speech idle animator.
Tests if the animator can move the servos correctly.
"""

import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from nevil_framework.speech_idle_animator import SpeechIdleAnimator

# Import picarx
from nodes.navigation.picarx import Picarx

def test_idle_animator():
    """Test the idle animator with a real car"""
    print("="*60)
    print("Speech Idle Animator Test")
    print("="*60)

    # Initialize car
    print("\n1. Initializing car...")
    car = Picarx()
    print("✓ Car initialized")

    # Reset to neutral
    print("\n2. Resetting to neutral position...")
    car.set_cam_pan_angle(0)
    car.set_cam_tilt_angle(0)
    car.set_dir_servo_angle(0)
    time.sleep(1)
    print("✓ Neutral position set")

    # Create animator
    print("\n3. Creating idle animator...")
    animator = SpeechIdleAnimator(get_car_callback=lambda: car)
    animator.set_animation_intensity("expressive")
    print("✓ Animator created with EXPRESSIVE intensity")
    print(f"   - Head pan range: ±{animator.head_pan_range}°")
    print(f"   - Head tilt range: ±{animator.head_tilt_range}°")
    print(f"   - Wheel angle range: ±{animator.wheel_angle_range}°")

    # Start animation
    print("\n4. Starting animation...")
    animator.start_animation()
    print("✓ Animation started")

    # Let it run
    print("\n5. Animating for 10 seconds...")
    print("   Watch for:")
    print("   - Head panning left/right")
    print("   - Head tilting up/down")
    print("   - Front wheels rocking")
    print("   - Occasional weight shifts")
    print()

    for i in range(10, 0, -1):
        print(f"   {i} seconds remaining...", end='\r')
        time.sleep(1)

    # Stop animation
    print("\n\n6. Stopping animation...")
    animator.stop_animation()
    print("✓ Animation stopped")

    # Verify neutral
    print("\n7. Verifying return to neutral...")
    time.sleep(0.5)
    print(f"   - Pan angle: {getattr(car, 'current_pan_angle', 'unknown')}")
    print(f"   - Tilt angle: {getattr(car, 'current_tilt_angle', 'unknown')}")
    print(f"   - Wheel angle: {getattr(car, 'current_dir_angle', 'unknown')}")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
    print("\nDid you see the animations?")
    print("If YES: Animations are working correctly! ✓")
    print("If NO: Check servo connections and calibration.")

if __name__ == "__main__":
    try:
        test_idle_animator()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
