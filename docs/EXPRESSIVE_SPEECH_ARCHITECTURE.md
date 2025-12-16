# Expressive Speech Architecture - Cost-Effective Animation System

## Problem
- Sending 109 gesture functions to AI costs ~$0.09/conversation
- AI rarely calls gesture functions (maybe 1-2 per conversation)
- Nevil appears static during speech (not expressive)
- Wasting tokens on functions that don't get used

## Solution: Separate Gesture Control from AI

### Old Architecture (Expensive)
```
User speaks → AI decides gesture → Calls function → Robot moves
                ↑
        109 functions sent to AI ($$$)
        AI rarely calls them
```

### New Architecture (Expressive + Cheap)
```
AI generates speech → Speech synthesis adds gestures automatically
                              ↓
                    Keyword/mood detection
                              ↓
                    Auto-trigger gestures (no AI decision needed)

+ Background idle animations (always moving slightly)
+ Critical functions only in AI (movement, camera, memory)
```

---

## Part 1: Minimal AI Function Set

### Keep ONLY Critical Functions (4 functions instead of 109)

```python
# In ai_cognition_realtime_node.py

# MINIMAL function set - only what AI MUST control
CRITICAL_FUNCTIONS = [
    "take_snapshot",    # Camera (AI needs to see)
    "remember",         # Memory storage
    "recall",           # Memory retrieval
    "navigation_mode"   # Enable/disable autonomous movement
]

# REMOVE all gesture functions from AI
# Speech synthesis will handle expressiveness automatically
```

**Savings**: $0.08-0.09 per conversation (90% reduction in function tokens)

---

## Part 2: Expressive Speech Synthesis

### Create SpeechAnimationManager

```python
# nevil_framework/speech_animation_manager.py

import re
import random
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SpeechAnimationManager:
    """
    Add expressive gestures during speech synthesis.

    Triggers gestures based on:
    - Speech content (keywords)
    - Punctuation (pauses, emphasis)
    - Sentence mood (question, excitement, sadness)
    - Random idle movements during pauses
    """

    # Keyword → Gesture mapping
    KEYWORD_GESTURES = {
        # Positive emotions
        "happy|excited|great|awesome|wonderful": ["happy_spin:fast", "excited_bounce:fast"],
        "yes|yeah|yep|sure|absolutely": ["nod:med", "affirmative_nod:med"],
        "love|like": ["heart_gesture:med", "happy_wiggle:med"],

        # Negative emotions
        "no|nope|nah|never": ["shake_head:med", "negative_shake:med"],
        "sad|sorry|unfortunately": ["sad_droop:slow", "sympathy_lean:slow"],
        "worried|concerned": ["concerned_tilt:slow"],

        # Actions
        "forward|ahead|go": ["lean_forward:med"],
        "back|backward|retreat": ["lean_back:med"],
        "left": ["turn_head_left:med"],
        "right": ["turn_head_right:med"],
        "look|see|watch": ["look_around:med"],

        # Questions
        "why|how|what|where|when|who": ["curious_tilt:med", "thinking_pose:slow"],

        # Greetings
        "hello|hi|hey|greetings": ["wave:med", "friendly_nod:med"],
        "bye|goodbye|see you": ["wave_goodbye:med"],

        # Emphasis
        "really|very|super|extremely": ["emphasis_lean:fast"],
        "maybe|perhaps|possibly": ["uncertain_wobble:slow"],
    }

    # Punctuation → Gesture mapping
    PUNCTUATION_GESTURES = {
        "!": ["excited_bounce:fast", "emphasis_nod:fast"],
        "?": ["curious_tilt:med", "thinking_pose:slow"],
        "...": ["pause_think:slow"],
    }

    # Background idle animations (play randomly during speech)
    IDLE_ANIMATIONS = [
        "subtle_sway:slow",
        "breathing_motion:slow",
        "slight_head_tilt:slow",
        "micro_adjustment:slow",
    ]

    def __init__(self, publish_callback):
        """
        Initialize speech animation manager.

        Args:
            publish_callback: Function to publish robot_action messages
        """
        self.publish = publish_callback
        self.last_gesture_time = 0
        self.gesture_cooldown = 1.5  # Minimum seconds between gestures

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
        punctuation_gestures = self._detect_punctuation_gestures(text)
        gestures.extend(punctuation_gestures)

        # 3. Mood-based gesture
        if voice_mood != "neutral":
            mood_gesture = self._get_mood_gesture(voice_mood)
            if mood_gesture:
                gestures.append(mood_gesture)

        # 4. Add idle animation if no gestures detected
        if not gestures:
            gestures.append(random.choice(self.IDLE_ANIMATIONS))

        # Limit to 2-3 gestures per utterance (avoid over-animation)
        return gestures[:3]

    def _detect_keyword_gestures(self, text: str) -> List[str]:
        """Detect gestures from keywords in text"""
        gestures = []
        text_lower = text.lower()

        for pattern, gesture_options in self.KEYWORD_GESTURES.items():
            if re.search(pattern, text_lower):
                # Pick random gesture from options
                gesture = random.choice(gesture_options)
                gestures.append(gesture)
                # Only match first keyword to avoid over-animation
                break

        return gestures

    def _detect_punctuation_gestures(self, text: str) -> List[str]:
        """Detect gestures from punctuation"""
        gestures = []

        # Check for exclamation
        if "!" in text:
            gestures.append(random.choice(self.PUNCTUATION_GESTURES["!"]))

        # Check for question
        elif "?" in text:
            gestures.append(random.choice(self.PUNCTUATION_GESTURES["?"]))

        # Check for ellipsis (thinking)
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
        }
        return mood_map.get(mood.lower())

    def trigger_gesture(self, gesture_action: str, priority: int = 50):
        """
        Trigger a gesture via robot_action message.

        Args:
            gesture_action: Gesture string (e.g., "happy_spin:fast")
            priority: Action priority (0-100)
        """
        import time

        # Cooldown check
        if time.time() - self.last_gesture_time < self.gesture_cooldown:
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
            logger.debug(f"Triggered gesture: {gesture_action}")

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
        if is_complete or text_chunk.endswith((".", "!", "?")):
            gestures = self.add_expression_to_speech(text_chunk)

            # Trigger first gesture
            if gestures:
                self.trigger_gesture(gestures[0])


# Example usage in speech_synthesis_realtime_node.py
```

---

## Part 3: Integration with Speech Synthesis

### Modify speech_synthesis_realtime_node.py

```python
# In speech_synthesis_realtime_node.py

from nevil_framework.speech_animation_manager import SpeechAnimationManager

class SpeechSynthesisRealtimeNode(NevilNode):
    def __init__(self):
        super().__init__("speech_synthesis_realtime")

        # Create animation manager
        self.animation_manager = SpeechAnimationManager(self.publish)

        # Track current utterance
        self.current_utterance = ""
        self.utterance_start_time = None

    def _on_audio_transcript_delta(self, event):
        """Handle streaming transcript and trigger gestures"""
        try:
            delta = event.get('delta', '')
            if delta:
                self.current_utterance += delta

                # Check for sentence boundaries
                if delta.endswith((".", "!", "?")):
                    # Trigger gesture based on completed sentence
                    self.animation_manager.animate_speech_chunk(
                        self.current_utterance,
                        is_complete=False
                    )
                    self.current_utterance = ""  # Reset for next sentence

        except Exception as e:
            self.logger.error(f"Error in transcript delta animation: {e}")

    def _on_audio_transcript_done(self, event):
        """Handle completed transcript and trigger final gesture"""
        try:
            # Trigger gesture for final utterance if any
            if self.current_utterance:
                self.animation_manager.animate_speech_chunk(
                    self.current_utterance,
                    is_complete=True
                )
                self.current_utterance = ""

        except Exception as e:
            self.logger.error(f"Error in transcript done animation: {e}")
```

---

## Part 4: Background Idle Animations

### Create IdleAnimationManager

```python
# nevil_framework/idle_animation_manager.py

import time
import random
import threading
import logging

logger = logging.getLogger(__name__)


class IdleAnimationManager:
    """
    Background idle animations when Nevil is not speaking or moving.

    Makes Nevil feel alive even when idle.
    """

    IDLE_BEHAVIORS = [
        # Subtle breathing/swaying
        {"action": "subtle_sway:slow", "duration": 3.0, "probability": 0.3},
        {"action": "breathing_motion:slow", "duration": 2.0, "probability": 0.4},

        # Occasional head movements
        {"action": "look_left:slow", "duration": 2.0, "probability": 0.1},
        {"action": "look_right:slow", "duration": 2.0, "probability": 0.1},
        {"action": "slight_head_tilt:slow", "duration": 1.5, "probability": 0.15},

        # Micro-adjustments
        {"action": "micro_adjustment:slow", "duration": 1.0, "probability": 0.2},
        {"action": "settle_stance:slow", "duration": 1.5, "probability": 0.15},
    ]

    def __init__(self, publish_callback, check_idle_callback):
        """
        Initialize idle animation manager.

        Args:
            publish_callback: Function to publish robot_action
            check_idle_callback: Function that returns True if robot is idle
        """
        self.publish = publish_callback
        self.check_idle = check_idle_callback

        self.running = False
        self.thread = None
        self.min_idle_time = 3.0  # Minimum seconds idle before animating
        self.last_animation_time = 0

    def start(self):
        """Start idle animation thread"""
        if self.running:
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
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Idle animation manager stopped")

    def _idle_loop(self):
        """Background loop for idle animations"""
        while self.running:
            time.sleep(1.0)  # Check every second

            # Check if robot is idle
            if not self.check_idle():
                continue

            # Check minimum idle time
            time_since_last = time.time() - self.last_animation_time
            if time_since_last < self.min_idle_time:
                continue

            # Randomly pick an idle behavior
            self._trigger_random_idle_behavior()

    def _trigger_random_idle_behavior(self):
        """Trigger a random idle behavior based on probability"""
        # Roll dice for each behavior
        for behavior in self.IDLE_BEHAVIORS:
            if random.random() < behavior["probability"]:
                # Trigger this behavior
                robot_action_data = {
                    "actions": [behavior["action"]],
                    "source_text": "idle_animation",
                    "mood": "neutral",
                    "priority": 10,  # Low priority (can be interrupted)
                    "timestamp": time.time()
                }

                if self.publish("robot_action", robot_action_data):
                    self.last_animation_time = time.time()
                    logger.debug(f"Idle behavior: {behavior['action']}")

                    # Sleep for behavior duration
                    time.sleep(behavior["duration"])
                    break  # Only one behavior at a time
```

### Integration with Speech Synthesis Node

```python
# In speech_synthesis_realtime_node.py

from nevil_framework.idle_animation_manager import IdleAnimationManager

class SpeechSynthesisRealtimeNode(NevilNode):
    def __init__(self):
        super().__init__("speech_synthesis_realtime")

        # Animation managers
        self.animation_manager = SpeechAnimationManager(self.publish)
        self.idle_manager = IdleAnimationManager(
            self.publish,
            self._is_idle
        )

        self.is_speaking = False
        self.last_speech_time = 0

    def initialize(self):
        """Initialize and start idle animations"""
        super().initialize()
        self.idle_manager.start()

    def cleanup(self):
        """Stop idle animations"""
        self.idle_manager.stop()
        super().cleanup()

    def _is_idle(self) -> bool:
        """Check if robot is idle (not speaking, not moving)"""
        # Idle if:
        # 1. Not currently speaking
        # 2. At least 5 seconds since last speech
        # 3. No recent robot actions (check message bus)

        if self.is_speaking:
            return False

        time_since_speech = time.time() - self.last_speech_time
        if time_since_speech < 5.0:
            return False

        return True

    def _on_response_audio_delta(self, event):
        """Track speaking state"""
        self.is_speaking = True
        # ... existing playback code ...

    def _on_response_audio_done(self, event):
        """Update speaking state"""
        self.is_speaking = False
        self.last_speech_time = time.time()
        # ... existing cleanup code ...
```

---

## Part 5: Minimal AI Function Set

### Updated ai_cognition_realtime_node.py

```python
# In ai_cognition_realtime_node.py

def _load_gesture_library(self):
    """Load MINIMAL critical functions only (gestures handled by speech synthesis)"""

    # CRITICAL FUNCTIONS ONLY (4 functions instead of 109)
    self.gesture_definitions = [
        # Camera
        {
            "type": "function",
            "name": "take_snapshot",
            "description": "Take a camera snapshot to see what's in front of you",
            "parameters": {"type": "object", "properties": {}}
        },

        # Memory
        {
            "type": "function",
            "name": "remember",
            "description": "Store a memory for later recall. Use when user shares important information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "User's message"},
                    "response": {"type": "string", "description": "Your response"},
                    "category": {
                        "type": "string",
                        "enum": ["preference", "personal", "intense", "general"]
                    },
                    "importance": {"type": "number", "description": "1-10"}
                },
                "required": ["message", "response", "category", "importance"]
            }
        },

        {
            "type": "function",
            "name": "recall",
            "description": "Recall memories using semantic search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "number", "description": "Max results (default 5)"}
                },
                "required": ["query"]
            }
        },

        # Navigation mode (enable/disable autonomous movement)
        {
            "type": "function",
            "name": "set_navigation_mode",
            "description": "Enable or disable autonomous navigation (only call if user explicitly requests movement)",
            "parameters": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "description": "Enable navigation"},
                    "mode": {
                        "type": "string",
                        "enum": ["follow", "explore", "manual"],
                        "description": "Navigation mode"
                    }
                },
                "required": ["enabled"]
            }
        }
    ]

    self.logger.info(f"Loaded {len(self.gesture_definitions)} CRITICAL functions (gestures handled by speech synthesis)")
```

---

## Implementation Timeline

### Phase 1: Remove Unused Gestures (Immediate - 15 min)
1. ✅ Edit `ai_cognition_realtime_node.py`
2. ✅ Replace 109 functions with 4 critical functions
3. ✅ Restart Nevil
4. ✅ Measure cost reduction (~80% on function tokens)

**Files to modify**:
- `nodes/ai_cognition_realtime/ai_cognition_realtime_node.py` (replace `_load_gesture_library()`)

### Phase 2: Add Speech Animations (30-45 min)
1. ✅ Create `nevil_framework/speech_animation_manager.py`
2. ✅ Integrate with `speech_synthesis_realtime_node.py`
3. ✅ Test keyword-based gestures
4. ✅ Tune gesture mappings

**Files to create**:
- `nevil_framework/speech_animation_manager.py`

**Files to modify**:
- `nodes/speech_synthesis_realtime/speech_synthesis_realtime_node.py`

### Phase 3: Add Idle Animations (30 min)
1. ✅ Create `nevil_framework/idle_animation_manager.py`
2. ✅ Integrate with speech synthesis node
3. ✅ Test idle behaviors
4. ✅ Tune probabilities and timing

**Files to create**:
- `nevil_framework/idle_animation_manager.py`

---

## Expected Results

### Cost Reduction
- **Before**: ~$0.09/conversation on function definitions (109 functions)
- **After**: ~$0.005/conversation on function definitions (4 functions)
- **Savings**: ~$0.085/conversation (95% reduction on function tokens)
- **Monthly savings**: $8.50/month (on 100 conversations)

### Expressiveness Improvement
- **Before**: Static during speech (gestures only if AI calls function)
- **After**:
  - Automatic gestures during speech (keyword-triggered)
  - Punctuation-based emphasis
  - Background idle animations
  - Feels more alive and responsive

### API Performance
- **Before**: 109 functions = ~18,000 tokens per session
- **After**: 4 functions = ~400 tokens per session
- **Latency improvement**: 200-400ms faster session initialization

---

## Gesture Customization

### Add New Keyword Mappings

```python
# In speech_animation_manager.py

# Add your own keyword patterns
KEYWORD_GESTURES = {
    "dance|music|party": ["dance_move:fast", "groove:med"],
    "sleep|tired|sleepy": ["yawn:slow", "drowsy_lean:slow"],
    "hungry|food|eat": ["lick_chops:med"],  # If Nevil has a tongue servo!
    # ... add as many as you want (zero API cost!)
}
```

### Adjust Gesture Frequency

```python
# In speech_animation_manager.py

def __init__(self, publish_callback):
    # Increase for more expressive, decrease for calmer
    self.gesture_cooldown = 1.0  # Allow gestures every 1 second

# In idle_animation_manager.py

# Adjust idle animation frequency
IDLE_BEHAVIORS = [
    {"action": "subtle_sway:slow", "probability": 0.5},  # 50% chance
    # Higher probability = more frequent
]
```

---

## Advanced: Mood-Aware Animations

```python
# Track conversation mood over time
class MoodTracker:
    """Track conversation mood for adaptive animations"""

    def __init__(self):
        self.recent_moods = []  # Last 5 utterances
        self.current_mood = "neutral"

    def update_mood(self, text: str):
        """Analyze text sentiment and update mood"""
        # Simple keyword-based mood detection
        if re.search(r"happy|joy|love|great|awesome", text, re.I):
            mood = "happy"
        elif re.search(r"sad|sorry|bad|terrible", text, re.I):
            mood = "sad"
        elif re.search(r"angry|mad|frustrated", text, re.I):
            mood = "angry"
        else:
            mood = "neutral"

        self.recent_moods.append(mood)
        if len(self.recent_moods) > 5:
            self.recent_moods.pop(0)

        # Current mood is most common recent mood
        self.current_mood = max(set(self.recent_moods), key=self.recent_moods.count)

    def get_mood(self) -> str:
        return self.current_mood

# Use in animation manager
class SpeechAnimationManager:
    def __init__(self, publish_callback):
        self.mood_tracker = MoodTracker()
        # ...

    def add_expression_to_speech(self, text: str):
        # Update mood
        self.mood_tracker.update_mood(text)
        current_mood = self.mood_tracker.get_mood()

        # Use current mood for gesture selection
        gestures = self._detect_keyword_gestures(text)
        mood_gesture = self._get_mood_gesture(current_mood)
        # ...
```

---

## Migration Checklist

### Immediate (15 min)
- [ ] Backup `ai_cognition_realtime_node.py`
- [ ] Replace `_load_gesture_library()` with minimal 4-function version
- [ ] Restart Nevil
- [ ] Test one conversation
- [ ] Verify cost reduction in logs

### Week 1 (1-2 hours)
- [ ] Create `speech_animation_manager.py`
- [ ] Integrate with speech synthesis node
- [ ] Test keyword gestures with 10 conversations
- [ ] Tune gesture mappings based on what sounds natural
- [ ] Measure expressiveness improvement

### Week 2 (30 min)
- [ ] Create `idle_animation_manager.py`
- [ ] Integrate with speech synthesis node
- [ ] Test idle behaviors for 24 hours
- [ ] Adjust probabilities and timing
- [ ] Verify idle animations don't interfere with speech

---

## Testing Scenarios

### Test 1: Expressiveness
- Have conversation with Nevil
- Count gestures in old vs new system
- **Expected**: More gestures in new system (keyword-triggered)

### Test 2: Cost Reduction
- Run 10 conversations
- Compare function token usage
- **Expected**: 95% reduction in function tokens

### Test 3: Idle Behavior
- Leave Nevil idle for 5 minutes
- Count idle animations
- **Expected**: 3-5 subtle movements per minute

### Test 4: Response Quality
- Verify AI responses are still good quality
- Check if AI is confused by reduced function set
- **Expected**: No degradation (AI focuses on conversation)

---

## Summary

**This architecture gives you**:
✅ **95% cost reduction** on function tokens ($0.09 → $0.005 per conversation)
✅ **More expressive Nevil** (automatic gesture triggering)
✅ **Faster responses** (fewer tokens to process)
✅ **Background animations** (always feels alive)
✅ **Zero-cost customization** (add gestures without API cost)
✅ **Cleaner AI focus** (conversation, not gesture choreography)

**Start with Phase 1 today** - 15 minutes to cut function costs by 95%!

Want me to implement Phase 1 right now?
