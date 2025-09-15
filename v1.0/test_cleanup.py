#!/usr/bin/env python3

import sys
import time
import subprocess
import signal

print("Testing Nevil v3.0 cleanup mechanism...")
print("This will launch Nevil and then send a SIGINT after 5 seconds")
print("-" * 50)

# Launch nevil in background
print("Launching Nevil...")
proc = subprocess.Popen([sys.executable, "nevil.py", "--keyboard", "--no-img"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)

print(f"Nevil PID: {proc.pid}")
print("Waiting 5 seconds before sending interrupt...")

# Wait a bit for it to initialize
time.sleep(5)

# Send interrupt signal
print("\nSending SIGINT (Ctrl+C) to test cleanup...")
proc.send_signal(signal.SIGINT)

# Wait for process to finish
print("Waiting for cleanup to complete...")
stdout, stderr = proc.communicate(timeout=10)

print("\n" + "=" * 50)
print("STDOUT:")
print(stdout)
print("\nSTDERR:")
print(stderr)
print("=" * 50)

# Check if cleanup messages appeared
if "Cleaning up Nevil resources" in stdout or "Cleaning up Nevil resources" in stderr:
    print("\n✅ Cleanup handler was triggered!")
else:
    print("\n❌ Cleanup handler may not have been triggered")

if "Cleanup complete" in stdout or "Cleanup complete" in stderr:
    print("✅ Cleanup completed successfully!")
else:
    print("❌ Cleanup may not have completed")

print(f"\nExit code: {proc.returncode}")