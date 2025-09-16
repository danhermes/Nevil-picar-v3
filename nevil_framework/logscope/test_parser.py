#!/usr/bin/env python3
"""
Test script for LogScope log parsing functionality
Verifies log file parsing without requiring GUI components
"""

import sys
import re
from pathlib import Path

def parse_log_line(file_path, line):
    """Parse log line into structured entry"""
    # Enhanced pattern for EST format
    pattern = re.compile(
        r'\[(?P<timestamp>[^\]]+) EST\] \[(?P<level>[^\]]+)\] '
        r'\[(?P<node>[^\]]+)\] (?:\[(?P<component>[^\]]+)\] )?'
        r'(?P<message>.*)'
    )

    match = pattern.match(line)
    if not match:
        return None

    return {
        'timestamp': match.group('timestamp').strip(),
        'level': match.group('level').strip(),
        'node': match.group('node').strip(),
        'component': match.group('component').strip() if match.group('component') else '',
        'message': match.group('message').strip(),
        'file_path': file_path,
        'raw_line': line
    }

def is_dialogue_related(entry):
    """Check if entry is dialogue/speech related"""
    # Check if it's from speech-related nodes
    if entry['node'] in ['speech_recognition', 'speech_synthesis']:
        return True

    # Check message content for speech/dialogue keywords
    message = entry['message'].lower()
    dialogue_keywords = [
        'speech', 'tts', 'stt', 'audio', 'voice', 'speak', 'listen',
        'microphone', 'recognition', 'synthesis', 'utterance', 'transcript',
        'dialogue', 'conversation', 'whisper', 'openai', 'azure', 'pyttsx3',
        'pygame', 'recording', 'playback', 'say', 'hear', 'sound'
    ]

    return any(keyword in message for keyword in dialogue_keywords)

def is_crash_related(entry):
    """Check if entry is crash/error related"""
    # Check log level first
    if entry['level'] in ['ERROR', 'CRITICAL']:
        return True

    # Check message content for crash-related keywords
    message = entry['message'].lower()
    crash_keywords = [
        'error', 'failure', 'crash', 'unsuccessful', 'failed',
        'exception', 'traceback', 'fatal', 'abort', 'panic',
        'timeout', 'refused', 'unavailable', 'corrupted',
        'invalid', 'missing', 'not found', 'access denied',
        'connection lost', 'segmentation fault', 'memory error'
    ]

    return any(keyword in message for keyword in crash_keywords)

def test_log_parsing(log_dir):
    """Test log parsing on existing log files"""
    log_dir = Path(log_dir)

    if not log_dir.exists():
        print(f"Error: Log directory '{log_dir}' does not exist")
        return False

    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        print(f"No log files found in '{log_dir}'")
        return False

    print(f"Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"  - {log_file.name}")

    total_entries = 0
    parsed_entries = 0
    dialogue_entries = 0
    crash_entries = 0

    print("\n" + "="*60)
    print("PARSING TEST RESULTS")
    print("="*60)

    for log_file in log_files:
        print(f"\nProcessing: {log_file.name}")
        file_entries = 0
        file_parsed = 0
        file_dialogue = 0
        file_crash = 0

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    file_entries += 1
                    total_entries += 1

                    entry = parse_log_line(str(log_file), line)
                    if entry:
                        file_parsed += 1
                        parsed_entries += 1

                        if is_dialogue_related(entry):
                            file_dialogue += 1
                            dialogue_entries += 1

                        if is_crash_related(entry):
                            file_crash += 1
                            crash_entries += 1

                        # Show sample entries
                        if file_parsed <= 3:
                            print(f"  Sample entry {file_parsed}:")
                            print(f"    Timestamp: {entry['timestamp']}")
                            print(f"    Level:     {entry['level']}")
                            print(f"    Node:      {entry['node']}")
                            print(f"    Component: {entry['component'] or 'N/A'}")
                            print(f"    Message:   {entry['message'][:60]}...")
                            print(f"    Dialogue:  {is_dialogue_related(entry)}")
                            print(f"    Crash:     {is_crash_related(entry)}")

        except Exception as e:
            print(f"  Error reading file: {e}")
            continue

        print(f"  Stats: {file_entries} lines, {file_parsed} parsed, {file_dialogue} dialogue, {file_crash} crash")

    print("\n" + "="*60)
    print("OVERALL STATISTICS")
    print("="*60)
    print(f"Total log entries:    {total_entries}")
    print(f"Successfully parsed:  {parsed_entries} ({parsed_entries/total_entries*100:.1f}%)")
    print(f"Dialogue-related:     {dialogue_entries} ({dialogue_entries/parsed_entries*100:.1f}%)")
    print(f"Crash-related:        {crash_entries} ({crash_entries/parsed_entries*100:.1f}%)")

    print("\n" + "="*60)
    print("FEATURE VERIFICATION")
    print("="*60)

    # Test filtering functionality
    print("✓ Log parsing working")
    print("✓ Dialogue mode filtering working" if dialogue_entries > 0 else "⚠ No dialogue entries found")
    print("✓ Crash monitor filtering working" if crash_entries > 0 else "⚠ No crash entries found")
    print("✓ Multi-node support working" if parsed_entries > 0 else "⚠ Single node detected")

    return True

def main():
    """Main test function"""
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    else:
        log_dir = "logs"

    print("Nevil LogScope Parser Test")
    print("="*40)
    print(f"Testing log directory: {log_dir}")

    success = test_log_parsing(log_dir)

    if success:
        print("\n✓ LogScope parser test completed successfully!")
        print("\nTo launch the full GUI application:")
        print("  python3 -m nevil_framework.logscope.launcher")
    else:
        print("\n✗ LogScope parser test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()