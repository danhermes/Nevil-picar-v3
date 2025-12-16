# Hybrid Vision System - Technical Implementation

## Overview
Nevil now uses a **hybrid approach** for vision:
- **Realtime API** (voice/audio) - handles conversation, gestures, sounds
- **Chat Completions API** (vision) - analyzes camera images

## Why Hybrid?

### The Problem
OpenAI's Realtime API **does not support images**. Attempting to send images caused:
```
ERROR: Invalid value: 'image_url'. Supported values are: 'input_text' and 'input_audio'.
→ response_in_progress flag stuck
→ Nevil frozen, unresponsive
```

### The Solution
Use Chat Completions API (gpt-4o) for vision, inject results back into Realtime conversation.

## Architecture

```
USER: "Show me your artwork"
  ↓
REALTIME API: Nevil calls take_snapshot()
  ↓
CAMERA: Captures image → visual_data topic
  ↓
CHAT COMPLETIONS API: Analyzes image
  - Model: gpt-4o
  - Input: base64 image + prompt
  - Output: "I see a vibrant mix of artwork with bold colors and geometric shapes..."
  ↓
REALTIME API: Receives vision description as text
  - Injected as: "[Camera view: I see vibrant artwork...]"
  - Generates natural spoken response
  ↓
NEVIL: Speaks about what he "saw"
```

## Implementation Details

### 1. Vision Client Initialization
```python
# ai_node22.py:245-248
if api_key:
    self.openai_vision_client = OpenAI(api_key=api_key, max_retries=2)
    self.vision_model = os.getenv('NEVIL_VISION_MODEL', 'gpt-4o')
    self.logger.info(f"✅ Vision API initialized with model: {self.vision_model}")
```

### 2. Vision Processing (on_visual_data)
```python
# ai_node22.py:1115-1137
response = self.openai_vision_client.chat.completions.create(
    model=self.vision_model,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                        "detail": "low"  # Faster, cheaper
                    }
                }
            ]
        }
    ],
    max_tokens=150,
    temperature=0.7
)
```

### 3. Injection into Realtime Conversation
```python
# ai_node22.py:1147-1159
self.connection_manager.send_sync({
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [
            {
                "type": "input_text",
                "text": f"[Camera view: {vision_description}]"
            }
        ]
    }
})
```

## Configuration

### Environment Variables
```bash
# .env
OPENAI_API_KEY=sk-...          # Required for both APIs
NEVIL_VISION_MODEL=gpt-4o      # Optional, defaults to gpt-4o
```

### Vision Models
- `gpt-4o` (recommended) - Latest, best quality
- `gpt-4-vision-preview` - Alternative

## Cost Optimization

### Vision API Settings
```python
"detail": "low"          # Lower resolution, faster, cheaper
max_tokens=150           # Limit response length
temperature=0.7          # Consistent descriptions
```

### Processing Rules
- Only processes when `response_in_progress == False`
- Queues images during active responses
- Skips if vision client unavailable

## Error Handling

### Vision API Errors
```python
except Exception as vision_error:
    self.logger.error(f"Vision API error: {vision_error}")
    # Don't crash - just skip this image
```

### Realtime API Errors
- Previous bug: Images caused `invalid_value` error → stuck flag
- **Fixed**: Vision never sent to Realtime API

## Testing

### Test Flow
1. Say "Let me show you my artwork"
2. Nevil calls `take_snapshot()`
3. Camera captures → `visual_data` published
4. Vision API analyzes
5. Description injected: `[Camera view: ...]`
6. Nevil responds via Realtime voice

### Expected Logs
```
📸 Received visual data: snap_0_1234567890
🔍 Analyzing image with gpt-4o...
👁️ Vision analysis: I see a vibrant mix of artwork...
✅ Vision analysis injected into conversation: snap_0_1234567890
🤖 NEVIL RESPONSE (audio): "That's a beautiful piece! I love the bold colors..."
```

## Files Modified

### nodes/ai_cognition_realtime/ai_node22.py
- **Line 36**: Import OpenAI client
- **Line 86-87**: Vision client initialization
- **Line 245-248**: Vision client setup in initialize()
- **Line 1070-1182**: Complete rewrite of on_visual_data()

### nodes/ai_cognition_realtime/.messages
- **Line 56-67**: Camera usage instructions (from previous camera fix)

## Previous Fixes Applied

### 1. Camera Prompt Enhancement
Made camera usage as prominent as gestures in system prompt.

### 2. Image Ignore Bug
**Before this fix**, images were being ignored:
```python
if self.response_in_progress:
    return  # ❌ Image never added to conversation
```

**After both fixes:**
- Images sent to Vision API ✅
- Description injected as text ✅
- No freeze, no errors ✅

## Benefits

✅ **Vision works** - Nevil can see and describe what's in front of him  
✅ **No freezing** - Proper API usage, no error cascade  
✅ **Natural responses** - Speaks about what he sees via Realtime voice  
✅ **Cost optimized** - Low detail, limited tokens  
✅ **Robust** - Graceful error handling  
✅ **Configurable** - Model selection via env var  

## Limitations

⚠️ **Two-stage process** - Vision analysis takes ~1-2 seconds  
⚠️ **No real-time vision** - Can't stream video, only snapshots  
⚠️ **Text intermediary** - Vision description injected as text, not direct image  

## Future Enhancements

1. **Caching** - Remember recently seen images
2. **Multi-shot** - Analyze multiple camera angles
3. **Motion detection** - Only analyze when scene changes
4. **Context awareness** - Use conversation history in vision prompt

## Conclusion

The hybrid approach solves the freeze issue while enabling full vision capabilities. Nevil can now:
- Take photos with his camera ✅
- Analyze what he sees ✅
- Speak naturally about his observations ✅
- Continue normal voice conversation ✅

No more freezing! 🎉
