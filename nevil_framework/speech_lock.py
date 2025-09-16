"""
Shared speech lock for coordinating speech recognition and synthesis
Prevents Nevil from talking to himself by ensuring mutual exclusion
"""

import threading
import time
import logging

class SpeechLock:
    """
    Singleton lock manager for speech pipeline
    Ensures only one component (recognition OR synthesis) is active at a time
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

        self.speech_mutex = threading.Lock()
        self.current_owner = None
        self.logger = logging.getLogger("SpeechLock")
        self._initialized = True

    def acquire_for_recognition(self, timeout=30.0):
        """Acquire lock for speech recognition"""
        acquired = self.speech_mutex.acquire(timeout=timeout)
        if acquired:
            self.current_owner = "recognition"
            self.logger.debug("Lock acquired for speech recognition")
        else:
            self.logger.warning(f"Failed to acquire lock for recognition (timeout: {timeout}s)")
        return acquired

    def acquire_for_synthesis(self, timeout=30.0):
        """Acquire lock for speech synthesis"""
        acquired = self.speech_mutex.acquire(timeout=timeout)
        if acquired:
            self.current_owner = "synthesis"
            self.logger.debug("Lock acquired for speech synthesis")
        else:
            self.logger.warning(f"Failed to acquire lock for synthesis (timeout: {timeout}s)")
        return acquired

    def release(self):
        """Release the speech lock"""
        if self.speech_mutex.locked():
            previous_owner = self.current_owner
            self.current_owner = None
            self.speech_mutex.release()
            self.logger.debug(f"Lock released by {previous_owner}")
        else:
            self.logger.warning("Attempted to release unlocked mutex")

    def is_locked(self):
        """Check if lock is currently held"""
        return self.speech_mutex.locked()

    def get_owner(self):
        """Get current lock owner"""
        return self.current_owner

# Global singleton instance
speech_lock = SpeechLock()