
# Extended gesture library for PiCar-X expressive choreography.
# Redesigned for REAL VARIETY - static poses, real locomotion, dance movements
# Import time in case caller module doesn't import it.
import time
from enum import Enum

# GESTURE SPEED SYSTEM
# Speed affects pause durations throughout gestures for expressive variation
class GestureSpeed(Enum):
    """Enum for gesture speed control"""
    SLOW = 4.0  # Languid, thoughtful, melancholic, brooding (4x pauses)
    MED = 2.5   # Normal, default (2.5x pauses)
    FAST = 1.5  # Zippy, excited, playful, nervous (1.5x pauses)

# Legacy string mapping for backward compatibility
SPEED_MULTIPLIERS = {
    'slow': GestureSpeed.SLOW.value,
    'med': GestureSpeed.MED.value,
    'fast': GestureSpeed.FAST.value,
    GestureSpeed.SLOW: GestureSpeed.SLOW.value,
    GestureSpeed.MED: GestureSpeed.MED.value,
    GestureSpeed.FAST: GestureSpeed.FAST.value
}

def _sleep(duration, speed='med'):
    """Sleep with speed multiplier applied - accepts string or GestureSpeed enum"""
    if isinstance(speed, GestureSpeed):
        multiplier = speed.value
    elif isinstance(speed, str):
        multiplier = SPEED_MULTIPLIERS.get(speed, 1.0)
    else:
        multiplier = 1.0
    time.sleep(duration * multiplier)

# Helper: optional nudge forward/back small distances via raw motor speeds.
def _pulse(car, speed, dur, gesture_speed='med'):
    car.set_motor_speed(1, speed)
    car.set_motor_speed(2, speed)
    _sleep(dur, gesture_speed)
    car.set_motor_speed(1, 0)
    car.set_motor_speed(2, 0)


# ============================================================================
# OBSERVATION GESTURES (15) - STATIC or HEAD-ONLY
# ============================================================================

def look_left_then_right(car, speed='med'):
    """HEAD ONLY - Smooth pan sweep from left to right, no wheel movement"""
    try:
        # Smooth sweep left
        car.set_cam_pan_angle(-35, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)

        # Pause at left
        _sleep(0.3, speed)

        # Smooth sweep to right
        car.set_cam_pan_angle(35, smooth=True)
        _sleep(0.6, speed)

        # Pause at right
        _sleep(0.3, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def look_up_then_down(car, speed='med'):
    """HEAD ONLY - Tilt up then down, no wheel movement"""
    try:
        # Tilt up to look at ceiling/sky
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(30, smooth=True)
        _sleep(0.5, speed)

        # Pause at top
        _sleep(0.4, speed)

        # Tilt down to look at floor
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(0.6, speed)

        # Pause at bottom
        _sleep(0.4, speed)

        # Return to center
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def look_up(car, speed='med'):
    """STATIC - Just tilt camera up 35°, hold"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(35, smooth=True)
        _sleep(0.5, speed)
        # Don't reset camera - leave it looking up for better view
    except Exception:
        try:
            car.stop()
        except Exception:
            pass


def inspect_floor(car, speed='med'):
    """STATIC - Tilt down and move forward slightly to inspect floor"""
    try:
        # Tilt camera down to look at floor
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(0.4, speed)

        # Slight forward movement to get closer
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(0.13, speed)  # Move ~10cm forward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Hold position and observe
        _sleep(0.6, speed)

        # Return to center
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def look_around_nervously(car, speed='med'):
    """HEAD ONLY - Quick pan snaps left-right-left, nervous energy"""
    try:
        # Quick snap to right
        car.set_cam_pan_angle(35, smooth=False)
        _sleep(0.15, speed)

        # Quick snap to left
        car.set_cam_pan_angle(-35, smooth=False)
        _sleep(0.2, speed)

        # Quick snap back to right
        car.set_cam_pan_angle(30, smooth=False)
        _sleep(0.15, speed)

        # Quick snap to center
        car.set_cam_pan_angle(0, smooth=False)
        _sleep(0.2, speed)

        # Quick snap left again
        car.set_cam_pan_angle(-25, smooth=False)
        _sleep(0.15, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def curious_peek(car, speed='med'):
    """STATIC+HEAD - Lean forward 10cm, tilt head 20°"""
    try:
        # Move forward slightly (lean in)
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(0.13, speed)  # ~10cm forward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Tilt head to peek
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(20, smooth=True)
        _sleep(0.5, speed)

        # Hold peek position
        _sleep(0.4, speed)

        # Return head to center
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def reverse_peek(car, speed='med'):
    """STATIC+HEAD - Back 10cm, tilt head sideways"""
    try:
        # Move backward (retreat)
        car.set_motor_speed(1, -15)
        car.set_motor_speed(2, -15)
        _sleep(0.13, speed)  # ~10cm backward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Tilt head sideways to peek
        car.set_cam_pan_angle(30, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.5, speed)

        # Hold peek position
        _sleep(0.4, speed)

        # Return head to center
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def head_spin_survey(car, speed='med'):
    """HEAD ONLY - Slow 360° pan rotation"""
    try:
        # Start from center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.2, speed)

        # Slow continuous pan to create 360° effect
        # Pan left
        car.set_cam_pan_angle(-50, smooth=True)
        _sleep(0.6, speed)

        # Continue panning through right
        car.set_cam_pan_angle(50, smooth=True)
        _sleep(1.2, speed)  # Slow sweep across

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.6, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def alert_scan(car, speed='med'):
    """HEAD ONLY - Fast pan -40° +40° -40°"""
    try:
        # Fast snap left
        car.set_cam_pan_angle(-40, smooth=False)
        _sleep(0.2, speed)

        # Fast snap right
        car.set_cam_pan_angle(40, smooth=False)
        _sleep(0.2, speed)

        # Fast snap left again
        car.set_cam_pan_angle(-40, smooth=False)
        _sleep(0.2, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def search_pattern(car, speed='med'):
    """HEAD+SLOW TURN - Pan while slow 90° turn"""
    try:
        # Start panning head left
        car.set_cam_pan_angle(-35, smooth=True)
        _sleep(0.3, speed)

        # Turn body slowly right while panning head
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.2, speed)
        car.set_motor_speed(1, 12)
        car.set_motor_speed(2, 12)
        _sleep(0.5, speed)  # Slow turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Pan head right while body settles
        car.set_cam_pan_angle(35, smooth=True)
        _sleep(0.6, speed)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def scout_mode(car, speed='med'):
    """FORWARD+HEAD - Move 20cm forward, scan around"""
    try:
        # Look ahead
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(-10, smooth=True)
        _sleep(0.2, speed)

        # Move forward
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.22, speed)  # ~20cm forward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Scan left
        car.set_cam_pan_angle(-30, smooth=True)
        _sleep(0.4, speed)

        # Scan right
        car.set_cam_pan_angle(30, smooth=True)
        _sleep(0.6, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def investigate_noise(car, speed='med'):
    """HEAD ONLY - Snap turn to one side, hold, listen"""
    try:
        # Quick snap to right (investigating sound)
        car.set_cam_pan_angle(40, smooth=False)
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.2, speed)

        # Hold and "listen"
        _sleep(0.8, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def scan_environment(car, speed='med'):
    """HEAD ONLY - Methodical left-center-right scan"""
    try:
        # Scan to left
        car.set_cam_pan_angle(-35, smooth=True)
        _sleep(0.5, speed)

        # Hold at left
        _sleep(0.3, speed)

        # Scan to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)

        # Hold at center
        _sleep(0.3, speed)

        # Scan to right
        car.set_cam_pan_angle(35, smooth=True)
        _sleep(0.5, speed)

        # Hold at right
        _sleep(0.3, speed)

        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def approach_object(car, speed='med'):
    """FORWARD - Smooth 15cm forward, look down"""
    try:
        # Tilt camera down to watch approach
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.3, speed)

        # Move forward smoothly
        car.set_motor_speed(1, 18)
        car.set_motor_speed(2, 18)
        _sleep(0.18, speed)  # ~15cm forward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Hold and observe
        _sleep(0.4, speed)

        # Return camera to center
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def avoid_object(car, speed='med'):
    """BACKWARD - Quick 15cm back, turn 45°"""
    try:
        # Quick backward movement
        car.set_motor_speed(1, -22)
        car.set_motor_speed(2, -22)
        _sleep(0.14, speed)  # ~15cm backward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Turn 45° to avoid
        car.set_dir_servo_angle(35, smooth=True)
        _sleep(0.2, speed)
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(0.15, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return steering to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


# ============================================================================
# MOVEMENT GESTURES (16) - REAL LOCOMOTION
# ============================================================================

def circle_dance(car, speed='med'):
    """SPIN - 360° turn at speed 20"""
    try:
        # Set steering for turning in place
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.2, speed)

        # Spin 360° - differential steering creates rotation
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(1.5, speed)  # Duration for ~360° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return steering to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def wiggle_and_wait(car, speed='med'):
    """DANCE - Side-to-side weight shift (differential)"""
    try:
        # Shift weight right
        car.set_dir_servo_angle(25, smooth=True)
        _sleep(0.3, speed)

        # Shift weight left
        car.set_dir_servo_angle(-25, smooth=True)
        _sleep(0.3, speed)

        # Shift right again
        car.set_dir_servo_angle(25, smooth=True)
        _sleep(0.3, speed)

        # Shift left again
        car.set_dir_servo_angle(-25, smooth=True)
        _sleep(0.3, speed)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def bump_check(car, speed='med'):
    """FORWARD-STOP - 5cm fwd, pause, 3cm back"""
    try:
        # Move forward 5cm
        car.set_motor_speed(1, 18)
        car.set_motor_speed(2, 18)
        _sleep(0.06, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Pause
        _sleep(0.3, speed)

        # Move back 3cm
        car.set_motor_speed(1, -18)
        car.set_motor_speed(2, -18)
        _sleep(0.04, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def approach_gently(car, speed='med'):
    """SLOW FORWARD - 30cm at speed 12"""
    try:
        # Gentle forward motion
        car.set_motor_speed(1, 12)
        car.set_motor_speed(2, 12)
        _sleep(0.5, speed)  # ~30cm at slow speed
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def happy_spin(car, speed='med'):
    """FAST SPIN - 720° double rotation speed 25"""
    try:
        # Set steering for turning
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.2, speed)

        # Fast double spin 720°
        car.set_motor_speed(1, 25)
        car.set_motor_speed(2, 25)
        _sleep(2.5, speed)  # Duration for ~720° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return steering to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def eager_start(car, speed='med'):
    """BOUNCE - Fwd 5cm, back 3cm, fwd 5cm, back 3cm"""
    try:
        # Forward bounce
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.05, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.1, speed)

        # Back bounce
        car.set_motor_speed(1, -20)
        car.set_motor_speed(2, -20)
        _sleep(0.04, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.1, speed)

        # Forward bounce again
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.05, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.1, speed)

        # Back bounce again
        car.set_motor_speed(1, -20)
        car.set_motor_speed(2, -20)
        _sleep(0.04, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_off(car, speed='med'):
    """SPIN+STOP - Quick 180° spin, pause, 180° back"""
    try:
        # Quick 180° spin right
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 28)
        car.set_motor_speed(2, 28)
        _sleep(0.75, speed)  # ~180° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Pause
        _sleep(0.4, speed)

        # Quick 180° spin back left
        car.set_dir_servo_angle(-40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 28)
        car.set_motor_speed(2, 28)
        _sleep(0.75, speed)  # ~180° turn back
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def zigzag(car, speed='med'):
    """ZIGZAG - Fwd 10cm turn left, fwd 10cm turn right"""
    try:
        # Forward with left turn
        car.set_dir_servo_angle(-30, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.12, speed)  # ~10cm
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Forward with right turn
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.12, speed)  # ~10cm
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def charge_forward(car, speed='med'):
    """BURST - 40cm forward at speed 35"""
    try:
        # Fast forward charge
        car.set_motor_speed(1, 35)
        car.set_motor_speed(2, 35)
        _sleep(0.25, speed)  # ~40cm at high speed
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def retreat_fast(car, speed='med'):
    """BURST BACK - 40cm backward at speed 30"""
    try:
        # Fast backward retreat
        car.set_motor_speed(1, -30)
        car.set_motor_speed(2, -30)
        _sleep(0.28, speed)  # ~40cm backward
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def patrol_mode(car, speed='med'):
    """PATROL - Fwd 20cm, turn 90°, fwd 20cm"""
    try:
        # Forward 20cm
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.22, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.2, speed)

        # Turn 90° right
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.6, speed)  # ~90° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Forward 20cm
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.22, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def moonwalk(car, speed='med'):
    """BACKWARD DANCE - Smooth backward 25cm with sway"""
    try:
        # Sway left while moving backward
        car.set_dir_servo_angle(-20, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, -18)
        car.set_motor_speed(2, -18)
        _sleep(0.15, speed)

        # Sway right while moving backward
        car.set_dir_servo_angle(20, smooth=True)
        _sleep(0.1, speed)
        _sleep(0.15, speed)

        # Sway left while moving backward
        car.set_dir_servo_angle(-20, smooth=True)
        _sleep(0.1, speed)
        _sleep(0.15, speed)

        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def ballet_spin(car, speed='med'):
    """GRACEFUL SPIN - Slow 360° turn speed 15"""
    try:
        # Set steering for gentle turn
        car.set_dir_servo_angle(35, smooth=True)
        _sleep(0.2, speed)

        # Slow graceful 360° spin
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(2.0, speed)  # Slow elegant rotation
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return steering to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def figure_eight(car, speed='med'):
    """FIGURE 8 - Flowing S-curve path"""
    try:
        # First curve - turn left while moving forward
        car.set_dir_servo_angle(-35, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.8, speed)

        # Second curve - turn right while moving forward
        car.set_dir_servo_angle(35, smooth=True)
        _sleep(0.1, speed)
        _sleep(0.8, speed)

        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def crescent_arc_left(car, speed='med'):
    """ARC LEFT - Wide arc turn going forward"""
    try:
        # Arc left while moving forward
        car.set_dir_servo_angle(-30, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.9, speed)  # Wide arc
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def crescent_arc_right(car, speed='med'):
    """ARC RIGHT - Wide arc turn going forward"""
    try:
        # Arc right while moving forward
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.9, speed)  # Wide arc
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)

        # Return to center
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)

        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass

# ============================================================================
# REACTIONS GESTURES (13) - QUICK/JERKY responses
# ============================================================================

def recoil_surprise(car, speed='med'):
    """FAST JERK - Quick 12cm back + head snap up"""
    try:
        # Sudden backward jerk
        car.set_motor_speed(1, -35)
        car.set_motor_speed(2, -35)
        car.set_cam_tilt_angle(30, smooth=False)  # Snap head up simultaneously
        _sleep(0.08, speed)  # Short burst
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold surprised pose
        _sleep(0.5, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def flinch(car, speed='med'):
    """INSTANT JERK - 5cm back + pan away fast"""
    try:
        # Quick flinch backward + head snap left
        car.set_motor_speed(1, -30)
        car.set_motor_speed(2, -30)
        car.set_cam_pan_angle(-40, smooth=False)
        _sleep(0.04, speed)  # Very short
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        _sleep(0.2, speed)
        
        # Return head
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def twitchy_nervous(car, speed='med'):
    """RAPID TWITCHES - Fast servo snaps, no wheels"""
    try:
        # Twitch 1: pan right
        car.set_cam_pan_angle(20, smooth=False)
        _sleep(0.08, speed)
        
        # Twitch 2: pan left
        car.set_cam_pan_angle(-25, smooth=False)
        _sleep(0.08, speed)
        
        # Twitch 3: tilt down
        car.set_cam_tilt_angle(-15, smooth=False)
        _sleep(0.08, speed)
        
        # Twitch 4: pan center
        car.set_cam_pan_angle(0, smooth=False)
        _sleep(0.08, speed)
        
        # Twitch 5: tilt up
        car.set_cam_tilt_angle(10, smooth=False)
        _sleep(0.08, speed)
        
        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def angry_shake(car, speed='med'):
    """VIOLENT SHAKE - Fast pan oscillations"""
    try:
        # Shake left-right-left-right rapidly
        car.set_cam_pan_angle(-30, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(30, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(-30, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(30, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(-30, smooth=False)
        _sleep(0.1, speed)
        
        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def playful_bounce(car, speed='med'):
    """BOUNCE - Rapid fwd-back-fwd-back 4cm pulses"""
    try:
        for _ in range(4):
            # Forward bounce
            car.set_motor_speed(1, 25)
            car.set_motor_speed(2, 25)
            _sleep(0.04, speed)
            car.set_motor_speed(1, 0)
            car.set_motor_speed(2, 0)
            _sleep(0.06, speed)
            
            # Backward bounce
            car.set_motor_speed(1, -25)
            car.set_motor_speed(2, -25)
            _sleep(0.04, speed)
            car.set_motor_speed(1, 0)
            car.set_motor_speed(2, 0)
            _sleep(0.06, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def backflip_attempt(car, speed='med'):
    """BURST BACK - 15cm sudden backward + head up"""
    try:
        # Sudden backward burst with head tilt up
        car.set_motor_speed(1, -40)
        car.set_motor_speed(2, -40)
        car.set_cam_tilt_angle(35, smooth=False)
        _sleep(0.08, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold
        _sleep(0.4, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def defensive_curl(car, speed='med'):
    """RETREAT - 20cm back + head down defensive"""
    try:
        # Retreat backward
        car.set_motor_speed(1, -22)
        car.set_motor_speed(2, -22)
        car.set_cam_tilt_angle(-25, smooth=True)
        _sleep(0.2, speed)  # ~20cm back
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold defensive position
        _sleep(0.6, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def jump_excited(car, speed='med'):
    """RAPID PULSES - 6x quick 3cm forward jumps"""
    try:
        for _ in range(6):
            car.set_motor_speed(1, 30)
            car.set_motor_speed(2, 30)
            _sleep(0.025, speed)  # Very short pulse
            car.set_motor_speed(1, 0)
            car.set_motor_speed(2, 0)
            _sleep(0.05, speed)  # Quick pause between
        
        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def quick_look_left(car, speed='med'):
    """HEAD SNAP - Instant pan left, hold, return"""
    try:
        # Snap left
        car.set_cam_pan_angle(-40, smooth=False)
        _sleep(0.4, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def quick_look_right(car, speed='med'):
    """HEAD SNAP - Instant pan right, hold, return"""
    try:
        # Snap right
        car.set_cam_pan_angle(40, smooth=False)
        _sleep(0.4, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_surprise(car, speed='med'):
    """BURST - Quick 8cm back + head snap up + pan wide"""
    try:
        # Sudden backward + head up + pan
        car.set_motor_speed(1, -32)
        car.set_motor_speed(2, -32)
        car.set_cam_tilt_angle(30, smooth=False)
        car.set_cam_pan_angle(25, smooth=False)
        _sleep(0.06, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold surprised look
        _sleep(0.5, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_fear(car, speed='med'):
    """FEAR - 25cm fast retreat + head down"""
    try:
        # Fast backward retreat + head down
        car.set_motor_speed(1, -28)
        car.set_motor_speed(2, -28)
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(0.2, speed)  # ~25cm back
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold fearful position
        _sleep(0.6, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_disgust(car, speed='med'):
    """RECOIL - Pan away sharp + slight back"""
    try:
        # Sharp pan away + small backward
        car.set_cam_pan_angle(-35, smooth=False)
        car.set_cam_tilt_angle(15, smooth=False)
        car.set_motor_speed(1, -18)
        car.set_motor_speed(2, -18)
        _sleep(0.08, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold disgusted look
        _sleep(0.5, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# SOCIAL GESTURES (14) - STATIC POSES or SLOW SEQUENCES
# ============================================================================

def bow_respectfully(car, speed='med'):
    """SLOW BOW - Gradual tilt down, hold, gradual up"""
    try:
        # Slow bow down
        car.set_cam_tilt_angle(-35, smooth=True)
        _sleep(0.8, speed)  # Slow descent
        
        # Hold bow
        _sleep(0.6, speed)
        
        # Slow return up
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def bow_apologetically(car, speed='med'):
    """DEEP SLOW BOW - Very gradual deep tilt, long hold"""
    try:
        # Very slow deep bow
        car.set_cam_tilt_angle(-40, smooth=True)
        _sleep(1.2, speed)  # Very slow descent
        
        # Long hold
        _sleep(1.0, speed)
        
        # Slow return
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(1.0, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def intro_pose(car, speed='med'):
    """STATIC - Head up 20°, hold proud"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(20, smooth=True)
        _sleep(0.5, speed)
        
        # Hold proud pose
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def end_pose(car, speed='med'):
    """STATIC - Return to center, composed stillness"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        # Hold still
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
        except Exception:
            pass


def greet_wave(car, speed='med'):
    """WAVE - Slow continuous pan left-right-left"""
    try:
        # Continuous wave motion - no pauses
        car.set_cam_pan_angle(-30, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_pan_angle(30, smooth=True)
        _sleep(0.7, speed)
        
        car.set_cam_pan_angle(-30, smooth=True)
        _sleep(0.7, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def farewell_wave(car, speed='med'):
    """WAVE + RETREAT - Pan wave while backing 15cm"""
    try:
        # Start backing slowly while waving
        car.set_motor_speed(1, -12)
        car.set_motor_speed(2, -12)
        
        # Wave left
        car.set_cam_pan_angle(-25, smooth=True)
        _sleep(0.4, speed)
        
        # Wave right
        car.set_cam_pan_angle(25, smooth=True)
        _sleep(0.4, speed)
        
        # Wave left
        car.set_cam_pan_angle(-25, smooth=True)
        _sleep(0.4, speed)
        
        # Stop and center
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def hello_friend(car, speed='med'):
    """APPROACH - Slow 15cm forward + head nod"""
    try:
        # Slow forward approach
        car.set_motor_speed(1, 12)
        car.set_motor_speed(2, 12)
        _sleep(0.28, speed)  # ~15cm
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Friendly nod
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.4, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def goodbye_friend(car, speed='med'):
    """SLOW BACK - 20cm retreat + slow head down"""
    try:
        # Slow backward + head tilt down gradually
        car.set_motor_speed(1, -10)
        car.set_motor_speed(2, -10)
        car.set_cam_tilt_angle(-25, smooth=True)
        _sleep(0.45, speed)  # ~20cm slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold
        _sleep(0.4, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def beckon_forward(car, speed='med'):
    """BECKONING - Continuous nod while backing"""
    try:
        # Start backing
        car.set_motor_speed(1, -12)
        car.set_motor_speed(2, -12)
        
        # Continuous nodding motion
        car.set_cam_tilt_angle(-20, smooth=True)
        _sleep(0.3, speed)
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.3, speed)
        car.set_cam_tilt_angle(-20, smooth=True)
        _sleep(0.3, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        # Stop motors
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def wait_here(car, speed='med'):
    """STATIC - Slight pan aside, hold still"""
    try:
        car.set_cam_pan_angle(15, smooth=True)
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.4, speed)
        
        # Hold idle position
        _sleep(1.0, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def bashful_hide(car, speed='med'):
    """SHY - 18cm slow back + head down gradual"""
    try:
        # Slow retreat + gradual head drop
        car.set_motor_speed(1, -10)
        car.set_motor_speed(2, -10)
        car.set_cam_tilt_angle(-28, smooth=True)
        car.set_cam_pan_angle(-15, smooth=True)
        _sleep(0.4, speed)  # ~18cm slow retreat
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold shy position
        _sleep(0.7, speed)
        
        # Gradual return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def peekaboo(car, speed='med'):
    """PLAYFUL - Continuous down-up-down-up rhythm"""
    try:
        # Continuous rhythmic motion - no pauses
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_tilt_angle(25, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(25, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_love(car, speed='med'):
    """HEART SHAPE - Continuous pan arc right-down-left-up"""
    try:
        # Draw heart shape with continuous movement
        car.set_cam_pan_angle(20, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_tilt_angle(-10, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_pan_angle(-20, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def present_left(car, speed='med'):
    """STATIC - Turn body 45° left, hold pose"""
    try:
        # Turn body to show left side
        car.set_dir_servo_angle(-35, smooth=True)
        car.set_cam_pan_angle(-25, smooth=True)
        _sleep(0.5, speed)
        
        # Small forward to show off
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold pose
        _sleep(0.8, speed)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def present_right(car, speed='med'):
    """STATIC - Turn body 45° right, hold pose"""
    try:
        # Turn body to show right side
        car.set_dir_servo_angle(35, smooth=True)
        car.set_cam_pan_angle(25, smooth=True)
        _sleep(0.5, speed)
        
        # Small forward to show off
        car.set_motor_speed(1, 15)
        car.set_motor_speed(2, 15)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold pose
        _sleep(0.8, speed)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# CELEBRATION GESTURES (7) - ENERGETIC
# ============================================================================

def spin_celebrate(car, speed='med'):
    """CELEBRATION - 360° spin + excited nod"""
    try:
        # Fast 360° spin
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 28)
        car.set_motor_speed(2, 28)
        _sleep(1.3, speed)  # ~360° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Excited nod
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_tilt_angle(-20, smooth=False)
        _sleep(0.15, speed)
        car.set_cam_tilt_angle(10, smooth=False)
        _sleep(0.15, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def spin_reverse(car, speed='med'):
    """CELEBRATION - 360° reverse spin"""
    try:
        # Fast 360° spin opposite direction
        car.set_dir_servo_angle(-40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 28)
        car.set_motor_speed(2, 28)
        _sleep(1.3, speed)  # ~360° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def cheer_wave(car, speed='med'):
    """ENERGETIC - Fast pan waves + bounces"""
    try:
        # Fast wave left
        car.set_cam_pan_angle(-35, smooth=False)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.08, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.1, speed)
        
        # Fast wave right
        car.set_cam_pan_angle(35, smooth=False)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.08, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        _sleep(0.1, speed)
        
        # Fast wave left
        car.set_cam_pan_angle(-35, smooth=False)
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.08, speed)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def celebrate_big(car, speed='med'):
    """BIG CELEBRATION - 720° spin + head up"""
    try:
        # Double spin 720°
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 30)
        car.set_motor_speed(2, 30)
        car.set_cam_tilt_angle(25, smooth=True)
        _sleep(2.5, speed)  # ~720° double spin
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold triumphant pose
        _sleep(0.5, speed)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def applaud_motion(car, speed='med'):
    """APPLAUSE - Left-right hops"""
    try:
        # Hop left (differential turn without moving forward)
        car.set_dir_servo_angle(-30, smooth=True)
        _sleep(0.08, speed)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.08, speed)
        
        # Hop right
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.08, speed)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.08, speed)
        
        # Hop left
        car.set_dir_servo_angle(-30, smooth=True)
        _sleep(0.08, speed)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.08, speed)
        
        # Hop right
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.08, speed)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.08, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def victory_pose(car, speed='med'):
    """VICTORY - Head up high + forward 10cm"""
    try:
        # Triumphant head tilt up
        car.set_cam_tilt_angle(35, smooth=True)
        _sleep(0.4, speed)
        
        # Victory roll forward
        car.set_motor_speed(1, 22)
        car.set_motor_speed(2, 22)
        _sleep(0.1, speed)  # ~10cm
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold victory pose
        _sleep(0.8, speed)
        
        # Return
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_joy(car, speed='med'):
    """JOY - Bouncy nod + 180° turn"""
    try:
        # Bouncy excited nod
        car.set_cam_tilt_angle(-15, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_tilt_angle(10, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_tilt_angle(-15, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        
        # Happy 180° turn
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 25)
        car.set_motor_speed(2, 25)
        _sleep(0.7, speed)  # ~180° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# EMOTIONAL GESTURES (15) - SLOW/EXPRESSIVE continuous movements
# ============================================================================

def sad_turnaway(car, speed='med'):
    """SLOW SAD - Gradual back 20cm + slow head droop"""
    try:
        # Very slow backward retreat + continuous head drop
        car.set_motor_speed(1, -8)
        car.set_motor_speed(2, -8)
        car.set_cam_tilt_angle(-30, smooth=True)
        car.set_cam_pan_angle(-20, smooth=True)
        _sleep(0.55, speed)  # ~20cm very slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold sad pose
        _sleep(0.9, speed)
        
        # Slow return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.7, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def confused_tilt(car, speed='med'):
    """SLOW CONTINUOUS - Gradual tilt left, pause, tilt right"""
    try:
        # Continuous slow tilt left
        car.set_cam_pan_angle(-25, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.8, speed)
        
        # Pause confused
        _sleep(0.4, speed)
        
        # Continuous slow tilt right
        car.set_cam_pan_angle(25, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.8, speed)
        
        # Return slowly
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def look_proud(car, speed='med'):
    """SLOW RISE - Gradual head lift up, hold high"""
    try:
        # Slow continuous rise
        car.set_cam_tilt_angle(35, smooth=True)
        _sleep(0.9, speed)
        
        # Hold proud
        _sleep(1.0, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def sigh(car, speed='med'):
    """SLOW DROOP - Gradual head drop, long hold"""
    try:
        # Very slow droop
        car.set_cam_tilt_angle(-30, smooth=True)
        _sleep(1.2, speed)
        
        # Long hold
        _sleep(1.0, speed)
        
        # Slow rise
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def yawn(car, speed='med'):
    """SLOW STRETCH - Gradual tilt up, pause, slow down"""
    try:
        # Slow stretch up
        car.set_cam_tilt_angle(30, smooth=True)
        _sleep(1.0, speed)
        
        # Hold at top
        _sleep(0.6, speed)
        
        # Slow drop down
        car.set_cam_tilt_angle(-25, smooth=True)
        _sleep(0.9, speed)
        
        # Return
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def stretch(car, speed='med'):
    """SLOW FORWARD - Gradual 15cm extension + head up"""
    try:
        # Slow forward stretch
        car.set_motor_speed(1, 8)
        car.set_motor_speed(2, 8)
        car.set_cam_tilt_angle(25, smooth=True)
        _sleep(0.42, speed)  # ~15cm very slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold stretch
        _sleep(0.7, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def bored_idle(car, speed='med'):
    """VERY SLOW - Tiny continuous pan left-center-right"""
    try:
        # Very slow drift left
        car.set_cam_pan_angle(-15, smooth=True)
        _sleep(1.2, speed)
        
        # Very slow drift right
        car.set_cam_pan_angle(15, smooth=True)
        _sleep(1.5, speed)
        
        # Very slow return
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(1.0, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def think_long(car, speed='med'):
    """SLOW SPIRAL - Continuous pan and tilt together"""
    try:
        # Slow continuous spiral motion
        car.set_cam_pan_angle(-30, smooth=True)
        car.set_cam_tilt_angle(20, smooth=True)
        _sleep(0.9, speed)
        
        car.set_cam_pan_angle(30, smooth=True)
        car.set_cam_tilt_angle(-20, smooth=True)
        _sleep(1.2, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.9, speed)
        
        # Pause thinking
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def ponder(car, speed='med'):
    """SLOW ALTERNATING - Gradual tilt left, right, left"""
    try:
        # Slow continuous alternating tilts
        car.set_cam_pan_angle(-20, smooth=True)
        car.set_cam_tilt_angle(10, smooth=True)
        _sleep(0.9, speed)
        
        car.set_cam_pan_angle(20, smooth=True)
        _sleep(1.0, speed)
        
        car.set_cam_pan_angle(-20, smooth=True)
        _sleep(1.0, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.7, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def dreamy_stare(car, speed='med'):
    """STATIC - Head up, complete stillness"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(25, smooth=True)
        _sleep(0.6, speed)
        
        # Long dreamy stillness
        _sleep(1.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def ponder_and_nod(car, speed='med'):
    """SLOW SEQUENCE - Think then slow double nod"""
    try:
        # Pondering tilt
        car.set_cam_pan_angle(-18, smooth=True)
        car.set_cam_tilt_angle(12, smooth=True)
        _sleep(0.8, speed)
        
        # Pause
        _sleep(0.6, speed)
        
        # Return to center
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        # Slow nod 1
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.6, speed)
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.6, speed)
        
        # Slow nod 2
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.6, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def approach_slowly(car, speed='med'):
    """VERY SLOW - 25cm at speed 8 with pauses"""
    try:
        # Very slow forward
        car.set_motor_speed(1, 8)
        car.set_motor_speed(2, 8)
        _sleep(0.7, speed)  # ~25cm very slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        _sleep(0.3, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def back_off_slowly(car, speed='med'):
    """VERY SLOW BACK - 25cm retreat speed 8 + head up"""
    try:
        # Very slow backward
        car.set_motor_speed(1, -8)
        car.set_motor_speed(2, -8)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.7, speed)  # ~25cm very slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold
        _sleep(0.4, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def dance_sad(car, speed='med'):
    """SLOW SWAY - Continuous slow steering sway, no forward"""
    try:
        # Continuous slow sway left-right-left
        car.set_dir_servo_angle(-25, smooth=True)
        car.set_cam_pan_angle(-15, smooth=True)
        car.set_cam_tilt_angle(-10, smooth=True)
        _sleep(1.0, speed)
        
        car.set_dir_servo_angle(25, smooth=True)
        car.set_cam_pan_angle(15, smooth=True)
        _sleep(1.2, speed)
        
        car.set_dir_servo_angle(-25, smooth=True)
        car.set_cam_pan_angle(-15, smooth=True)
        _sleep(1.2, speed)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_thoughtfulness(car, speed='med'):
    """SLOW CONTINUOUS - Pan and tilt oscillate together"""
    try:
        # Continuous thoughtful motion - both servos move together
        car.set_cam_pan_angle(-25, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(1.0, speed)
        
        car.set_cam_pan_angle(25, smooth=True)
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(1.3, speed)
        
        car.set_cam_pan_angle(-25, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(1.3, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.9, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# FUNCTIONAL GESTURES (12) - CLEAR POSES
# ============================================================================

def sleep_mode(car, speed='med'):
    """STATIC - Head down, complete stillness"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(-35, smooth=True)
        _sleep(0.6, speed)
        
        # Hold sleep position
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def wake_up(car, speed='med'):
    """RISE - Gradual head lift + small shake"""
    try:
        # Rise from sleep
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.7, speed)
        
        # Small shake awake
        car.set_cam_pan_angle(-10, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(10, smooth=False)
        _sleep(0.1, speed)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def guard_pose(car, speed='med'):
    """STATIC - Centered, head slow pan"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        # Slow guard scan
        car.set_cam_pan_angle(-30, smooth=True)
        _sleep(1.0, speed)
        
        car.set_cam_pan_angle(30, smooth=True)
        _sleep(1.2, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def listen(car, speed='med'):
    """STATIC - Slight tilt up, total stillness"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(12, smooth=True)
        _sleep(0.4, speed)
        
        # Complete stillness while listening
        _sleep(1.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def listen_close(car, speed='med'):
    """LEAN IN - 8cm forward + head forward"""
    try:
        # Lean in closer
        car.set_motor_speed(1, 12)
        car.set_motor_speed(2, 12)
        car.set_cam_tilt_angle(8, smooth=True)
        _sleep(0.15, speed)  # ~8cm
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold listening position
        _sleep(1.0, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def ready_pose(car, speed='med'):
    """STATIC - Center all, ready stance"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        # Hold ready
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def charge_pose(car, speed='med'):
    """STATIC - Head down slightly, coiled ready"""
    try:
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.4, speed)
        
        # Hold charge ready pose
        _sleep(0.7, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def failure_pose(car, speed='med'):
    """DROOP - Head down + slow 15cm back"""
    try:
        # Defeated head drop + slow retreat
        car.set_motor_speed(1, -10)
        car.set_motor_speed(2, -10)
        car.set_cam_tilt_angle(-35, smooth=True)
        _sleep(0.35, speed)  # ~15cm slow retreat
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold defeated pose
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def question_pose(car, speed='med'):
    """STATIC - Tilt right, hold still questioningly"""
    try:
        car.set_cam_pan_angle(25, smooth=True)
        car.set_cam_tilt_angle(18, smooth=True)
        _sleep(0.5, speed)
        
        # Hold questioning pose
        _sleep(0.9, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def affirm_pose(car, speed='med'):
    """NOD - Quick single nod"""
    try:
        # Quick nod down
        car.set_cam_tilt_angle(-18, smooth=False)
        _sleep(0.15, speed)
        
        # Quick nod up
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def idle_breath(car, speed='med'):
    """VERY SLOW - Micro tilt up-down continuous"""
    try:
        # Very subtle breathing motion
        car.set_cam_tilt_angle(3, smooth=True)
        _sleep(1.0, speed)
        
        car.set_cam_tilt_angle(-3, smooth=True)
        _sleep(1.2, speed)
        
        car.set_cam_tilt_angle(3, smooth=True)
        _sleep(1.2, speed)
        
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.8, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_shyness(car, speed='med'):
    """SHY - Head down + slow 12cm back"""
    try:
        # Shy retreat
        car.set_motor_speed(1, -10)
        car.set_motor_speed(2, -10)
        car.set_cam_tilt_angle(-25, smooth=True)
        car.set_cam_pan_angle(-12, smooth=True)
        _sleep(0.28, speed)  # ~12cm slow
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold shy
        _sleep(0.8, speed)
        
        # Return head
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# SIGNALING GESTURES (10) - DISTINCT CLEAR signals
# ============================================================================

def wave_head_no(car, speed='med'):
    """NO SIGNAL - Wide pan oscillation left-right-left"""
    try:
        # Wide "no" shake
        car.set_cam_pan_angle(-40, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_pan_angle(40, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_pan_angle(-40, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def wave_head_yes(car, speed='med'):
    """YES SIGNAL - Slow firm nod down-up-down"""
    try:
        # Slow deliberate nod
        car.set_cam_tilt_angle(-25, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(-25, smooth=True)
        _sleep(0.5, speed)
        
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def call_attention(car, speed='med'):
    """ATTENTION - Quick 90° spin + nod"""
    try:
        # Quick 90° turn to get attention
        car.set_dir_servo_angle(40, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 25)
        car.set_motor_speed(2, 25)
        _sleep(0.55, speed)  # ~90° turn
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Attention nod
        car.set_cam_tilt_angle(-20, smooth=False)
        _sleep(0.15, speed)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        # Return steering
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_curiosity(car, speed='med'):
    """CURIOUS - Slow pan/tilt exploration"""
    try:
        # Curious exploration motion
        car.set_cam_pan_angle(-25, smooth=True)
        car.set_cam_tilt_angle(15, smooth=True)
        _sleep(0.7, speed)
        
        car.set_cam_pan_angle(25, smooth=True)
        car.set_cam_tilt_angle(-10, smooth=True)
        _sleep(0.9, speed)
        
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.6, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def acknowledge_signal(car, speed='med'):
    """ACK - Single firm nod"""
    try:
        # Clear acknowledgment nod
        car.set_cam_tilt_angle(-22, smooth=True)
        _sleep(0.3, speed)
        
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def reject_signal(car, speed='med'):
    """REJECT - Head shake + 8cm back"""
    try:
        # Rejection shake
        car.set_cam_pan_angle(-30, smooth=False)
        car.set_motor_speed(1, -15)
        car.set_motor_speed(2, -15)
        _sleep(0.12, speed)
        
        car.set_cam_pan_angle(30, smooth=False)
        _sleep(0.12, speed)
        
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def error_shrug(car, speed='med'):
    """ERROR - Tilt down + pan aside"""
    try:
        car.set_cam_pan_angle(-20, smooth=True)
        car.set_cam_tilt_angle(-15, smooth=True)
        _sleep(0.5, speed)
        
        # Hold error pose
        _sleep(0.6, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def signal_complete(car, speed='med'):
    """COMPLETE - Nod + return to rest"""
    try:
        # Completion nod
        car.set_cam_tilt_angle(-20, smooth=True)
        _sleep(0.4, speed)
        
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.4, speed)
        
        # Return to rest
        car.set_cam_pan_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def signal_error(car, speed='med'):
    """ERROR - Shake head + short back"""
    try:
        # Error shake
        car.set_cam_pan_angle(-25, smooth=False)
        _sleep(0.12, speed)
        car.set_cam_pan_angle(25, smooth=False)
        _sleep(0.12, speed)
        car.set_cam_pan_angle(0, smooth=True)
        
        # Short backward step
        car.set_motor_speed(1, -15)
        car.set_motor_speed(2, -15)
        _sleep(0.08, speed)  # ~5cm back
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        _sleep(0.2, speed)
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def show_confidence(car, speed='med'):
    """CONFIDENT - Steady 20cm forward, level head"""
    try:
        # Confident forward march
        car.set_cam_pan_angle(0, smooth=True)
        car.set_cam_tilt_angle(5, smooth=True)
        _sleep(0.2, speed)
        
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        _sleep(0.22, speed)  # ~20cm steady
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Hold confident pose
        _sleep(0.5, speed)
        
        # Return head
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass



# ============================================================================
# ADVANCED GESTURES (4) - PRECISE MOVEMENT
# ============================================================================

def dance_happy(car, speed='med'):
    """DANCE - Rhythmic continuous turn-forward-turn"""
    try:
        # Dance sequence with continuous motion
        # Turn left
        car.set_dir_servo_angle(-30, smooth=True)
        _sleep(0.1, speed)
        car.set_motor_speed(1, 18)
        car.set_motor_speed(2, 18)
        _sleep(0.3, speed)
        
        # Straight
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        # Turn right
        car.set_dir_servo_angle(30, smooth=True)
        _sleep(0.1, speed)
        _sleep(0.3, speed)
        
        # Straight
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.2, speed)
        
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        
        # Return
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def flirt(car, speed='med'):
    """PLAYFUL - Light continuous pan sweeps + tiny sway"""
    try:
        # Playful flirtatious motion - continuous
        car.set_cam_pan_angle(-22, smooth=True)
        car.set_dir_servo_angle(-15, smooth=True)
        _sleep(0.6, speed)
        
        car.set_cam_pan_angle(22, smooth=True)
        car.set_dir_servo_angle(15, smooth=True)
        _sleep(0.7, speed)
        
        car.set_cam_pan_angle(-22, smooth=True)
        car.set_dir_servo_angle(-15, smooth=True)
        _sleep(0.7, speed)
        
        # Return
        car.set_cam_pan_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=True)
        _sleep(0.5, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass


def come_on_then(car, speed='med'):
    """BECKONING - Continuous nods while backing 15cm"""
    try:
        # Start backing
        car.set_motor_speed(1, -12)
        car.set_motor_speed(2, -12)
        
        # Continuous beckoning nods
        car.set_cam_tilt_angle(-18, smooth=True)
        _sleep(0.25, speed)
        car.set_cam_tilt_angle(8, smooth=True)
        _sleep(0.25, speed)
        car.set_cam_tilt_angle(-18, smooth=True)
        _sleep(0.25, speed)
        car.set_cam_tilt_angle(8, smooth=True)
        _sleep(0.25, speed)
        
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_tilt_angle(0, smooth=True)
        _sleep(0.3, speed)
        
        car.stop()
    except Exception:
        try:
            car.stop()
            car.set_cam_pan_angle(0, smooth=True)
            car.set_cam_tilt_angle(0, smooth=True)
            car.set_dir_servo_angle(0, smooth=True)
        except Exception:
            pass

