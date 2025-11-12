# Nevil 2.2 Realtime API Integration Tests

Comprehensive integration tests for the Nevil 2.2 Realtime API implementation covering the complete voice pipeline: STT → AI → TTS.

## Test Files

### 1. test_integration_realtime_pipeline.py (~270 lines)
**Full Voice Pipeline Integration Tests**

Tests the complete end-to-end voice interaction pipeline:
- STT → AI → TTS message flow
- WebSocket connection management and recovery
- Message bus communication between nodes
- Error handling and graceful degradation
- Multi-turn conversation flows
- Audio streaming and buffering
- Performance and latency tracking

**Test Classes:**
- `TestRealtimePipelineIntegration` - Core pipeline tests (13 tests)
- `TestPipelinePerformance` - Performance and throughput (3 tests)
- `TestPipelineEdgeCases` - Edge cases and error handling (4 tests)

**Total: 20 tests**

### 2. test_audio_playback_validation.py (~230 lines)
**Critical Hardware Validation Tests**

Validates that speech_synthesis_node22 uses the EXACT same playback method as v3.0:
- ✅ Uses AudioOutput from audio/audio_output.py
- ✅ Calls robot_hat.Music() for playback
- ✅ Saves to WAV before playback (required)
- ✅ Does NOT use PyAudio for playback
- ✅ Enables GPIO pin 20 speaker switch
- ✅ Compatible with HiFiBerry DAC

**Test Classes:**
- `TestAudioOutputIntegration` - AudioOutput integration (5 tests)
- `TestWAVFileSaveRequirement` - WAV file validation (3 tests)
- `TestMusicPlaybackPath` - robot_hat.Music() path (3 tests)
- `TestAudioBuffering` - Streaming buffer management (3 tests)
- `TestHardwareCompatibility` - Hardware requirements (4 tests)
- `TestMicrophoneMutex` - Mutex coordination (3 tests)
- `TestPlaybackStatuses` - Status publishing (2 tests)

**Total: 23 tests**

### 3. test_node_integration.py (~240 lines)
**Node Communication Integration Tests**

Tests message bus integration and inter-node communication:
- speech_recognition_node22 publishes voice_command
- ai_node22 subscribes to voice_command, publishes text_response
- speech_synthesis_node22 subscribes to text_response
- System mode coordination
- Message bus reliability

**Test Classes:**
- `TestSpeechRecognitionNodeIntegration` - STT node messaging (5 tests)
- `TestAiNodeIntegration` - AI node messaging (6 tests)
- `TestSpeechSynthesisNodeIntegration` - TTS node messaging (4 tests)
- `TestNodeToNodeCommunication` - Inter-node flows (3 tests)
- `TestSystemModeCoordination` - Mode synchronization (2 tests)
- `TestMessageBusReliability` - Error handling (3 tests)
- `TestConversationContext` - Context management (2 tests)

**Total: 25 tests**

## Running Tests

### Run All Integration Tests
```bash
pytest tests/realtime/ -v
```

### Run Specific Test File
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py -v
pytest tests/realtime/test_audio_playback_validation.py -v
pytest tests/realtime/test_node_integration.py -v
```

### Run Specific Test Class
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py::TestRealtimePipelineIntegration -v
pytest tests/realtime/test_audio_playback_validation.py::TestAudioOutputIntegration -v
pytest tests/realtime/test_node_integration.py::TestNodeToNodeCommunication -v
```

### Run Specific Test
```bash
pytest tests/realtime/test_integration_realtime_pipeline.py::TestRealtimePipelineIntegration::test_complete_pipeline_single_turn -v
```

### Run with Coverage
```bash
pytest tests/realtime/ --cov=nevil_framework.realtime --cov-report=html
```

### Run with Output
```bash
pytest tests/realtime/ -v -s
```

### Quick Validation
```bash
# Just check tests are collected correctly
pytest tests/realtime/ --collect-only
```

## Test Summary

| File | Lines | Tests | Coverage Area |
|------|-------|-------|---------------|
| test_integration_realtime_pipeline.py | ~270 | 20 | Full pipeline, performance, edge cases |
| test_audio_playback_validation.py | ~230 | 23 | Hardware validation, playback path |
| test_node_integration.py | ~240 | 25 | Message bus, inter-node communication |
| **TOTAL** | **~740** | **68** | **Complete integration coverage** |

## Key Validation Points

### Pipeline Flow
✅ Voice command flows from STT → AI
✅ Text response flows from AI → TTS
✅ Conversation IDs propagate correctly
✅ System modes coordinate between nodes
✅ Error recovery and reconnection work

### Hardware Playback
✅ Uses robot_hat.Music() (not PyAudio)
✅ Saves to WAV before playback
✅ GPIO pin 20 speaker enabled
✅ 24kHz PCM16 mono format
✅ HiFiBerry DAC compatible

### Message Bus
✅ All nodes publish to correct topics
✅ All nodes subscribe to required topics
✅ Message schemas are valid
✅ Concurrent publications handled
✅ Error handling is graceful

## Mocking Strategy

Tests use comprehensive mocking to avoid hardware dependencies:
- **WebSocket connections**: Mocked with AsyncMock
- **robot_hat.Music()**: Mocked to avoid audio hardware
- **PyAudio**: Mocked to avoid microphone hardware
- **GPIO pins**: Mocked with os.popen patches
- **File I/O**: Mocked with wave.open patches
- **Message bus**: Custom MockMessageBus implementation

## Dependencies

Required packages for tests:
```bash
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
unittest.mock (built-in)
```

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

## Test Patterns

### Integration Test Pattern
```python
def test_complete_flow():
    # 1. Create mock message bus
    bus = MockMessageBus()

    # 2. Create nodes with mocked dependencies
    with patch('os.getenv', return_value='test_key'):
        stt_node = SpeechRecognitionNode22()
        ai_node = AiNode22()
        tts_node = SpeechSynthesisNode22()

    # 3. Wire up message bus subscriptions
    bus.subscribe('voice_command', ai_node.on_voice_command)
    bus.subscribe('text_response', tts_node.on_text_response)

    # 4. Trigger pipeline
    stt_node._process_transcript("Hello")

    # 5. Verify messages flow correctly
    assert len(bus.get_published('voice_command')) == 1
    assert len(bus.get_published('text_response')) == 1
```

### Hardware Validation Pattern
```python
def test_hardware_requirement():
    with patch('audio.audio_output.Music') as mock_music:
        # Create node
        tts_node = SpeechSynthesisNode22()

        # Verify hardware setup
        assert tts_node.audio_output.music is not None
        mock_music.assert_called_once()

        # Verify correct hardware path used
        assert not uses_pyaudio_for_playback()
```

## CI/CD Integration

These tests are designed to run in CI/CD pipelines without hardware:
- All hardware dependencies are mocked
- No actual audio devices required
- No GPIO hardware required
- WebSocket connections are mocked
- Tests run quickly (~5-10 seconds total)

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
cd /home/dan/Nevil-picar-v3
pytest tests/realtime/ -v
```

### Async Warnings
Install pytest-asyncio if you see async warnings:
```bash
pip install pytest-asyncio
```

### Mock Issues
If mocks aren't working correctly, verify patch paths:
```python
# Correct: Patch where it's imported, not where it's defined
with patch('nevil_framework.realtime.speech_synthesis_node22.AudioOutput'):
    # Not: with patch('audio.audio_output.AudioOutput')
```

## Contributing

When adding new tests:
1. Follow existing test patterns
2. Mock all hardware dependencies
3. Use descriptive test names
4. Add docstrings explaining what's tested
5. Keep tests focused and atomic
6. Update this README with new test counts

## Related Documentation

- [Realtime API Implementation](../../nevil_framework/realtime/README.md)
- [Audio Output Documentation](../../audio/README.md)
- [Message Bus Architecture](../../nevil_framework/README.md)
