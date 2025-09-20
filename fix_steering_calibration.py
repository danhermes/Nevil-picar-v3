#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def fix_steering_calibration():
    """Quick fix for steering servo calibration issues"""

    print("=== Fixing Steering Servo Calibration ===")

    # First, check current values
    car = Picarx()
    print(f"Current calibration value: {car.dir_cali_val}")

    if abs(car.dir_cali_val) > 20:
        print(f"WARNING: Calibration value {car.dir_cali_val} is outside normal range!")
        print("Resetting to 0 and testing...")

        # Reset calibration to 0
        car.dir_cali_val = 0
        car.config_flie.set("picarx_dir_servo", "0")
        print("Reset calibration to 0")

        # Test steering
        print("\nTesting steering with calibration = 0:")

        print("Center (0°)...")
        car.set_dir_servo_angle(0, smooth=False)
        time.sleep(2)

        print("Left (-30°)...")
        car.set_dir_servo_angle(-30, smooth=False)
        time.sleep(2)

        print("Right (+30°)...")
        car.set_dir_servo_angle(30, smooth=False)
        time.sleep(2)

        print("Center (0°)...")
        car.set_dir_servo_angle(0, smooth=False)
        time.sleep(1)

        print("\nSteering should now be working!")
        print("If wheels are not straight at center, run:")
        print("python3 test_steering_servo.py calibrate")

    else:
        print("Calibration value looks normal. Testing movement...")

        # Test current calibration
        print("Testing current calibration:")

        movements = [
            ("Center", 0),
            ("Left", -30),
            ("Right", 30),
            ("Center", 0)
        ]

        for name, angle in movements:
            print(f"{name} ({angle}°)...")
            car.set_dir_servo_angle(angle, smooth=False)
            time.sleep(2)

        print("If steering still not working, check:")
        print("1. Servo connections (P2 pin)")
        print("2. Power supply to servos")
        print("3. Servo mechanical issues")

if __name__ == "__main__":
    try:
        fix_steering_calibration()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()