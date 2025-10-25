"""
Microphone mutex for Nevil
Prevents speech recognition from running during noisy activities (TTS, navigation)
while allowing TTS and navigation to run in parallel
"""

import threading
import time
import logging

class MicrophoneMutex:
    """
    Manages microphone access to prevent speech recognition during noisy activities.

    Architecture:
    - Speech Recognition ↔ Speech Synthesis: MUTUAL EXCLUSION (can't run together)
    - Speech Recognition ↔ Navigation: MUTUAL EXCLUSION (can't run together)
    - Speech Synthesis ↔ Navigation: INDEPENDENT (can run in parallel)

    Implementation:
    - Speech synthesis and navigation acquire "noisy_activity" lock
    - Speech recognition checks if any noisy activities are running
    - Multiple noisy activities can run simultaneously (reference counting)
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

        self.mutex_lock = threading.Lock()
        self.noisy_activity_count = 0  # Reference count of noisy activities
        self.active_activities = set()  # Track which activities are running
        self.logger = logging.getLogger("MicrophoneMutex")
        self._initialized = True

    def acquire_noisy_activity(self, activity_name="unknown"):
        """
        Acquire noisy activity lock (for TTS and navigation)
        Multiple noisy activities can run in parallel

        Args:
            activity_name: Name of the activity (e.g., "speaking", "navigation")
        """
        with self.mutex_lock:
            self.noisy_activity_count += 1
            self.active_activities.add(activity_name)
            self.logger.debug(f"Noisy activity started: {activity_name} (count: {self.noisy_activity_count}, active: {self.active_activities})")

    def release_noisy_activity(self, activity_name="unknown"):
        """
        Release noisy activity lock

        Args:
            activity_name: Name of the activity being released
        """
        with self.mutex_lock:
            if self.noisy_activity_count > 0:
                self.noisy_activity_count -= 1
                self.active_activities.discard(activity_name)
                self.logger.debug(f"Noisy activity ended: {activity_name} (count: {self.noisy_activity_count}, active: {self.active_activities})")
            else:
                self.logger.warning(f"Attempted to release noisy activity {activity_name} but count is already 0")

    def is_microphone_available(self):
        """
        Check if microphone is available for speech recognition
        Returns True only if NO noisy activities are running
        """
        with self.mutex_lock:
            available = self.noisy_activity_count == 0
            if not available:
                self.logger.debug(f"Microphone unavailable (active: {self.active_activities})")
            return available

    def get_active_activities(self):
        """Get list of currently active noisy activities"""
        with self.mutex_lock:
            return list(self.active_activities)

    def get_status(self):
        """Get current microphone mutex status"""
        with self.mutex_lock:
            return {
                "microphone_available": self.noisy_activity_count == 0,
                "noisy_activity_count": self.noisy_activity_count,
                "active_activities": list(self.active_activities)
            }

# Global singleton instance
microphone_mutex = MicrophoneMutex()
