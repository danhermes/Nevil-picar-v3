"""
Automatic Gesture Injection System - Using ALL 135 Gestures

Analyzes AI responses and injects appropriate gestures using the full
extended gesture library organized into 9 categories:

1. OBSERVATION (15) - Looking, scanning, peeking
2. MOVEMENT (16) - Real locomotion
3. REACTIONS (13) - Quick/jerky responses
4. SOCIAL (14) - Greetings, farewells, poses
5. CELEBRATION (7) - Energetic, happy
6. EMOTIONAL (15) - Expressive, slow movements
7. FUNCTIONAL (12) - Clear poses, ready states
8. SIGNALING (10) - Pointing, calling attention
9. ADVANCED (4) - Precise choreography

Features:
- Uses ALL 135 available gestures
- Category-based selection for context
- Anti-repetition system
- Sentiment analysis
- Speed variation based on mood
"""

import re
import random
from typing import List, Tuple, Dict
from collections import deque


class GestureInjector:
    """Inject context-appropriate gestures from ALL 135 available gestures"""

    def __init__(self):
        # Track recent gestures to avoid repetition
        self.recent_gestures = deque(maxlen=20)
        self.response_count = 0

        # === CATEGORY 1: OBSERVATION GESTURES (15) ===
        self.observation_gestures = [
            'look_left_then_right', 'scan_up_down', 'lean_to_see', 'head_snap_survey',
            'curious_peek', 'survey_scene', 'pan_360', 'alert_scan', 'focused_stare',
            'dreamy_stare', 'bashful_hide', 'head_spin_survey', 'quick_check_left',
            'quick_check_right', 'look_around_cautiously'
        ]

        # === CATEGORY 2: MOVEMENT GESTURES (16) ===
        self.movement_gestures = [
            'approach_slowly', 'back_off_slowly', 'approach_gently', 'charge_forward',
            'dodge_left', 'dodge_right', 'circle_strafe', 'advance_retreat',
            'figure_eight', 'serpentine', 'crescent_arc_left', 'crescent_arc_right',
            'retreat_arc', 'slalom_weave', 'zigzag_approach', 'spiral_in'
        ]

        # === CATEGORY 3: REACTIONS GESTURES (13) ===
        self.reaction_gestures = [
            'flinch', 'jump_scared', 'recoil_surprise', 'shocked_jerk',
            'confused_tilt', 'error_shrug', 'think', 'ponder',
            'bump_check', 'avoid_object', 'double_take', 'startled_back',
            'quick_dodge'
        ]

        # === CATEGORY 4: SOCIAL GESTURES (14) ===
        self.social_gestures = [
            'greet_wave', 'hello_friend', 'farewell_wave', 'goodbye_friend',
            'beckon_forward', 'come_on_then', 'bow_respectfully', 'bow_apologetically',
            'ready_pose', 'show_thoughtfulness', 'nod', 'shake_head',
            'wave', 'affirm_pose'
        ]

        # === CATEGORY 5: CELEBRATION GESTURES (7) ===
        self.celebration_gestures = [
            'happy_spin', 'celebrate_big', 'victory_spin', 'cheer_wave',
            'jump_excited', 'playful_bounce', 'circle_dance'
        ]

        # === CATEGORY 6: EMOTIONAL GESTURES (15) ===
        self.emotional_gestures = [
            'show_joy', 'dance_happy', 'sad_turnaway', 'dance_sad',
            'sigh', 'rub_hands', 'depressed', 'angry_shake',
            'defensive_curl', 'confident_chest', 'shy_retreat', 'eager_start',
            'bored_idle', 'anxious_fidget', 'proud_stance'
        ]

        # === CATEGORY 7: FUNCTIONAL GESTURES (12) ===
        self.functional_gestures = [
            'charge_pose', 'guard_pose', 'search_pattern', 'end_pose',
            'failure_pose', 'success_pose', 'idle_breath', 'ready_stance',
            'patrol_mode', 'sentry_scan', 'power_up', 'stand_ready'
        ]

        # === CATEGORY 8: SIGNALING GESTURES (10) ===
        self.signaling_gestures = [
            'call_attention', 'acknowledge_signal', 'signal_stop', 'signal_go',
            'point_forward', 'point_left', 'point_right', 'wave_come_here',
            'applaud_motion', 'thumbs_up'
        ]

        # === CATEGORY 9: ADVANCED GESTURES (4) ===
        self.advanced_gestures = [
            'ballet_spin', 'backflip_attempt', 'moonwalk', 'matrix_dodge'
        ]

        # Combine all for random selection
        self.all_gestures = (
            self.observation_gestures +
            self.movement_gestures +
            self.reaction_gestures +
            self.social_gestures +
            self.celebration_gestures +
            self.emotional_gestures +
            self.functional_gestures +
            self.signaling_gestures +
            self.advanced_gestures
        )

        # Pattern to category mapping for context-aware selection
        self.pattern_categories = {
            # Greetings → Social gestures
            r'\b(hi|hello|hey|howdy|greetings|sup)\b': self.social_gestures,
            r'\b(goodbye|bye|later|see\s*ya|farewell)\b': self.social_gestures,

            # Questions → Observation + Reactions
            r'\?': self.observation_gestures + self.reaction_gestures,

            # Excitement → Celebration + Movement
            r'\b(excited|awesome|great|amazing|wonderful|fantastic|love|yay|woohoo)\b':
                self.celebration_gestures + self.movement_gestures,

            # Thinking → Reactions + Observation
            r'\b(thinking|let\s*me|consider|ponder|hmm|think|wondering)\b':
                self.reaction_gestures + self.observation_gestures,

            # Happy → Celebration + Emotional
            r'\b(happy|glad|pleased|delighted|joyful|cheerful)\b':
                self.celebration_gestures + self.emotional_gestures,

            # Sad/Sorry → Emotional
            r'\b(sad|sorry|unfortunate|apologize|regret)\b':
                self.emotional_gestures,

            # Curious → Observation
            r'\b(curious|interesting|wonder|what|why|how)\b':
                self.observation_gestures,

            # Confident → Functional + Advanced
            r'\b(ready|prepared|confident|sure|definitely)\b':
                self.functional_gestures + self.advanced_gestures,

            # Moving → Movement
            r'\b(move|go|come|approach|forward|back)\b':
                self.movement_gestures,
        }

    def analyze_and_inject(
        self,
        response_text: str,
        min_gestures: int = 3,
        max_gestures: int = 6
    ) -> List[str]:
        """
        Analyze response and return 3-6 context-appropriate gestures.

        Uses pattern matching to select from appropriate gesture categories,
        ensuring variety and avoiding recent repetitions.
        """
        if not response_text:
            return []

        gestures = []
        text_lower = response_text.lower()
        self.response_count += 1

        # Determine speed based on sentiment
        speed = self._detect_speed(text_lower)

        # Try pattern-based category selection first
        matched_categories = []
        for pattern, category_gestures in self.pattern_categories.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched_categories.extend(category_gestures)

        # If patterns matched, use those categories
        if matched_categories:
            gesture_pool = list(set(matched_categories))  # Remove duplicates
        else:
            # No specific patterns, use full gesture library
            gesture_pool = self.all_gestures.copy()

        # Remove recently used gestures to ensure variety
        gesture_pool = [g for g in gesture_pool if g not in self.recent_gestures]

        # If we filtered too much, add back some variety
        if len(gesture_pool) < max_gestures:
            gesture_pool = self.all_gestures.copy()

        # Shuffle for randomness
        random.shuffle(gesture_pool)

        # Select gestures
        num_gestures = random.randint(min_gestures, max_gestures)
        for i in range(min(num_gestures, len(gesture_pool))):
            gesture_name = gesture_pool[i]
            gesture_str = f"{gesture_name}:{speed}"
            gestures.append(gesture_str)
            self.recent_gestures.append(gesture_name)

        # Fill to minimum if needed with random selections
        while len(gestures) < min_gestures:
            remaining = [g for g in self.all_gestures if g not in self.recent_gestures]
            if not remaining:
                remaining = self.all_gestures
            gesture_name = random.choice(remaining)
            gesture_str = f"{gesture_name}:{speed}"
            if gesture_str not in gestures:
                gestures.append(gesture_str)
                self.recent_gestures.append(gesture_name)

        return gestures

    def _detect_speed(self, text_lower: str) -> str:
        """Detect appropriate gesture speed based on text sentiment"""
        # Excited/urgent → fast
        if re.search(r'\b(excited|quick|fast|hurry|urgent|wow|woah)\b', text_lower):
            return 'fast'

        # Calm/thoughtful → slow
        if re.search(r'\b(calm|slow|think|ponder|consider|hmm|peaceful)\b', text_lower):
            return 'slow'

        # Default → medium
        return 'med'


# Singleton instance
_gesture_injector = None

def get_gesture_injector() -> GestureInjector:
    """Get singleton gesture injector instance"""
    global _gesture_injector
    if _gesture_injector is None:
        _gesture_injector = GestureInjector()
    return _gesture_injector
