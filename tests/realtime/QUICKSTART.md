# Quick Start Guide - Nevil 2.2 Integration Tests

Get up and running with the Realtime API integration tests in under 2 minutes.

## TL;DR - Run All Tests

```bash
cd /home/dan/Nevil-picar-v3
./tests/realtime/run_tests.sh
```

**Expected Output:**
```
================================================
  ALL TESTS PASSED ✓
================================================
```

---

## What These Tests Validate

### 🎯 Critical Validations
- ✅ **STT → AI → TTS pipeline** works end-to-end
- ✅ **robot_hat.Music()** used for playback (NOT PyAudio)
- ✅ **WAV files saved** before playback (required)
- ✅ **GPIO pin 20** speaker switch enabled
- ✅ **Message bus** communication working
- ✅ **Error recovery** and reconnection functional

### 📊 Test Coverage
- **68 integration tests** across 3 files
- **~740 lines** of test code
- **~5-10 seconds** execution time
- **100% mocked** (no hardware required)

---

## Quick Commands

### Run Everything
```bash
./tests/realtime/run_tests.sh
```

### Run with Verbose Output
```bash
./tests/realtime/run_tests.sh -v
```

### Run with Coverage Report
```bash
./tests/realtime/run_tests.sh -c
# Opens htmlcov/index.html
```

### Just List Tests
```bash
./tests/realtime/run_tests.sh --collect
```

### Run Specific File
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py -v
pytest tests/realtime/test_audio_playback_validation.py -v
pytest tests/realtime/test_node_integration.py -v
```

---

## Test Files

| File | Purpose | Tests | Lines |
|------|---------|-------|-------|
| `test_integration_realtime_pipeline.py` | Full pipeline STT→AI→TTS | 20 | 270 |
| `test_audio_playback_validation.py` | Hardware playback validation | 23 | 230 |
| `test_node_integration.py` | Message bus & node comms | 25 | 240 |

---

## Common Use Cases

### 1. Quick Validation Before Commit
```bash
./tests/realtime/run_tests.sh
```

### 2. Debugging a Specific Test
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py::TestRealtimePipelineIntegration::test_complete_pipeline_single_turn -v -s
```

### 3. Check What Tests Exist
```bash
pytest tests/realtime/ --collect-only | grep "Function"
```

### 4. Run Only Hardware Tests
```bash
pytest tests/realtime/test_audio_playback_validation.py -v
```

### 5. Run Only Pipeline Tests
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py -v
```

### 6. Run Only Communication Tests
```bash
pytest tests/realtime/test_node_integration.py -v
```

---

## Expected Test Results

### ✅ All Passing
```
================================================
  Test Results Summary
================================================

✓ Pipeline Integration Tests: PASSED (20/20)
✓ Audio Playback Validation: PASSED (23/23)
✓ Node Integration Tests: PASSED (25/25)

================================================
  ALL TESTS PASSED ✓
================================================
```

### ❌ If Tests Fail

Check:
1. **Import errors**: Run from project root
2. **Missing packages**: `pip install pytest pytest-asyncio`
3. **Mock issues**: Check patch paths in error message
4. **Async warnings**: `pip install pytest-asyncio`

---

## Install Test Dependencies

If tests fail with import errors:

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

---

## Test Architecture

```
STT Node (speech_recognition_node22)
   ↓ publishes: voice_command
   ↓
AI Node (ai_node22)
   ↓ publishes: text_response
   ↓
TTS Node (speech_synthesis_node22)
   ↓ uses: AudioOutput
   ↓ calls: robot_hat.Music()
   ↓ saves: WAV file
   ↓ plays: via speaker (GPIO 20)
```

---

## Key Test Patterns

### 1. Pipeline Test Pattern
```python
def test_pipeline():
    # Create mock message bus
    bus = MockMessageBus()

    # Create nodes
    stt_node = SpeechRecognitionNode22()
    ai_node = AiNode22()
    tts_node = SpeechSynthesisNode22()

    # Wire up subscriptions
    bus.subscribe('voice_command', ai_node.on_voice_command)

    # Trigger pipeline
    stt_node._process_transcript("Hello")

    # Verify message flow
    assert len(bus.get_published('voice_command')) == 1
```

### 2. Hardware Validation Pattern
```python
def test_hardware():
    with patch('audio.audio_output.Music') as mock_music:
        tts_node = SpeechSynthesisNode22()

        # Verify Music() was created
        mock_music.assert_called_once()

        # Verify NOT using PyAudio
        assert 'pyaudio' not in dir(tts_node)
```

---

## What's Being Tested

### Message Flow (18 tests)
- STT publishes voice_command
- AI subscribes to voice_command
- AI publishes text_response
- TTS subscribes to text_response
- All message schemas correct

### Hardware Validation (23 tests)
- Uses AudioOutput class
- Calls robot_hat.Music()
- Saves to WAV before playback
- GPIO pin 20 enabled
- 24kHz PCM16 mono format
- HiFiBerry DAC compatible

### Error Handling (9 tests)
- Empty transcripts handled
- Long transcripts handled
- WebSocket reconnection works
- Publish failures graceful
- Exception handling correct

### Performance (4 tests)
- Latency tracking (<100ms)
- High throughput (100+ msgs)
- Concurrent conversations
- No memory leaks

---

## Troubleshooting

### "Module not found" errors
```bash
cd /home/dan/Nevil-picar-v3  # Must run from project root
pytest tests/realtime/ -v
```

### "No module named pytest"
```bash
pip install pytest pytest-asyncio
```

### "AsyncMock not found"
```bash
pip install pytest-asyncio
```

### Tests hang or timeout
```bash
# All WebSocket operations are mocked
# Check for infinite loops in test code
pytest tests/realtime/ -v --timeout=10
```

---

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Realtime API Tests
  run: |
    cd /home/dan/Nevil-picar-v3
    ./tests/realtime/run_tests.sh
```

### Jenkins
```groovy
stage('Integration Tests') {
    steps {
        sh './tests/realtime/run_tests.sh'
    }
}
```

---

## Next Steps

1. ✅ Run tests: `./tests/realtime/run_tests.sh`
2. ✅ Review output for any failures
3. ✅ Check coverage: `./tests/realtime/run_tests.sh -c`
4. ✅ Add to CI/CD pipeline
5. ✅ Run before every commit

---

## File Locations

All test files are in: `/home/dan/Nevil-picar-v3/tests/realtime/`

- `test_integration_realtime_pipeline.py` - Pipeline integration
- `test_audio_playback_validation.py` - Hardware validation
- `test_node_integration.py` - Node communication
- `run_tests.sh` - Test runner script
- `README.md` - Detailed documentation
- `TEST_SUMMARY.md` - Complete test summary
- `QUICKSTART.md` - This file

---

## Help & Support

### Get Help
```bash
./tests/realtime/run_tests.sh --help
```

### View Detailed Documentation
```bash
cat tests/realtime/README.md
```

### View Test Summary
```bash
cat tests/realtime/TEST_SUMMARY.md
```

---

## Success Indicators

✅ **All tests pass**
✅ **Execution under 10 seconds**
✅ **No hardware dependencies**
✅ **Coverage >90%**
✅ **CI/CD ready**

---

**Status:** ✅ Ready to use
**Last Updated:** 2025-11-11
**Test Count:** 68 integration tests
**Execution Time:** ~5-10 seconds
