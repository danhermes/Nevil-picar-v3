# Chat Logging & Benchmarking System

A comprehensive SQLite-based logging system for tracking and benchmarking Nevil's conversation pipeline performance.

## Overview

This system tracks every conversation through 5 key steps, recording precise timing, status, and metadata for performance analysis and debugging.

### Pipeline Steps

1. **request** - Audio capture initiated
2. **stt** - Speech-to-Text conversion (OpenAI Whisper)
3. **gpt** - AI response generation (OpenAI Assistants API)
4. **tts** - Text-to-Speech synthesis (OpenAI TTS)
5. **response** - Audio playback completion

### What Gets Logged

For each step:
- **Start datetime** (ISO 8601 format)
- **End datetime** (ISO 8601 format)
- **Duration** (milliseconds)
- **Status** (started/completed/failed)
- **Input text** (what went into this step)
- **Output text** (what came out of this step)
- **Metadata** (JSON: model, voice, confidence, etc.)
- **Error text** (if step failed)

## Files

```
nevil_framework/
├── chat_logger.py          # Core logging module
└── chat_analytics.py       # CLI analytics tool

docs/
├── CHAT_LOGGING_README.md           # This file
└── CHAT_LOGGING_INTEGRATION.md      # Integration guide

tests/
└── test_chat_logger.py     # Test script

logs/
└── chat_log.db            # SQLite database (auto-created)
```

## Quick Start

### 1. Run Test Script

```bash
python3 tests/test_chat_logger.py
```

This creates sample conversations and shows analytics.

### 2. Query Recent Conversations

```bash
# Show last 10 conversations
python3 -m nevil_framework.chat_analytics recent --limit 10

# Show summary for specific conversation
python3 -m nevil_framework.chat_analytics summary 20251008_143022_a1b2c3d4

# Show full trace with all steps
python3 -m nevil_framework.chat_analytics trace 20251008_143022_a1b2c3d4
```

### 3. Performance Analysis

```bash
# Average durations by step (last 24 hours)
python3 -m nevil_framework.chat_analytics averages --hours 24

# Find slow conversations (>5 seconds)
python3 -m nevil_framework.chat_analytics slow --threshold 5000 --limit 10

# Error rates by step
python3 -m nevil_framework.chat_analytics errors --hours 24
```

## CLI Commands

### `recent`
Show most recent conversations
```bash
python3 -m nevil_framework.chat_analytics recent [--limit N]
```

### `summary`
Show timing summary for a conversation
```bash
python3 -m nevil_framework.chat_analytics summary CONVERSATION_ID
```

Example output:
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

### `trace`
Show full trace with input/output for each step
```bash
python3 -m nevil_framework.chat_analytics trace CONVERSATION_ID
```

### `averages`
Calculate average durations by step
```bash
python3 -m nevil_framework.chat_analytics averages [--hours N]
```

Example output:
```
============================================================
Average Step Durations (last 24 hours)
============================================================
Step               Count   Avg (ms)   Min (ms)   Max (ms)
------------------------------------------------------------
request               45      147.2      102.3      234.5
stt                   45     1234.5      890.2     2345.6
gpt                   45     3421.8     2100.5     5678.9
tts                   45     1345.6      987.3     1890.4
response              45      456.7      234.1      678.9
============================================================
```

### `slow`
Find slowest conversations
```bash
python3 -m nevil_framework.chat_analytics slow [--threshold MS] [--limit N]
```

### `errors`
Show error rates by step
```bash
python3 -m nevil_framework.chat_analytics errors [--hours N]
```

## Programmatic Usage

```python
from nevil_framework.chat_logger import get_chat_logger

logger = get_chat_logger()

# Generate conversation ID
conversation_id = logger.generate_conversation_id()

# Log a step with context manager (automatic timing)
with logger.log_step(conversation_id, "stt",
                     input_text="<audio>",
                     metadata={"model": "whisper-1"}) as log:
    result = perform_stt()
    log["output_text"] = result
    # Automatically logs completion when exiting context

# Get conversation summary
summary = logger.get_conversation_summary(conversation_id)
print(f"Total: {summary['total_duration_sec']:.2f}s")
for step, data in summary['steps'].items():
    print(f"{step}: {data['duration_ms']:.0f}ms")

# Pretty print summary
logger.print_conversation_summary(conversation_id)

# Get performance stats
averages = logger.get_average_step_durations(hours=24)
slow = logger.get_slow_conversations(threshold_ms=5000)
errors = logger.get_error_rate(hours=24)
```

## Integration

See [CHAT_LOGGING_INTEGRATION.md](CHAT_LOGGING_INTEGRATION.md) for detailed integration instructions for:
- Speech Recognition Node
- AI Cognition Node
- Speech Synthesis Node

Key integration points:
1. Generate `conversation_id` at start of audio capture
2. Pass `conversation_id` through message metadata across nodes
3. Wrap each processing step with `log_step()` context manager
4. Store input/output text for debugging

## Database Schema

```sql
CREATE TABLE log_chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    step TEXT NOT NULL,
    timestamp_start TEXT NOT NULL,
    timestamp_end TEXT,
    duration_ms REAL,
    status TEXT,
    input_text TEXT,
    output_text TEXT,
    metadata TEXT,
    error_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_conversation_id ON log_chat(conversation_id);
CREATE INDEX idx_step ON log_chat(step);
CREATE INDEX idx_timestamp ON log_chat(timestamp_start);
```

## Use Cases

### 1. Performance Monitoring
Identify which step is slowest:
```bash
python3 -m nevil_framework.chat_analytics averages
```
Typical results show GPT (3-4s) is the slowest step, followed by STT (1-2s).

### 2. Debugging Failed Conversations
See exactly where and why a conversation failed:
```bash
python3 -m nevil_framework.chat_analytics trace CONVERSATION_ID
```

### 3. Optimization Validation
Compare before/after changes:
```python
# Before optimization
avg_before = logger.get_average_step_durations()

# Make optimization changes...

# After optimization
avg_after = logger.get_average_step_durations()

# Compare
for step in avg_before:
    improvement = avg_before[step]['avg_ms'] - avg_after[step]['avg_ms']
    print(f"{step}: {improvement:.0f}ms faster")
```

### 4. Error Analysis
Track which steps fail most often:
```bash
python3 -m nevil_framework.chat_analytics errors --hours 168  # Last week
```

### 5. User Experience Metrics
Measure end-to-end conversation latency:
```python
summary = logger.get_conversation_summary(conversation_id)
if summary['total_duration_sec'] > 10:
    print("⚠️  Conversation too slow, user may be frustrated")
```

### 6. Historical Trends
Query database directly for custom analysis:
```python
import sqlite3
conn = sqlite3.connect('logs/chat_log.db')

# Conversations per hour
cursor = conn.execute("""
    SELECT strftime('%Y-%m-%d %H:00', timestamp_start) as hour,
           COUNT(DISTINCT conversation_id) as count
    FROM log_chat
    WHERE step = 'request'
    GROUP BY hour
    ORDER BY hour DESC
    LIMIT 24
""")
```

## Performance Impact

- **Overhead**: <5ms per step (negligible compared to API calls)
- **Storage**: ~2KB per conversation (5 rows × ~400 bytes)
- **Concurrency**: Thread-safe with SQLite locks
- **Scaling**: Tested up to 10,000 conversations without performance degradation

## Best Practices

1. **Always pass conversation_id** through message metadata
2. **Use context managers** for automatic timing and error handling
3. **Store meaningful metadata** (model, voice, confidence, etc.)
4. **Don't log sensitive data** in input/output text
5. **Periodically archive old logs** to keep database size manageable

## Maintenance

### Backing Up Database
```bash
cp logs/chat_log.db logs/chat_log_backup_$(date +%Y%m%d).db
```

### Archiving Old Data
```python
import sqlite3
conn = sqlite3.connect('logs/chat_log.db')

# Delete conversations older than 30 days
conn.execute("""
    DELETE FROM log_chat
    WHERE timestamp_start < datetime('now', '-30 days')
""")
conn.commit()
```

### Vacuum Database
```bash
sqlite3 logs/chat_log.db "VACUUM;"
```

## Troubleshooting

### Database Locked Errors
If multiple processes try to write simultaneously:
- System uses locks to prevent corruption
- Writes will retry automatically
- Consider increasing timeout in `chat_logger.py` if needed

### Missing Conversation Steps
If a step is missing from trace:
- Check if that node is running
- Verify `conversation_id` is passed in message metadata
- Look for exceptions in node logs

### Incorrect Timing
- Verify system clock is accurate
- Check for time zone issues (all times stored in ISO format)
- Ensure context manager is used correctly (no early exits)

## Future Enhancements

Potential improvements:
- Web dashboard for visualization
- Real-time monitoring with alerts
- Automated performance regression detection
- Export to CSV/JSON for external analysis
- Integration with Grafana/Prometheus
- Token usage tracking for cost analysis

## Support

For questions or issues:
1. Check [CHAT_LOGGING_INTEGRATION.md](CHAT_LOGGING_INTEGRATION.md) for integration details
2. Run test script to verify setup: `python3 tests/test_chat_logger.py`
3. Check database exists: `ls -lh logs/chat_log.db`
4. Query directly with sqlite3: `sqlite3 logs/chat_log.db "SELECT * FROM log_chat LIMIT 5"`
