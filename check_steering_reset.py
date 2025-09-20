#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def check_what_resets_steering():
    """Check what might be resetting the steering to left skew"""

    print("=== Checking Steering Reset Behavior ===")

    car = Picarx()
    print(f"Initial calibration: {car.dir_cali_val}")

    print("\n1. Testing initial servo position after Picarx() init...")
    time.sleep(2)
    print("   Check if wheels are already skewed after initialization")

    print("\n2. Testing explicit center command...")
    car.set_dir_servo_angle(0, smooth=False)
    time.sleep(2)
    print("   Check if wheels are straight now")

    print("\n3. Testing car.reset() function...")
    if hasattr(car, 'reset'):
        print("   Calling car.reset()...")
        car.reset()
        time.sleep(2)
        print("   Check if reset() caused the skew")
    else:
        print("   No reset() method found")

    print("\n4. Testing what happens during initialization...")

    # Check the initialization sequence
    print("   Current servo angles:")
    print(f"   - dir_current_angle: {car.dir_current_angle}")
    print(f"   - dir_cali_val: {car.dir_cali_val}")

    # Manually set to various positions to test
    print("\n5. Testing manual positions...")

    positions = [
        ("Raw 35°", 35),
        ("Raw 40°", 40),
        ("Raw 42°", 42),
        ("Raw 45°", 45)
    ]

    for name, angle in positions:
        print(f"\n   Setting {name}...")
        car.dir_servo_pin.angle(angle)
        time.sleep(2)
        response = input(f"   Is {name} straight? (y/n): ").strip().lower()
        if response == 'y':
            print(f"   *** {name} appears to be the correct center! ***")

def test_initialization_sequence():
    """Test what happens during Picarx initialization"""

    print("=== Testing Initialization Sequence ===")

    print("Creating new Picarx instance and watching initialization...")

    # This will show us what the init does
    car = Picarx()

    print(f"After init:")
    print(f"  - Calibration value: {car.dir_cali_val}")
    print(f"  - Current angle: {car.dir_current_angle}")

    print("\nThe servo was set to calibration value during init.")
    print("If wheels are skewed, the calibration value is wrong.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "init":
        test_initialization_sequence()
    else:
        check_what_resets_steering()