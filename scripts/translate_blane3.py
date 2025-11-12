#!/usr/bin/env python3
"""
Translate Blane3 TypeScript code to Nevil Python
Migrates proven Realtime API implementation instead of reinventing
"""

import os
import re
import sys

BLANE3_PATH = "../candy_mountain/blane3"
NEVIL_PATH = "."

# TypeScript to Python translation rules
TRANSLATIONS = {
    # TypeScript types -> Python types
    r':\s*string': ': str',
    r':\s*number': ': int | float',
    r':\s*boolean': ': bool',
    r':\s*void': ': None',
    r'Promise<([^>]+)>': r'\1',  # Remove Promise wrapper
    r'async\s+': 'async ',

    # Class patterns
    r'export\s+class\s+': 'class ',
    r'private\s+': '',
    r'public\s+': '',
    r'protected\s+': '',

    # Method patterns
    r'constructor\(': 'def __init__(self, ',
    r'(\w+)\([^)]*\)\s*:\s*(\w+)\s*{': r'def \1(self):\n    ',

    # WebSocket patterns
    r'new\s+WebSocket\(': 'await websockets.connect(',
    r'this\.ws\.send\(': 'await self.ws.send(',
    r'this\.ws\.close\(': 'await self.ws.close(',

    # Event patterns
    r'this\.emit\(': 'self._emit_event(',
    r'EventEmitter': 'object',

    # Audio patterns
    r'AudioContext': 'pyaudio.PyAudio',
    r'new\s+AudioContext\(': 'pyaudio.PyAudio(',
}

def translate_typescript_to_python(ts_code: str, context: str = "") -> str:
    """
    Translate TypeScript code to Python

    Args:
        ts_code: TypeScript source code
        context: Context (realtime, audio, etc) for specialized translations

    Returns:
        Python source code
    """
    py_code = ts_code

    # Apply general translations
    for pattern, replacement in TRANSLATIONS.items():
        py_code = re.sub(pattern, replacement, py_code)

    # Context-specific translations
    if context == "realtime":
        py_code = translate_realtime_client(py_code)
    elif context == "audio_capture":
        py_code = translate_audio_capture(py_code)
    elif context == "audio_playback":
        py_code = translate_audio_playback(py_code)

    return py_code

def translate_realtime_client(ts_code: str) -> str:
    """Translate RealtimeClient.ts to Python"""
    # Add Python-specific imports
    header = '''"""
RealtimeConnectionManager - Translated from Blane3 RealtimeClient.ts
Production-tested WebSocket client for OpenAI Realtime API
"""

import asyncio
import websockets
import json
import base64
import logging
from typing import Dict, Callable, Any, Optional
from threading import Thread, Lock

logger = logging.getLogger(__name__)

'''

    # Translate class structure
    py_code = ts_code

    # Replace constructor
    py_code = re.sub(
        r'constructor\((.*?)\)\s*{',
        r'def __init__(self, \1):\n        ',
        py_code
    )

    return header + py_code

def translate_audio_capture(ts_code: str) -> str:
    """Translate AudioCaptureManager.ts to Python"""
    header = '''"""
AudioCaptureManager - Translated from Blane3
Handles microphone input for Realtime API (24kHz PCM16)
"""

import pyaudio
import numpy as np
import base64
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

'''
    return header + ts_code

def translate_audio_playback(ts_code: str) -> str:
    """
    Translate AudioPlaybackManager.ts to Python

    ⚠️ CRITICAL: We do NOT use this directly
    Instead, buffer audio and use robot_hat.Music()
    """
    header = '''"""
AudioBufferManager - Adapted from Blane3 AudioPlaybackManager.ts

⚠️ CRITICAL: This ONLY buffers audio chunks
It does NOT do playback - that stays with robot_hat.Music()

Use this to accumulate streaming audio, then:
1. Concatenate chunks
2. Save to WAV file
3. Play via audio/audio_output.py (robot_hat.Music())
"""

import base64
import logging
from typing import List
import wave

logger = logging.getLogger(__name__)

'''
    return header + ts_code

def migrate_file(src_path: str, dest_path: str, context: str):
    """Migrate a single TypeScript file to Python"""
    print(f"Migrating: {src_path} -> {dest_path}")

    if not os.path.exists(src_path):
        print(f"  [WARN] Source not found: {src_path}")
        return

    with open(src_path, 'r', encoding='utf-8') as f:
        ts_code = f.read()

    # Translate
    py_code = translate_typescript_to_python(ts_code, context)

    # Add translation notice
    notice = f'''#
# Translated from Blane3: {os.path.basename(src_path)}
# Original: {src_path}
# Translation date: 2025-11-11
# Manual adaptation required for full Nevil integration
#
'''
    py_code = notice + py_code

    # Write output
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(py_code)

    print(f"  [OK] Created: {dest_path} ({len(py_code)} bytes)")

def main():
    """Main migration script"""
    print("[TRANSLATE] Blane3 TypeScript -> Nevil Python")
    print("=" * 60)

    # Check if Blane3 exists
    if not os.path.exists(BLANE3_PATH):
        print(f"[ERROR] Blane3 not found at: {BLANE3_PATH}")
        print("   Please update BLANE3_PATH in this script")
        sys.exit(1)

    migrations = [
        # (source, destination, context)
        (
            f"{BLANE3_PATH}/lib/realtime/RealtimeClient.ts",
            f"{NEVIL_PATH}/nevil_framework/realtime/realtime_client_translated.py",
            "realtime"
        ),
        (
            f"{BLANE3_PATH}/lib/audio/AudioCaptureManager.ts",
            f"{NEVIL_PATH}/nevil_framework/realtime/audio_capture_translated.py",
            "audio_capture"
        ),
        (
            f"{BLANE3_PATH}/lib/audio/AudioPlaybackManager.ts",
            f"{NEVIL_PATH}/nevil_framework/realtime/audio_buffer_translated.py",
            "audio_playback"
        ),
    ]

    print("\n[PLAN] Migration Plan:")
    for src, dest, ctx in migrations:
        print(f"  * {os.path.basename(src)} -> {os.path.basename(dest)} ({ctx})")

    print("\n[WARNING] This is a rough translation. Manual adaptation needed for:")
    print("  - Python asyncio patterns")
    print("  - NevilNode base class integration")
    print("  - robot_hat.Music() playback (CRITICAL)")
    print("  - Message bus integration")

    input("\nPress Enter to continue or Ctrl+C to cancel...")

    print("\n[MIGRATE] Starting migration...\n")

    for src, dest, ctx in migrations:
        migrate_file(src, dest, ctx)

    print("\n" + "=" * 60)
    print("[SUCCESS] Translation complete!")
    print("\n[FILES] Generated files:")
    print("  * nevil_framework/realtime/realtime_client_translated.py")
    print("  * nevil_framework/realtime/audio_capture_translated.py")
    print("  * nevil_framework/realtime/audio_buffer_translated.py")

    print("\n[NEXT] Next steps:")
    print("  1. Review translated files")
    print("  2. Adapt for Python asyncio patterns")
    print("  3. Integrate with NevilNode base class")
    print("  4. Test on Raspberry Pi")

if __name__ == "__main__":
    main()
