#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def test_steering_servo():
    """Test and diagnose steering servo issues"""

    print("=== Steering Servo Diagnostic ===")

    print("Initializing Picarx...")
    car = Picarx()
    time.sleep(1)

    # Check current calibration values
    print(f"\nCurrent calibration values:")
    print(f"Direction servo calibration: {car.dir_cali_val}")
    print(f"Current direction angle: {car.dir_current_angle}")
    print(f"DIR_MIN: {car.DIR_MIN}, DIR_MAX: {car.DIR_MAX}")

    try:
        print("\n=== Testing Raw Servo Movement ===")

        print("1. Testing center position (calibration value only)...")
        car.dir_servo_pin.angle(car.dir_cali_val)
        time.sleep(2)

        print("2. Testing manual servo angles...")
        test_angles = [0, -30, 30, 0]

        for angle in test_angles:
            print(f"   Setting servo to raw angle: {angle}")
            car.dir_servo_pin.angle(angle)
            time.sleep(1.5)

        print("\n=== Testing Picarx set_dir_servo_angle Method ===")

        # Test the picarx method
        test_directions = [-30, -15, 0, 15, 30, 0]

        for direction in test_directions:
            print(f"   Setting direction via picarx method: {direction}")
            car.set_dir_servo_angle(direction, smooth=False)
            calculated_angle = direction + car.dir_cali_val
            print(f"   (Calculated servo angle: {calculated_angle})")
            time.sleep(1.5)

        print("\n=== Testing Calibration Reset ===")

        # Test with different calibration values
        print("Testing with calibration value of 0...")
        car.dir_cali_val = 0
        car.config_flie.set("picarx_dir_servo", "0")

        for direction in [-20, 0, 20, 0]:
            print(f"   Direction: {direction} (with cal=0)")
            car.set_dir_servo_angle(direction, smooth=False)
            time.sleep(1.5)

        print("\nSteering test complete!")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Return to center
        print("\nReturning to center...")
        car.set_dir_servo_angle(0, smooth=True)

def calibrate_steering():
    """Interactive calibration of steering servo"""

    print("\n=== Interactive Steering Calibration ===")
    print("This will help you find the correct calibration value")

    car = Picarx()

    try:
        print("\nTesting different calibration values...")
        print("Watch the front wheels and note when they're straight")

        # Test range of calibration values
        for cal_val in range(-10, 41, 5):
            print(f"\nTesting calibration value: {cal_val}")
            car.dir_servo_pin.angle(cal_val)
            time.sleep(2)

            response = input(f"Are wheels straight with cal={cal_val}? (y/n/q to quit): ").strip().lower()
            if response == 'y':
                print(f"Found good calibration value: {cal_val}")
                car.dir_cali_val = cal_val
                car.config_flie.set("picarx_dir_servo", str(cal_val))
                print(f"Updated configuration file with calibration: {cal_val}")
                break
            elif response == 'q':
                break

        print("\nTesting final calibration...")
        car.set_dir_servo_angle(0)
        time.sleep(1)
        car.set_dir_servo_angle(-30)
        time.sleep(1)
        car.set_dir_servo_angle(30)
        time.sleep(1)
        car.set_dir_servo_angle(0)

    except KeyboardInterrupt:
        print("\nCalibration interrupted")
    except Exception as e:
        print(f"Error during calibration: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "calibrate":
        calibrate_steering()
    else:
        test_steering_servo()

    print("\nTo run calibration mode: python3 test_steering_servo.py calibrate")