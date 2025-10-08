#!/usr/bin/env python3
"""
Example custom queries for chat log database.
Shows how to extract insights beyond the built-in analytics commands.
"""

import sqlite3
from datetime import datetime, timedelta
import json


def connect_db(db_path="logs/chat_log.db"):
    """Connect to chat log database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def conversations_per_hour(conn, hours=24):
    """Count conversations per hour"""
    print(f"\nConversations per Hour (last {hours} hours)")
    print("=" * 60)

    cursor = conn.execute("""
        SELECT
            strftime('%Y-%m-%d %H:00', timestamp_start) as hour,
            COUNT(DISTINCT conversation_id) as count
        FROM log_chat
        WHERE step = 'request'
          AND timestamp_start > datetime('now', '-' || ? || ' hours')
        GROUP BY hour
        ORDER BY hour DESC
    """, (hours,))

    print(f"{'Hour':<20} {'Conversations':>15}")
    print("-" * 60)
    for row in cursor:
        print(f"{row['hour']:<20} {row['count']:>15}")


def busiest_times(conn, limit=10):
    """Find busiest hours of the day"""
    print(f"\nBusiest Hours of Day (top {limit})")
    print("=" * 60)

    cursor = conn.execute("""
        SELECT
            strftime('%H', timestamp_start) as hour_of_day,
            COUNT(DISTINCT conversation_id) as count
        FROM log_chat
        WHERE step = 'request'
        GROUP BY hour_of_day
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    print(f"{'Hour':<20} {'Conversations':>15}")
    print("-" * 60)
    for row in cursor:
        hour = int(row['hour_of_day'])
        hour_12 = hour % 12 or 12
        am_pm = "AM" if hour < 12 else "PM"
        print(f"{hour_12:02d}:00 {am_pm:<13} {row['count']:>15}")


def step_success_rate(conn):
    """Calculate success rate for each step"""
    print("\nStep Success Rates")
    print("=" * 60)

    cursor = conn.execute("""
        SELECT
            step,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
        FROM log_chat
        GROUP BY step
        ORDER BY step
    """)

    print(f"{'Step':<15} {'Total':>10} {'Completed':>12} {'Success %':>12}")
    print("-" * 60)
    for row in cursor:
        print(f"{row['step']:<15} {row['total']:>10} {row['completed']:>12} {row['success_rate']:>11}%")


def longest_conversations(conn, limit=5):
    """Find longest end-to-end conversations"""
    print(f"\nLongest End-to-End Conversations (top {limit})")
    print("=" * 80)

    cursor = conn.execute("""
        SELECT
            conversation_id,
            MIN(timestamp_start) as start_time,
            MAX(timestamp_end) as end_time,
            (julianday(MAX(timestamp_end)) - julianday(MIN(timestamp_start))) * 86400 as duration_sec
        FROM log_chat
        WHERE status = 'completed'
        GROUP BY conversation_id
        ORDER BY duration_sec DESC
        LIMIT ?
    """, (limit,))

    print(f"{'Conversation ID':<30} {'Duration (s)':>15} {'Start Time':<25}")
    print("-" * 80)
    for row in cursor:
        print(f"{row['conversation_id']:<30} {row['duration_sec']:>15.2f} {row['start_time']:<25}")


def step_duration_percentiles(conn, step):
    """Calculate percentile distribution for a step"""
    print(f"\nDuration Percentiles for '{step}' Step")
    print("=" * 60)

    # Get all durations for this step
    cursor = conn.execute("""
        SELECT duration_ms
        FROM log_chat
        WHERE step = ? AND status = 'completed'
        ORDER BY duration_ms
    """, (step,))

    durations = [row[0] for row in cursor.fetchall()]

    if not durations:
        print("No data available")
        return

    def percentile(data, p):
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1 if (f + 1) < len(data) else f
        if c == f:
            return data[f]
        return data[f] + (data[c] - data[f]) * (k - f)

    percentiles = [10, 25, 50, 75, 90, 95, 99]
    print(f"{'Percentile':<15} {'Duration (ms)':>15}")
    print("-" * 60)
    for p in percentiles:
        value = percentile(durations, p)
        print(f"P{p:<14} {value:>15.1f}")

    print(f"\n{'Samples':<15} {len(durations):>15}")


def common_errors(conn, limit=10):
    """Find most common error messages"""
    print(f"\nMost Common Errors (top {limit})")
    print("=" * 80)

    cursor = conn.execute("""
        SELECT
            step,
            error_text,
            COUNT(*) as count,
            MAX(timestamp_start) as last_occurrence
        FROM log_chat
        WHERE status = 'failed' AND error_text IS NOT NULL
        GROUP BY step, error_text
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    if not rows:
        print("No errors found")
        return

    print(f"{'Step':<12} {'Count':>8} {'Last Seen':<25} {'Error':<30}")
    print("-" * 80)
    for row in rows:
        error = row['error_text'][:30] + "..." if len(row['error_text']) > 30 else row['error_text']
        print(f"{row['step']:<12} {row['count']:>8} {row['last_occurrence']:<25} {error:<30}")


def conversation_timeline(conn, conversation_id):
    """Show detailed timeline for a conversation"""
    print(f"\nDetailed Timeline: {conversation_id}")
    print("=" * 80)

    cursor = conn.execute("""
        SELECT *
        FROM log_chat
        WHERE conversation_id = ?
        ORDER BY timestamp_start
    """, (conversation_id,))

    rows = cursor.fetchall()
    if not rows:
        print("Conversation not found")
        return

    start_time = None
    for i, row in enumerate(rows):
        if start_time is None:
            start_time = datetime.fromisoformat(row['timestamp_start'])
            elapsed_ms = 0
        else:
            current_time = datetime.fromisoformat(row['timestamp_start'])
            elapsed_ms = (current_time - start_time).total_seconds() * 1000

        print(f"\n[{i+1}] {row['step'].upper()} ({row['status']})")
        print(f"    Time from start: +{elapsed_ms:.0f}ms")
        print(f"    Duration: {row['duration_ms']:.1f}ms" if row['duration_ms'] else "    Duration: N/A")

        if row['input_text']:
            input_preview = row['input_text'][:50] + "..." if len(row['input_text']) > 50 else row['input_text']
            print(f"    Input: {input_preview}")

        if row['output_text']:
            output_preview = row['output_text'][:50] + "..." if len(row['output_text']) > 50 else row['output_text']
            print(f"    Output: {output_preview}")

        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
                print(f"    Metadata: {metadata}")
            except:
                pass

        if row['error_text']:
            print(f"    ERROR: {row['error_text']}")


def step_correlation(conn):
    """Analyze correlation between step durations"""
    print("\nStep Duration Correlation")
    print("=" * 60)
    print("(Analyzing if slow steps tend to occur together)")
    print()

    # Get conversations with all steps completed
    cursor = conn.execute("""
        SELECT
            conversation_id,
            MAX(CASE WHEN step = 'request' THEN duration_ms END) as request_ms,
            MAX(CASE WHEN step = 'stt' THEN duration_ms END) as stt_ms,
            MAX(CASE WHEN step = 'gpt' THEN duration_ms END) as gpt_ms,
            MAX(CASE WHEN step = 'tts' THEN duration_ms END) as tts_ms,
            MAX(CASE WHEN step = 'response' THEN duration_ms END) as response_ms
        FROM log_chat
        WHERE status = 'completed'
        GROUP BY conversation_id
        HAVING COUNT(DISTINCT step) = 5
    """)

    rows = cursor.fetchall()
    if len(rows) < 2:
        print("Not enough data for correlation analysis")
        return

    print(f"Analyzed {len(rows)} complete conversations")
    print("\nNote: Manual correlation calculation would go here.")
    print("For production, consider using numpy/pandas for statistical analysis.")


def main():
    """Run all example queries"""
    conn = connect_db()

    try:
        print("\n" + "="*80)
        print("Chat Log Database Analysis - Custom Queries")
        print("="*80)

        conversations_per_hour(conn, hours=168)  # Last week
        busiest_times(conn)
        step_success_rate(conn)
        longest_conversations(conn)
        step_duration_percentiles(conn, "gpt")
        common_errors(conn)
        step_correlation(conn)

        # Show timeline for most recent conversation
        cursor = conn.execute("""
            SELECT DISTINCT conversation_id
            FROM log_chat
            ORDER BY timestamp_start DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            conversation_timeline(conn, row['conversation_id'])

        print("\n" + "="*80)
        print("Analysis complete!")
        print("="*80 + "\n")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
