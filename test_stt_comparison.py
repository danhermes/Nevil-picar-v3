#!/usr/bin/env python3
"""Compare STT methods for speed"""

import time
import speech_recognition as sr
import os

def test_stt_speeds():
    """Test different STT methods with a sample audio file"""

    # Find a recent audio file
    audio_dir = "/home/dan/Nevil-picar-v3/audio/user_wavs"
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    if not audio_files:
        print("No audio files found!")
        return

    # Use the most recent file
    audio_files.sort()
    test_file = os.path.join(audio_dir, audio_files[-1])
    print(f"Testing with: {test_file}")
    print(f"File size: {os.path.getsize(test_file)} bytes")
    print("=" * 60)

    # Load audio
    recognizer = sr.Recognizer()
    with sr.AudioFile(test_file) as source:
        audio = recognizer.record(source)

    print(f"Audio duration: {len(audio.frame_data) / (audio.sample_rate * audio.sample_width):.2f}s")
    print("=" * 60)

    # Test 1: Google Speech Recognition (free, cloud)
    print("\n1. Google Speech Recognition (free, cloud)")
    try:
        t1 = time.time()
        text = recognizer.recognize_google(audio)
        t2 = time.time()
        print(f"   Time: {(t2-t1)*1000:.0f}ms")
        print(f"   Text: {text[:80]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Faster Whisper (local)
    print("\n2. Faster Whisper (local)")
    try:
        t1 = time.time()
        text = recognizer.recognize_faster_whisper(audio, language="en")
        t2 = time.time()
        print(f"   Time: {(t2-t1)*1000:.0f}ms")
        print(f"   Text: {text[:80]}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: OpenAI Whisper API (cloud, paid)
    print("\n3. OpenAI Whisper API (cloud, paid)")
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            t1 = time.time()
            text = recognizer.recognize_whisper_api(audio, api_key=api_key)
            t2 = time.time()
            print(f"   Time: {(t2-t1)*1000:.0f}ms")
            print(f"   Text: {text[:80]}")
        else:
            print("   Skipped: No OPENAI_API_KEY")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_stt_speeds()
