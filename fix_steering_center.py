#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def fix_steering_center():
    """Fix the steering to proper center position"""

    print("=== Fixing Steering Center Position ===")

    car = Picarx()
    print(f"Current calibration: {car.dir_cali_val}")

    print("\n1. Checking current state...")
    print(f"   dir_current_angle: {car.dir_current_angle}")
    print(f"   Calculated servo position: {car.dir_current_angle + car.dir_cali_val}")

    print("\n2. Setting explicit center (0°) with method...")
    car.set_dir_servo_angle(0, smooth=False)
    print(f"   After set_dir_servo_angle(0): dir_current_angle = {car.dir_current_angle}")
    time.sleep(2)

    if input("   Are wheels straight now? (y/n): ").strip().lower() != 'y':
        print("\n3. Problem detected! Testing direct servo control...")

        # Test direct servo control
        print("   Setting servo directly to 35°...")
        car.dir_servo_pin.angle(35)
        car.dir_current_angle = 0  # Update tracking
        time.sleep(2)

        if input("   Are wheels straight with direct control? (y/n): ").strip().lower() == 'y':
            print("   ✓ Direct control works - issue is in set_dir_servo_angle method")

            # Check the smooth movement logic
            print("\n4. Testing smooth vs non-smooth movement...")

            print("   Testing smooth=False...")
            car.set_dir_servo_angle(0, smooth=False)
            time.sleep(2)
            straight_no_smooth = input("   Straight with smooth=False? (y/n): ").strip().lower() == 'y'

            print("   Testing smooth=True...")
            car.set_dir_servo_angle(0, smooth=True)
            time.sleep(2)
            straight_with_smooth = input("   Straight with smooth=True? (y/n): ").strip().lower() == 'y'

            if straight_no_smooth and not straight_with_smooth:
                print("   ✗ Issue is with smooth movement logic!")
                return "smooth_movement_issue"
            elif not straight_no_smooth and not straight_with_smooth:
                print("   ✗ Issue is with set_dir_servo_angle method!")
                return "method_issue"
        else:
            print("   ✗ Even direct control doesn't work - hardware or calibration issue")
            return "hardware_issue"
    else:
        print("   ✓ Steering appears to be working correctly")
        return "working"

def test_steering_consistency():
    """Test if steering movements are consistent"""

    print("\n=== Testing Steering Consistency ===")

    car = Picarx()

    # Test sequence
    movements = [
        ("Initial center", 0),
        ("Left", -20),
        ("Center", 0),
        ("Right", 20),
        ("Center", 0),
        ("Final center", 0)
    ]

    for i, (name, angle) in enumerate(movements):
        print(f"\n{i+1}. {name} ({angle}°)")
        car.set_dir_servo_angle(angle, smooth=False)
        actual_servo = angle + car.dir_cali_val
        print(f"   Servo angle: {actual_servo}°")
        time.sleep(1.5)

        if angle == 0:  # Check center positions
            response = input(f"   Is {name} straight? (y/n): ").strip().lower()
            if response != 'y':
                print(f"   ✗ Problem at step {i+1}: {name}")
                return False

    print("   ✓ All movements appear consistent")
    return True

def create_steering_wrapper():
    """Create a reliable steering wrapper"""

    print("\n=== Creating Reliable Steering Wrapper ===")

    wrapper_code = '''
def reliable_set_steering(car, angle):
    """Reliable steering that always works"""
    # Clamp angle to safe range
    angle = max(-30, min(30, angle))

    # Set both the servo and tracking
    raw_servo_angle = angle + car.dir_cali_val
    car.dir_servo_pin.angle(raw_servo_angle)
    car.dir_current_angle = angle

    print(f"Steering: {angle}° (servo: {raw_servo_angle}°)")

# Replace the problematic method
car.reliable_steering = reliable_set_steering
'''

    with open('/home/dan/Nevil-picar-v3/steering_wrapper.py', 'w') as f:
        f.write(wrapper_code)

    print("Created reliable steering wrapper in steering_wrapper.py")
    print("Usage: exec(open('steering_wrapper.py').read())")
    print("       car.reliable_steering(car, angle)")

if __name__ == "__main__":
    result = fix_steering_center()

    if result == "working":
        print("\n✓ Steering is working correctly!")
        if input("Test consistency? (y/n): ").strip().lower() == 'y':
            test_steering_consistency()
    elif result == "smooth_movement_issue":
        print("\n⚠ Smooth movement logic has issues - use smooth=False")
    elif result == "method_issue":
        print("\n⚠ set_dir_servo_angle method has issues")
        create_steering_wrapper()
    else:
        print(f"\n✗ Issue detected: {result}")