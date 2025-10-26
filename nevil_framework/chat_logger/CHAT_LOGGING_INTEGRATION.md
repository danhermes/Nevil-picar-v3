# Chat Logging Integration Guide

This guide shows how to integrate the chat logging system into Nevil's conversation pipeline.

## Overview

The chat logging system tracks 5 key steps in each conversation:
1. **request** - Audio capture started
2. **stt** - Speech-to-text conversion
3. **gpt** - AI response generation
4. **tts** - Text-to-speech synthesis
5. **response** - Audio playback completion

Each step records:
- Start/end datetime (ISO format)
- Duration in milliseconds
- Status (started/completed/failed)
- Input/output text
- Metadata (confidence, model, voice, etc.)
- Errors if any

## Database Schema

```sql
CREATE TABLE log_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,           -- Unique per conversation
    step TEXT NOT NULL,                      -- 'request', 'stt', 'gpt', 'tts', 'response'
    timestamp_start TEXT NOT NULL,           -- ISO datetime
    timestamp_end TEXT,                      -- ISO datetime
    duration_ms REAL,                        -- Duration in milliseconds
    status TEXT,                             -- 'started', 'completed', 'failed'
    input_text TEXT,                         -- Input for this step
    output_text TEXT,                        -- Output from this step
    metadata TEXT,                           -- JSON metadata
    error_text TEXT,                         -- Error message if failed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Integration Points

### 1. Speech Recognition Node
**File**: `nodes/speech_recognition/speech_recognition_node.py`

#### Track REQUEST + STT

```python
from nevil_framework.chat_logger import get_chat_logger

class SpeechRecognitionNode(NevilNode):
    def __init__(self):
        super().__init__("speech_recognition")
        self.chat_logger = get_chat_logger()
        # ... existing init code ...

    def _process_audio_discrete(self, audio):
        """Discrete audio processing with logging"""
        # Generate conversation ID for this interaction
        conversation_id = self.chat_logger.generate_conversation_id()

        try:
            # STEP 1: Log REQUEST (audio capture)
            with self.chat_logger.log_step(conversation_id, "request",
                                          metadata={"source": "microphone"}) as req_log:
                self.logger.info(f"🎙️  Starting conversation: {conversation_id}")

            # STEP 2: Log STT (speech-to-text)
            recognition_start = time.time()
            language = self.recognition_config.get('language', 'en-US')

            with self.chat_logger.log_step(conversation_id, "stt",
                                          input_text="<audio_data>",
                                          metadata={"language": language}) as stt_log:
                text = self.speech_to_text(audio, language)
                stt_log["output_text"] = text  # Store recognized text

            if text and text.strip():
                # Calculate confidence
                recognition_time = time.time() - recognition_start
                confidence = self._estimate_confidence(text, recognition_time)

                # Publish voice command with conversation_id in metadata
                voice_command_data = {
                    "text": text.strip(),
                    "confidence": confidence,
                    "timestamp": time.time(),
                    "language": language,
                    "duration": recognition_time,
                    "conversation_id": conversation_id  # PASS TO NEXT STEP
                }

                self.publish("voice_command", voice_command_data)

        except Exception as e:
            self.logger.error(f"Error in audio processing: {e}")
```

### 2. AI Cognition Node
**File**: `nodes/ai_cognition/ai_cognition_node.py`

#### Track GPT

```python
from nevil_framework.chat_logger import get_chat_logger

class AiCognitionNode(NevilNode):
    def __init__(self):
        super().__init__("ai_cognition")
        self.chat_logger = get_chat_logger()
        # ... existing init code ...

    def on_voice_command(self, message):
        """Handle voice commands with logging"""
        try:
            text = message.data.get("text", "")
            confidence = message.data.get("confidence", 0.0)
            conversation_id = message.data.get("conversation_id")

            if not conversation_id:
                # Fallback if not provided
                conversation_id = self.chat_logger.generate_conversation_id()

            self.logger.info(f"Processing: '{text}' (conv: {conversation_id})")

            # Check confidence threshold
            if confidence < self.confidence_threshold:
                self.logger.warning(f"Low confidence, ignoring")
                return

            # STEP 3: Log GPT processing
            with self.chat_logger.log_step(conversation_id, "gpt",
                                          input_text=text,
                                          metadata={
                                              "model": self.model,
                                              "mode": self.mode,
                                              "confidence": confidence
                                          }) as gpt_log:
                response_text = self._generate_response(text)
                gpt_log["output_text"] = response_text

            if response_text:
                # Publish with conversation_id for next step
                text_response_data = {
                    "text": response_text,
                    "voice": "onyx",
                    "priority": 100,
                    "context_id": f"conv_{conversation_id}",
                    "timestamp": time.time(),
                    "conversation_id": conversation_id  # PASS TO NEXT STEP
                }

                self.publish("text_response", text_response_data)

        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")
```

### 3. Speech Synthesis Node
**File**: `nodes/speech_synthesis/speech_synthesis_node.py`

#### Track TTS + RESPONSE

```python
from nevil_framework.chat_logger import get_chat_logger

class SpeechSynthesisNode(NevilNode):
    def __init__(self):
        super().__init__("speech_synthesis")
        self.chat_logger = get_chat_logger()
        # ... existing init code ...

    def _process_tts_request(self, tts_request):
        """Process TTS request with logging"""
        text = tts_request.get("text", "")
        conversation_id = tts_request.get("conversation_id")

        if not text.strip():
            return

        if not conversation_id:
            # Fallback if not provided
            conversation_id = self.chat_logger.generate_conversation_id()

        if not busy_state.acquire("speaking"):
            return

        try:
            voice = tts_request.get("voice", "onyx")
            volume_db = self.audio_config.get("volume_db", -10)

            # STEP 4: Log TTS synthesis
            with self.chat_logger.log_step(conversation_id, "tts",
                                          input_text=text,
                                          metadata={
                                              "voice": voice,
                                              "volume_db": volume_db
                                          }) as tts_log:
                with self.speaking_lock:
                    self.is_speaking = True
                    self.current_text = text

                self._publish_speaking_status(True, text, voice)

                success = self.audio_output.generate_and_play_tts(
                    message=text,
                    openai_helper=self,
                    volume_db=volume_db,
                    voice=voice
                )

                tts_log["output_text"] = "<audio_file>" if success else None

            # STEP 5: Log RESPONSE (playback completion)
            with self.chat_logger.log_step(conversation_id, "response",
                                          input_text="<audio_file>",
                                          metadata={
                                              "success": success
                                          }) as resp_log:
                # Playback is complete at this point
                resp_log["output_text"] = "playback_complete"

            if success:
                self.logger.info(f"✓ Conversation complete: {conversation_id}")
                self.synthesis_count += 1

        finally:
            with self.speaking_lock:
                self.is_speaking = False
                self.current_text = ""

            self._publish_speaking_status(False, "", "")
            busy_state.release()

    def on_text_response(self, message):
        """Handle text response with conversation_id"""
        try:
            text = message.data.get("text", "")
            voice = message.data.get("voice", "onyx")
            priority = message.data.get("priority", 100)
            conversation_id = message.data.get("conversation_id")  # Extract

            if not text.strip():
                return

            # Create TTS request with conversation_id
            tts_request = {
                "text": text.strip(),
                "voice": voice,
                "speed": 1.0,
                "source": message.source_node,
                "timestamp": message.timestamp,
                "conversation_id": conversation_id  # PASS THROUGH
            }

            self.tts_queue.put_nowait((priority, message.timestamp, tts_request))

        except Exception as e:
            self.logger.error(f"Error handling text response: {e}")
```

## Usage Examples

### Query Recent Conversations

```bash
# Show recent conversations
python3 -m nevil_framework.chat_analytics recent --limit 10

# Show summary for specific conversation
python3 -m nevil_framework.chat_analytics summary 20251008_143022_a1b2c3d4

# Show full trace with all steps
python3 -m nevil_framework.chat_analytics trace 20251008_143022_a1b2c3d4
```

### Performance Analysis

```bash
# Average durations by step (last 24 hours)
python3 -m nevil_framework.chat_analytics averages --hours 24

# Find slow conversations (>5 seconds)
python3 -m nevil_framework.chat_analytics slow --threshold 5000 --limit 10

# Error rates by step
python3 -m nevil_framework.chat_analytics errors --hours 24
```

### Programmatic Access

```python
from nevil_framework.chat_logger import get_chat_logger

logger = get_chat_logger()

# Get conversation summary
summary = logger.get_conversation_summary(conversation_id)
print(f"Total duration: {summary['total_duration_sec']:.2f}s")

# Print formatted summary
logger.print_conversation_summary(conversation_id)

# Get performance statistics
averages = logger.get_average_step_durations(hours=24)
for step in averages:
    print(f"{step['step']}: {step['avg_ms']:.1f}ms average")

# Find slow conversations
slow = logger.get_slow_conversations(threshold_ms=5000, limit=10)
for conv in slow:
    print(f"{conv['conversation_id']}: {conv['total_ms']/1000:.2f}s")
```

## Example Output

### Conversation Summary
```
============================================================
Conversation: 20251008_143022_a1b2c3d4
============================================================
Start Time:    2025-10-08T14:30:22.123456
End Time:      2025-10-08T14:30:28.987654
Total Duration: 6.864s (6864ms)
Steps:         5

Step Breakdown:
------------------------------------------------------------
  ✓ request     :  0.150s ( 150.0ms)
  ✓ stt         :  1.234s (1234.0ms)
  ✓ gpt         :  3.567s (3567.0ms)
  ✓ tts         :  1.456s (1456.0ms)
  ✓ response    :  0.457s ( 457.0ms)
============================================================
```

### Average Step Durations
```
============================================================
Average Step Durations (last 24 hours)
============================================================
Step                Count   Avg (ms)   Min (ms)   Max (ms)
------------------------------------------------------------
request                45      147.2      102.3      234.5
stt                    45     1234.5      890.2     2345.6
gpt                    45     3421.8     2100.5     5678.9
tts                    45     1345.6      987.3     1890.4
response               45      456.7      234.1      678.9
============================================================
```

## Benefits

1. **Performance Monitoring**: Identify which step is slowest (usually GPT)
2. **Debugging**: Full trace of each conversation with timing
3. **Optimization**: Compare before/after changes to see impact
4. **Error Tracking**: See which steps fail most often
5. **User Experience**: Measure end-to-end conversation latency
6. **Historical Analysis**: Trends over time, detect regressions

## Notes

- Database stored at `logs/chat_log.db`
- Conversation IDs use format: `YYYYMMDD_HHMMSS_<uuid>`
- All timestamps in ISO 8601 format
- Thread-safe for concurrent access
- Minimal performance overhead (<5ms per step)
