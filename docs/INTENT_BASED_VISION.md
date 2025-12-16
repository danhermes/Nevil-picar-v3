# Intent-Based Vision System

## Problem with Function Calling

**The Realtime API function registry doesn't work for vision** because:
1. The GPT-4o Realtime model knows the Realtime API doesn't support images natively
2. Even though our hybrid system (Realtime + Vision API) DOES work, the model refuses to call `take_snapshot()`
3. The model will say "I can't see" or "I don't have visual capabilities" despite having them

## Solution: Intent Detection (No Function Calling)

**Instead of relying on the model to call functions, we detect user intent and trigger actions ourselves.**

### Implementation (ai_node22.py:1049-1086)

```python
# Detect vision-related questions
vision_keywords = [
    "what do you see", "what can you can", "what are you looking at",
    "what's in front", "look at", "describe what you see",
    "tell me what you see", "what do you observe", "what's around you",
    "look around", "take a look", "show me what you see", "check your camera"
]

if any(keyword in text_lower for keyword in vision_keywords):
    # Trigger camera DIRECTLY (bypass function calling)
    publish("snap_pic", ...)

    # Wait for vision data
    return  # Don't process further until vision arrives
```

### Flow

```
User: "What do you see?"
  ↓
[Intent Detection]
  ↓ Keyword match: "what do you see"
  ↓ Add question to conversation
  ↓ Trigger camera (direct publish to snap_pic)
  ↓ Return early (wait for vision)
  ↓
[Camera Node]
  ↓ Captures image
  ↓ Publishes visual_data
  ↓
[on_visual_data Handler]
  ↓ Calls GPT-4o Vision API
  ↓ Gets description: "A desk with laptop..."
  ↓ Injects: "[SYSTEM: Your camera shows: ...]"
  ↓ Triggers response.create
  ↓
[Nevil Responds]
  ✅ "I can see a desk with a laptop!"
```

## Key Differences from Function Calling

| Aspect | Function Calling ❌ | Intent Detection ✅ |
|--------|-------------------|-------------------|
| **Reliability** | Model refuses to call | Always triggers |
| **Control** | Relies on model decision | We control when to trigger |
| **Latency** | Model thinks → calls → triggers | Direct trigger |
| **Debugging** | Opaque (why didn't it call?) | Clear (keyword matched) |

## Vision Keywords

Current keywords that trigger camera:
- "what do you see"
- "what can you see"
- "what are you looking at"
- "what's in front"
- "look at"
- "describe what you see"
- "tell me what you see"
- "what do you observe"
- "what's around you"
- "look around"
- "take a look"
- "show me what you see"
- "check your camera"

### Adding More Keywords

Edit `ai_node22.py` line 1058:

```python
vision_keywords = [
    # ... existing keywords ...
    "what's there",           # Add new triggers
    "take a picture",
    "use your eyes"
]
```

## Vision Context Injection

When vision data arrives, it's injected as:

```
[SYSTEM: Your camera is showing you this view: {description}]
```

This makes it clear to Nevil:
- It's HIS camera
- The system is providing him visual data
- He should respond based on what he's being shown

## Testing

### Test 1: Basic Vision Query
```
User: "What do you see?"
Expected Log:
  🎥 VISION INTENT detected - bypassing function calling, triggering camera directly
  ⏸️ Waiting for vision data before responding...
  📸 Received visual data: capture_xyz
  🔍 Analyzing image with gpt-4o...
  👁️ Vision analysis: [description]
  ✅ Vision context provided, triggering response to user's question
```

### Test 2: Alternative Phrasing
```
User: "Look around and tell me what you observe"
Expected: Same flow (keyword "look around" triggers camera)
```

### Test 3: No Vision Intent
```
User: "What's your favorite color?"
Expected: No camera trigger, normal conversation response
```

## Fallbacks

### If Camera Fails
- Error logged but Nevil still responds
- Response will be without visual context
- Better than crashing or refusing to respond

### If Vision API Fails
- Error logged with retry count
- After 5+ errors, warning issued
- Nevil continues operating (graceful degradation)

## Statistics Tracking

```python
stats = ai_node.get_stats()
# vision_call_count: Total vision API calls
# vision_error_count: Failed vision calls
# vision_enabled: True if API key configured
```

## Cost Impact

**Per vision query**: ~$0.005 (using low detail)
**Trigger method**: Only when user asks (intent detection)
**Estimated usage**: 10-20 queries/hour = $0.05-0.10/hour

## Configuration

### Disable Intent Detection

To only use conversation (no automatic vision):

```python
# Comment out vision intent detection block
# if any(keyword in text_lower for keyword in vision_keywords):
#     ...
```

### Adjust Vision Model

```bash
export NEVIL_VISION_MODEL=gpt-4o        # Default (recommended)
export NEVIL_VISION_MODEL=gpt-4-turbo   # Alternative
```

### Adjust Vision Detail Level

In `ai_node22.py` line 1211:

```python
"detail": "low"   # Current: $0.005/image
# "detail": "high"  # Alternative: $0.055/image (11x more expensive!)
```

## Why This Works

**Without intent detection**:
- User: "What do you see?"
- Model thinks: "I can't see (Realtime API doesn't support images)"
- Model says: "I'm afraid I can't provide visual descriptions"
- ❌ User frustrated

**With intent detection**:
- User: "What do you see?"
- System detects: Keyword match → trigger camera
- Camera captures → Vision API analyzes → Description injected
- Model sees: "[SYSTEM: Your camera shows: A desk with laptop...]"
- Model says: "I can see a desk with a laptop!"
- ✅ Vision works!

## Future Enhancements

1. **Context-aware triggering**: Don't trigger on "see" in "see you later"
2. **Periodic autonomous vision**: Randomly trigger camera during idle time
3. **Visual memory**: Cache recent vision descriptions
4. **Multi-shot vision**: Take multiple angles and combine descriptions

## Related Files

- `ai_node22.py:1049-1086` - Vision intent detection
- `ai_node22.py:1172-1280` - Vision data handler
- `/docs/VISION_INTEGRATION.md` - Full vision architecture
- `/docs/VISION_FIX_SUMMARY.md` - Troubleshooting guide
