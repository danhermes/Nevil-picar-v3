#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def diagnose_steering_skew():
    """Diagnose why steering returns to left skew"""

    print("=== Diagnosing Steering Skew Issue ===")

    car = Picarx()

    print(f"Configuration file calibration: {car.dir_cali_val}")
    print(f"Current direction angle: {car.dir_current_angle}")

    print("\n=== Testing Different Calibration Values ===")

    # Test range around 35 to find the true center
    test_values = [30, 32, 35, 37, 40, 42, 45]

    for cal_val in test_values:
        print(f"\nTesting calibration value: {cal_val}")

        # Set the calibration temporarily
        car.dir_cali_val = cal_val

        # Command center position (0°)
        car.set_dir_servo_angle(0, smooth=False)
        raw_angle = 0 + cal_val
        print(f"  Commanded 0°, raw servo angle: {raw_angle}°")

        time.sleep(2)

        response = input(f"  Are wheels straight with cal={cal_val}? (y/n/s=skip): ").strip().lower()
        if response == 'y':
            print(f"*** Found correct calibration: {cal_val} ***")

            # Update config file
            car.config_flie.set("picarx_dir_servo", str(cal_val))
            print(f"Updated configuration file with: {cal_val}")

            # Test the new calibration
            print("\nTesting new calibration:")
            test_steering_with_cal(car, cal_val)
            break
        elif response == 's':
            continue

    print("\nDiagnosis complete.")

def test_steering_with_cal(car, cal_val):
    """Test steering with specific calibration value"""

    car.dir_cali_val = cal_val

    movements = [
        ("Center", 0),
        ("Left", -20),
        ("Center", 0),
        ("Right", 20),
        ("Center", 0)
    ]

    for name, angle in movements:
        print(f"  {name} ({angle}°)...")
        car.set_dir_servo_angle(angle, smooth=True)
        time.sleep(1.5)

    print(f"Final center position with cal={cal_val}")

def quick_center_test():
    """Quick test to see current center position"""

    print("=== Quick Center Position Test ===")

    car = Picarx()
    print(f"Current calibration: {car.dir_cali_val}")

    print("Setting to center (0°)...")
    car.set_dir_servo_angle(0, smooth=False)

    print("Is this straight? If not, we need to adjust calibration.")

def manual_calibration():
    """Manual calibration by testing raw servo angles"""

    print("=== Manual Raw Servo Calibration ===")
    print("Testing raw servo angles to find true center")

    car = Picarx()

    # Test raw servo angles (bypass picarx calibration)
    test_angles = [30, 35, 40, 45, 50]

    for angle in test_angles:
        print(f"\nTesting raw servo angle: {angle}°")
        car.dir_servo_pin.angle(angle)
        time.sleep(2)

        response = input(f"Are wheels straight at {angle}°? (y/n): ").strip().lower()
        if response == 'y':
            print(f"*** Raw servo center found at: {angle}° ***")
            print(f"This should be your calibration value.")

            # Update calibration
            car.dir_cali_val = angle
            car.config_flie.set("picarx_dir_servo", str(angle))
            print(f"Updated configuration to: {angle}")

            # Test with picarx method
            print("\nTesting with picarx method:")
            car.set_dir_servo_angle(0, smooth=False)
            break

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_center_test()
        elif sys.argv[1] == "manual":
            manual_calibration()
        else:
            diagnose_steering_skew()
    else:
        print("Usage:")
        print("  python3 diagnose_steering_skew.py          # Full diagnosis")
        print("  python3 diagnose_steering_skew.py quick    # Quick center test")
        print("  python3 diagnose_steering_skew.py manual   # Manual raw angle calibration")
        print()
        diagnose_steering_skew()