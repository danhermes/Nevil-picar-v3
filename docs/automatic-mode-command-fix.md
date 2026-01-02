# Automatic Mode Command Fix

## Problem

When saying "**go play**" to trigger automatic mode, Nevil was interpreting it as a command to play music instead of entering autonomous exploration mode.

## Root Cause

The direct command handler was using simple substring matching (`if trigger in text_lower`), which meant:
- "go play" would match
- "go play music" would also match and trigger automatic mode incorrectly
- The AI might also process "play" as a music command before the direct handler catches it

## Solution

### 1. Word Boundary Checking (direct_commands.py:104-160)

Added regex word boundary checking to ensure commands match complete phrases:

```python
pattern = r'\b' + re.escape(trigger) + r'\b'
if re.search(pattern, text_lower):
    # Command matches
```

This ensures "go play" matches but "go playing around" does not.

### 2. Music Command Filter (direct_commands.py:122-133)

Added specific logic for "go play" to check if it's followed by music-related words:

```python
if trigger == 'go play':
    # Check if followed by "music", "song", "audio", "sound", etc.
    after_match = re.search(r'go play\s+(\w+)', text_lower)
    if after_match:
        next_word = after_match.group(1)
        music_words = ['music', 'song', 'audio', 'sound', 'radio', 'spotify']
        if next_word in music_words:
            # Skip - this is a music command, not automatic mode
            continue
```

**Result**:
- "go play" → Automatic mode ✅
- "go play music" → NOT automatic mode (lets AI handle it) ✅

### 3. Additional Clear Commands (direct_commands.py:32-47)

Added more explicit commands that won't be confused with other actions:

**Priority order (checked first to last):**
1. `nevil go play` - Most specific, least ambiguous
2. `start auto` / `start automatic`
3. `auto mode` / `automatic mode` / `enter automatic mode`
4. `go play` - Checked with word boundaries and music filter
5. Other variants: `seeya nevil`, `go have fun`, `go explore`, etc.

## Usage

### Entering Automatic Mode

Say any of these phrases:

**Recommended (clearest):**
- "**Nevil, go play**"
- "**Start automatic**"
- "**Automatic mode**"

**Also works:**
- "Go play"
- "Go have fun"
- "Go explore"
- "Seeya Nevil"
- "Do your thing"

### Exiting Automatic Mode

Say any of these:
- "**Come back**"
- "**Stop auto**"
- "Stop playing"
- "Stop automatic"
- "Manual mode"
- "Nevil, come back"

## How It Works

1. **Speech Recognition** (speech_recognition_node.py:338-344)
   - User speech is recognized via Whisper
   - Text is passed to DirectCommandHandler BEFORE AI processing

2. **Direct Command Handler** (direct_commands.py:47-70)
   - Checks for automatic mode commands with word boundaries
   - Applies "go play" music filter
   - If matched, publishes `auto_mode_command` message
   - Returns `True` to skip AI processing

3. **Navigation Node** (navigation_node.py:863-889)
   - Receives `auto_mode_command` via `on_auto_mode_command` callback
   - Calls `start_auto_mode()` or `stop_auto_mode()`
   - Activates autonomous behavior thread

4. **Automatic Module** (automatic.py:135-228)
   - Runs autonomous cycle with observation and commentary
   - Uses vision 80-95% of the time
   - GPT makes all movement and speech decisions

## Testing

### Test Case 1: "Go play" (alone)
```
User: "Go play"
Expected: Automatic mode activates ✅
Logs: 🤖 [AUTO TRIGGER] Detected: 'go play'
```

### Test Case 2: "Go play music"
```
User: "Go play music"
Expected: AI processes as music command (NOT automatic mode) ✅
Logs: 🚫 [AUTO TRIGGER] Skipping 'go play' - detected 'music' after it
```

### Test Case 3: "Nevil go play"
```
User: "Nevil go play"
Expected: Automatic mode activates ✅
Logs: 🤖 [AUTO TRIGGER] Detected: 'nevil go play'
```

### Test Case 4: "Start automatic"
```
User: "Start automatic"
Expected: Automatic mode activates ✅
Logs: 🤖 [AUTO TRIGGER] Detected: 'start automatic'
```

## Files Modified

1. **nodes/speech_recognition/direct_commands.py**
   - Added word boundary checking with regex
   - Added music command filter for "go play"
   - Expanded trigger phrase list with clearer commands
   - Reordered triggers by specificity

## Alternative Commands if Issues Persist

If "go play" still conflicts with music playback, use these unambiguous alternatives:

1. **"Nevil go play"** - Uses robot name, very clear
2. **"Start automatic"** - Technical but unambiguous
3. **"Auto mode"** - Short and clear
4. **"Go explore"** - Different verb, no music conflict

---

**Result**: "Go play" now reliably enters automatic mode instead of trying to play music, and there are multiple clear alternative commands available.
