#!/usr/bin/env python3
import signal
import os

def signal_handler(signum, frame):
    print(f"\nSignal {signum} received! Exiting...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("About to import pyaudio...")
import pyaudio
print("PyAudio imported successfully")

# This will block if ALSA has issues
print("Initializing PyAudio...")
p = pyaudio.PyAudio()
print("PyAudio initialized")
p.terminate()
print("Done")