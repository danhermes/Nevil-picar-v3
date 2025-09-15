#!/usr/bin/env python3

import speech_recognition as sr
import pyaudio
import numpy as np
import time

def test_microphone_basic():
    """Test basic microphone functionality"""
    print("Testing microphone basic functionality...")

    # List available audio devices
    p = pyaudio.PyAudio()
    print(f"\nAvailable audio devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  Device {i}: {info['name']} - {info['maxInputChannels']} input channels")
    p.terminate()

def test_microphone_levels():
    """Test microphone input levels"""
    print("\n" + "="*50)
    print("Testing microphone input levels...")
    print("Speak into the microphone for 5 seconds...")
    print("="*50)

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {recognizer.energy_threshold}")

            print("\nListening for 5 seconds...")
            for i in range(5):
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    # Calculate rough audio level
                    audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_data**2))
                    print(f"Second {i+1}: Audio RMS level: {rms:.0f}")
                except sr.WaitTimeoutError:
                    print(f"Second {i+1}: No audio detected")

    except Exception as e:
        print(f"Microphone test error: {e}")

def test_speech_recognition():
    """Test speech recognition"""
    print("\n" + "="*50)
    print("Testing speech recognition...")
    print("Say something (you have 5 seconds)...")
    print("="*50)

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)

            print("Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"✅ Recognized: '{text}'")

    except sr.UnknownValueError:
        print("❌ Could not understand audio")
    except sr.RequestError as e:
        print(f"❌ Speech recognition error: {e}")
    except sr.WaitTimeoutError:
        print("❌ No speech detected within timeout")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_nevil_mic_config():
    """Test with Nevil's microphone configuration"""
    print("\n" + "="*50)
    print("Testing with Nevil's mic configuration...")
    print("="*50)

    recognizer = sr.Recognizer()

    # Use Nevil's settings
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_adjustment_damping = 0.1
    recognizer.dynamic_energy_ratio = 1.2
    recognizer.pause_threshold = 0.5
    recognizer.operation_timeout = 18

    print(f"Energy threshold: {recognizer.energy_threshold}")
    print(f"Pause threshold: {recognizer.pause_threshold}")

    try:
        with sr.Microphone() as source:
            print("\nSay 'hello nevil' or similar...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)

            print("Processing with Nevil settings...")
            text = recognizer.recognize_google(audio)
            print(f"✅ Nevil heard: '{text}'")

    except Exception as e:
        print(f"❌ Nevil mic test error: {e}")

if __name__ == "__main__":
    print("🎤 Nevil Microphone Test Suite")
    print("=" * 50)

    test_microphone_basic()
    test_microphone_levels()
    test_speech_recognition()
    test_nevil_mic_config()

    print("\n" + "=" * 50)
    print("🏁 Microphone testing complete!")