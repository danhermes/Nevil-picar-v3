"""
SpeechIdleAnimator - Continuous subtle movements while Nevil is talking

Adds lifelike motion to make Nevil appear more animated and expressive during speech.
Movements include:
- Head micro-movements (subtle pan/tilt variations)
- Front wheel gentle rocking
- Back wheel micro-adjustments for weight shifting

All movements are subtle and non-disruptive to conversation.
"""

import threading
import time
import random
import logging
import math
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class SpeechIdleAnimator:
    """
    Provides continuous subtle animations while Nevil is speaking.

    Creates natural, lifelike motion through:
    - Gentle head movements (pan/tilt)
    - Subtle wheel rocking
    - Breathing-like rhythmic motion
    """

    def __init__(self, get_car_callback: Callable):
        """
        Initialize speech idle animator.

        Args:
            get_car_callback: Function that returns the car/picarx object when called
        """
        self.get_car = get_car_callback
        self.is_animating = False
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Animation parameters - all movements are SUBTLE
        self.head_pan_range = 8  # ±8 degrees max
        self.head_tilt_range = 5  # ±5 degrees max
        self.wheel_angle_range = 4  # ±4 degrees for gentle rocking

        # Timing parameters
        self.movement_interval = 0.27  # Update every 270ms (expressive but smooth pace)
        self.phase = 0  # Animation phase for smooth transitions

        # Base positions (will be set when animation starts)
        self.base_pan = 0
        self.base_tilt = 0
        self.base_wheel_angle = 0

    def start_animation(self):
        """Start continuous idle animation during speech"""
        # Stop any existing animation first
        if self.is_animating:
            logger.debug("Animation already running - stopping it first")
            self.stop_animation()
            time.sleep(0.1)  # Brief pause to ensure clean stop

        self.is_animating = True
        self.stop_event.clear()
        self.phase = 0
        self.animation_start_time = time.time()  # Track start time for safety timeout

        # Get current car state as base position
        car = self.get_car()
        if car:
            self.base_pan = getattr(car, 'current_pan_angle', 0)
            self.base_tilt = getattr(car, 'current_tilt_angle', 0)
            self.base_wheel_angle = getattr(car, 'current_dir_angle', 0)

        # Start animation thread
        self.animation_thread = threading.Thread(
            target=self._animation_loop,
            name="SpeechIdleAnimator",
            daemon=True
        )
        self.animation_thread.start()
        logger.info("🎬 Started speech idle animation")

    def stop_animation(self):
        """Stop idle animation and return to neutral position"""
        if not self.is_animating:
            logger.debug("Animation already stopped")
            return

        logger.info("🛑 Stopping speech idle animation...")

        # Set both stop flags
        self.is_animating = False
        self.stop_event.set()

        # Wait for thread to finish with timeout
        if self.animation_thread and self.animation_thread.is_alive():
            logger.debug("Waiting for animation thread to stop...")
            self.animation_thread.join(timeout=2.0)

            # Check if thread actually stopped
            if self.animation_thread.is_alive():
                logger.warning("⚠️ Animation thread did not stop within timeout - it's a daemon so will be killed on exit")
            else:
                logger.debug("✓ Animation thread stopped successfully")

        # Return to base positions smoothly
        self._reset_to_neutral()
        logger.info("🎬 Stopped speech idle animation")

    def _animation_loop(self):
        """
        Main animation loop - runs in separate thread.
        Creates gentle, breathing-like motion patterns.
        """
        logger.debug("Animation loop started")
        max_animation_duration = 120.0  # Safety timeout: 2 minutes max

        while not self.stop_event.is_set() and self.is_animating:
            try:
                # Safety timeout check - prevent endless animation
                if hasattr(self, 'animation_start_time'):
                    elapsed = time.time() - self.animation_start_time
                    if elapsed > max_animation_duration:
                        logger.warning(f"Animation safety timeout reached ({elapsed:.1f}s) - forcing stop")
                        break

                # Check stop signal before doing any work
                if self.stop_event.is_set() or not self.is_animating:
                    break

                car = self.get_car()
                if not car:
                    logger.warning("No car available for animation")
                    # Use stop_event.wait() instead of sleep for immediate stop response
                    if self.stop_event.wait(timeout=0.5):
                        break
                    continue

                # Generate smooth motion using sine waves with different phases
                # This creates natural, flowing movement
                self.phase += 0.15  # Moderate phase increment for expressive but relaxed movement

                # Head pan: slow side-to-side sway (like looking around gently)
                pan_offset = math.sin(self.phase * 0.65) * self.head_pan_range * 0.8
                target_pan = self.base_pan + pan_offset

                # Head tilt: gentle up-down motion (like breathing/thinking)
                tilt_offset = math.sin(self.phase * 0.85) * self.head_tilt_range * 0.75
                target_tilt = self.base_tilt + tilt_offset

                # Front wheels: subtle rocking (like shifting weight)
                wheel_offset = math.sin(self.phase * 0.5) * self.wheel_angle_range * 0.85
                target_wheel = self.base_wheel_angle + wheel_offset

                # Check stop signal before servo movements
                if self.stop_event.is_set() or not self.is_animating:
                    break

                # Apply movements smoothly (these might block briefly)
                try:
                    if hasattr(car, 'set_cam_pan_angle'):
                        car.set_cam_pan_angle(target_pan, smooth=True)
                        if int(self.phase) % 20 == 0:  # Log every 20 cycles
                            logger.info(f"🎬 Animation active: pan={target_pan:.1f}°")
                    else:
                        logger.warning("Car has no set_cam_pan_angle method!")

                    if hasattr(car, 'set_cam_tilt_angle'):
                        car.set_cam_tilt_angle(target_tilt, smooth=True)
                    else:
                        logger.warning("Car has no set_cam_tilt_angle method!")

                    if hasattr(car, 'set_dir_servo_angle'):
                        car.set_dir_servo_angle(target_wheel, smooth=True)
                    else:
                        logger.warning("Car has no set_dir_servo_angle method!")

                except Exception as servo_error:
                    logger.debug(f"Servo command error (normal during stop): {servo_error}")
                    # If servo commands fail, animation is likely stopping - exit gracefully
                    break

                # Check stop signal after servo movements
                if self.stop_event.is_set() or not self.is_animating:
                    break

                # Add occasional micro-adjustments to back wheels for realism
                # More frequent weight shifting for expressive vibe
                if random.random() < 0.07:  # 7% chance each iteration (~every 4 seconds)
                    # Check stop before weight shift
                    if not self.stop_event.is_set() and self.is_animating:
                        self._subtle_weight_shift(car)

                # Log animation state periodically
                if int(self.phase) % 10 == 0:
                    logger.debug(f"Animation phase: {self.phase:.1f}, pan: {target_pan:.1f}, tilt: {target_tilt:.1f}, wheel: {target_wheel:.1f}")

                # Use stop_event.wait() with timeout instead of sleep for immediate response
                if self.stop_event.wait(timeout=self.movement_interval):
                    break

            except Exception as e:
                logger.error(f"Error in animation loop: {e}", exc_info=True)
                # Use stop_event.wait() for error recovery too
                if self.stop_event.wait(timeout=1.0):
                    break

        logger.debug("Animation loop ended - cleaning up")
        # Final cleanup - ensure we're truly stopped
        self.is_animating = False

    def _subtle_weight_shift(self, car):
        """
        Create a tiny weight shift by briefly pulsing the motors.
        This makes Nevil appear more alive/present.
        """
        try:
            # Gentle motor pulse for expressive but smooth vibe
            pulse_strength = random.choice([8, -8, 10, -10, 12, -12])  # Low-medium power
            duration = 0.06  # 60ms pulse

            if hasattr(car, 'set_motor_speed'):
                # Pulse both motors in same direction for weight shift
                car.set_motor_speed(1, pulse_strength)
                car.set_motor_speed(2, pulse_strength)
                time.sleep(duration)
                car.set_motor_speed(1, 0)
                car.set_motor_speed(2, 0)

                logger.debug(f"Applied weight shift: {pulse_strength} for {duration}s")

        except Exception as e:
            logger.error(f"Error in weight shift: {e}")

    def _reset_to_neutral(self):
        """Smoothly return all servos to neutral/base position"""
        try:
            car = self.get_car()
            if not car:
                return

            # Return to base positions smoothly
            if hasattr(car, 'set_cam_pan_angle'):
                car.set_cam_pan_angle(self.base_pan, smooth=True)

            if hasattr(car, 'set_cam_tilt_angle'):
                car.set_cam_tilt_angle(self.base_tilt, smooth=True)

            if hasattr(car, 'set_dir_servo_angle'):
                car.set_dir_servo_angle(self.base_wheel_angle, smooth=True)

            logger.debug("Reset to neutral position")

        except Exception as e:
            logger.error(f"Error resetting to neutral: {e}")

    def set_animation_intensity(self, intensity: str):
        """
        Adjust animation intensity.

        Args:
            intensity: "subtle", "medium", or "expressive"
        """
        intensity_map = {
            "subtle": (5, 3, 2),       # (pan_range, tilt_range, wheel_range)
            "medium": (8, 5, 4),       # Balanced
            "expressive": (15, 9, 8),  # More animated and expressive
        }

        if intensity.lower() in intensity_map:
            pan, tilt, wheel = intensity_map[intensity.lower()]
            self.head_pan_range = pan
            self.head_tilt_range = tilt
            self.wheel_angle_range = wheel
            logger.info(f"Animation intensity set to {intensity} (pan={pan}°, tilt={tilt}°, wheel={wheel}°)")
        else:
            logger.warning(f"Unknown intensity '{intensity}', use: subtle, medium, expressive")

    def cleanup(self):
        """Stop animation and cleanup resources"""
        self.stop_animation()
