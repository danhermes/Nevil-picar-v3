#!/usr/bin/env python3
import signal
import time
import os

def signal_handler(signum, frame):
    print(f"\nSignal {signum} received! Exiting...")
    os._exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print("Test signal handler. Press Ctrl+C to test...")
while True:
    print(".", end="", flush=True)
    time.sleep(1)