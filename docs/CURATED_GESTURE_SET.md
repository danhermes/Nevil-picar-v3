# Curated Gesture Set - AI-Driven Economical Expressiveness

## The Right Balance

**Problem with 109 gestures**: Too expensive ($0.09/conversation)
**Problem with categories**: Programmatic, not AI-driven
**Solution**: Curate 15-20 BEST gestures, let AI choose directly

---

## Philosophy

Instead of giving AI 109 options (expensive) or categories (programmatic), give AI a **carefully selected set of the most expressive gestures**.

Like a painter with 20 colors instead of 200:
- Still has full creative control
- Each color is purposefully chosen
- Can express anything needed
- More focused, less overwhelming

---

## The Curated Set (17 Core Gestures)

### Emotions (6 gestures)
```python
{
    "name": "happy_spin",
    "description": "Spin with joy - use when excited, happy, or celebrating",
    "speed": "fast"
},
{
    "name": "excited_bounce",
    "description": "Bounce with excitement - use for high energy, enthusiasm",
    "speed": "fast"
},
{
    "name": "sad_droop",
    "description": "Droop sadly - use for sadness, sympathy, disappointment",
    "speed": "slow"
},
{
    "name": "curious_tilt",
    "description": "Tilt head curiously - use when interested, questioning, wondering",
    "speed": "med"
},
{
    "name": "thinking_pose",
    "description": "Strike thinking pose - use when pondering, considering, processing",
    "speed": "slow"
},
{
    "name": "confident_nod",
    "description": "Nod confidently - use when certain, assured, affirming",
    "speed": "med"
}
```

### Communication (6 gestures)
```python
{
    "name": "wave",
    "description": "Wave greeting - use for hello, goodbye, getting attention",
    "speed": "med"
},
{
    "name": "emphatic_nod",
    "description": "Nod emphatically - use for strong agreement, 'yes!', affirmation",
    "speed": "fast"
},
{
    "name": "shake_head",
    "description": "Shake head - use for disagreement, 'no', negation",
    "speed": "med"
},
{
    "name": "welcoming_gesture",
    "description": "Open welcoming gesture - use to invite, welcome, show openness",
    "speed": "med"
},
{
    "name": "point_ahead",
    "description": "Point forward - use to indicate direction, focus attention",
    "speed": "med"
},
{
    "name": "look_around",
    "description": "Look around slowly - use to scan, observe, show awareness",
    "speed": "slow"
}
```

### Reactions (3 gestures)
```python
{
    "name": "surprised_lean",
    "description": "Lean back in surprise - use for shock, unexpected news",
    "speed": "fast"
},
{
    "name": "playful_bounce",
    "description": "Bounce playfully - use for fun, games, lightheartedness",
    "speed": "fast"
},
{
    "name": "sympathetic_lean",
    "description": "Lean forward sympathetically - use to show care, empathy, concern",
    "speed": "slow"
}
```

### Utility (2 gestures)
```python
{
    "name": "neutral_stance",
    "description": "Return to neutral stance - use to reset, pause, neutral position",
    "speed": "slow"
},
{
    "name": "settle_stance",
    "description": "Settle into stance - use after movement, to conclude gesture",
    "speed": "slow"
}
```

---

## Implementation

### Update ai_cognition_realtime_node.py

```python
def _load_gesture_library(self):
    """Load curated set of most expressive gestures for AI-driven selection"""

    # Curated set: 17 gestures chosen for maximum expressiveness
    # AI chooses directly from this set (not programmatic categories)

    self.gesture_definitions = [
        # === EMOTIONS ===
        {
            "type": "function",
            "name": "happy_spin",
            "description": "Spin with joy. Use when excited, happy, celebrating, or expressing delight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med", "fast"],
                        "description": "Speed: slow=gentle joy, med=happy, fast=ecstatic",
                        "default": "fast"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "excited_bounce",
            "description": "Bounce with excitement. Use for high energy, enthusiasm, 'yes!', or anticipation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["med", "fast"],
                        "description": "Speed: med=enthusiastic, fast=super excited",
                        "default": "fast"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "sad_droop",
            "description": "Droop sadly. Use for sadness, sympathy, disappointment, or compassion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for genuine emotion",
                        "default": "slow"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "curious_tilt",
            "description": "Tilt head curiously. Use when interested, questioning, wondering, or intrigued.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med"],
                        "description": "Speed: slow=deep thought, med=quick curiosity",
                        "default": "med"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "thinking_pose",
            "description": "Strike thinking pose. Use when pondering, considering, processing information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for thoughtful consideration",
                        "default": "slow"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "confident_nod",
            "description": "Nod confidently. Use when certain, assured, affirming, or showing confidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["med", "fast"],
                        "description": "Speed: med=confident, fast=very sure",
                        "default": "med"
                    }
                }
            }
        },

        # === COMMUNICATION ===
        {
            "type": "function",
            "name": "wave",
            "description": "Wave greeting. Use for hello, goodbye, getting attention, or acknowledging someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med", "fast"],
                        "description": "Speed: slow=gentle bye, med=friendly hello, fast=excited greeting",
                        "default": "med"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "emphatic_nod",
            "description": "Nod emphatically. Use for strong agreement, 'yes!', 'exactly!', or emphatic affirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["fast"],
                        "description": "Always fast for emphasis",
                        "default": "fast"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "shake_head",
            "description": "Shake head. Use for disagreement, 'no', negation, or disapproval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med", "fast"],
                        "description": "Speed: slow=gentle no, med=disagreement, fast=strong no",
                        "default": "med"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "welcoming_gesture",
            "description": "Open welcoming gesture. Use to invite, welcome, show openness, or encourage approach.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow", "med"],
                        "description": "Speed: slow=gentle invite, med=friendly welcome",
                        "default": "med"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "point_ahead",
            "description": "Point forward. Use to indicate direction, focus attention, or show the way.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["med", "fast"],
                        "description": "Speed: med=indicate, fast=urgent pointing",
                        "default": "med"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "look_around",
            "description": "Look around slowly. Use to scan environment, observe, show awareness, or search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for deliberate observation",
                        "default": "slow"
                    }
                }
            }
        },

        # === REACTIONS ===
        {
            "type": "function",
            "name": "surprised_lean",
            "description": "Lean back in surprise. Use for shock, unexpected news, or 'whoa!'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["fast"],
                        "description": "Always fast for genuine surprise",
                        "default": "fast"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "playful_bounce",
            "description": "Bounce playfully. Use for fun, games, lightheartedness, or playful mood.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["med", "fast"],
                        "description": "Speed: med=playful, fast=very fun",
                        "default": "fast"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "sympathetic_lean",
            "description": "Lean forward sympathetically. Use to show care, empathy, concern, or listening.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for genuine empathy",
                        "default": "slow"
                    }
                }
            }
        },

        # === UTILITY ===
        {
            "type": "function",
            "name": "neutral_stance",
            "description": "Return to neutral stance. Use to reset position, pause, or neutral baseline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for smooth reset",
                        "default": "slow"
                    }
                }
            }
        },

        {
            "type": "function",
            "name": "settle_stance",
            "description": "Settle into stance. Use after movement, to conclude gesture, or finish interaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "string",
                        "enum": ["slow"],
                        "description": "Always slow for smooth settling",
                        "default": "slow"
                    }
                }
            }
        },

        # === CRITICAL NON-GESTURE FUNCTIONS ===
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
            "description": "Recall memories using semantic search",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
    ]

    self.logger.info(f"Loaded {len(self.gesture_definitions)} curated gestures for AI-driven expressiveness (80% cost reduction)")
```

### Update Function Handler

```python
def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute function - gestures are called directly by AI"""

    # List of gesture function names
    GESTURE_FUNCTIONS = [
        "happy_spin", "excited_bounce", "sad_droop", "curious_tilt", "thinking_pose",
        "confident_nod", "wave", "emphatic_nod", "shake_head", "welcoming_gesture",
        "point_ahead", "look_around", "surprised_lean", "playful_bounce",
        "sympathetic_lean", "neutral_stance", "settle_stance"
    ]

    # Handle gesture functions
    if function_name in GESTURE_FUNCTIONS:
        speed = args.get('speed', 'med')
        action = f"{function_name}:{speed}"

        self.logger.info(f"🤖 AI chose gesture: {action}")

        robot_action_data = {
            "actions": [action],
            "source_text": "ai_direct_choice",
            "mood": "neutral",
            "priority": 100,
            "timestamp": time.time()
        }

        if self.publish("robot_action", robot_action_data):
            return {"status": "success", "action": action}
        else:
            return {"status": "error", "message": "Failed to publish gesture"}

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
```

---

## Cost Analysis

### Before (109 gestures)
```
109 individual gestures
~165 tokens each × 109 = 17,985 tokens
$0.09 per 10-minute conversation
```

### After (17 gestures)
```
17 curated gestures
~165 tokens each × 17 = 2,805 tokens
$0.015 per 10-minute conversation
```

### Savings
- **Token reduction**: 84% (17,985 → 2,805)
- **Cost reduction**: 83% ($0.09 → $0.015)
- **Monthly savings**: ~$7.50 (on 100 conversations)
- **Annual savings**: ~$90

---

## Why These 17 Gestures?

### Coverage Analysis
- **6 emotions** = full emotional range (happy, sad, excited, curious, thoughtful, confident)
- **6 communication** = all social needs (greet, affirm, deny, welcome, direct, observe)
- **3 reactions** = spontaneous responses (surprise, playfulness, empathy)
- **2 utility** = technical needs (reset, conclude)

### What We Removed (92 gestures)
- **Redundant variants**: "wave:slow", "wave:med", "wave:fast" → just "wave" with speed parameter
- **Rarely used**: Complex multi-step gestures that AI never calls
- **Niche behaviors**: Very specific gestures for rare situations
- **Overlapping**: Multiple gestures that express the same thing

---

## AI Intelligence Preserved

### Example: User Shares Good News

**AI Reasoning**:
```
User: "I got the job!"
AI thinks:
  - User is excited (emotion detected)
  - This deserves high-energy response
  - I should match their energy
  - Options: happy_spin, excited_bounce, playful_bounce
  - Best choice: excited_bounce (direct excitement expression)
  - Speed: fast (high energy)

AI calls: excited_bounce(speed="fast")
```

**No programmatic mapping** - AI made every decision:
- WHICH gesture (excited_bounce not happy_spin)
- WHEN to use it (immediately on hearing news)
- WHY it makes sense (match user's energy)
- HOW energetic (fast speed)

---

## Benefits vs Categories

### ❌ Categories (Programmatic)
```python
express_emotion(emotion="happy", intensity="high")
→ Code picks random from [spin, bounce, wiggle]
→ AI doesn't choose actual gesture
→ Programmatic randomness
```

### ✅ Curated Set (AI-Driven)
```python
excited_bounce(speed="fast")
→ AI directly chose this specific gesture
→ AI chose the speed
→ AI timed it with conversation
→ True AI intelligence
```

---

## Migration Guide

1. **Backup**:
```bash
cp nodes/ai_cognition_realtime/ai_cognition_realtime_node.py{,.backup}
```

2. **Replace `_load_gesture_library()`** with curated version

3. **Update `_execute_function()`** to handle gestures directly

4. **Restart**:
```bash
sudo systemctl restart nevil
```

5. **Test expressiveness**:
   - Talk about happy things → should see happy_spin, excited_bounce
   - Ask questions → should see curious_tilt, thinking_pose
   - Say goodbye → should see wave

6. **Monitor costs**:
```bash
grep "session.update" logs/ai_cognition_realtime.log
# Should see ~2,800 tokens instead of ~18,000
```

---

## Extensibility

**Want to add more gestures later?**

Just add to the curated set:
```python
{
    "name": "dance_move",
    "description": "Dance playfully. Use when music playing or celebrating.",
    "parameters": {...}
}
```

Cost per additional gesture: ~165 tokens = ~$0.0008/conversation

Add 10 more gestures = still only $0.02/conversation (vs $0.09 with old system)

---

## Summary

**This curated approach gives you**:
✅ **83% cost reduction** ($0.09 → $0.015 per conversation)
✅ **True AI control** (AI chooses specific gestures, not categories)
✅ **Full expressiveness** (17 carefully chosen gestures cover all needs)
✅ **Easy to extend** (add gestures without category complexity)
✅ **Better than categories** (no programmatic mapping)
✅ **Better than full set** (dramatically cheaper, equally expressive)

**The sweet spot**: Small enough to be economical, large enough to be expressive, AI-driven enough to be intelligent.
