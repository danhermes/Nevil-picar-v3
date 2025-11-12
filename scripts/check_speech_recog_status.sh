#!/bin/bash
# Check if speech_recognition_realtime has the latest fixes

echo "=== Checking speech_recognition_node22.py for fixes ==="
echo ""

echo "Fix 1: .on() method (not .register_event_handler):"
grep -n "\.on(" nodes/speech_recognition_realtime/speech_recognition_node22.py | head -3
echo ""

echo "Fix 2: session.instructions (not null):"
grep -n "instructions=" nodes/speech_recognition_realtime/speech_recognition_node22.py
echo ""

echo "Fix 3: input_audio_transcription enabled:"
grep -n "input_audio_transcription" nodes/speech_recognition_realtime/speech_recognition_node22.py
echo ""

echo "Fix 4: start_recording() called:"
grep -n "start_recording()" nodes/speech_recognition_realtime/speech_recognition_node22.py
echo ""

echo "Fix 5: listening_status published:"
grep -n "_publish_listening_status.*initialized" nodes/speech_recognition_realtime/speech_recognition_node22.py
echo ""

echo "=== All fixes present? ==="
if grep -q "\.on(" nodes/speech_recognition_realtime/speech_recognition_node22.py && \
   grep -q "instructions=" nodes/speech_recognition_realtime/speech_recognition_node22.py && \
   grep -q "input_audio_transcription" nodes/speech_recognition_realtime/speech_recognition_node22.py && \
   grep -q "start_recording()" nodes/speech_recognition_realtime/speech_recognition_node22.py && \
   grep -q "_publish_listening_status.*initialized" nodes/speech_recognition_realtime/speech_recognition_node22.py; then
    echo "✅ ALL FIXES PRESENT - Ready to test!"
    echo ""
    echo "Run: ./nevil start"
    echo ""
    echo "Expected logs:"
    echo "  [speech_recognition_realtime] Audio capture started - streaming to Realtime API"
    echo "  [speech_recognition_realtime] Published listening status: active"
else
    echo "❌ SOME FIXES MISSING - File may not be saved/synced"
fi
