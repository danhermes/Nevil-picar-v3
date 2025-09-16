#!/usr/bin/env python3
"""
Speech Lifecycle Debug Tool for Nevil
Tracks the "talks to himself" issue by analyzing speech state transitions
"""

import sys
import re
from pathlib import Path
from datetime import datetime

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object"""
    try:
        # Remove EST and parse
        clean_ts = timestamp_str.replace(' EST', '')
        return datetime.strptime(clean_ts, '%Y-%m-%d %H:%M:%S,%f')
    except:
        return None

def analyze_speech_lifecycle(log_dir):
    """Analyze speech recognition and synthesis logs for synchronization issues"""
    log_dir = Path(log_dir)

    # Read logs
    speech_rec_file = log_dir / "speech_recognition.log"
    speech_syn_file = log_dir / "speech_synthesis.log"

    if not speech_rec_file.exists() or not speech_syn_file.exists():
        print("Error: Speech log files not found")
        return

    print("🔍 Analyzing Speech Lifecycle Synchronization")
    print("=" * 60)

    # Parse events
    events = []

    # Parse speech recognition events
    print("📥 Reading speech recognition events...")
    with open(speech_rec_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # Look for key state transitions
            if "Started discrete speech listening" in line:
                timestamp = extract_timestamp(line)
                events.append({
                    'timestamp': timestamp,
                    'type': 'listening_started',
                    'source': 'speech_recognition',
                    'message': 'Started listening',
                    'line': line_num
                })
            elif "Stopped discrete speech listening" in line:
                timestamp = extract_timestamp(line)
                events.append({
                    'timestamp': timestamp,
                    'type': 'listening_stopped',
                    'source': 'speech_recognition',
                    'message': 'Stopped listening',
                    'line': line_num
                })
            elif "Resumed speech recognition - system finished speaking" in line:
                timestamp = extract_timestamp(line)
                events.append({
                    'timestamp': timestamp,
                    'type': 'listening_resumed',
                    'source': 'speech_recognition',
                    'message': 'Resumed after TTS finished',
                    'line': line_num
                })
            elif "✓ Speech processed:" in line:
                timestamp = extract_timestamp(line)
                # Extract the recognized text
                speech_match = re.search(r"✓ Speech processed: '([^']+)'", line)
                speech_text = speech_match.group(1) if speech_match else "Unknown"
                events.append({
                    'timestamp': timestamp,
                    'type': 'speech_recognized',
                    'source': 'speech_recognition',
                    'message': f'Recognized: "{speech_text[:50]}..."',
                    'full_text': speech_text,
                    'line': line_num
                })

    # Parse speech synthesis events
    print("📤 Reading speech synthesis events...")
    with open(speech_syn_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            if "Processing TTS:" in line:
                timestamp = extract_timestamp(line)
                # Extract TTS text
                tts_match = re.search(r"Processing TTS: '([^']+)'", line)
                tts_text = tts_match.group(1) if tts_match else "Unknown"
                events.append({
                    'timestamp': timestamp,
                    'type': 'tts_started',
                    'source': 'speech_synthesis',
                    'message': f'TTS Started: "{tts_text[:50]}..."',
                    'full_text': tts_text,
                    'line': line_num
                })
            elif "✓ TTS completed:" in line:
                timestamp = extract_timestamp(line)
                # Extract completion time
                time_match = re.search(r"in ([\d.]+)s", line)
                duration = time_match.group(1) if time_match else "?"
                events.append({
                    'timestamp': timestamp,
                    'type': 'tts_completed',
                    'source': 'speech_synthesis',
                    'message': f'TTS Completed ({duration}s)',
                    'duration': duration,
                    'line': line_num
                })
            elif "Stopping current synthesis due to mode change" in line:
                timestamp = extract_timestamp(line)
                events.append({
                    'timestamp': timestamp,
                    'type': 'tts_interrupted',
                    'source': 'speech_synthesis',
                    'message': 'TTS Interrupted (mode change)',
                    'line': line_num
                })

    # Sort events by timestamp
    events = [e for e in events if e['timestamp']]
    events.sort(key=lambda x: x['timestamp'])

    print(f"📊 Found {len(events)} speech events")
    print()

    # Analyze patterns
    analyze_timing_issues(events)
    find_self_talk_patterns(events)
    show_recent_timeline(events[-20:] if len(events) > 20 else events)

def extract_timestamp(line):
    """Extract timestamp from log line"""
    match = re.match(r'\[([^\]]+) EST\]', line)
    if match:
        return parse_timestamp(match.group(1))
    return None

def analyze_timing_issues(events):
    """Analyze timing between TTS completion and listening resumption"""
    print("⏱️  TIMING ANALYSIS")
    print("-" * 40)

    tts_gaps = []
    listening_overlaps = []

    for i in range(len(events) - 1):
        current = events[i]
        next_event = events[i + 1]

        # Check for gaps between TTS completion and listening resumption
        if (current['type'] == 'tts_completed' and
            next_event['type'] == 'listening_resumed'):
            gap = (next_event['timestamp'] - current['timestamp']).total_seconds()
            tts_gaps.append(gap)
            if gap > 2.0:  # Suspicious gap
                print(f"⚠️  Long gap: {gap:.2f}s between TTS completion and listening resumption")

        # Check for listening during TTS
        if (current['type'] == 'listening_started' and
            next_event['type'] == 'tts_started'):
            overlap = (next_event['timestamp'] - current['timestamp']).total_seconds()
            if overlap < 1.0:  # Listening started too close to TTS
                listening_overlaps.append(overlap)
                print(f"🚨 POTENTIAL SELF-TALK: Listening started {overlap:.2f}s before TTS")

    if tts_gaps:
        avg_gap = sum(tts_gaps) / len(tts_gaps)
        print(f"📈 Average TTS→Listening gap: {avg_gap:.2f}s")
        print(f"📈 Max gap: {max(tts_gaps):.2f}s, Min gap: {min(tts_gaps):.2f}s")

    if listening_overlaps:
        print(f"🚨 Found {len(listening_overlaps)} potential self-talk events!")
    else:
        print("✅ No obvious timing overlaps detected")

    print()

def find_self_talk_patterns(events):
    """Find patterns where Nevil might be talking to himself"""
    print("🗣️  SELF-TALK PATTERN ANALYSIS")
    print("-" * 40)

    self_talk_sequences = []
    current_sequence = []

    for i, event in enumerate(events):
        if event['type'] == 'speech_recognized':
            # Check if this recognition happened too soon after TTS started
            recent_tts = [e for e in events[max(0, i-5):i]
                         if e['type'] == 'tts_started']

            if recent_tts:
                last_tts = recent_tts[-1]
                time_diff = (event['timestamp'] - last_tts['timestamp']).total_seconds()

                if time_diff < 3.0:  # Recognition within 3 seconds of TTS start
                    print(f"🚨 SELF-TALK DETECTED:")
                    print(f"   TTS: \"{last_tts.get('full_text', 'Unknown')[:60]}...\"")
                    print(f"   Recognition: \"{event.get('full_text', 'Unknown')[:60]}...\"")
                    print(f"   Time gap: {time_diff:.2f}s")
                    print(f"   Lines: TTS={last_tts['line']}, Recognition={event['line']}")
                    print()

                    current_sequence.append((last_tts, event, time_diff))

    if not current_sequence:
        print("✅ No obvious self-talk patterns detected in recent logs")
    else:
        print(f"🚨 Found {len(current_sequence)} potential self-talk sequences")

    print()

def show_recent_timeline(events):
    """Show recent event timeline"""
    print("📅 RECENT EVENT TIMELINE")
    print("-" * 40)

    for event in events:
        time_str = event['timestamp'].strftime('%H:%M:%S.%f')[:-3]
        source_emoji = "🎤" if event['source'] == 'speech_recognition' else "🔊"
        type_colors = {
            'listening_started': '🟢',
            'listening_stopped': '🔴',
            'listening_resumed': '🟡',
            'speech_recognized': '💬',
            'tts_started': '🗣️',
            'tts_completed': '✅',
            'tts_interrupted': '❌'
        }

        color = type_colors.get(event['type'], '⚪')
        print(f"{time_str} {source_emoji} {color} {event['message']}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
    else:
        log_dir = "logs"

    print("Nevil Speech Lifecycle Debug Tool")
    print("Analyzing 'talks to himself' synchronization issue")
    print()

    analyze_speech_lifecycle(log_dir)

    print()
    print("💡 RECOMMENDATIONS:")
    print("1. If TTS→Listening gaps are inconsistent, check message bus timing")
    print("2. If self-talk detected, verify TTS completion signals are proper")
    print("3. Consider adding explicit speech recognition pause during TTS")
    print("4. Use LogScope dialogue mode to monitor this in real-time:")
    print("   python3 -m nevil_framework.logscope.cli --dialogue")

if __name__ == "__main__":
    main()