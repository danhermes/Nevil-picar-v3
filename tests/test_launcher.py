#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nevil_framework.launcher import NevilLauncher

print("[TEST] Creating launcher...")
launcher = NevilLauncher()

print("[TEST] Starting system...")
result = launcher.start_system()
print(f"[TEST] start_system returned: {result}")

if result:
    print("[TEST] Success!")
else:
    print("[TEST] Failed!")