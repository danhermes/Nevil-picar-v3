"""
IdleAnimationManager - Background idle animations

Makes Nevil feel alive with subtle movements when not actively speaking or moving.
"""

import time
import random
import threading
import logging
from typing import Callable, List, Dict, Any

logger = logging.getLogger(__name__)


class IdleAnimationManager:
    """
    Background idle animations when Nevil is not speaking or moving.

    Makes Nevil feel alive even when idle.
    """

    # Idle behavior definitions
    # Each behavior has: action, duration, and probability
    IDLE_BEHAVIORS = [
        # Subtle breathing/swaying (most common)
        {"action": "subtle_sway:slow", "duration": 3.0, "probability": 0.3},
        {"action": "breathing_motion:slow", "duration": 2.0, "probability": 0.4},

        # Occasional head movements
        {"action": "look_left:slow", "duration": 2.0, "probability": 0.1},
        {"action": "look_right:slow", "duration": 2.0, "probability": 0.1},
        {"action": "slight_head_tilt:slow", "duration": 1.5, "probability": 0.15},
        {"action": "head_turn_scan:slow", "duration": 3.0, "probability": 0.08},

        # Micro-adjustments (subtle)
        {"action": "micro_adjustment:slow", "duration": 1.0, "probability": 0.2},
        {"action": "settle_stance:slow", "duration": 1.5, "probability": 0.15},
        {"action": "weight_shift:slow", "duration": 1.0, "probability": 0.12},

        # Occasional "personality" behaviors (rare)
        {"action": "curious_look_around:slow", "duration": 3.0, "probability": 0.05},
        {"action": "attentive_pose:slow", "duration": 2.0, "probability": 0.06},
    ]

    def __init__(self, publish_callback: Callable, check_idle_callback: Callable):
        """
        Initialize idle animation manager.

        Args:
            publish_callback: Function to publish robot_action messages
            check_idle_callback: Function that returns True if robot is idle
        """
        self.publish = publish_callback
        self.check_idle = check_idle_callback

        self.running = False
        self.thread = None

        # Configuration
        self.min_idle_time = 3.0  # Minimum seconds idle before animating
        self.check_interval = 1.0  # Check idle state every N seconds
        self.last_animation_time = 0

        # Stats
        self.total_behaviors_triggered = 0

    def start(self):
        """Start idle animation background thread"""
        if self.running:
            logger.warning("Idle animation manager already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._idle_loop,
            daemon=True,
            name="IdleAnimations"
        )
        self.thread.start()
        logger.info("Idle animation manager started")

    def stop(self):
        """Stop idle animations"""
        if not self.running:
            return

        logger.info("Stopping idle animation manager...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        logger.info(f"Idle animation manager stopped (triggered {self.total_behaviors_triggered} behaviors)")

    def _idle_loop(self):
        """Background loop for idle animations"""
        logger.debug("Idle animation loop started")

        while self.running:
            try:
                # Sleep for check interval
                time.sleep(self.check_interval)

                # Check if robot is idle
                if not self.check_idle():
                    continue

                # Check minimum idle time
                time_since_last = time.time() - self.last_animation_time
                if time_since_last < self.min_idle_time:
                    continue

                # Trigger random idle behavior
                self._trigger_random_idle_behavior()

            except Exception as e:
                logger.error(f"Error in idle animation loop: {e}", exc_info=True)
                time.sleep(1.0)  # Prevent tight error loop

        logger.debug("Idle animation loop ended")

    def _trigger_random_idle_behavior(self):
        """Trigger a random idle behavior based on probability"""
        # Roll dice for each behavior
        for behavior in self.IDLE_BEHAVIORS:
            if random.random() < behavior["probability"]:
                # Trigger this behavior
                success = self._execute_idle_behavior(behavior)

                if success:
                    self.total_behaviors_triggered += 1

                    # Sleep for behavior duration (blocking - only one behavior at a time)
                    time.sleep(behavior["duration"])

                    break  # Only one behavior per cycle

    def _execute_idle_behavior(self, behavior: Dict[str, Any]) -> bool:
        """
        Execute an idle behavior.

        Args:
            behavior: Behavior dict with 'action', 'duration', 'probability'

        Returns:
            True if behavior was executed successfully
        """
        robot_action_data = {
            "actions": [behavior["action"]],
            "source_text": "idle_animation",
            "mood": "neutral",
            "priority": 10,  # Low priority (can be interrupted)
            "timestamp": time.time()
        }

        success = self.publish("robot_action", robot_action_data)

        if success:
            self.last_animation_time = time.time()
            logger.debug(f"Idle behavior: {behavior['action']} ({behavior['duration']}s)")
        else:
            logger.debug(f"Idle behavior blocked: {behavior['action']}")

        return success

    def set_idle_frequency(self, min_idle_seconds: float):
        """
        Set how long Nevil must be idle before starting animations.

        Args:
            min_idle_seconds: Minimum idle time before animating
                Lower = more frequent animations
                Higher = calmer, fewer animations
        """
        self.min_idle_time = min_idle_seconds
        logger.info(f"Idle animation frequency set to {min_idle_seconds}s minimum idle")

    def set_behavior_probabilities(self, intensity: str):
        """
        Adjust idle animation intensity.

        Args:
            intensity: "low", "medium", or "high"
        """
        multipliers = {
            "low": 0.5,      # Half as frequent
            "medium": 1.0,   # Default
            "high": 1.5,     # 50% more frequent
        }

        multiplier = multipliers.get(intensity.lower(), 1.0)

        # Adjust probabilities
        for behavior in self.IDLE_BEHAVIORS:
            base_prob = behavior.get("_original_probability")
            if base_prob is None:
                # Store original probability
                behavior["_original_probability"] = behavior["probability"]
                base_prob = behavior["probability"]

            # Apply multiplier (capped at 1.0)
            behavior["probability"] = min(base_prob * multiplier, 1.0)

        logger.info(f"Idle animation intensity set to {intensity} (multiplier={multiplier})")

    def get_stats(self) -> Dict[str, Any]:
        """Get idle animation statistics"""
        return {
            "running": self.running,
            "total_behaviors_triggered": self.total_behaviors_triggered,
            "min_idle_time": self.min_idle_time,
            "last_animation_time": self.last_animation_time,
        }


# Example integration callback
def example_is_idle_callback() -> bool:
    """
    Example idle check callback.

    Returns True if robot is idle (not speaking, not moving).
    """
    # Check various conditions:
    # - Not currently speaking
    # - Not playing audio
    # - No recent robot actions
    # - No user input detected

    # This should be implemented by the node using IdleAnimationManager
    return True
