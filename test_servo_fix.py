#!/usr/bin/env python3

import sys
import time
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from picarx import Picarx

def test_servo_movements():
    """Test servo movements with the new smooth transitions"""

    print("Initializing Picarx with improved servo control...")
    car = Picarx()
    time.sleep(1)  # Let initialization complete

    print("\n=== Testing Direction Servo ===")
    print("Testing smooth large angle changes...")

    # Test direction servo with smooth movements
    print("Moving to -30 degrees (smooth)...")
    car.set_dir_servo_angle(-30, smooth=True)
    time.sleep(0.5)

    print("Moving to +30 degrees (smooth)...")
    car.set_dir_servo_angle(30, smooth=True)
    time.sleep(0.5)

    print("Centering (smooth)...")
    car.set_dir_servo_angle(0, smooth=True)
    time.sleep(0.5)

    print("\n=== Testing Camera Servos ===")

    # Test camera pan
    print("Testing camera pan...")
    car.set_cam_pan_angle(-45, smooth=True)
    time.sleep(0.5)
    car.set_cam_pan_angle(45, smooth=True)
    time.sleep(0.5)
    car.set_cam_pan_angle(0, smooth=True)
    time.sleep(0.5)

    # Test camera tilt
    print("Testing camera tilt...")
    car.set_cam_tilt_angle(-20, smooth=True)
    time.sleep(0.5)
    car.set_cam_tilt_angle(20, smooth=True)
    time.sleep(0.5)
    car.set_cam_tilt_angle(0, smooth=True)
    time.sleep(0.5)

    print("\n=== Testing Small Angle Changes (no smoothing) ===")

    # Test small movements (should be direct)
    print("Small adjustments...")
    for angle in [-5, 5, -3, 3, 0]:
        car.set_dir_servo_angle(angle, smooth=True)
        time.sleep(0.3)

    print("\n=== Testing Motor Control ===")

    # Test smooth stop
    print("Starting motors...")
    car.forward(50)
    time.sleep(1)

    print("Smooth stop...")
    car.stop()
    time.sleep(0.5)

    print("\nTest complete! Servo movements should be smoother with less clicking.")

    # Reset to center
    print("Resetting all servos to center...")
    car.set_dir_servo_angle(0, smooth=True)
    car.set_cam_pan_angle(0, smooth=True)
    car.set_cam_tilt_angle(0, smooth=True)

if __name__ == "__main__":
    try:
        test_servo_movements()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()