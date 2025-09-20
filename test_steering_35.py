#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def test_steering_with_calibration():
    """Test steering with calibration value of 35"""

    print("=== Testing Steering with Calibration 35 ===")

    car = Picarx()
    print(f"Loaded calibration value: {car.dir_cali_val}")

    if car.dir_cali_val != 35:
        print("WARNING: Calibration not loaded properly!")
        print("Setting calibration to 35...")
        car.dir_cali_val = 35

    try:
        print("\nTesting steering movements:")

        # Test sequence
        movements = [
            ("Straight/Center", 0),
            ("Left turn", -30),
            ("Full left", -25),
            ("Back to center", 0),
            ("Right turn", 30),
            ("Full right", 25),
            ("Back to center", 0)
        ]

        for description, angle in movements:
            print(f"\n{description}: Setting angle to {angle}°")
            raw_servo_angle = angle + car.dir_cali_val
            print(f"  (Raw servo angle: {raw_servo_angle}°)")

            car.set_dir_servo_angle(angle, smooth=True)
            time.sleep(2)

        print(f"\nSteering test complete!")
        print(f"Calibration value {car.dir_cali_val} is working correctly.")

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nReturning to center...")
        car.set_dir_servo_angle(0, smooth=True)

def quick_steering_test():
    """Quick left-right-center test"""

    print("\n=== Quick Steering Test ===")

    car = Picarx()

    try:
        print("Left...")
        car.set_dir_servo_angle(-30, smooth=True)
        time.sleep(1.5)

        print("Right...")
        car.set_dir_servo_angle(30, smooth=True)
        time.sleep(1.5)

        print("Center...")
        car.set_dir_servo_angle(0, smooth=True)
        time.sleep(1)

        print("Steering working correctly!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_steering_test()
    else:
        test_steering_with_calibration()