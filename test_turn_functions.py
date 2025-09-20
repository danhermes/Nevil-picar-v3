#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx
from action_helper import turn_left, turn_right, turn_left_in_place, turn_right_in_place

def test_actual_turn_functions():
    """Test the actual turn functions that should now work"""

    print("=== Testing Actual Turn Functions ===")
    print("These are the functions called when you command left/right")

    car = Picarx()

    try:
        print("\n1. Testing turn_left_in_place()...")
        print("   (Should turn wheels left and hold)")
        turn_left_in_place(car)
        time.sleep(2)

        print("\n2. Testing turn_right_in_place()...")
        print("   (Should turn wheels right and hold)")
        turn_right_in_place(car)
        time.sleep(2)

        print("\n3. Testing center position...")
        car.set_dir_servo_angle(0, smooth=True)
        time.sleep(2)

        print("\n4. Testing full turn_left() sequence...")
        print("   (Will move forward while turning)")
        if input("   Execute full turn sequence? (y/n): ").strip().lower() == 'y':
            turn_left(car)
            time.sleep(1)

        print("\n5. Testing full turn_right() sequence...")
        print("   (Will move forward while turning)")
        if input("   Execute full turn sequence? (y/n): ").strip().lower() == 'y':
            turn_right(car)
            time.sleep(1)

        print("\nAll turn functions completed!")
        print("Front wheels should be moving properly now.")

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nReturning to center...")
        car.set_dir_servo_angle(0, smooth=True)

if __name__ == "__main__":
    test_actual_turn_functions()