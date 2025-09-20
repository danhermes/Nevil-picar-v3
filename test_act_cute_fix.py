#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx
from action_helper import act_cute

def test_improved_act_cute():
    """Test the improved act_cute function"""

    print("=== Testing Improved act_cute Function ===")
    print("This should be gentle wiggling, not violent head banging!")

    car = Picarx()
    time.sleep(1)

    try:
        print("\nOLD act_cute behavior:")
        print("- Violent forward/backward jerking (15 times)")
        print("- Extreme camera tilt (-20°)")
        print("- Fast movements causing head banging")

        print("\nNEW act_cute behavior:")
        print("- Gentle left/right wiggling motion")
        print("- Mild camera tilt (-10°)")
        print("- Smooth, cute movements")

        print("\nExecuting improved act_cute...")
        act_cute(car)

        print("\nact_cute complete!")
        print("This should have been much gentler and actually cute!")

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure robot is in safe state
        print("\nReturning to safe position...")
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        car.stop()

def old_act_cute_demo(car):
    """Demo of what the old act_cute was doing (for comparison)"""
    print("OLD act_cute (for comparison - don't run this!):")
    print("car.set_cam_tilt_angle(-20)")
    print("for i in range(15):")
    print("    car.forward(5)")
    print("    sleep(0.04)")
    print("    car.backward(5)")
    print("    sleep(0.04)")
    print("= 15 rapid forward/backward jerks = head banging!")

if __name__ == "__main__":
    test_improved_act_cute()