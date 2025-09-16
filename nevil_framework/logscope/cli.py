#!/usr/bin/env python3
"""
CLI version of LogScope for headless environments
Provides log monitoring and filtering without GUI
"""

import sys
import time
import re
import argparse
from pathlib import Path
from datetime import datetime

def parse_log_line(file_path, line):
    """Parse log line into structured entry"""
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

def format_entry(entry, color=True):
    """Format log entry for CLI display"""
    if not color:
        return f"[{entry['timestamp']}] [{entry['level']:8}] [{entry['node']:15}] {entry['message']}"

    # ANSI color codes
    colors = {
        'DEBUG': '\033[96m',     # Cyan
        'INFO': '\033[92m',      # Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    level_color = colors.get(entry['level'], '')
    reset = colors['RESET']

    return f"[{entry['timestamp']}] [{level_color}{entry['level']:8}{reset}] [{entry['node']:15}] {entry['message']}"

def filter_entry(entry, levels=None, nodes=None, search=None, dialogue_mode=False, crash_mode=False):
    """Check if entry passes filters"""
    if crash_mode:
        return is_crash_related(entry)

    if dialogue_mode:
        return is_dialogue_related(entry)

    if levels and entry['level'] not in levels:
        return False

    if nodes and entry['node'] not in nodes:
        return False

    if search and search.lower() not in entry['message'].lower():
        return False

    return True

def is_dialogue_related(entry):
    """Check if entry is dialogue/speech related"""
    if entry['node'] in ['speech_recognition', 'speech_synthesis']:
        return True

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
    if entry['level'] in ['ERROR', 'CRITICAL']:
        return True

    message = entry['message'].lower()
    crash_keywords = [
        'error', 'failure', 'crash', 'unsuccessful', 'failed',
        'exception', 'traceback', 'fatal', 'abort', 'panic',
        'timeout', 'refused', 'unavailable', 'corrupted',
        'invalid', 'missing', 'not found', 'access denied',
        'connection lost', 'segmentation fault', 'memory error'
    ]

    return any(keyword in message for keyword in crash_keywords)

def tail_logs(log_dir, args):
    """Tail log files with filtering"""
    log_dir = Path(log_dir)
    file_positions = {}

    print(f"Monitoring logs in: {log_dir}")
    print(f"Filters - Levels: {args.levels or 'ALL'}, Nodes: {args.nodes or 'ALL'}")
    print(f"Special modes - Dialogue: {args.dialogue}, Crash: {args.crash}")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            log_files = list(log_dir.glob("*.log"))

            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        last_pos = file_positions.get(str(log_file), 0)
                        f.seek(last_pos)

                        new_lines = f.readlines()
                        if new_lines:
                            file_positions[str(log_file)] = f.tell()

                            for line in new_lines:
                                line = line.strip()
                                if not line:
                                    continue

                                entry = parse_log_line(str(log_file), line)
                                if entry and filter_entry(
                                    entry,
                                    levels=args.levels,
                                    nodes=args.nodes,
                                    search=args.search,
                                    dialogue_mode=args.dialogue,
                                    crash_mode=args.crash
                                ):
                                    print(format_entry(entry, color=not args.no_color))

                except Exception as e:
                    print(f"Error reading {log_file}: {e}")

            time.sleep(1)  # Poll every second

    except KeyboardInterrupt:
        print("\nLogScope CLI stopped")

def search_logs(log_dir, args):
    """Search through existing log files"""
    log_dir = Path(log_dir)
    log_files = list(log_dir.glob("*.log"))

    if not log_files:
        print(f"No log files found in {log_dir}")
        return

    matches = 0
    total_entries = 0

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    total_entries += 1
                    entry = parse_log_line(str(log_file), line)

                    if entry and filter_entry(
                        entry,
                        levels=args.levels,
                        nodes=args.nodes,
                        search=args.search,
                        dialogue_mode=args.dialogue,
                        crash_mode=args.crash
                    ):
                        matches += 1
                        if args.count:
                            continue

                        print(format_entry(entry, color=not args.no_color))

                        if args.max_results and matches >= args.max_results:
                            print(f"\n... (stopped at {args.max_results} results)")
                            break

        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    if args.count:
        print(f"Found {matches} matching entries out of {total_entries} total")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Nevil LogScope CLI - Headless Log Monitor")
    parser.add_argument("--log-dir", "-d", default="logs", help="Log directory to monitor")
    parser.add_argument("--levels", "-l", nargs="+",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Filter by log levels")
    parser.add_argument("--nodes", "-n", nargs="+",
                       help="Filter by node names")
    parser.add_argument("--search", "-s", help="Search in log messages")
    parser.add_argument("--dialogue", action="store_true",
                       help="Dialogue mode - show only speech-related logs")
    parser.add_argument("--crash", action="store_true",
                       help="Crash mode - show only error/crash-related logs")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--count", "-c", action="store_true",
                       help="Only show count of matches (search mode)")
    parser.add_argument("--max-results", "-m", type=int, default=1000,
                       help="Maximum results to show (search mode)")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Tail command (default)
    tail_parser = subparsers.add_parser("tail", help="Monitor logs in real-time")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search existing logs")

    args = parser.parse_args()

    # Default to tail command
    if not args.command:
        args.command = "tail"

    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Error: Log directory '{log_dir}' does not exist")
        sys.exit(1)

    print(f"Nevil LogScope CLI - {args.command.title()} Mode")
    print("=" * 50)

    if args.command == "tail":
        tail_logs(log_dir, args)
    elif args.command == "search":
        search_logs(log_dir, args)

if __name__ == "__main__":
    main()