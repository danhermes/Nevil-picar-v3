# Single Gesture Function - Full Library, Minimal Cost

## The Problem
- Sending 109 function definitions = ~18,000 tokens = $0.09/conversation
- Curated set (17 gestures) = ~2,800 tokens = $0.015/conversation
- But what if we want AI to have access to ALL 109 gestures?

## The Solution: Parameter-Based Gesture Selection

Send **ONE function** that accepts **ANY gesture name as a parameter**:

```python
# Instead of 109 functions, send 1 function:
perform_gesture(gesture_name="happy_spin", speed="fast")
```

AI has full access to all 109 gestures, but we only send ~800 tokens per session!

---

## How It Works

### Old Way (109 Functions)
```python
# Session sends 109 separate function definitions:
{
    "name": "happy_spin",
    "description": "Spin happily",
    "parameters": {"speed": ...}
},
{
    "name": "excited_bounce",
    "description": "Bounce with excitement",
    "parameters": {"speed": ...}
},
... 107 more ...

Total tokens: ~18,000
```

### New Way (1 Function, 109 Gestures)
```python
# Session sends 1 function definition:
{
    "name": "perform_gesture",
    "description": "Perform any gesture from the library. Available gestures: happy_spin (spin with joy), excited_bounce (bounce with excitement), sad_droop (droop sadly), curious_tilt (tilt head curiously), ... [all 109 listed with descriptions]",
    "parameters": {
        "gesture_name": {
            "type": "string",
            "description": "Name of gesture to perform from the list above"
        },
        "speed": {
            "type": "string",
            "enum": ["slow", "med", "fast"],
            "description": "Speed of gesture"
        }
    }
}

Total tokens: ~800
```

---

## Implementation

### Step 1: Build Gesture Library Map

```python
# In ai_cognition_realtime_node.py

def _load_gesture_library(self):
    """Load gesture library with single function interface"""
    try:
        # Import gesture functions
        import sys
        gestures_path = Path(__file__).parent.parent.parent / "nodes" / "navigation"
        if str(gestures_path) not in sys.path:
            sys.path.insert(0, str(gestures_path))

        import extended_gestures

        # Build gesture name → function mapping (for execution)
        self.gesture_functions = {}
        self.gesture_descriptions = []

        # Get all gesture function names
        gesture_names = [
            name for name in dir(extended_gestures)
            if callable(getattr(extended_gestures, name))
            and not name.startswith('_')
            and name not in ['time', 'Enum', 'GestureSpeed']
        ]

        # Build mapping and description list
        for gesture_name in gesture_names:
            self.gesture_functions[gesture_name] = getattr(extended_gestures, gesture_name)

            # Create brief description for each gesture
            description = f"{gesture_name.replace('_', ' ')}"
            self.gesture_descriptions.append(f"{gesture_name} ({description})")

        # Build gesture list string for function description
        gesture_list = ", ".join(self.gesture_descriptions)

        # Create SINGLE function definition with ALL gestures
        self.gesture_definitions = [
            {
                "type": "function",
                "name": "perform_gesture",
                "description": f"Perform any expressive gesture to enhance communication. Choose gestures that match your emotional response and the conversation context. Available gestures: {gesture_list}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "gesture_name": {
                            "type": "string",
                            "description": "Name of the gesture to perform (choose from the list in the function description)"
                        },
                        "speed": {
                            "type": "string",
                            "enum": ["slow", "med", "fast"],
                            "description": "Speed: slow=gentle/thoughtful, med=normal energy, fast=excited/emphatic"
                        }
                    },
                    "required": ["gesture_name"]
                }
            },

            # Add sound effects as single function too
            {
                "type": "function",
                "name": "play_sound",
                "description": "Play a sound effect. Available sounds: honk (car horn), rev_engine (engine sound), beep (friendly beep), chime (pleasant chime)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sound_name": {
                            "type": "string",
                            "description": "Name of sound to play"
                        }
                    },
                    "required": ["sound_name"]
                }
            },

            # Critical functions
            {
                "type": "function",
                "name": "take_snapshot",
                "description": "Take a camera snapshot to see what's in front of you",
                "parameters": {"type": "object", "properties": {}}
            },

            {
                "type": "function",
                "name": "remember",
                "description": "Store a memory for later recall",
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
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]

        self.logger.info(
            f"Loaded {len(self.gesture_functions)} gestures via single function "
            f"(96% cost reduction: {len(self.gesture_functions)} gestures, 5 functions)"
        )

    except Exception as e:
        self.logger.error(f"Failed to load gesture library: {e}")
        self.gesture_functions = {}
        self.gesture_definitions = []
```

### Step 2: Update Function Handler

```python
# In ai_cognition_realtime_node.py

def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a function call"""
    try:
        self.logger.info(f"🎬 Executing function: {function_name} with args: {args}")

        # Handle gesture performance
        if function_name == "perform_gesture":
            return self._handle_perform_gesture(args)

        # Handle sound effects
        elif function_name == "play_sound":
            return self._handle_play_sound(args)

        # Handle camera
        elif function_name == "take_snapshot":
            return self._handle_take_snapshot()

        # Handle memory
        elif function_name == "remember":
            return self._handle_remember(args)

        elif function_name == "recall":
            return self._handle_recall(args)

        else:
            return {"status": "error", "message": f"Unknown function: {function_name}"}

    except Exception as e:
        self.logger.error(f"Error executing function {function_name}: {e}")
        return {"status": "error", "message": str(e)}


def _handle_perform_gesture(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle gesture performance - AI chose gesture by name"""
    try:
        gesture_name = args.get('gesture_name', '')
        speed = args.get('speed', 'med')

        if not gesture_name:
            return {"status": "error", "message": "No gesture_name provided"}

        # Validate gesture exists
        if gesture_name not in self.gesture_functions:
            # Try to find close match (handle typos/variations)
            available = ", ".join(list(self.gesture_functions.keys())[:10]) + "..."
            return {
                "status": "error",
                "message": f"Unknown gesture '{gesture_name}'. Available: {available}"
            }

        # Build action string
        action = f"{gesture_name}:{speed}"

        self.logger.info(f"🤖 AI chose gesture: {action}")

        # Publish gesture
        robot_action_data = {
            "actions": [action],
            "source_text": "ai_gesture_choice",
            "mood": "neutral",
            "priority": 100,
            "timestamp": time.time()
        }

        if self.publish("robot_action", robot_action_data):
            return {"status": "success", "gesture": action}
        else:
            return {"status": "error", "message": "Failed to publish gesture"}

    except Exception as e:
        self.logger.error(f"Error performing gesture: {e}")
        return {"status": "error", "message": str(e)}


def _handle_play_sound(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sound effect playback"""
    try:
        sound_name = args.get('sound_name', 'honk')

        self.logger.info(f"🔊 AI chose sound: {sound_name}")

        # Publish sound action
        robot_action_data = {
            "actions": [f"play_sound {sound_name}"],
            "source_text": "ai_sound_choice",
            "mood": "neutral",
            "priority": 100,
            "timestamp": time.time()
        }

        if self.publish("robot_action", robot_action_data):
            return {"status": "success", "sound": sound_name}
        else:
            return {"status": "error", "message": "Failed to publish sound"}

    except Exception as e:
        self.logger.error(f"Error playing sound: {e}")
        return {"status": "error", "message": str(e)}
```

---

## Cost Analysis

### Token Breakdown

**Old System (109 separate functions)**:
```
Each function definition: ~165 tokens
109 functions × 165 tokens = 17,985 tokens
Cost per session: $0.09
```

**New System (1 function, 109 gestures listed)**:
```
Function definition header: ~100 tokens
Gesture list (109 gestures × 6 tokens avg): ~650 tokens
Parameters definition: ~50 tokens
Total: ~800 tokens
Cost per session: $0.004
```

**Additional functions**:
```
play_sound: ~150 tokens
take_snapshot: ~100 tokens
remember: ~200 tokens
recall: ~100 tokens
Total: ~550 tokens
```

**Grand Total**: ~1,350 tokens vs 18,000 tokens

### Savings
- **Token reduction**: 93% (18,000 → 1,350)
- **Cost reduction**: 93% ($0.09 → $0.0065 per conversation)
- **Monthly savings**: ~$8.35 (on 100 conversations)
- **Annual savings**: ~$100

---

## AI Intelligence Preserved

### Example Interaction

**User**: "I'm so excited! I got the job!"

**AI reasoning**:
```
AI thinks:
  - User is very excited (detected emotion)
  - I should match their energy
  - I have 109 gestures available
  - Best choices: happy_spin, excited_bounce, enthusiastic_jump
  - I'll pick excited_bounce because it's most direct
  - Speed should be fast to match high energy

AI calls: perform_gesture(gesture_name="excited_bounce", speed="fast")
```

**AI directly chose**:
- ✅ Specific gesture: "excited_bounce" (from 109 options)
- ✅ Speed: "fast" (from 3 options)
- ✅ Timing: Right after user's message
- ✅ Context: Matching user's emotional energy

**No programmatic mapping** - Pure AI decision!

---

## Benefits

### 1. Full Gesture Library ✅
- AI has access to ALL 109 gestures
- No limitations on expressiveness
- Can use any gesture from original library

### 2. Minimal Cost ✅
- 93% cost reduction
- ~1,350 tokens instead of 18,000
- $0.0065 per conversation instead of $0.09

### 3. AI Control ✅
- AI directly chooses gesture name
- AI decides speed
- AI times it with conversation
- No programmatic randomness

### 4. Easy to Extend ✅
- Add new gestures to library
- No need to update function definitions
- Automatically available to AI
- Zero additional API cost

---

## Advanced: Organized Gesture List

To help AI find gestures faster, organize the description:

```python
# Build organized gesture list by category
gesture_categories = {
    "Emotions": ["happy_spin", "excited_bounce", "sad_droop", "curious_tilt", ...],
    "Communication": ["wave", "nod", "shake_head", "point_ahead", ...],
    "Reactions": ["surprised_lean", "playful_bounce", ...],
}

# Build categorized description
description_parts = ["Perform any gesture to enhance communication. "]
for category, gestures in gesture_categories.items():
    gesture_list = ", ".join(gestures)
    description_parts.append(f"{category}: {gesture_list}. ")

full_description = "".join(description_parts)
```

Result:
```
"Perform any gesture to enhance communication.
Emotions: happy_spin, excited_bounce, sad_droop, curious_tilt, thinking_pose.
Communication: wave, nod, shake_head, point_ahead, welcoming_gesture.
Reactions: surprised_lean, playful_bounce, sympathetic_lean."
```

This helps AI:
- Find gestures by category
- Understand gesture purposes
- Make better choices faster

---

## Handling Invalid Gestures

What if AI chooses a gesture that doesn't exist?

```python
def _handle_perform_gesture(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle gesture with fuzzy matching for typos"""
    gesture_name = args.get('gesture_name', '')

    # Exact match
    if gesture_name in self.gesture_functions:
        # Execute gesture
        ...

    # Fuzzy match for typos (e.g., "hapyy_spin" → "happy_spin")
    else:
        from difflib import get_close_matches
        matches = get_close_matches(gesture_name, self.gesture_functions.keys(), n=1, cutoff=0.6)

        if matches:
            corrected = matches[0]
            self.logger.warning(f"Gesture '{gesture_name}' not found, using '{corrected}' instead")
            gesture_name = corrected
            # Execute gesture
            ...
        else:
            # Return error with suggestions
            return {
                "status": "error",
                "message": f"Gesture '{gesture_name}' not found. Did you mean one of: {', '.join(list(self.gesture_functions.keys())[:5])}?"
            }
```

---

## Migration Guide

### Step 1: Backup (1 min)
```bash
cp nodes/ai_cognition_realtime/ai_cognition_realtime_node.py{,.backup}
```

### Step 2: Update Code (15 min)
1. Replace `_load_gesture_library()` with single-function version
2. Update `_execute_function()` to handle `perform_gesture`
3. Add `_handle_perform_gesture()` method

### Step 3: Test (10 min)
```bash
sudo systemctl restart nevil

# Test various gestures
# Talk to Nevil and observe which gestures AI chooses
tail -f logs/ai_cognition_realtime.log | grep "AI chose gesture"
```

### Step 4: Verify Savings (5 min)
```bash
# Check session.update token count
grep "session.update" logs/ai_cognition_realtime.log

# Should see ~1,350 tokens instead of ~18,000
```

---

## Comparison: All Approaches

| Approach | Gestures Available | Functions Sent | Tokens | Cost | AI Control |
|----------|-------------------|----------------|--------|------|------------|
| **Current (109 functions)** | 109 | 109 | 18,000 | $0.090 | ✅ Full |
| **Categories** | 109 | 10 | 2,000 | $0.010 | ❌ Programmatic |
| **Curated (17)** | 17 | 17 | 2,800 | $0.015 | ✅ Full |
| **Single Function** | 109 | 5 | 1,350 | $0.007 | ✅ Full |

**Single function = Best of all worlds!**
- ✅ All 109 gestures available
- ✅ Lowest cost (93% reduction)
- ✅ Full AI control
- ✅ Easy to extend

---

## Summary

**This approach gives you**:
✅ **93% cost reduction** ($0.09 → $0.007 per conversation)
✅ **Full gesture library** (all 109 gestures available)
✅ **True AI control** (AI picks gestures by name)
✅ **Easy extensibility** (add gestures to library, not function defs)
✅ **Best of all approaches** (cheaper than curated, full access to library)

**Implementation time**: 30 minutes
**Annual savings**: ~$100 (on 100 conversations/month)

This is the optimal solution - you get everything without compromise!
