# Actions Not Executing - Root Cause & Fix

**Date**: 2025-11-20
**Issue**: Nevil stopped performing gestures and movements - only talking

## Problem Analysis

### Symptoms
```
AI Response: "Dawg, I'm here, loud and clear. What's on your mind?"
(No actions, no gestures, no movements)
```

### Root Cause

**Conflicting instructions in system prompt**

The system prompt contained JSON formatting instructions that conflicted with the Realtime API's function calling system:

```
## Response with Json Format, eg:
{"actions": ["start_engine", "honk", "wave_hands"], "answer": "Hello, I am Nevil..."}
```

**The Problem**:
1. Realtime API was configured with 106+ gesture functions available
2. But the prompt told the AI to respond in JSON format
3. OpenAI Realtime API doesn't reliably follow JSON formatting in prompts
4. The AI chose to follow the JSON instruction (plain text) instead of calling functions
5. Result: No function calls = No actions = No gestures

## The Fix

**File**: `nodes/ai_cognition_realtime/.messages` (line 56)

### Removed
```
## Response with Json Format, eg: {\"actions\": [...], \"answer\": \"...\"}
## Another examples {\"answer\": \"...\", \"actions\": [...], \"mood\": \"...\"}
```

### Added
```
## CRITICAL: USE YOUR AVAILABLE FUNCTIONS!
You have 100+ gesture functions available - USE THEM FREQUENTLY!
Create long, expressive sequences (5-12 gestures) that match your speech.
Call multiple gesture functions in sequence to create elaborate performances.
Vary speeds (:slow, :med, :fast) within each sequence.
Every response should include gestures unless you're being very sleepy or brooding.
```

## How Function Calling Works

### System Architecture

1. **Gesture Library Loading** (ai_node22.py:98-150)
   - Loads 106 gestures from extended_gestures.py
   - Creates function definitions for each gesture
   - Adds movement functions (forward, backward, turn_left, turn_right)
   - Adds sound functions (play_sound, honk, rev_engine)
   - Adds camera function (take_snapshot)
   - Adds memory functions (remember, recall)

2. **Function Registration** (ai_node22.py:321)
   - `tools=self.gesture_definitions` sent to Realtime API
   - `tool_choice="auto"` allows AI to use functions freely

3. **Event Handling** (ai_node22.py:368-370)
   - `response.output_item.added` - Function call detected
   - `response.function_call_arguments.delta` - Arguments streaming
   - `response.function_call_arguments.done` - Execute function

### Available Functions

**Gestures (106)**: look_left_then_right, happy_spin, ponder, greet_wave, celebrate_big, etc.
**Movements (5)**: move_forward, move_backward, turn_left, turn_right, stop_movement
**Sounds (14)**: play_sound, honk, rev_engine (various effects)
**Camera (1)**: take_snapshot
**Memory (2)**: remember, recall

## Expected Behavior After Fix

### Before (Plain Text Only)
```
User: "Hey Nevil!"
AI: "Dawg, I'm here, loud and clear. What's on your mind?"
Actions: NONE
```

### After (Function Calling)
```
User: "Hey Nevil!"
AI: "Dawg, I'm here, loud and clear! What's on your mind?"
Functions Called:
  - greet_wave(speed="med")
  - happy_spin(speed="fast")
  - look_left_then_right(speed="med")
  - show_curiosity(speed="slow")
Actions Executed: 4 gestures performed
```

## Testing

Try these commands to verify actions are working:

1. **Greeting**:
   - User: "Hey Nevil!"
   - Expected: Greet gestures (wave, spin, look around)

2. **Movement Command**:
   - User: "Move forward 30cm"
   - Expected: move_forward function called, robot moves

3. **Celebration**:
   - User: "Great job!"
   - Expected: Celebration gestures (jump_excited, cheer_wave, celebrate_big)

4. **Investigation**:
   - User: "What's that?"
   - Expected: Observational gestures (curious_peek, inspect_floor, look_left_then_right)

## Monitoring Function Calls

Check logs for function call activity:

```bash
# Watch for function calls
sudo journalctl -u nevil -f | grep -i "function\|gesture\|output_item"

# Should see:
# - output_item.added events when functions are called
# - function_call_arguments events with parameters
# - Action execution confirmations
```

## Troubleshooting

### If Actions Still Don't Work

1. **Check Logs for Function Events**:
   ```bash
   sudo journalctl -u nevil -n 100 | grep "output_item.added"
   ```

   - If you see output_item events: Functions are being called, check execution
   - If no output_item events: AI still not using functions

2. **Verify Tools Configuration**:
   ```bash
   sudo journalctl -u nevil -n 500 | grep "Loaded.*gestures"
   ```

   Should show: "Loaded 106 gestures + movement + camera + sounds + memory"

3. **Check Session Config**:
   Look for session.update event in logs showing tools array is populated

### If AI Uses Functions But Actions Don't Execute

Problem is in the execution pipeline (navigation node), not the AI cognition.

Check navigation logs:
```bash
sudo journalctl -u nevil -f | grep navigation
```

## Files Modified

1. **nodes/ai_cognition_realtime/.messages** (line 56)
   - Removed JSON formatting instructions
   - Added explicit function usage directives
   - Emphasized creating long gesture sequences

## Benefits of Function Calling

1. **Reliability**: Functions are always properly structured (no JSON parsing errors)
2. **Discoverability**: AI can see all available functions and their parameters
3. **Type Safety**: Parameters are validated by the API
4. **Flexibility**: Easy to add new gestures without changing prompt format
5. **Natural Integration**: Works seamlessly with Realtime API streaming

## Architecture Notes

The system uses a hybrid approach:
- **Text Response**: Streamed via `response.audio_transcript.delta` events
- **Function Calls**: Processed via `response.output_item.added` events
- **Action Execution**: Functions → Navigation Node → Robot Hardware

This separation allows:
- Speech and movement to happen simultaneously
- Multiple gestures in sequence
- Mood changes, camera snapshots, and memory operations
- All coordinated through the function calling system

## References

- OpenAI Realtime API Function Calling: https://platform.openai.com/docs/guides/function-calling
- Extended Gestures Library: nodes/navigation/extended_gestures.py
- AI Cognition Node: nodes/ai_cognition_realtime/ai_node22.py
- Realtime Connection Manager: nevil_framework/realtime/realtime_connection_manager.py
