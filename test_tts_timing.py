#!/usr/bin/env python3
"""Test TTS timing breakdown"""

import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio.tts_providers.factory import get_tts_provider

def test_espeak_timing():
    """Test espeak TTS timing"""
    print("=" * 60)
    print("Testing Espeak TTS Timing Breakdown")
    print("=" * 60)

    # Test text
    text = "Hello, this is a test of the espeak text to speech system."
    output_file = "/tmp/test_espeak_timing.wav"

    # Step 1: Get provider
    t1 = time.time()
    provider = get_tts_provider("espeak")
    t2 = time.time()
    print(f"1. Get espeak provider: {(t2-t1)*1000:.1f}ms")

    # Step 2: Generate speech
    t3 = time.time()
    success = provider.generate_speech(text, output_file, voice="onyx")
    t4 = time.time()
    print(f"2. Generate speech file: {(t4-t3)*1000:.1f}ms")

    # Step 3: Check file exists
    t5 = time.time()
    exists = os.path.exists(output_file)
    file_size = os.path.getsize(output_file) if exists else 0
    t6 = time.time()
    print(f"3. Check file ({file_size} bytes): {(t6-t5)*1000:.1f}ms")

    # Step 4: Simulate Music() playback (just check the file)
    print(f"\n4. Total espeak generation time: {(t4-t1)*1000:.1f}ms")
    print(f"   Success: {success}")

    # Cleanup
    if os.path.exists(output_file):
        os.remove(output_file)

    print("=" * 60)

if __name__ == "__main__":
    test_espeak_timing()
