"""
Chat Logger for Nevil v3.0

Tracks conversation pipeline steps with timing benchmarks in SQLite database.
Logs: request, STT, GPT, TTS, response with precise datetime stamps and durations.
"""

import sqlite3
import time
import uuid
import json
from datetime import datetime
from contextlib import contextmanager
from threading import Lock
import os


class ChatLogger:
    """
    SQLite-based logger for tracking conversation pipeline performance.

    Pipeline steps:
    - request: Audio capture started
    - stt: Speech-to-text (Whisper API)
    - gpt: AI response generation (OpenAI Assistants API)
    - tts: Text-to-speech synthesis
    - response: Audio playback completion
    """

    def __init__(self, db_path="logs/chat_log.db"):
        self.db_path = db_path
        self.lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database and create tables if needed"""
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS log_chat (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        step TEXT NOT NULL,
                        timestamp_start TEXT NOT NULL,
                        timestamp_end TEXT,
                        duration_ms REAL,
                        status TEXT,
                        input_text TEXT,
                        output_text TEXT,
                        metadata TEXT,
                        error_text TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for fast queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_conversation_id
                    ON log_chat(conversation_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_step
                    ON log_chat(step)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON log_chat(timestamp_start)
                """)

                conn.commit()
            finally:
                conn.close()

    def generate_conversation_id(self):
        """Generate unique conversation ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}"

    @contextmanager
    def log_step(self, conversation_id, step, input_text="", metadata=None, output_text=""):
        """
        Context manager to automatically log step timing.

        Usage:
            with chat_logger.log_step(conv_id, "stt", input_text="audio") as log_id:
                result = perform_stt()
                # Updates log with completion automatically
        """
        log_id = self._start_step(conversation_id, step, input_text, metadata)
        start_time = time.time()
        result = {"log_id": log_id, "output_text": None}

        try:
            yield result
            duration_ms = (time.time() - start_time) * 1000
            self._complete_step(
                log_id,
                duration_ms,
                "completed",
                output_text=result.get("output_text", output_text)
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._complete_step(log_id, duration_ms, "failed", error=str(e))
            raise

    def _start_step(self, conversation_id, step, input_text, metadata):
        """Log the start of a pipeline step"""
        timestamp_start = datetime.now().isoformat()

        metadata_json = json.dumps(metadata) if metadata else None

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.execute("""
                    INSERT INTO log_chat
                    (conversation_id, step, timestamp_start, status, input_text, metadata)
                    VALUES (?, ?, ?, 'started', ?, ?)
                """, (conversation_id, step, timestamp_start, input_text, metadata_json))

                log_id = cursor.lastrowid
                conn.commit()
                return log_id
            finally:
                conn.close()

    def _complete_step(self, log_id, duration_ms, status, output_text="", error=None):
        """Mark a step as completed with timing and output"""
        timestamp_end = datetime.now().isoformat()

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    UPDATE log_chat
                    SET timestamp_end = ?,
                        duration_ms = ?,
                        status = ?,
                        output_text = ?,
                        error_text = ?
                    WHERE id = ?
                """, (timestamp_end, duration_ms, status, output_text, error, log_id))

                conn.commit()
            finally:
                conn.close()

    def log_step_sync(self, conversation_id, step, input_text="", output_text="",
                      duration_ms=0, status="completed", metadata=None, error=None):
        """
        Synchronous logging for steps already completed.
        Use when you can't wrap with context manager.
        """
        timestamp_start = datetime.now().isoformat()
        timestamp_end = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("""
                    INSERT INTO log_chat
                    (conversation_id, step, timestamp_start, timestamp_end,
                     duration_ms, status, input_text, output_text, metadata, error_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (conversation_id, step, timestamp_start, timestamp_end,
                      duration_ms, status, input_text, output_text, metadata_json, error))

                conn.commit()
            finally:
                conn.close()

    def get_conversation_trace(self, conversation_id):
        """Get full trace of a conversation with all steps"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute("""
                    SELECT * FROM log_chat
                    WHERE conversation_id = ?
                    ORDER BY timestamp_start
                """, (conversation_id,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_conversation_summary(self, conversation_id):
        """
        Get summarized metrics for a conversation.
        Returns total duration and breakdown by step.
        """
        trace = self.get_conversation_trace(conversation_id)

        if not trace:
            return None

        total_duration = sum(row.get("duration_ms", 0) or 0 for row in trace)

        steps = {}
        for row in trace:
            step = row["step"]
            steps[step] = {
                "duration_ms": row.get("duration_ms", 0) or 0,
                "status": row["status"],
                "timestamp_start": row["timestamp_start"],
                "timestamp_end": row.get("timestamp_end"),
            }

        first_step = trace[0]["timestamp_start"]
        last_step = trace[-1].get("timestamp_end") or trace[-1]["timestamp_start"]

        return {
            "conversation_id": conversation_id,
            "total_duration_ms": total_duration,
            "total_duration_sec": total_duration / 1000,
            "start_time": first_step,
            "end_time": last_step,
            "steps": steps,
            "step_count": len(trace)
        }

    def get_average_step_durations(self, limit_hours=24):
        """Get average duration for each step type over recent time period"""
        cutoff_time = datetime.now().timestamp() - (limit_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute("""
                    SELECT
                        step,
                        COUNT(*) as count,
                        AVG(duration_ms) as avg_ms,
                        MIN(duration_ms) as min_ms,
                        MAX(duration_ms) as max_ms
                    FROM log_chat
                    WHERE status = 'completed'
                      AND timestamp_start > ?
                    GROUP BY step
                """, (cutoff_iso,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_slow_conversations(self, threshold_ms=5000, limit=10):
        """Find conversations that took longer than threshold"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute("""
                    SELECT
                        conversation_id,
                        SUM(duration_ms) as total_ms,
                        MIN(timestamp_start) as start_time,
                        MAX(timestamp_end) as end_time,
                        COUNT(*) as step_count
                    FROM log_chat
                    WHERE status = 'completed'
                    GROUP BY conversation_id
                    HAVING total_ms > ?
                    ORDER BY total_ms DESC
                    LIMIT ?
                """, (threshold_ms, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def get_error_rate(self, limit_hours=24):
        """Calculate error rate by step over recent time period"""
        cutoff_time = datetime.now().timestamp() - (limit_hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff_time).isoformat()

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                cursor = conn.execute("""
                    SELECT
                        step,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures,
                        ROUND(100.0 * SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate_pct
                    FROM log_chat
                    WHERE timestamp_start > ?
                    GROUP BY step
                """, (cutoff_iso,))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()

    def print_conversation_summary(self, conversation_id):
        """Pretty print a conversation summary with timing breakdown"""
        summary = self.get_conversation_summary(conversation_id)

        if not summary:
            print(f"No conversation found: {conversation_id}")
            return

        print(f"\n{'='*60}")
        print(f"Conversation: {conversation_id}")
        print(f"{'='*60}")
        print(f"Start Time:    {summary['start_time']}")
        print(f"End Time:      {summary['end_time']}")
        print(f"Total Duration: {summary['total_duration_sec']:.3f}s ({summary['total_duration_ms']:.0f}ms)")
        print(f"Steps:         {summary['step_count']}")
        print(f"\nStep Breakdown:")
        print(f"{'-'*60}")

        for step, data in summary['steps'].items():
            duration_sec = data['duration_ms'] / 1000
            status_symbol = "✓" if data['status'] == 'completed' else "✗"
            print(f"  {status_symbol} {step:12s}: {duration_sec:6.3f}s ({data['duration_ms']:7.1f}ms)")

        print(f"{'='*60}\n")


# Global singleton instance
_chat_logger = None


def get_chat_logger():
    """Get or create global ChatLogger instance"""
    global _chat_logger
    if _chat_logger is None:
        _chat_logger = ChatLogger()
    return _chat_logger
