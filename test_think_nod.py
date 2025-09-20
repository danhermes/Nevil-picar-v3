#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx
from action_helper import think, nod, shake_head

def test_smooth_animations():
    """Test the improved smooth servo animations"""

    print("Initializing Picarx for animation testing...")
    car = Picarx()
    time.sleep(1)  # Let initialization complete

    print("\n=== Testing Improved Servo Animations ===")

    try:
        print("\n1. Testing 'think' animation (should be smooth)...")
        think(car)
        time.sleep(1)

        print("\n2. Testing 'nod' animation (should be smooth)...")
        nod(car)
        time.sleep(1)

        print("\n3. Testing 'shake_head' animation (should be smooth)...")
        shake_head(car)
        time.sleep(1)

        print("\nAll animations complete! Servos should have been much smoother.")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Reset all servos to center smoothly
        print("\nResetting all servos to center...")
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)

if __name__ == "__main__":
    test_smooth_animations()