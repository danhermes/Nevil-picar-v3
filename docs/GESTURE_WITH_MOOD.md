# Gesture Function with Mood Intelligence

## Current Implementation (Wasteful)

```python
# My previous version just sets mood to "neutral" - not using it!
robot_action_data = {
    "actions": [action],
    "mood": "neutral",  # ← Always neutral, not intelligent!
    "priority": 100,
    "timestamp": time.time()
}
```

**This is dumb** - we have mood capability but aren't using it!

---

## Enhanced Implementation: Mood-Aware Gestures

### The Insight

AI should specify BOTH gesture AND mood, because:
- **Gesture** = WHAT to do (physical movement)
- **Mood** = HOW to do it (emotional coloring)

Same gesture, different mood = different feel:
```python
# Wave hello (friendly mood)
perform_gesture(gesture_name="wave", speed="med", mood="happy")
→ Bright, enthusiastic wave

# Wave goodbye (sad mood)
perform_gesture(gesture_name="wave", speed="slow", mood="sad")
→ Reluctant, melancholy wave
```

---

## Implementation

### Enhanced Function Definition

```python
def _load_gesture_library(self):
    """Load gesture library with mood-aware single function"""

    # Build gesture list (same as before)
    # ... gesture_functions, gesture_descriptions ...

    gesture_list = ", ".join(self.gesture_descriptions)

    # Enhanced function with MOOD parameter
    self.gesture_definitions = [
        {
            "type": "function",
            "name": "perform_gesture",
            "description": f"Perform an expressive gesture with emotional mood. The gesture defines the physical movement, while the mood colors how it's performed. For example, 'wave' with 'happy' mood is bright and energetic, while 'wave' with 'sad' mood is slow and melancholy. Available gestures: {gesture_list}",
            "parameters": {
                "type": "object",
                "properties": {
                    "gesture_name": {
                        "type": "string",
                        "description": "Name of the gesture to perform (choose from the list above)"
                    },
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med", "fast"],
                        "description": "Speed: slow=gentle/thoughtful, med=normal, fast=excited/emphatic"
                    },
                    "mood": {
                        "type": "string",
                        "enum": ["neutral", "happy", "sad", "excited", "calm", "curious", "confident", "playful", "empathetic"],
                        "description": "Emotional mood that colors the gesture: happy (bright/positive), sad (melancholy/gentle), excited (high-energy), calm (peaceful/serene), curious (inquisitive), confident (assured), playful (fun/lighthearted), empathetic (caring/supportive), neutral (no emotional coloring)"
                    }
                },
                "required": ["gesture_name"]
            }
        },

        # Other functions (sound, camera, memory) stay the same
        # ...
    ]

    self.logger.info(
        f"Loaded {len(self.gesture_functions)} gestures with mood intelligence "
        f"(93% cost reduction, full expressiveness)"
    )
```

### Enhanced Handler

```python
def _handle_perform_gesture(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mood-aware gesture performance"""
    try:
        gesture_name = args.get('gesture_name', '')
        speed = args.get('speed', 'med')
        mood = args.get('mood', 'neutral')  # ← Now we USE mood!

        if not gesture_name:
            return {"status": "error", "message": "No gesture_name provided"}

        # Validate gesture exists
        if gesture_name not in self.gesture_functions:
            available = ", ".join(list(self.gesture_functions.keys())[:10]) + "..."
            return {
                "status": "error",
                "message": f"Unknown gesture '{gesture_name}'. Available: {available}"
            }

        # Build action string
        action = f"{gesture_name}:{speed}"

        self.logger.info(f"🤖 AI chose gesture: {action} with mood: {mood}")

        # Publish gesture with MEANINGFUL mood
        robot_action_data = {
            "actions": [action],
            "source_text": "ai_gesture_with_mood",
            "mood": mood,  # ← Actual mood from AI's decision!
            "priority": 100,
            "timestamp": time.time()
        }

        if self.publish("robot_action", robot_action_data):
            return {
                "status": "success",
                "gesture": action,
                "mood": mood
            }
        else:
            return {"status": "error", "message": "Failed to publish gesture"}

    except Exception as e:
        self.logger.error(f"Error performing gesture: {e}")
        return {"status": "error", "message": str(e)}
```

---

## How AI Uses Mood

### Example 1: Matching User's Emotion

**User**: "I'm so happy! I got the job!"

**AI thinks**:
```
- User is happy and excited
- I should match their energy
- Gesture: excited_bounce (physical action)
- Mood: happy (emotional coloring)
- Speed: fast (intensity)
```

**AI calls**:
```python
perform_gesture(
    gesture_name="excited_bounce",
    speed="fast",
    mood="happy"
)
```

**Result**: Nevil bounces with bright, joyful energy

---

### Example 2: Contrasting Emotion (Empathy)

**User**: "I'm really sad today. I lost my pet."

**AI thinks**:
```
- User is sad and needs comfort
- I should show empathy, not mirror sadness
- Gesture: sympathetic_lean (physical comfort)
- Mood: empathetic (caring support)
- Speed: slow (gentle, not rushed)
```

**AI calls**:
```python
perform_gesture(
    gesture_name="sympathetic_lean",
    speed="slow",
    mood="empathetic"
)
```

**Result**: Nevil leans forward gently with caring, supportive energy

---

### Example 3: Playful Interaction

**User**: "Let's play a game!"

**AI thinks**:
```
- User wants to play
- I should be playful and fun
- Gesture: playful_bounce
- Mood: playful (fun/lighthearted)
- Speed: fast (energetic)
```

**AI calls**:
```python
perform_gesture(
    gesture_name="playful_bounce",
    speed="fast",
    mood="playful"
)
```

**Result**: Nevil bounces with fun, game-ready energy

---

## Why Mood Matters

### Same Gesture, Different Mood

**Wave Gesture**:
```python
# Excited greeting
perform_gesture(gesture_name="wave", speed="fast", mood="excited")
→ Big, energetic, "OMG HI!" wave

# Friendly greeting
perform_gesture(gesture_name="wave", speed="med", mood="happy")
→ Warm, welcoming "hello!" wave

# Sad goodbye
perform_gesture(gesture_name="wave", speed="slow", mood="sad")
→ Reluctant, melancholy "I'll miss you" wave

# Calm acknowledgment
perform_gesture(gesture_name="wave", speed="slow", mood="calm")
→ Gentle, peaceful "I see you" wave
```

**Nod Gesture**:
```python
# Confident agreement
perform_gesture(gesture_name="nod", speed="med", mood="confident")
→ Assured, "absolutely!" nod

# Empathetic understanding
perform_gesture(gesture_name="nod", speed="slow", mood="empathetic")
→ Gentle, "I understand" nod

# Excited agreement
perform_gesture(gesture_name="nod", speed="fast", mood="excited")
→ Eager, "yes yes yes!" nod
```

---

## Mood Processing in Robot Actions

### In the navigation/action handler:

```python
# In robot_action_handler or extended_gestures

def execute_gesture_with_mood(gesture_name: str, speed: str, mood: str):
    """Execute gesture with mood modulation"""

    # Get base gesture function
    gesture_func = get_gesture_function(gesture_name)

    # Mood affects execution parameters
    mood_modifiers = {
        "happy": {
            "energy": 1.2,      # 20% more energetic
            "brightness": 1.0,  # Full brightness (if LEDs)
            "tempo": 1.1        # 10% faster tempo
        },
        "sad": {
            "energy": 0.7,      # 30% less energy
            "brightness": 0.6,  # Dimmer (if LEDs)
            "tempo": 0.8        # 20% slower tempo
        },
        "excited": {
            "energy": 1.5,      # 50% more energy!
            "brightness": 1.0,
            "tempo": 1.3        # 30% faster
        },
        "calm": {
            "energy": 0.8,      # Gentle
            "brightness": 0.8,
            "tempo": 0.9        # Slightly slower
        },
        "empathetic": {
            "energy": 0.9,      # Soft energy
            "brightness": 0.9,
            "tempo": 0.85       # Gentle pace
        },
        # ... more moods
    }

    # Get modifiers for this mood
    modifiers = mood_modifiers.get(mood, {"energy": 1.0, "brightness": 1.0, "tempo": 1.0})

    # Execute gesture with mood modulation
    gesture_func(
        speed=speed,
        energy_multiplier=modifiers["energy"],
        tempo_multiplier=modifiers["tempo"]
    )

    # If you have LEDs, also modulate them
    if has_leds():
        set_led_brightness(modifiers["brightness"])
        set_led_color_for_mood(mood)  # e.g., yellow=happy, blue=sad
```

---

## AI Decision Examples

### Complex Emotional Response

**User**: "I'm nervous about my presentation tomorrow."

**AI reasoning**:
```
- User is anxious/nervous
- I should be supportive and confident
- Don't mirror nervousness (not helpful)
- Show confidence to reassure them

Gesture: confident_nod (reassuring gesture)
Mood: confident (to transfer confidence)
Speed: med (steady, not rushed)
```

**AI calls**:
```python
perform_gesture(
    gesture_name="confident_nod",
    speed="med",
    mood="confident"
)
```

**AI responds**: "You've got this! I believe in you."

**Result**: Confident, reassuring nod that transfers certainty

---

## Cost Analysis

### Enhanced Function (with mood)

```
Function definition: ~100 tokens
Gesture list (109 gestures): ~650 tokens
Parameters (gesture_name, speed, mood): ~80 tokens
Total: ~830 tokens

5 functions total: ~1,400 tokens
Cost: $0.007 per conversation
```

**Adding mood parameter**: +30 tokens = negligible cost increase

---

## Benefits of Mood-Aware Gestures

### 1. Richer Expressiveness ✅
- Same gesture, multiple emotional colorings
- 109 gestures × 9 moods = 981 possible expressions!
- No additional API cost

### 2. Smarter AI Decisions ✅
- AI considers both WHAT to do and HOW to feel
- Can match or contrast user's emotions appropriately
- More nuanced emotional intelligence

### 3. Better User Experience ✅
- Gestures feel more alive and contextual
- Emotional resonance with user's state
- More human-like interaction

### 4. No Performance Cost ✅
- Mood is just a parameter (cheap)
- No additional function definitions
- Same 93% cost savings

---

## Advanced: Mood Tracking

Track conversation mood over time:

```python
class ConversationMoodTracker:
    """Track mood evolution during conversation"""

    def __init__(self):
        self.mood_history = []  # Last 10 moods
        self.current_base_mood = "neutral"

    def update_mood(self, new_mood: str):
        """Update mood based on gesture choice"""
        self.mood_history.append(new_mood)
        if len(self.mood_history) > 10:
            self.mood_history.pop(0)

        # Current mood is most frequent recent mood
        from collections import Counter
        mood_counts = Counter(self.mood_history)
        self.current_base_mood = mood_counts.most_common(1)[0][0]

    def get_mood_suggestion(self, user_emotion: str) -> str:
        """Suggest mood based on user emotion and conversation flow"""
        # If user is upset, be empathetic
        if user_emotion in ["sad", "angry", "frustrated"]:
            return "empathetic"

        # If user is excited and we've been calm, match their energy
        if user_emotion == "excited" and self.current_base_mood == "calm":
            return "excited"

        # Otherwise match user's emotion
        return user_emotion
```

---

## Summary

**Enhanced version with mood**:
✅ **93% cost reduction** (same as before)
✅ **Full gesture library** (all 109 gestures)
✅ **Mood intelligence** (9 moods × 109 gestures = 981 expressions)
✅ **AI-driven** (AI chooses gesture, speed, AND mood)
✅ **Negligible cost increase** (+30 tokens for mood parameter)
✅ **Richer expressiveness** (same gesture, different emotional coloring)

**Parameters AI Controls**:
1. **gesture_name**: Which physical movement (109 options)
2. **speed**: How fast to execute (slow/med/fast)
3. **mood**: Emotional coloring (9 options)

**Total possibilities**: 109 gestures × 3 speeds × 9 moods = **2,943 unique expressions!**

All for $0.007 per conversation (93% savings from original $0.09)!

Want me to implement this mood-aware version?
