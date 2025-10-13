"""
Simple busy state manager for Nevil
Prevents concurrent activities that cause self-talk
"""

import threading
import time
import logging

class BusyStateManager:
    """
    Singleton IsBusy flag that prevents concurrent:
    - Speech Recognition (hearing itself)
    - Speech Synthesis (speaking)
    - Navigation Actions (servo noise)
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.busy_lock = threading.Lock()
        self.is_busy = False
        self.current_activity = None  # Track what Nevil is doing
        self.interrupt_requested = False  # Flag for interrupt requests
        self.interruptible = True  # Whether current activity can be interrupted
        self.logger = logging.getLogger("BusyState")
        self._initialized = True

    def acquire(self, activity_name="unknown", timeout=120.0, can_interrupt=False, interruptible=True):
        """
        Acquire the busy state for a specific activity

        Args:
            activity_name: Name of the activity requesting the lock
            timeout: Maximum time to wait for the lock
            can_interrupt: If True, this activity can interrupt lower-priority activities
            interruptible: If True, this activity can be interrupted by higher-priority activities

        Default timeout: 2 minutes to prevent freezing
        """
        # If this is an interruptible request (like TTS), try to interrupt current activity
        if can_interrupt and self.is_busy and self.interruptible:
            self.logger.warning(f"🚨 {activity_name} interrupting {self.current_activity}")
            self.interrupt_requested = True
            # Give the current activity a brief moment to check interrupt flag and release
            time.sleep(0.1)

        acquired = self.busy_lock.acquire(timeout=timeout)
        if acquired:
            self.is_busy = True
            self.current_activity = activity_name
            self.interruptible = interruptible
            self.interrupt_requested = False
            self.activity_start_time = time.time()
            self.logger.debug(f"Acquired busy state for: {activity_name} (interruptible: {interruptible})")
            return True
        else:
            # Log how long the current activity has been running
            if self.current_activity:
                duration = time.time() - getattr(self, 'activity_start_time', time.time())
                self.logger.warning(f"Could not acquire busy state for {activity_name} (timeout: {timeout}s)")
                self.logger.warning(f"Currently busy with: {self.current_activity} for {duration:.1f}s")

                # Force release if stuck too long (safety measure)
                if duration > 180.0:  # 3 minutes
                    self.logger.error(f"Force releasing stuck activity: {self.current_activity} (ran for {duration:.1f}s)")
                    self.force_release()
                    return self.acquire(activity_name, 5.0)  # Try again with short timeout
            return False

    def should_interrupt(self):
        """Check if current activity should be interrupted"""
        return self.interrupt_requested

    def release(self):
        """Release the busy state"""
        if self.busy_lock.locked():
            previous_activity = self.current_activity
            self.is_busy = False
            self.current_activity = None
            self.busy_lock.release()
            self.logger.debug(f"Released busy state (was: {previous_activity})")
        else:
            self.logger.debug("Busy state already released")

    def is_free(self):
        """Check if system is free (not busy)"""
        return not self.is_busy

    def force_release(self):
        """Force release a stuck mutex (emergency use only)"""
        try:
            if self.busy_lock.locked():
                self.busy_lock.release()
            self.is_busy = False
            stuck_activity = self.current_activity
            self.current_activity = None
            self.logger.error(f"FORCED RELEASE of stuck activity: {stuck_activity}")
        except Exception as e:
            self.logger.error(f"Error during force release: {e}")

    def get_status(self):
        """Get current busy state status"""
        if self.is_busy and hasattr(self, 'activity_start_time'):
            duration = time.time() - self.activity_start_time
            return {
                "is_busy": self.is_busy,
                "activity": self.current_activity,
                "duration": duration,
                "warning": duration > 60.0  # Warn if activity > 1 minute
            }
        return {
            "is_busy": self.is_busy,
            "activity": self.current_activity,
            "duration": 0.0,
            "warning": False
        }

# Global singleton instance
busy_state = BusyStateManager()