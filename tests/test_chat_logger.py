#!/usr/bin/env python3
"""
Test script for chat logging system.
Creates sample conversation logs to demonstrate functionality.
"""

import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nevil_framework.chat_logger import get_chat_logger


def simulate_conversation(logger):
    """Simulate a complete conversation with all 5 steps"""
    # Generate conversation ID
    conversation_id = logger.generate_conversation_id()
    print(f"\nSimulating conversation: {conversation_id}")

    # Step 1: REQUEST (audio capture)
    print("  [1/5] REQUEST - Capturing audio...")
    with logger.log_step(conversation_id, "request",
                        metadata={"source": "microphone", "device": "default"}) as req_log:
        time.sleep(0.15)  # Simulate 150ms audio capture

    # Step 2: STT (speech-to-text)
    print("  [2/5] STT - Converting speech to text...")
    with logger.log_step(conversation_id, "stt",
                        input_text="<audio_data>",
                        metadata={"model": "whisper-1", "language": "en-US"}) as stt_log:
        time.sleep(1.2)  # Simulate 1.2s STT processing
        stt_log["output_text"] = "What is the weather like today?"

    # Step 3: GPT (AI response)
    print("  [3/5] GPT - Generating AI response...")
    with logger.log_step(conversation_id, "gpt",
                        input_text="What is the weather like today?",
                        metadata={
                            "model": "gpt-4",
                            "assistant_id": "asst_test123",
                            "confidence": 0.95
                        }) as gpt_log:
        time.sleep(3.4)  # Simulate 3.4s GPT processing
        gpt_log["output_text"] = "I can see it's sunny outside with clear blue skies!"

    # Step 4: TTS (text-to-speech)
    print("  [4/5] TTS - Synthesizing speech...")
    with logger.log_step(conversation_id, "tts",
                        input_text="I can see it's sunny outside with clear blue skies!",
                        metadata={"voice": "onyx", "model": "tts-1"}) as tts_log:
        time.sleep(1.4)  # Simulate 1.4s TTS synthesis
        tts_log["output_text"] = "<audio_file>"

    # Step 5: RESPONSE (playback)
    print("  [5/5] RESPONSE - Playing audio...")
    with logger.log_step(conversation_id, "response",
                        input_text="<audio_file>",
                        metadata={"playback_device": "speaker"}) as resp_log:
        time.sleep(0.45)  # Simulate 450ms playback
        resp_log["output_text"] = "playback_complete"

    print(f"✓ Conversation complete: {conversation_id}")
    return conversation_id


def simulate_failed_conversation(logger):
    """Simulate a conversation that fails during GPT step"""
    conversation_id = logger.generate_conversation_id()
    print(f"\nSimulating failed conversation: {conversation_id}")

    try:
        # Step 1: REQUEST
        print("  [1/5] REQUEST - Capturing audio...")
        with logger.log_step(conversation_id, "request") as req_log:
            time.sleep(0.15)

        # Step 2: STT
        print("  [2/5] STT - Converting speech...")
        with logger.log_step(conversation_id, "stt",
                            input_text="<audio_data>") as stt_log:
            time.sleep(1.1)
            stt_log["output_text"] = "Tell me a story"

        # Step 3: GPT - FAILS
        print("  [3/5] GPT - Generating response (will fail)...")
        with logger.log_step(conversation_id, "gpt",
                            input_text="Tell me a story",
                            metadata={"model": "gpt-4"}) as gpt_log:
            time.sleep(0.5)
            raise Exception("API rate limit exceeded")

    except Exception as e:
        print(f"✗ Conversation failed: {e}")
        return conversation_id


def main():
    logger = get_chat_logger()
    print("="*60)
    print("Chat Logger Test Script")
    print("="*60)

    # Simulate multiple successful conversations
    conv_ids = []
    for i in range(3):
        conv_id = simulate_conversation(logger)
        conv_ids.append(conv_id)
        time.sleep(0.5)

    # Simulate a failed conversation
    failed_id = simulate_failed_conversation(logger)

    # Show analytics
    print("\n" + "="*60)
    print("Analytics")
    print("="*60)

    # Show summary for first conversation
    print("\n1. Conversation Summary:")
    logger.print_conversation_summary(conv_ids[0])

    # Show average durations
    print("\n2. Average Step Durations:")
    averages = logger.get_average_step_durations(limit_hours=1)
    print(f"\n{'Step':<15} {'Count':>8} {'Avg (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10}")
    print("-"*60)
    for row in averages:
        print(f"{row['step']:<15} {row['count']:>8} "
              f"{row['avg_ms']:>10.1f} {row['min_ms']:>10.1f} {row['max_ms']:>10.1f}")

    # Show error rates
    print("\n3. Error Rates:")
    errors = logger.get_error_rate(limit_hours=1)
    print(f"\n{'Step':<15} {'Total':>8} {'Failures':>10} {'Error Rate':>12}")
    print("-"*60)
    for row in errors:
        print(f"{row['step']:<15} {row['total']:>8} "
              f"{row['failures']:>10} {row['error_rate_pct']:>11.2f}%")

    print("\n" + "="*60)
    print("Test complete! Database: logs/chat_log.db")
    print("="*60)

    print("\nTry these commands:")
    print(f"  python3 -m nevil_framework.chat_analytics summary {conv_ids[0]}")
    print(f"  python3 -m nevil_framework.chat_analytics trace {failed_id}")
    print(f"  python3 -m nevil_framework.chat_analytics averages")
    print(f"  python3 -m nevil_framework.chat_analytics recent")


if __name__ == '__main__':
    main()
