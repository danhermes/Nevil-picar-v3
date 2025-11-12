#!/usr/bin/env python3
"""
Realtime Connection Manager - Usage Example

Demonstrates how to use the production-ready RealtimeConnectionManager
for connecting to OpenAI's Realtime API.

This example shows:
1. Basic connection setup
2. Event handling
3. Audio streaming
4. Session management
5. Metrics monitoring
6. Graceful shutdown
"""

import os
import sys
import time
import base64
import signal
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from nevil_framework.realtime import (
    create_realtime_connection,
    ConnectionState
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealtimeExample:
    """Example application using RealtimeConnectionManager"""

    def __init__(self):
        # Get ephemeral token from environment
        ephemeral_token = os.getenv('OPENAI_EPHEMERAL_TOKEN')
        if not ephemeral_token:
            logger.error("OPENAI_EPHEMERAL_TOKEN not set")
            logger.info("Get token from: https://platform.openai.com/api-keys")
            sys.exit(1)

        # Create connection manager
        self.manager = create_realtime_connection(
            ephemeral_token=ephemeral_token,
            model="gpt-4o-realtime-preview-2024-12-17",
            voice="cedar",
            debug=True
        )

        # Setup event handlers
        self.setup_handlers()

        # Running flag
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_handlers(self):
        """Register event handlers"""

        # Connection events
        self.manager.on('connect', self.on_connect)
        self.manager.on('disconnect', self.on_disconnect)
        self.manager.on('reconnecting', self.on_reconnecting)
        self.manager.on('state_change', self.on_state_change)
        self.manager.on('error', self.on_error)

        # Session events
        self.manager.on('session.created', self.on_session_created)
        self.manager.on('session.updated', self.on_session_updated)

        # Response events
        self.manager.on('response.created', self.on_response_created)
        self.manager.on('response.done', self.on_response_done)

        # Audio events
        self.manager.on('response.audio.delta', self.on_audio_delta)
        self.manager.on('response.audio_transcript.delta', self.on_transcript_delta)

        # Conversation events
        self.manager.on('conversation.item.created', self.on_conversation_item)

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def on_connect(self):
        """Handle connection established"""
        logger.info("✅ Connected to OpenAI Realtime API")

        # Update session with custom instructions
        # Note: This is handled automatically by the manager,
        # but you can update it at runtime if needed

    def on_disconnect(self, reason):
        """Handle disconnection"""
        logger.warning(f"❌ Disconnected: {reason}")

    def on_reconnecting(self, options):
        """Handle reconnection attempt"""
        logger.warning(
            f"🔄 Reconnecting... "
            f"attempt {options.attempt}/{options.max_attempts}, "
            f"delay: {options.delay}s"
        )

    def on_state_change(self, data):
        """Handle state transitions"""
        logger.info(
            f"📊 State: {data['from'].value} → {data['to'].value}"
        )

    def on_error(self, error):
        """Handle errors"""
        logger.error(f"❌ Error: {error}")

    def on_session_created(self, event):
        """Handle session creation"""
        logger.info("🎉 Session created")
        logger.debug(f"Session details: {event}")

    def on_session_updated(self, event):
        """Handle session updates"""
        logger.info("🔄 Session updated")
        logger.debug(f"Session config: {event}")

    def on_response_created(self, event):
        """Handle response creation"""
        logger.info("💬 AI response started")

    def on_response_done(self, event):
        """Handle response completion"""
        logger.info("✅ AI response complete")

        # Get response details
        response = event.get('response', {})
        usage = response.get('usage', {})

        logger.info(
            f"   Tokens: input={usage.get('input_tokens', 0)}, "
            f"output={usage.get('output_tokens', 0)}"
        )

    def on_audio_delta(self, event):
        """Handle audio chunk received"""
        delta = event.get('delta')
        if delta:
            # Audio data is base64 encoded PCM16
            audio_bytes = base64.b64decode(delta)
            logger.debug(f"🔊 Audio chunk: {len(audio_bytes)} bytes")

            # Here you would:
            # 1. Decode PCM16 audio
            # 2. Play through speakers
            # 3. Or save to file

    def on_transcript_delta(self, event):
        """Handle transcript chunk"""
        delta = event.get('delta')
        if delta:
            # Print transcript as it arrives (streaming)
            print(delta, end='', flush=True)

    def on_conversation_item(self, event):
        """Handle new conversation item"""
        item = event.get('item', {})
        item_type = item.get('type')
        logger.info(f"💬 New conversation item: {item_type}")

    # ========================================================================
    # Application Logic
    # ========================================================================

    def run(self):
        """Main application loop"""
        logger.info("Starting Realtime Connection Example")

        # Start connection in background
        self.manager.start()

        # Wait for connection
        logger.info("Waiting for connection...")
        for _ in range(30):  # Wait up to 30 seconds
            if self.manager.is_connected():
                break
            time.sleep(1)
        else:
            logger.error("Connection timeout")
            return

        logger.info("Connection established! Ready for interaction.")
        logger.info("=" * 60)

        # Example: Send a text message
        self.send_text_message("Hello! Can you hear me?")

        # Main loop - monitor status
        while self.running:
            try:
                # Display metrics every 10 seconds
                self.display_metrics()
                time.sleep(10)

            except KeyboardInterrupt:
                break

        logger.info("Shutting down...")

    def send_text_message(self, text: str):
        """Send a text message to the AI"""
        logger.info(f"📤 Sending: {text}")

        # Create conversation item with text
        message = {
            'type': 'conversation.item.create',
            'item': {
                'type': 'message',
                'role': 'user',
                'content': [
                    {
                        'type': 'input_text',
                        'text': text
                    }
                ]
            }
        }

        # Send and request response
        self.manager.send_sync(message)
        self.manager.send_sync({'type': 'response.create'})

    def send_audio_message(self, audio_path: str):
        """Send an audio file to the AI"""
        logger.info(f"📤 Sending audio: {audio_path}")

        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        # Encode to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        # Send audio buffer
        self.manager.send_sync({
            'type': 'input_audio_buffer.append',
            'audio': audio_base64
        })

        # Commit and request response
        self.manager.send_sync({'type': 'input_audio_buffer.commit'})
        self.manager.send_sync({'type': 'response.create'})

    def display_metrics(self):
        """Display connection metrics"""
        metrics = self.manager.get_metrics()
        event_stats = self.manager.get_event_stats()

        logger.info("=" * 60)
        logger.info("📊 CONNECTION METRICS")
        logger.info(f"   State: {metrics['current_state']}")
        logger.info(f"   Connected: {metrics['is_connected']}")
        logger.info(f"   Uptime: {metrics['total_uptime']:.1f}s")
        logger.info(f"   Messages sent: {metrics['messages_sent']}")
        logger.info(f"   Messages received: {metrics['messages_received']}")
        logger.info(f"   Connection attempts: {metrics['connection_attempts']}")
        logger.info(f"   Reconnect attempts: {metrics['reconnect_attempts']}")

        if event_stats:
            logger.info("📈 EVENT STATS")
            for event_type, count in sorted(event_stats.items()):
                logger.info(f"   {event_type}: {count}")

        logger.info("=" * 60)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")

        # Display final metrics
        self.display_metrics()

        # Destroy manager
        self.manager.destroy()

        logger.info("Cleanup complete")


def main():
    """Entry point"""
    # Create and run example
    example = RealtimeExample()

    try:
        example.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        example.cleanup()


if __name__ == '__main__':
    main()
