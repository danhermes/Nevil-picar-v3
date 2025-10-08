#!/usr/bin/env python3
"""
Chat Analytics Tool for Nevil v3.0

Query and analyze conversation performance logs.
"""

import argparse
import sys
from nevil_framework.chat_logger import ChatLogger


def cmd_summary(logger, args):
    """Show summary for a specific conversation"""
    logger.print_conversation_summary(args.conversation_id)


def cmd_trace(logger, args):
    """Show full trace for a conversation"""
    trace = logger.get_conversation_trace(args.conversation_id)

    if not trace:
        print(f"No conversation found: {args.conversation_id}")
        return

    print(f"\n{'='*80}")
    print(f"Full Trace: {args.conversation_id}")
    print(f"{'='*80}\n")

    for row in trace:
        print(f"Step: {row['step']}")
        print(f"  Start:    {row['timestamp_start']}")
        print(f"  End:      {row.get('timestamp_end', 'N/A')}")
        print(f"  Duration: {row.get('duration_ms', 0):.1f}ms")
        print(f"  Status:   {row['status']}")

        if row.get('input_text'):
            print(f"  Input:    {row['input_text'][:100]}")
        if row.get('output_text'):
            print(f"  Output:   {row['output_text'][:100]}")
        if row.get('error_text'):
            print(f"  Error:    {row['error_text'][:100]}")

        print()


def cmd_averages(logger, args):
    """Show average durations by step"""
    averages = logger.get_average_step_durations(args.hours)

    print(f"\n{'='*60}")
    print(f"Average Step Durations (last {args.hours} hours)")
    print(f"{'='*60}")
    print(f"{'Step':<15} {'Count':>8} {'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10}")
    print(f"{'-'*60}")

    for row in averages:
        print(f"{row['step']:<15} {row['count']:>8} "
              f"{row['avg_ms']:>10.1f} {row['min_ms']:>10.1f} {row['max_ms']:>10.1f}")

    print(f"{'='*60}\n")


def cmd_slow(logger, args):
    """Show slowest conversations"""
    slow = logger.get_slow_conversations(args.threshold, args.limit)

    print(f"\n{'='*80}")
    print(f"Slowest Conversations (>{args.threshold}ms)")
    print(f"{'='*80}")

    if not slow:
        print("No slow conversations found.")
        return

    print(f"{'Conversation ID':<30} {'Duration (s)':>12} {'Steps':>8} {'Start Time':<20}")
    print(f"{'-'*80}")

    for row in slow:
        duration_sec = row['total_ms'] / 1000
        print(f"{row['conversation_id']:<30} {duration_sec:>12.3f} "
              f"{row['step_count']:>8} {row['start_time']:<20}")

    print(f"{'='*80}\n")


def cmd_errors(logger, args):
    """Show error rates by step"""
    errors = logger.get_error_rate(args.hours)

    print(f"\n{'='*60}")
    print(f"Error Rates by Step (last {args.hours} hours)")
    print(f"{'='*60}")
    print(f"{'Step':<15} {'Total':>8} {'Failures':>10} {'Error Rate':>12}")
    print(f"{'-'*60}")

    for row in errors:
        print(f"{row['step']:<15} {row['total']:>8} "
              f"{row['failures']:>10} {row['error_rate_pct']:>11.2f}%")

    print(f"{'='*60}\n")


def cmd_recent(logger, args):
    """Show most recent conversations"""
    import sqlite3

    conn = sqlite3.connect(logger.db_path)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.execute("""
            SELECT DISTINCT conversation_id, MIN(timestamp_start) as start_time
            FROM log_chat
            GROUP BY conversation_id
            ORDER BY start_time DESC
            LIMIT ?
        """, (args.limit,))

        rows = cursor.fetchall()

        print(f"\n{'='*80}")
        print(f"Recent Conversations (last {args.limit})")
        print(f"{'='*80}")

        if not rows:
            print("No conversations found.")
            return

        print(f"{'Conversation ID':<30} {'Start Time':<30}")
        print(f"{'-'*80}")

        for row in rows:
            print(f"{row['conversation_id']:<30} {row['start_time']:<30}")

        print(f"{'='*80}\n")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Nevil Chat Analytics - Query conversation performance logs"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Summary command
    parser_summary = subparsers.add_parser('summary', help='Show conversation summary')
    parser_summary.add_argument('conversation_id', help='Conversation ID')

    # Trace command
    parser_trace = subparsers.add_parser('trace', help='Show full conversation trace')
    parser_trace.add_argument('conversation_id', help='Conversation ID')

    # Averages command
    parser_avg = subparsers.add_parser('averages', help='Show average step durations')
    parser_avg.add_argument('--hours', type=int, default=24,
                           help='Time window in hours (default: 24)')

    # Slow conversations command
    parser_slow = subparsers.add_parser('slow', help='Show slowest conversations')
    parser_slow.add_argument('--threshold', type=int, default=5000,
                            help='Duration threshold in ms (default: 5000)')
    parser_slow.add_argument('--limit', type=int, default=10,
                            help='Number of results (default: 10)')

    # Errors command
    parser_errors = subparsers.add_parser('errors', help='Show error rates by step')
    parser_errors.add_argument('--hours', type=int, default=24,
                              help='Time window in hours (default: 24)')

    # Recent command
    parser_recent = subparsers.add_parser('recent', help='Show recent conversations')
    parser_recent.add_argument('--limit', type=int, default=10,
                              help='Number of results (default: 10)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    logger = ChatLogger()

    commands = {
        'summary': cmd_summary,
        'trace': cmd_trace,
        'averages': cmd_averages,
        'slow': cmd_slow,
        'errors': cmd_errors,
        'recent': cmd_recent,
    }

    commands[args.command](logger, args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
