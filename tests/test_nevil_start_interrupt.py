#!/usr/bin/env python3

import sys
import time
import subprocess
import signal
import threading

print("Testing 'nevil start' Ctrl+C handling...")
print("This will launch 'nevil start' and then send a SIGINT after 5 seconds")
print("-" * 60)

# Launch nevil start in background
print("Launching 'nevil start'...")
proc = subprocess.Popen(["./nevil", "start"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       text=True)

print(f"Nevil start PID: {proc.pid}")
print("Waiting 5 seconds before sending interrupt...")

# Wait a bit for it to initialize
time.sleep(5)

# Send interrupt signal
print("\nSending SIGINT (Ctrl+C) to test shutdown...")
proc.send_signal(signal.SIGINT)

# Wait for process to finish
print("Waiting for shutdown to complete...")
try:
    stdout, stderr = proc.communicate(timeout=15)
    print(f"\nProcess finished with exit code: {proc.returncode}")
except subprocess.TimeoutExpired:
    print("\nTIMEOUT: Process didn't shut down within 15 seconds!")
    proc.kill()
    stdout, stderr = proc.communicate()
    print(f"Process killed. Exit code: {proc.returncode}")

print("\n" + "=" * 60)
print("STDOUT:")
print(stdout)
print("\nSTDERR:")
print(stderr)
print("=" * 60)

# Check for proper shutdown messages
if "Received signal 2" in stdout or "shutting down" in stdout.lower():
    print("\n✅ Signal handling appears to be working!")
else:
    print("\n❌ Signal handling may not be working properly")

if "shutdown complete" in stdout.lower():
    print("✅ Clean shutdown completed!")
else:
    print("❌ Clean shutdown may not have completed")

if proc.returncode == 0:
    print("✅ Process exited with success code")
else:
    print(f"❌ Process exited with error code: {proc.returncode}")

print(f"\nTest complete. Final exit code: {proc.returncode}")