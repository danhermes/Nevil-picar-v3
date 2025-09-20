#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def test_motor_directions():
    """Test and diagnose motor direction issues"""

    print("=== Motor Direction Diagnostic ===")

    car = Picarx()
    print(f"Current motor direction calibration: {car.cali_dir_value}")

    try:
        print("\n=== Testing Individual Motors ===")

        print("\n1. Testing Motor 1 (Left) forward...")
        car.set_motor_speed(1, 30)
        time.sleep(2)
        car.set_motor_speed(1, 0)

        response = input("   Did Motor 1 go FORWARD? (y/n): ").strip().lower()
        motor1_forward_correct = response == 'y'

        print("\n2. Testing Motor 2 (Right) forward...")
        car.set_motor_speed(2, 30)
        time.sleep(2)
        car.set_motor_speed(2, 0)

        response = input("   Did Motor 2 go FORWARD? (y/n): ").strip().lower()
        motor2_forward_correct = response == 'y'

        print("\n=== Testing Combined Forward Motion ===")

        print("\n3. Testing forward() method (straight)...")
        car.set_dir_servo_angle(0)  # Straight
        time.sleep(0.5)
        car.forward(30)
        time.sleep(2)
        car.stop()

        response = input("   Did robot go FORWARD straight? (y/n): ").strip().lower()
        forward_method_correct = response == 'y'

        print("\n=== Testing Right Turn ===")

        print("\n4. Testing right turn with forward motion...")
        car.set_dir_servo_angle(30)  # Right turn
        time.sleep(0.5)
        car.forward(30)
        time.sleep(2)
        car.stop()
        car.set_dir_servo_angle(0)  # Straighten

        response = input("   Did robot turn RIGHT while moving forward? (y/n): ").strip().lower()
        right_turn_correct = response == 'y'

        print("\n=== Diagnosis Results ===")
        print(f"Motor 1 forward correct: {motor1_forward_correct}")
        print(f"Motor 2 forward correct: {motor2_forward_correct}")
        print(f"Forward method correct: {forward_method_correct}")
        print(f"Right turn correct: {right_turn_correct}")

        if not motor1_forward_correct or not motor2_forward_correct:
            print("\n⚠ MOTOR DIRECTION ISSUE DETECTED!")
            print("Need to flip motor direction calibration")

            new_cal = []
            if not motor1_forward_correct:
                new_cal.append(-1)
                print("Motor 1 needs to be flipped: 1 → -1")
            else:
                new_cal.append(1)

            if not motor2_forward_correct:
                new_cal.append(-1)
                print("Motor 2 needs to be flipped: 1 → -1")
            else:
                new_cal.append(1)

            print(f"\nRecommended motor calibration: {new_cal}")

            if input("Apply fix? (y/n): ").strip().lower() == 'y':
                car.cali_dir_value = new_cal
                car.config_flie.set("picarx_dir_motor", str(new_cal))
                print(f"Updated motor calibration to: {new_cal}")

                print("\nTesting with new calibration...")
                car.set_dir_servo_angle(0)
                car.forward(30)
                time.sleep(2)
                car.stop()

                if input("Does forward work correctly now? (y/n): ").strip().lower() == 'y':
                    print("✅ Motor direction fix successful!")
                else:
                    print("❌ Still having issues - may need further investigation")

    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nStopping all motors...")
        car.stop()
        car.set_dir_servo_angle(0)

if __name__ == "__main__":
    test_motor_directions()