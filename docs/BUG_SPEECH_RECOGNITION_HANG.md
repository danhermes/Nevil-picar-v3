# Bug: Speech Recognition Hangs After 5-10 Minutes Idle

## Symptoms
- After 5-10 minutes of inactivity, Nevil's listening light continues blinking
- No recordings are processed - microphone appears stuck
- Speech recognition log stops updating
- Speech recognition process may die entirely

## Root Cause
The `audio_input.listen_for_speech()` method (line 169 in speech_recognition_node.py) can hang indefinitely if the microphone gets into a bad state after idle time.

## Evidence from Logs
```
[2025-10-29 22:59:14,420 EST] Started discrete speech listening
[2025-10-29 22:59:14,420 EST] Resumed speech recognition - robot finished actions
```
After this point, no more log entries - the recording loop is stuck at `listen_for_speech()`.

## Technical Details
- File: `nodes/speech_recognition/speech_recognition_node.py:169`
- Method: `audio_input.listen_for_speech(timeout=10.0, phrase_time_limit=10.0)`
- The timeout parameter should prevent infinite blocking, but the microphone itself may be hung
- The speech_recognition library's underlying PyAudio may have issues with long-idle microphones

## Workaround
Restart Nevil:
```bash
./nevil restart
```

## Potential Fixes

### Option 1: Microphone Watchdog Timer
Add a thread that monitors if `listen_for_speech()` takes too long:
```python
def _recording_with_watchdog(self):
    start = time.time()
    audio = self.audio_input.listen_for_speech(timeout=10.0)
    if time.time() - start > 15.0:  # 15 sec watchdog
        self.logger.error("Microphone hung, restarting...")
        self._restart_microphone()
```

### Option 2: Periodic Microphone Restart
Reinitialize the microphone every N minutes:
```python
if time.time() - self.last_mic_restart > 300:  # 5 minutes
    self._restart_microphone()
    self.last_mic_restart = time.time()
```

### Option 3: Process-Level Restart
If speech recognition thread doesn't log for 30 seconds, restart the entire node (requires supervisor/watchdog process).

## Related Issues
- Microphone may have hardware timeout issues
- PyAudio may not properly release/reacquire device after long idle
- Speech Recognition library may have threading issues

## Status
**UNRESOLVED** - Requires fix in audio_input.py or speech_recognition_node.py
