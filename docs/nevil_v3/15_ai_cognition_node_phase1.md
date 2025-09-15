# Nevil v3.0 AI Cognition Node - Phase 1

## Overview

The AI Cognition Node is the intelligent brain of Nevil v3.0, processing voice commands and generating natural responses using OpenAI's Assistants API. It currently works with thread-based conversation management but needs JSON parsing to properly extract and route responses.

**Current Issue**: AI responses like `{"answer": "Hello!", "actions": ["wave"], "mood": "happy"}` are sent as raw JSON to speech synthesis instead of extracting just "Hello!" for speaking.

**Phase 1 Goal**: Parse JSON to extract clean answer text for speech while routing actions and mood to navigation node.

### Current Flow
```
Voice Command → AI Cognition → OpenAI Assistants API → Raw JSON Text → Speech Synthesis
```

### Target Flow
```
Voice Command → AI Cognition → OpenAI Assistants API → JSON Response
                                                        ↓
                    Answer → Speech Synthesis    Actions → Navigation    Mood → Navigation
```

## Feature Sets

### 1. OpenAI Assistant Response (✅ Working)

Thread-based conversation management using OpenAI Assistants API:
- Persistent thread creation and management
- Assistant ID configuration from environment
- Response retrieval and basic processing
- Error handling and fallback to echo mode

**Configuration**: `OPENAI_API_KEY`, `OPENAI_ASSISTANT_ID` from environment

### 2. JSON Parsing (🔄 Needs Implementation)

Parse assistant responses in nevil_prompt.txt format:
```json
{
    "answer": "Let me check that out!",
    "actions": ["keep_think", "forward 30", "left"],
    "mood": "curious"
}
```

**Answer Field**: Clean text for speech synthesis (removes JSON structure)
**Actions Field**: Array of movement/expression commands for navigation
**Mood Field**: Behavioral state for navigation node adaptation

### 3. Message Routing to Speech Synthesis Node (🔄 Needs Enhancement)

**Current**: Sends raw JSON text to `text_response` topic
**Target**: Send only extracted "answer" field for clean speech

```yaml
# Existing topic - needs clean answer extraction
publishes:
  - topic: "text_response"
    message_type: "TextResponse"
    schema:
      text: "Hello there!"  # Clean answer, not raw JSON
      voice: "onyx"
      priority: 100
```

### 4. Message Routing to Navigation Node (🔄 New Implementation)

**Actions**: Send movement/expression commands to navigation
```yaml
publishes:
  - topic: "robot_action"
    message_type: "RobotAction"
    schema:
      actions: ["forward 30", "wave_hands"]
      source_text: "move forward and wave"
      mood: "playful"
      priority: 100
```

**Mood**: Send behavioral state changes
```yaml
publishes:
  - topic: "mood_change"
    message_type: "MoodChange"
    schema:
      mood: "curious"
      source: "ai_response"
      timestamp: 1693872000.0
```


## JSON Response Format

AI responses follow nevil_prompt.txt specification:
```json
{
    "answer": "Let me check that out!",
    "actions": ["keep_think", "forward 30", "left"],
    "mood": "curious"
}
```

### Phase 1 Implementation Needed

```python
def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
    """Parse AI response to extract text, actions, and mood"""
    try:
        # Try to parse as JSON
        response_data = json.loads(response_text)

        return {
            'answer': response_data.get('answer', ''),
            'actions': response_data.get('actions', []),
            'mood': response_data.get('mood', 'neutral')
        }

    except json.JSONDecodeError:
        # Fallback for non-JSON responses
        return {
            'answer': response_text,
            'actions': [],
            'mood': 'neutral'
        }

def _publish_parsed_response(self, parsed_response: Dict[str, Any], original_command: Dict):
    """Publish text, actions, and mood separately"""

    # 1. Publish text response (existing)
    if parsed_response['answer']:
        self.publish("text_response", {
            "text": parsed_response['answer'],
            "voice": "onyx",
            "priority": 100,
            "timestamp": time.time()
        })

    # 2. Publish robot actions (NEW)
    if parsed_response['actions']:
        self.publish("robot_action", {
            "actions": parsed_response['actions'],
            "source_text": original_command.get('text', ''),
            "mood": parsed_response['mood'],
            "priority": 100,
            "timestamp": time.time()
        })

    # 3. Publish mood change (NEW)
    if parsed_response['mood'] != 'neutral':
        self.publish("mood_change", {
            "mood": parsed_response['mood'],
            "source": "ai_response",
            "timestamp": time.time()
        })
```

### Message Topics

Add to `.messages` file:

```yaml
# nodes/ai_cognition/.messages

publishes:
  - topic: "text_response"
    message_type: "TextResponse"
    description: "AI-generated text responses using OpenAI GPT"
    # ... existing schema

  - topic: "robot_action"  # NEW
    message_type: "RobotAction"
    description: "Movement and expression commands from AI"
    schema:
      actions:
        type: "array"
        required: true
        description: "List of action commands to execute"
      source_text:
        type: "string"
        required: true
        description: "Original user command"
      mood:
        type: "string"
        required: false
        description: "Current AI mood affecting actions"
      priority:
        type: "integer"
        default: 100

  - topic: "mood_change"  # NEW
    message_type: "MoodChange"
    description: "AI mood changes for behavioral adaptation"
    schema:
      mood:
        type: "string"
        required: true
        enum: ["playful", "brooding", "curious", "melancholic", "zippy", "lonely", "mischievous", "sleepy"]
      source:
        type: "string"
        required: true
        description: "What triggered the mood change"
```


## Actions & Mood

### Actions (from v1.0 action_helper.py)
- **Movement**: `forward [dist] [speed]`, `backward`, `left`, `right`, `stop`
- **Expression**: `shake_head`, `nod`, `wave_hands`, `think`, `celebrate`
- **Sound**: `honk`, `start_engine`

### Mood States
- `playful`, `brooding`, `curious`, `melancholic`, `zippy`, `lonely`, `mischievous`, `sleepy`
- Influences movement speed, action timing, expression selection

## Configuration

**Environment**: `OPENAI_API_KEY`, `OPENAI_ASSISTANT_ID`
**Model**: gpt-3.5-turbo, 150 tokens, 0.7 temperature
**Confidence**: 0.3 threshold

## Error Handling

- **JSON errors**: Fall back to text-only
- **API failures**: Use echo mode
- **Missing fields**: Default values
- **Thread errors**: Reset and retry

## Phase 1 Priority

1. ✅ OpenAI Assistants API integration
2. 🔄 JSON response parsing enhancement
3. 🔄 Robot action message publishing
4. 🔄 Mood change message publishing