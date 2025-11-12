#!/usr/bin/env python3
"""
Realtime Audio Capture Example for Nevil

Demonstrates how to use AudioCaptureManager with OpenAI Realtime API
on Raspberry Pi hardware.

Usage:
    python examples/realtime_audio_capture_example.py

Requirements:
    - Microphone connected to Raspberry Pi
    - OpenAI API key in .env file
    - PyAudio installed (pip install pyaudio)
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nevil_framework.realtime.audio_capture_manager import (
    AudioCaptureManager,
    AudioCaptureConfig,
    AudioCaptureCallbacks,
    CaptureState,
    create_audio_capture
)
from nevil_framework.realtime.realtime_connection_manager import RealtimeConnectionManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_capture():
    """
    Example 1: Basic audio capture with callbacks

    Captures audio and prints statistics.
    No WebSocket connection - just local processing.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Audio Capture")
    print("="*60)

    # Define callbacks
    def on_audio_data(base64_audio: str, volume: float):
        logger.info(f"Audio chunk: {len(base64_audio)} bytes, volume: {volume:.3f}")

    def on_volume_change(volume: float):
        # Create simple volume meter
        bar_length = int(volume * 50)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"\rVolume: {bar} {volume:.3f}", end="", flush=True)

    def on_state_change(state: CaptureState):
        logger.info(f"State changed: {state.value}")

    def on_error(error: Exception):
        logger.error(f"Error: {error}")

    # Create callbacks
    callbacks = AudioCaptureCallbacks(
        on_audio_data=on_audio_data,
        on_volume_change=on_volume_change,
        on_state_change=on_state_change,
        on_error=on_error
    )

    # Create configuration
    config = AudioCaptureConfig(
        sample_rate=24000,
        channel_count=1,
        chunk_size=4800,  # 200ms chunks
        vad_enabled=False
    )

    # Create and initialize manager
    manager = AudioCaptureManager(config=config, callbacks=callbacks)

    try:
        logger.info("Initializing audio capture...")
        manager.initialize()

        logger.info("Starting recording for 10 seconds...")
        logger.info("Speak into the microphone!")

        manager.start_recording()
        time.sleep(10)
        manager.stop_recording()

        # Print statistics
        stats = manager.get_stats()
        print("\n\nCapture Statistics:")
        print(f"  Total samples: {stats['total_samples']}")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Duration: {stats['total_samples'] / stats['sample_rate']:.2f}s")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        manager.dispose()
        logger.info("Cleanup complete")


def example_vad_capture():
    """
    Example 2: Audio capture with Voice Activity Detection

    Only processes audio when speech is detected.
    Useful for saving bandwidth and processing.
    """
    print("\n" + "="*60)
    print("Example 2: VAD-Enabled Audio Capture")
    print("="*60)

    # Track VAD state
    vad_state = {"speaking": False}

    def on_vad_speech_start():
        vad_state["speaking"] = True
        print("\n🎤 Speech detected - recording...", flush=True)

    def on_vad_speech_end():
        vad_state["speaking"] = False
        print("\n🔇 Silence detected - paused", flush=True)

    def on_audio_data(base64_audio: str, volume: float):
        if vad_state["speaking"]:
            logger.info(f"Sending audio: {len(base64_audio)} bytes")

    # Create callbacks
    callbacks = AudioCaptureCallbacks(
        on_audio_data=on_audio_data,
        on_vad_speech_start=on_vad_speech_start,
        on_vad_speech_end=on_vad_speech_end
    )

    # Create configuration with VAD enabled
    config = AudioCaptureConfig(
        sample_rate=24000,
        vad_enabled=True,
        vad_threshold=0.02  # Adjust based on environment noise
    )

    # Create manager
    manager = AudioCaptureManager(config=config, callbacks=callbacks)

    try:
        logger.info("Initializing audio capture with VAD...")
        manager.initialize()

        logger.info("Starting VAD monitoring for 20 seconds...")
        logger.info("Try speaking and being silent!")

        manager.start_recording()
        time.sleep(20)
        manager.stop_recording()

        # Print statistics
        stats = manager.get_stats()
        print("\n\nCapture Statistics:")
        print(f"  Total chunks sent: {stats['total_chunks']}")
        print(f"  VAD enabled: {stats['vad_enabled']}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        manager.dispose()


def example_realtime_integration():
    """
    Example 3: Full integration with OpenAI Realtime API

    Captures audio and streams to Realtime API WebSocket.
    Requires OpenAI API key.
    """
    print("\n" + "="*60)
    print("Example 3: Realtime API Integration")
    print("="*60)

    # Load API key
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env file")
        return

    # Create connection manager
    logger.info("Creating Realtime API connection...")
    connection = RealtimeConnectionManager(api_key=api_key)

    # Register event handlers
    def on_server_event(event):
        event_type = event.get('type', 'unknown')
        logger.info(f"Server event: {event_type}")

        if event_type == 'response.audio.delta':
            audio_data = event.get('delta', '')
            logger.info(f"Received audio delta: {len(audio_data)} bytes")
        elif event_type == 'response.text.delta':
            text = event.get('delta', '')
            logger.info(f"Received text: {text}")

    connection.register_event_handler('response.audio.delta', on_server_event)
    connection.register_event_handler('response.text.delta', on_server_event)
    connection.register_event_handler('error', lambda e: logger.error(f"API error: {e}"))

    # Create audio capture with connection manager
    logger.info("Creating audio capture manager...")
    manager = create_audio_capture(
        connection_manager=connection,
        sample_rate=24000,
        vad_enabled=True
    )

    try:
        # Start connection
        logger.info("Starting Realtime API connection...")
        connection.start()
        time.sleep(2)  # Wait for connection

        # Configure session
        logger.info("Configuring session...")
        connection.send_event({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful assistant for the Nevil robot.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        })

        logger.info("Starting audio capture...")
        logger.info("Speak to Nevil! (20 seconds)")

        manager.start_recording()
        time.sleep(20)
        manager.stop_recording()

        logger.info("Stopping capture...")

        # Print statistics
        conn_stats = connection.get_stats()
        capture_stats = manager.get_stats()

        print("\n\nSession Statistics:")
        print("Connection:")
        print(f"  Messages sent: {conn_stats['messages_sent']}")
        print(f"  Messages received: {conn_stats['messages_received']}")
        print(f"  Connected: {conn_stats['connected']}")

        print("\nAudio Capture:")
        print(f"  Total chunks: {capture_stats['total_chunks']}")
        print(f"  Total samples: {capture_stats['total_samples']}")
        print(f"  Duration: {capture_stats['total_samples'] / capture_stats['sample_rate']:.2f}s")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        manager.dispose()
        connection.stop()
        logger.info("Cleanup complete")


def example_device_selection():
    """
    Example 4: List audio devices and select specific device

    Helpful for multi-microphone setups.
    """
    print("\n" + "="*60)
    print("Example 4: Audio Device Selection")
    print("="*60)

    import pyaudio

    # List available devices
    audio = pyaudio.PyAudio()
    device_count = audio.get_device_count()

    print("\nAvailable audio input devices:")
    input_devices = []

    for i in range(device_count):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append((i, info))
            print(f"  [{i}] {info['name']}")
            print(f"      Channels: {info['maxInputChannels']}")
            print(f"      Sample Rate: {int(info['defaultSampleRate'])} Hz")

    audio.terminate()

    if not input_devices:
        print("\nNo input devices found!")
        return

    # Let user select device (or use default)
    print("\nUsing device 0 (default) for this example")
    device_index = None  # None = use default

    # Create configuration with specific device
    config = AudioCaptureConfig(
        device_index=device_index,
        sample_rate=24000
    )

    callbacks = AudioCaptureCallbacks(
        on_audio_data=lambda audio, vol: print(f".", end="", flush=True)
    )

    manager = AudioCaptureManager(config=config, callbacks=callbacks)

    try:
        manager.initialize()
        logger.info("Recording for 5 seconds...")

        manager.start_recording()
        time.sleep(5)
        manager.stop_recording()

        print("\n✓ Recording complete")

    finally:
        manager.dispose()


def main():
    """Run examples"""
    print("\n" + "="*60)
    print("Nevil Realtime Audio Capture Examples")
    print("="*60)

    examples = [
        ("Basic audio capture", example_basic_capture),
        ("VAD-enabled capture", example_vad_capture),
        ("Realtime API integration", example_realtime_integration),
        ("Device selection", example_device_selection)
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nWhich example would you like to run?")
    print("Enter number (1-4) or 'all' to run all examples: ", end="")

    try:
        choice = input().strip().lower()

        if choice == 'all':
            for name, func in examples:
                print(f"\nRunning: {name}")
                func()
                time.sleep(2)
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            print(f"\nRunning: {name}")
            func()
        else:
            print("Invalid choice. Running basic example...")
            example_basic_capture()

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
