"""
SpeechAnimationManager - Expressive gesture triggering during speech

Adds automatic gestures based on:
- Keywords in speech text
- Punctuation (emphasis, questions)
- Overall mood/sentiment
- Random idle movements

Zero API cost - all gestures triggered locally from speech content.
"""

import re
import random
import logging
import time
from typing import List, Optional, Callable

logger = logging.getLogger(__name__)


class SpeechAnimationManager:
    """
    Add expressive gestures during speech synthesis.

    Triggers gestures based on speech content without requiring AI decisions.
    """

    # Keyword → Gesture mapping (regex patterns → gesture actions)
    KEYWORD_GESTURES = {
        # Positive emotions
        r"\b(happy|excited|great|awesome|wonderful|amazing)\b": [
            "happy_spin:fast", "excited_bounce:fast", "happy_wiggle:med"
        ],
        r"\b(yes|yeah|yep|sure|absolutely|definitely)\b": [
            "nod:med", "affirmative_nod:med", "enthusiastic_nod:fast"
        ],
        r"\b(love|like|enjoy)\b": [
            "heart_gesture:med", "happy_wiggle:med"
        ],

        # Negative emotions
        r"\b(no|nope|nah|never)\b": [
            "shake_head:med", "negative_shake:med"
        ],
        r"\b(sad|sorry|unfortunately|regret)\b": [
            "sad_droop:slow", "sympathy_lean:slow", "dejected_slump:slow"
        ],
        r"\b(worried|concerned|anxious)\b": [
            "concerned_tilt:slow", "nervous_fidget:med"
        ],

        # Directional/movement
        r"\b(forward|ahead|go)\b": [
            "lean_forward:med"
        ],
        r"\b(back|backward|retreat)\b": [
            "lean_back:med"
        ],
        r"\b(left)\b": [
            "turn_head_left:med", "look_left:med"
        ],
        r"\b(right)\b": [
            "turn_head_right:med", "look_right:med"
        ],
        r"\b(look|see|watch|observe)\b": [
            "look_around:med", "scan_area:slow"
        ],

        # Questions/thinking
        r"\b(why|how|what|where|when|who)\b": [
            "curious_tilt:med", "thinking_pose:slow", "head_scratch:slow"
        ],
        r"\b(think|consider|wonder|ponder)\b": [
            "thinking_pose:slow", "contemplative_lean:slow"
        ],

        # Greetings/farewells
        r"\b(hello|hi|hey|greetings|howdy)\b": [
            "wave:med", "friendly_nod:med", "welcoming_gesture:med"
        ],
        r"\b(bye|goodbye|see you|farewell)\b": [
            "wave_goodbye:med", "farewell_bow:slow"
        ],

        # Emphasis/intensity
        r"\b(really|very|super|extremely|totally)\b": [
            "emphasis_lean:fast", "emphatic_nod:fast"
        ],
        r"\b(maybe|perhaps|possibly|might)\b": [
            "uncertain_wobble:slow", "hesitant_tilt:slow"
        ],

        # Fun/playful
        r"\b(fun|play|game|dance)\b": [
            "playful_bounce:fast", "dance_move:fast"
        ],
        r"\b(tired|sleepy|yawn)\b": [
            "yawn:slow", "drowsy_lean:slow"
        ],
    }

    # Punctuation → Gesture mapping
    PUNCTUATION_GESTURES = {
        "!": ["excited_bounce:fast", "emphasis_nod:fast", "emphatic_lean:med"],
        "?": ["curious_tilt:med", "thinking_pose:slow", "questioning_look:med"],
        "...": ["pause_think:slow", "contemplative_lean:slow"],
    }

    # Background idle animations (when no specific gesture is triggered)
    IDLE_ANIMATIONS = [
        "subtle_sway:slow",
        "breathing_motion:slow",
        "slight_head_tilt:slow",
        "micro_adjustment:slow",
        "settle_stance:slow",
    ]

    def __init__(self, publish_callback: Callable):
        """
        Initialize speech animation manager.

        Args:
            publish_callback: Function to publish robot_action messages
        """
        self.publish = publish_callback
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.5  # Minimum seconds between gestures
        self.max_gestures_per_utterance = 2  # Limit gestures to avoid over-animation

    def add_expression_to_speech(self, text: str, voice_mood: str = "neutral") -> List[str]:
        """
        Analyze speech text and return list of gestures to perform.

        Args:
            text: Speech text to analyze
            voice_mood: Overall mood (happy, sad, neutral, excited, etc.)

        Returns:
            List of gesture action strings
        """
        gestures = []

        # 1. Keyword-based gestures
        keyword_gestures = self._detect_keyword_gestures(text)
        gestures.extend(keyword_gestures)

        # 2. Punctuation-based gestures
        if not gestures:  # Only check punctuation if no keyword match
            punctuation_gestures = self._detect_punctuation_gestures(text)
            gestures.extend(punctuation_gestures)

        # 3. Mood-based gesture (if specified and no other gestures)
        if not gestures and voice_mood != "neutral":
            mood_gesture = self._get_mood_gesture(voice_mood)
            if mood_gesture:
                gestures.append(mood_gesture)

        # 4. Add subtle idle animation if no gestures detected
        if not gestures:
            gestures.append(random.choice(self.IDLE_ANIMATIONS))

        # Limit to prevent over-animation
        return gestures[:self.max_gestures_per_utterance]

    def _detect_keyword_gestures(self, text: str) -> List[str]:
        """Detect gestures from keywords in text"""
        gestures = []
        text_lower = text.lower()

        # Check each keyword pattern
        for pattern, gesture_options in self.KEYWORD_GESTURES.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Pick random gesture from options
                gesture = random.choice(gesture_options)
                gestures.append(gesture)
                # Only match first keyword to avoid over-animation
                break

        return gestures

    def _detect_punctuation_gestures(self, text: str) -> List[str]:
        """Detect gestures from punctuation"""
        gestures = []

        # Check for exclamation (excitement/emphasis)
        if "!" in text:
            gestures.append(random.choice(self.PUNCTUATION_GESTURES["!"]))

        # Check for question
        elif "?" in text:
            gestures.append(random.choice(self.PUNCTUATION_GESTURES["?"]))

        # Check for ellipsis (thinking/pausing)
        elif "..." in text:
            gestures.append(random.choice(self.PUNCTUATION_GESTURES["..."]))

        return gestures

    def _get_mood_gesture(self, mood: str) -> Optional[str]:
        """Get gesture based on overall mood"""
        mood_map = {
            "happy": "happy_wiggle:med",
            "excited": "excited_bounce:fast",
            "sad": "sad_droop:slow",
            "angry": "frustrated_shake:med",
            "curious": "curious_tilt:med",
            "thoughtful": "thinking_pose:slow",
            "playful": "playful_bounce:fast",
            "calm": "breathing_motion:slow",
        }
        return mood_map.get(mood.lower())

    def trigger_gesture(self, gesture_action: str, priority: int = 50) -> bool:
        """
        Trigger a gesture via robot_action message.

        Args:
            gesture_action: Gesture string (e.g., "happy_spin:fast")
            priority: Action priority (0-100)

        Returns:
            True if gesture was triggered, False if on cooldown
        """
        # Cooldown check
        if time.time() - self.last_gesture_time < self.gesture_cooldown:
            logger.debug(f"Gesture '{gesture_action}' skipped (cooldown)")
            return False

        # Publish gesture
        robot_action_data = {
            "actions": [gesture_action],
            "source_text": "speech_animation",
            "mood": "neutral",
            "priority": priority,
            "timestamp": time.time()
        }

        success = self.publish("robot_action", robot_action_data)

        if success:
            self.last_gesture_time = time.time()
            logger.debug(f"✓ Triggered gesture: {gesture_action}")
        else:
            logger.warning(f"✗ Failed to trigger gesture: {gesture_action}")

        return success

    def animate_speech_chunk(self, text_chunk: str, is_complete: bool = False):
        """
        Animate a chunk of speech text as it's being spoken.

        Call this from speech synthesis as text is being spoken.

        Args:
            text_chunk: Current chunk of text being spoken
            is_complete: Whether this is the final chunk
        """
        # Only trigger gestures on sentence boundaries or completion
        if is_complete or text_chunk.endswith((".", "!", "?", "...", ":")):
            gestures = self.add_expression_to_speech(text_chunk)

            # Trigger first gesture
            if gestures:
                self.trigger_gesture(gestures[0])

    def set_gesture_frequency(self, cooldown_seconds: float):
        """
        Adjust gesture frequency.

        Args:
            cooldown_seconds: Minimum seconds between gestures
                Lower = more frequent gestures
                Higher = calmer, fewer gestures
        """
        self.gesture_cooldown = cooldown_seconds
        logger.info(f"Gesture cooldown set to {cooldown_seconds}s")

    def set_animation_intensity(self, intensity: str):
        """
        Set animation intensity level.

        Args:
            intensity: "low", "medium", or "high"
        """
        intensity_map = {
            "low": (2.0, 1),      # cooldown=2s, max_gestures=1
            "medium": (1.5, 2),   # cooldown=1.5s, max_gestures=2
            "high": (1.0, 3),     # cooldown=1s, max_gestures=3
        }

        if intensity.lower() in intensity_map:
            cooldown, max_gestures = intensity_map[intensity.lower()]
            self.gesture_cooldown = cooldown
            self.max_gestures_per_utterance = max_gestures
            logger.info(f"Animation intensity set to {intensity} (cooldown={cooldown}s, max={max_gestures})")
        else:
            logger.warning(f"Unknown intensity '{intensity}', use: low, medium, high")
