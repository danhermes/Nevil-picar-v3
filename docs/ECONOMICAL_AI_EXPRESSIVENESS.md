# Economical AI-Driven Expressiveness

## Goal
Keep AI in control of Nevil's expressions BUT reduce function token costs from $0.09 to $0.01 per conversation (90% savings).

## The Problem
- Sending 109 individual gesture functions = ~18,000 tokens per session
- AI rarely uses most gestures (maybe 2-3 per conversation)
- We're paying for 106 unused function definitions

## The Solution: Smart Function Grouping

Instead of 109 individual functions, create **category-based "super-functions"** that let AI choose gestures economically.

---

## Architecture

### Old Way (Expensive)
```
AI has 109 options:
- wave:slow
- wave:med
- wave:fast
- nod:slow
- nod:med
- nod:fast
... 103 more

= 18,000 tokens per session
```

### New Way (Economical)
```
AI has 10 category functions with parameters:
- express_emotion(emotion="happy", intensity="high")
- gesture_greeting(type="wave", energy="excited")
- show_agreement(confidence="strong")
- show_disagreement(confidence="weak")
- express_curiosity(intensity="medium")

= 2,000 tokens per session
```

---

## Implementation

### Step 1: Create Gesture Category Functions

```python
# In ai_cognition_realtime_node.py

def _load_gesture_library(self):
    """Load economical category-based gesture functions"""

    # Map emotion categories to actual gestures
    self.emotion_gesture_map = {
        "happy": ["happy_spin", "excited_bounce", "happy_wiggle", "joyful_dance"],
        "sad": ["sad_droop", "sympathy_lean", "dejected_slump"],
        "excited": ["excited_bounce", "enthusiastic_jump", "hyperactive_spin"],
        "calm": ["gentle_sway", "peaceful_stance", "serene_nod"],
        "curious": ["curious_tilt", "inquisitive_lean", "head_scratch"],
        "confident": ["proud_stance", "assertive_nod", "confident_lean"],
        "playful": ["playful_bounce", "silly_wobble", "mischievous_lean"],
        "thoughtful": ["thinking_pose", "contemplative_lean", "ponder_tilt"],
    }

    self.greeting_gesture_map = {
        "wave": ["wave", "friendly_wave", "enthusiastic_wave"],
        "nod": ["nod", "friendly_nod", "welcoming_nod"],
        "bow": ["polite_bow", "respectful_bow"],
    }

    self.agreement_gesture_map = {
        "strong": ["emphatic_nod", "vigorous_agreement", "enthusiastic_yes"],
        "medium": ["nod", "affirmative_nod"],
        "weak": ["slight_nod", "hesitant_agreement"],
    }

    self.disagreement_gesture_map = {
        "strong": ["vigorous_shake", "emphatic_no", "definite_shake"],
        "medium": ["shake_head", "negative_shake"],
        "weak": ["slight_shake", "uncertain_no"],
    }

    # Create CATEGORY-BASED function definitions (10 instead of 109)
    self.gesture_definitions = [
        {
            "type": "function",
            "name": "express_emotion",
            "description": "Express an emotion through body language. Use this to make responses more engaging and human-like.",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "enum": ["happy", "sad", "excited", "calm", "curious", "confident", "playful", "thoughtful"],
                        "description": "The emotion to express"
                    },
                    "intensity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "How strongly to express the emotion"
                    }
                },
                "required": ["emotion"]
            }
        },

        {
            "type": "function",
            "name": "gesture_greeting",
            "description": "Perform a greeting gesture when saying hello or goodbye",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["wave", "nod", "bow"],
                        "description": "Type of greeting"
                    },
                    "energy": {
                        "type": "string",
                        "enum": ["calm", "friendly", "excited"],
                        "description": "Energy level of greeting"
                    },
                    "is_goodbye": {
                        "type": "boolean",
                        "description": "True if this is a goodbye, false for hello"
                    }
                },
                "required": ["type"]
            }
        },

        {
            "type": "function",
            "name": "show_agreement",
            "description": "Show agreement or affirmation (nodding, yes gestures)",
            "parameters": {
                "type": "object",
                "properties": {
                    "confidence": {
                        "type": "string",
                        "enum": ["weak", "medium", "strong"],
                        "description": "How confidently agreeing"
                    }
                },
                "required": ["confidence"]
            }
        },

        {
            "type": "function",
            "name": "show_disagreement",
            "description": "Show disagreement or negation (head shaking, no gestures)",
            "parameters": {
                "type": "object",
                "properties": {
                    "confidence": {
                        "type": "string",
                        "enum": ["weak", "medium", "strong"],
                        "description": "How confidently disagreeing"
                    }
                },
                "required": ["confidence"]
            }
        },

        {
            "type": "function",
            "name": "express_curiosity",
            "description": "Show curiosity or interest (head tilts, looking around)",
            "parameters": {
                "type": "object",
                "properties": {
                    "intensity": {
                        "type": "string",
                        "enum": ["mild", "moderate", "intense"],
                        "description": "Level of curiosity"
                    }
                },
                "required": []
            }
        },

        {
            "type": "function",
            "name": "look_direction",
            "description": "Look in a specific direction",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["left", "right", "up", "down", "around"],
                        "description": "Direction to look"
                    },
                    "duration": {
                        "type": "string",
                        "enum": ["quick", "normal", "sustained"],
                        "description": "How long to maintain the look"
                    }
                },
                "required": ["direction"]
            }
        },

        {
            "type": "function",
            "name": "play_sound_effect",
            "description": "Play a sound effect to enhance communication",
            "parameters": {
                "type": "object",
                "properties": {
                    "sound": {
                        "type": "string",
                        "enum": ["honk", "rev_engine", "beep", "chime"],
                        "description": "Sound to play"
                    }
                },
                "required": ["sound"]
            }
        },

        # Keep critical non-gesture functions
        {
            "type": "function",
            "name": "take_snapshot",
            "description": "Take a camera snapshot",
            "parameters": {"type": "object", "properties": {}}
        },

        {
            "type": "function",
            "name": "remember",
            "description": "Store a memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "response": {"type": "string"},
                    "category": {"type": "string", "enum": ["preference", "personal", "intense", "general"]},
                    "importance": {"type": "number"}
                },
                "required": ["message", "response", "category", "importance"]
            }
        },

        {
            "type": "function",
            "name": "recall",
            "description": "Recall memories",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    ]

    self.logger.info(f"Loaded {len(self.gesture_definitions)} category-based functions (90% cost reduction)")
```

### Step 2: Implement Category Function Handlers

```python
# In ai_cognition_realtime_node.py

def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call"""
    try:
        self.logger.info(f"🎬 Executing function: {function_name} with args: {args}")

        # Handle category-based gesture functions
        if function_name == "express_emotion":
            return self._handle_express_emotion(args)

        elif function_name == "gesture_greeting":
            return self._handle_gesture_greeting(args)

        elif function_name == "show_agreement":
            return self._handle_show_agreement(args)

        elif function_name == "show_disagreement":
            return self._handle_show_disagreement(args)

        elif function_name == "express_curiosity":
            return self._handle_express_curiosity(args)

        elif function_name == "look_direction":
            return self._handle_look_direction(args)

        elif function_name == "play_sound_effect":
            return self._handle_sound_effect(args)

        # Handle critical functions
        elif function_name == "take_snapshot":
            return self._handle_take_snapshot()

        elif function_name == "remember":
            return self._handle_remember(args)

        elif function_name == "recall":
            return self._handle_recall(args)

        else:
            self.logger.warning(f"❌ Unknown function: {function_name}")
            return {"status": "error", "message": f"Unknown function: {function_name}"}

    except Exception as e:
        self.logger.error(f"Error executing function {function_name}: {e}")
        return {"status": "error", "message": str(e)}


def _handle_express_emotion(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle emotion expression"""
    import random

    emotion = args.get('emotion', 'happy')
    intensity = args.get('intensity', 'medium')

    # Get gesture options for this emotion
    gesture_options = self.emotion_gesture_map.get(emotion, ["neutral_stance"])

    # Pick random gesture from options
    base_gesture = random.choice(gesture_options)

    # Map intensity to speed
    speed_map = {"low": "slow", "medium": "med", "high": "fast"}
    speed = speed_map.get(intensity, "med")

    # Build action string
    action = f"{base_gesture}:{speed}"

    self.logger.info(f"💖 Expressing {emotion} at {intensity} intensity → {action}")

    # Publish gesture
    return self._publish_gesture(action, f"express_{emotion}")


def _handle_gesture_greeting(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle greeting gestures"""
    import random

    greeting_type = args.get('type', 'wave')
    energy = args.get('energy', 'friendly')
    is_goodbye = args.get('is_goodbye', False)

    # Get gesture options
    gesture_options = self.greeting_gesture_map.get(greeting_type, ["wave"])
    base_gesture = random.choice(gesture_options)

    # Map energy to speed
    speed_map = {"calm": "slow", "friendly": "med", "excited": "fast"}
    speed = speed_map.get(energy, "med")

    # Add goodbye modifier if needed
    if is_goodbye and greeting_type == "wave":
        base_gesture = "wave_goodbye"

    action = f"{base_gesture}:{speed}"

    self.logger.info(f"👋 Greeting: {greeting_type} ({energy}) → {action}")

    return self._publish_gesture(action, "greeting")


def _handle_show_agreement(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle agreement gestures"""
    import random

    confidence = args.get('confidence', 'medium')

    # Get gesture for confidence level
    gesture_options = self.agreement_gesture_map.get(confidence, ["nod"])
    base_gesture = random.choice(gesture_options)

    # Confidence maps to speed
    speed_map = {"weak": "slow", "medium": "med", "strong": "fast"}
    speed = speed_map.get(confidence, "med")

    action = f"{base_gesture}:{speed}"

    self.logger.info(f"✓ Showing agreement ({confidence}) → {action}")

    return self._publish_gesture(action, "agreement")


def _handle_show_disagreement(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle disagreement gestures"""
    import random

    confidence = args.get('confidence', 'medium')

    gesture_options = self.disagreement_gesture_map.get(confidence, ["shake_head"])
    base_gesture = random.choice(gesture_options)

    speed_map = {"weak": "slow", "medium": "med", "strong": "fast"}
    speed = speed_map.get(confidence, "med")

    action = f"{base_gesture}:{speed}"

    self.logger.info(f"✗ Showing disagreement ({confidence}) → {action}")

    return self._publish_gesture(action, "disagreement")


def _handle_express_curiosity(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle curiosity gestures"""
    import random

    intensity = args.get('intensity', 'moderate')

    curiosity_gestures = {
        "mild": ["slight_tilt:slow", "curious_look:slow"],
        "moderate": ["curious_tilt:med", "head_scratch:med"],
        "intense": ["intense_scan:fast", "eager_lean:fast"]
    }

    gesture_options = curiosity_gestures.get(intensity, ["curious_tilt:med"])
    action = random.choice(gesture_options)

    self.logger.info(f"🤔 Expressing curiosity ({intensity}) → {action}")

    return self._publish_gesture(action, "curiosity")


def _handle_look_direction(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle directional looking"""
    direction = args.get('direction', 'left')
    duration = args.get('duration', 'normal')

    # Map direction to gesture
    direction_map = {
        "left": "look_left",
        "right": "look_right",
        "up": "look_up",
        "down": "look_down",
        "around": "look_around"
    }

    base_gesture = direction_map.get(direction, "look_left")

    # Map duration to speed (longer duration = slower movement)
    speed_map = {"quick": "fast", "normal": "med", "sustained": "slow"}
    speed = speed_map.get(duration, "med")

    action = f"{base_gesture}:{speed}"

    self.logger.info(f"👀 Looking {direction} ({duration}) → {action}")

    return self._publish_gesture(action, f"look_{direction}")


def _handle_sound_effect(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sound effects"""
    sound = args.get('sound', 'honk')

    self.logger.info(f"🔊 Playing sound: {sound}")

    # Publish sound action
    return self._publish_gesture(sound, "sound_effect")


def _publish_gesture(self, action: str, source: str) -> Dict[str, Any]:
    """Helper to publish gesture actions"""
    robot_action_data = {
        "actions": [action],
        "source_text": f"ai_category_{source}",
        "mood": "neutral",
        "priority": 100,
        "timestamp": time.time()
    }

    if self.publish("robot_action", robot_action_data):
        self.logger.info(f"✓ Executed gesture: {action}")
        return {"status": "success", "action": action}
    else:
        return {"status": "error", "message": "Failed to publish gesture"}
```

---

## Cost Comparison

### Before (Individual Functions)
```
109 gesture functions
~18,000 tokens per session
$0.09 per 10-minute conversation

Example:
- wave:slow
- wave:med
- wave:fast
- nod:slow
- nod:med
- nod:fast
... 103 more
```

### After (Category Functions)
```
10 category functions
~2,000 tokens per session
$0.01 per 10-minute conversation
90% savings!

Example:
- express_emotion(emotion="happy", intensity="high")
- gesture_greeting(type="wave", energy="excited")
- show_agreement(confidence="strong")
```

---

## Benefits

### 1. Cost Reduction
- **90% savings** on function tokens ($0.09 → $0.01 per conversation)
- **$8/month savings** (on 100 conversations)

### 2. AI Stays In Control
- ✅ AI decides when to gesture
- ✅ AI chooses emotion/intensity
- ✅ AI coordinates gestures with speech
- ✅ Maintains expressiveness

### 3. Better Variety
- Random selection from gesture categories
- More natural movement (not always same gesture)
- Easy to add new gestures to categories

### 4. Easier to Extend
- Add new emotions: just update `emotion_gesture_map`
- No need to create new function definitions
- Zero cost to add more gesture variety

---

## Example AI Interactions

### Example 1: Greeting
```
User: "Hi Nevil!"

AI thinks: This is a friendly greeting
AI calls: gesture_greeting(type="wave", energy="excited")
Result: Nevil performs "enthusiastic_wave:fast"

AI responds: "Hi there! Great to see you!"
```

### Example 2: Excitement
```
User: "I got an A on my test!"

AI thinks: User is excited, I should match that energy
AI calls: express_emotion(emotion="excited", intensity="high")
Result: Nevil performs "excited_bounce:fast"

AI responds: "That's amazing! I'm so proud of you!"
```

### Example 3: Curiosity
```
User: "What do you think about space travel?"

AI thinks: This is a thoughtful question, show curiosity
AI calls: express_curiosity(intensity="moderate")
Result: Nevil performs "curious_tilt:med"

AI responds: "Space travel is fascinating! I think about..."
```

---

## Migration Guide

### Phase 1: Implement Category Functions (30 minutes)

1. **Backup current code**:
```bash
cp nodes/ai_cognition_realtime/ai_cognition_realtime_node.py \
   nodes/ai_cognition_realtime/ai_cognition_realtime_node.py.backup
```

2. **Replace `_load_gesture_library()`** with category version (see above)

3. **Replace `_execute_function()`** with category handlers (see above)

4. **Restart Nevil**:
```bash
sudo systemctl restart nevil
```

### Phase 2: Test & Tune (1 hour)

1. **Test each category**:
   - Greetings: "Hi Nevil!" / "Bye Nevil!"
   - Emotions: "I'm so happy!" / "I'm sad today"
   - Agreement: "You're absolutely right"
   - Curiosity: "What do you think?"

2. **Monitor AI usage**:
```bash
tail -f logs/ai_cognition_realtime.log | grep "Executing function"
```

3. **Adjust gesture mappings** if needed:
   - Too subtle? Add more intense gestures
   - Too hyperactive? Remove high-energy gestures
   - Not varied enough? Add more options to categories

---

## Advanced: Context-Aware Gesture Sets

For even more savings, load different gesture sets based on conversation context:

```python
# Only 5 functions when in "casual chat" mode
CASUAL_FUNCTIONS = ["express_emotion", "gesture_greeting", "show_agreement"]

# All 10 functions when in "interactive" mode
INTERACTIVE_FUNCTIONS = [...all 10...]

# Dynamically update session based on context
def update_gesture_set(self, mode: str):
    if mode == "casual":
        functions = self.CASUAL_FUNCTIONS
    else:
        functions = self.INTERACTIVE_FUNCTIONS

    self.connection_manager.send_sync({
        "type": "session.update",
        "session": {"tools": functions}
    })
```

---

## Summary

**This approach gives you**:
✅ **90% cost reduction** ($0.09 → $0.01 per conversation)
✅ **AI-driven expressiveness** (AI decides what/when to gesture)
✅ **Gesture variety** (random selection from categories)
✅ **Easy extensibility** (add gestures to maps, not function defs)
✅ **Natural behavior** (emotions + intensity instead of fixed gestures)

**Monthly savings**: ~$8/month (on 100 conversations)
**Implementation time**: 30 minutes
**Expressiveness**: IMPROVED (more natural, context-aware)

Want me to implement this for you right now?
