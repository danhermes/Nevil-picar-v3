# Vision Integration with OpenAI Realtime API

## Overview

The AI Cognition Realtime Node integrates OpenAI's Vision API (GPT-4o) with the Realtime API to enable Nevil to see and understand his environment through his camera.

## Architecture

### Hybrid Approach

Since the OpenAI Realtime API doesn't support image inputs directly, we use a hybrid approach:

1. **Vision Analysis**: Chat Completions API (GPT-4o) with vision capabilities
2. **Conversation**: Realtime API for low-latency voice interaction
3. **Context Injection**: Vision descriptions are injected into the Realtime conversation as text

## Workflow

```
Camera → visual_data → on_visual_data() → Vision API → Description → Realtime Context → Response
```

### Detailed Steps

1. **Camera Capture**: Camera node publishes `visual_data` message with base64-encoded image
2. **Image Receipt**: `on_visual_data()` receives image and stores it
3. **Vision Analysis**:
   - Calls Chat Completions API with vision prompt
   - Model: `gpt-4o` (or configured via `NEVIL_VISION_MODEL`)
   - Detail level: `low` (65 tokens vs 1105 for high - cost optimization)
   - Max tokens: 200
   - Timeout: 10 seconds
4. **Context Injection**:
   - Vision description is added to Realtime conversation as user message
   - Format: `[VISUAL CONTEXT - What I'm seeing through my camera right now: {description}]`
   - Follow-up prompt: `"What do you see?"` to trigger natural commentary
5. **Response Generation**: Realtime API generates spoken response based on visual context

## Configuration

### Environment Variables

```bash
# Vision model (default: gpt-4o)
NEVIL_VISION_MODEL=gpt-4o

# Realtime model
NEVIL_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

# API key (required for both vision and realtime)
OPENAI_API_KEY=sk-...
```

### Vision Prompt

The vision prompt instructs GPT-4o to:
- Describe the scene in 2-3 concise sentences
- Be specific about objects, people, colors, spatial relationships
- Use natural, conversational language
- Avoid preambles or meta-commentary

## Response Flow Management

### Queuing System

To prevent race conditions, the system implements a queuing mechanism:

1. **Response in Progress**: If Realtime API is generating a response, new vision images are queued
2. **Deferred Processing**: Queued images are processed after `response.done` event
3. **Flag Management**: `response_in_progress` flag prevents overlapping requests

### Code Example

```python
# Check if response in progress
if self.response_in_progress and not force_process:
    # Queue image for later processing
    self.pending_vision_image = {
        "data": image_data,
        "capture_id": capture_id,
        "timestamp": timestamp
    }
    return

# Process queued images after response completes
if self.pending_vision_image:
    # Process with force_process=True to override queue check
    self.on_visual_data(queued_message, force_process=True)
```

## Cost Optimization

### Image Detail Level

- **Low detail**: 65 tokens per image (~$0.0033 per image with GPT-4o)
- **High detail**: 1105 tokens per image (~$0.055 per image)
- **Savings**: 94% cost reduction by using low detail

### Token Limits

- Max tokens: 200 (sufficient for 2-3 sentence descriptions)
- Typical response: 50-100 tokens
- Cost per description: ~$0.005 (low detail + response)

## Error Handling

### Graceful Degradation

1. **Vision Disabled**: If no `OPENAI_API_KEY`, vision is disabled but Realtime API continues
2. **API Errors**: Vision errors are logged but don't crash the node
3. **Timeout**: 10-second timeout prevents hanging on slow API calls
4. **Error Tracking**: Counts errors and warns after 5+ consecutive failures

### Statistics

The node tracks:
- `vision_call_count`: Total successful vision API calls
- `vision_error_count`: Total failed vision API calls
- `vision_enabled`: Whether vision client is initialized

## Testing

### Manual Test

1. Start the AI node: `python nodes/ai_cognition_realtime/ai_node22.py`
2. Trigger camera: Ask "What do you see?" or call `take_snapshot` function
3. Check logs for:
   ```
   📸 Received visual data: capture_xyz
   🔍 Analyzing image with gpt-4o...
   👁️ Vision analysis: [description]
   ✅ Vision analysis injected with context, triggering response
   ```

### Integration Points

- **Subscribe**: `visual_data` topic (from camera node)
- **Publish**: `snap_pic` topic (requests camera snapshot)
- **Function**: `take_snapshot()` - AI can trigger camera via function call

## Limitations

1. **No Native Vision in Realtime API**: Must use separate Chat Completions call
2. **Latency**: Vision analysis adds ~1-2 seconds to response time
3. **Context Window**: Vision descriptions use conversation context tokens
4. **Rate Limits**: Subject to OpenAI API rate limits (separate from Realtime)

## Future Improvements

1. **Caching**: Cache vision descriptions for recently seen scenes
2. **Adaptive Detail**: Use high detail for specific requests, low for background awareness
3. **Multi-modal Streaming**: Wait for OpenAI to add native vision to Realtime API
4. **Local Vision**: Consider local vision models (CLIP, etc.) for faster processing

## Troubleshooting

### Vision Not Working

1. Check `OPENAI_API_KEY` is set
2. Verify API key has vision access (GPT-4o)
3. Check logs for `vision_error_count` and error messages
4. Confirm camera is publishing to `visual_data` topic

### High Costs

1. Verify `detail: "low"` is set (line 1173 in ai_node22.py)
2. Monitor `vision_call_count` to track usage
3. Consider reducing camera snapshot frequency
4. Implement caching for repeated scenes

### Slow Response

1. Check vision API timeout setting (currently 10s)
2. Monitor network latency to OpenAI
3. Consider disabling vision for real-time critical interactions
4. Use `force_process=False` to queue images during responses
