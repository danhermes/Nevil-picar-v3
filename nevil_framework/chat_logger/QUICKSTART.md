# Chat Analytics Quickstart

Quick reference for analyzing Nevil's conversation performance using the chat analytics tool.

## Quick Commands

### 📊 Most Useful: Performance Averages

Get average timing for all conversation steps over the last 24 hours:

```bash
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 24
```

**Example Output:**
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

**What Each Step Means:**
- `request` - Time to capture audio from microphone
- `stt` - Speech-to-text conversion (Whisper API)
- `gpt` - AI response generation (GPT API)
- `tts` - Text-to-speech synthesis (OpenAI TTS)
- `response` - Audio playback

**Typical Values:**
- `request`: ~150ms (very consistent)
- `stt`: 1000-2000ms (depends on audio length)
- `gpt`: 2000-5000ms (usually the bottleneck)
- `tts`: 1000-2000ms (depends on text length)
- `response`: ~450ms (very consistent)

**Customizing Time Range:**
```bash
# Last hour
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 1

# Last week
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 168

# Last 10 minutes
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 0.16
```

### 📝 Other Useful Commands

**See recent conversations:**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics recent --limit 10
```

**Find slow conversations (>7 seconds):**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics slow --threshold 7000 --limit 5
```

**Check error rates:**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics errors --hours 24
```

**Analyze specific conversation:**
```bash
# Get conversation ID from 'recent' command, then:
python3 -m nevil_framework.chat_logger.chat_analytics summary 20251025_143022_a1b2c3d4
```

**Detailed trace (for debugging):**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics trace 20251025_143022_a1b2c3d4
```

## Common Use Cases

### 🔍 Finding Performance Bottlenecks

1. Run averages to see overall performance:
   ```bash
   python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 24
   ```

2. Look for the slowest step (usually `gpt` or `stt`)

3. Find specific slow conversations:
   ```bash
   python3 -m nevil_framework.chat_logger.chat_analytics slow --threshold 8000 --limit 5
   ```

4. Analyze those conversations in detail:
   ```bash
   python3 -m nevil_framework.chat_logger.chat_analytics trace <conversation_id>
   ```

### ✅ Validating Optimizations

**Before optimization:**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 24
# Note the GPT average, e.g., 3421.8ms
```

**Make your changes...**

**After optimization (check last hour only):**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics averages --hours 1
# Compare GPT average to see improvement
```

### 🚨 Monitoring Errors

Check if any steps are failing:
```bash
python3 -m nevil_framework.chat_logger.chat_analytics errors --hours 24
```

Look for error rates >5% - anything higher needs investigation.

## Database Location

All data is stored in:
```
/home/dan/Nevil-picar-v3/logs/chat_log.db
```

This is a SQLite database you can query directly if needed.

## Performance Targets

**Good Performance:**
- Total conversation time: <7 seconds
- GPT step: <3.5 seconds
- STT step: <1.5 seconds
- Error rate: <5% per step

**Action Required:**
- Total conversation time: >10 seconds
- GPT step: >5 seconds
- Error rate: >10% per step

## Tips

1. **Run averages daily** to track trends
2. **Check errors after code changes** to catch regressions
3. **Use --hours 1** to isolate recent changes
4. **Compare min/max values** to understand variability
5. **Monitor GPT step** - it's usually the bottleneck

## Full Documentation

For complete details, see:
- [README](CHAT_LOGGING_README.md) - Overview and concepts
- [Integration Guide](CHAT_LOGGING_INTEGRATION.md) - How to add logging to code
- [Example Session](CHAT_LOGGING_EXAMPLE_SESSION.txt) - Full walkthrough
- [Complete Documentation](CHAT_LOGGING_COMPLETE_DOCUMENTATION.md) - All features

---

**Quick Help:**
```bash
python3 -m nevil_framework.chat_logger.chat_analytics --help
```
