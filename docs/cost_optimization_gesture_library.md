# Gesture Library Cost Optimization

## Problem
Currently sending 109 gesture functions (~15,000-20,000 tokens) in every session.update call.

## Solution: Context-Aware Function Loading

### Strategy 1: Core Functions Only (Recommended)
```python
# In ai_node22.py _load_gesture_library()

# Define core functions that are ALWAYS available (10-15 functions)
CORE_FUNCTIONS = [
    "move_forward", "move_backward", "turn_left", "turn_right", "stop_movement",
    "take_snapshot", "play_sound", "honk", "remember", "recall"
]

# Load ONLY core functions on session start
self.core_gesture_definitions = [
    defn for defn in self.gesture_definitions
    if defn['name'] in CORE_FUNCTIONS
]

# In session_config
tools=self.core_gesture_definitions,  # Only 10-15 functions instead of 109
```

**Savings**: ~85% reduction in function tokens (109 → 15 functions)

### Strategy 2: Lazy Loading on Demand
```python
# When user says "wave" or "dance", dynamically add those specific gestures
def _add_gesture_to_session(self, gesture_name: str):
    """Add a specific gesture to the current session"""
    gesture_def = next(
        (g for g in self.gesture_definitions if g['name'] == gesture_name),
        None
    )

    if gesture_def and self.connection_manager:
        # Add function to session
        self.connection_manager.send_sync({
            "type": "session.update",
            "session": {
                "tools": self.core_gesture_definitions + [gesture_def]
            }
        })
```

### Strategy 3: Category-Based Loading
```python
GESTURE_CATEGORIES = {
    "movement": ["move_forward", "move_backward", "turn_left", "turn_right"],
    "emotions": ["happy_spin", "sad_droop", "excited_bounce"],
    "sounds": ["honk", "rev_engine", "play_sound"],
    "camera": ["take_snapshot"],
    "memory": ["remember", "recall"]
}

# Load only "movement" + "sounds" + "camera" + "memory" by default
# Add "emotions" category only when context requires it
```

## Implementation

### File to Modify
- `nodes/ai_cognition_realtime/ai_cognition_realtime_node.py`
- Lines 98-290 (`_load_gesture_library()`)

### Changes
1. Replace `tools=self.gesture_definitions` with `tools=self.core_gesture_definitions`
2. Add dynamic function loading method
3. Add gesture usage tracking to optimize core set

## Expected Savings
- **Token reduction**: 85% (109 → 15 core functions)
- **Cost reduction**: 60-70% overall (functions are sent with EVERY message)
- **Latency improvement**: 200-400ms faster session.update calls
