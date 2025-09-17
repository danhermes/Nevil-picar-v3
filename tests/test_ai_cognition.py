#!/usr/bin/env python3
"""
Test script for AI Cognition Node with OpenAI integration
Tests the complete audio loop: Speech → STT → AI → Response
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("ai_cognition_test")

def test_openai_connection():
    """Test OpenAI API connection"""
    logger.info("=" * 60)
    logger.info("Testing OpenAI API Connection")
    logger.info("=" * 60)

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ No OpenAI API key found in environment variables")
        return False

    logger.info("✓ OpenAI API key found in environment")

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)

        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, I am working!' in exactly those words."}
            ],
            max_tokens=10
        )

        reply = response.choices[0].message.content.strip()
        logger.info(f"✓ OpenAI API Response: '{reply}'")
        return True

    except Exception as e:
        logger.error(f"❌ OpenAI API Error: {e}")
        return False

def test_ai_cognition_response():
    """Test AI Cognition node response generation"""
    logger.info("=" * 60)
    logger.info("Testing AI Cognition Response Generation")
    logger.info("=" * 60)

    try:
        from nodes.ai_cognition.ai_cognition_node import AiCognitionNode

        # Create mock logger for the node
        node_logger = logging.getLogger("ai_cognition_node")

        # Create AI cognition node instance
        ai_node = AiCognitionNode()
        ai_node.logger = node_logger

        # Manually set the API key since we're not using the full framework
        ai_node.openai_api_key = os.getenv('OPENAI_API_KEY')

        # Override config to force OpenAI mode
        ai_node.mode = 'openai'
        ai_node.model = 'gpt-3.5-turbo'
        ai_node.max_tokens = 150
        ai_node.temperature = 0.7
        ai_node.confidence_threshold = 0.3
        ai_node.system_prompt = "You are Nevil, a helpful robot assistant. Keep responses concise."
        ai_node.max_history_length = 10

        # Initialize node
        ai_node.initialize()

        # Test messages
        test_inputs = [
            "Hello, how are you?",
            "What is the weather today?",
            "Tell me a joke",
            "What is 2 + 2?",
            "Goodbye"
        ]

        logger.info("\nTesting AI responses to various inputs:")
        logger.info("-" * 40)

        for input_text in test_inputs:
            logger.info(f"\n📢 User: '{input_text}'")

            # Generate response
            response = ai_node._generate_response(input_text)

            if response:
                logger.info(f"🤖 Nevil: '{response}'")
            else:
                logger.warning("❌ No response generated")

            time.sleep(1)  # Brief pause between tests

        # Show conversation summary
        logger.info("\n" + "=" * 60)
        logger.info("Conversation Summary:")
        logger.info("-" * 40)
        summary = ai_node.get_conversation_summary()
        logger.info(summary)

        # Show statistics
        stats = ai_node.get_ai_stats()
        logger.info("\n" + "=" * 60)
        logger.info("AI Cognition Statistics:")
        logger.info("-" * 40)
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

        return True

    except Exception as e:
        logger.error(f"❌ AI Cognition Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_speech_to_text_simulation():
    """Test speech-to-text with a simulated audio file"""
    logger.info("=" * 60)
    logger.info("Testing Speech-to-Text Simulation")
    logger.info("=" * 60)

    # Check for existing audio files
    audio_dir = os.path.join(os.getcwd(), "audio", "user_wavs")
    if os.path.exists(audio_dir):
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        if audio_files:
            logger.info(f"Found {len(audio_files)} existing audio files:")
            for f in audio_files[:5]:  # Show first 5
                logger.info(f"  - {f}")

            # Try to transcribe the most recent one
            if audio_files:
                latest_file = sorted(audio_files)[-1]
                test_file = os.path.join(audio_dir, latest_file)
                logger.info(f"\nTesting transcription on: {latest_file}")

                try:
                    import openai
                    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

                    with open(test_file, "rb") as audio_file:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file
                        )

                    logger.info(f"✓ Transcription: '{transcript.text}'")
                    return True

                except Exception as e:
                    logger.error(f"❌ Transcription Error: {e}")
    else:
        logger.info("No captured audio directory found. Run the full system to capture audio.")

    return False

def main():
    """Run all AI cognition tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 AI COGNITION TEST SUITE")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment
    logger.info("\n📋 Environment Check:")
    logger.info(f"  Python: {sys.version.split()[0]}")
    logger.info(f"  Working Dir: {os.getcwd()}")
    logger.info(f"  OpenAI Key: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not Set'}")

    results = []

    # Test 1: OpenAI Connection
    logger.info("\n")
    results.append(("OpenAI Connection", test_openai_connection()))

    # Test 2: AI Cognition Response
    logger.info("\n")
    if results[0][1]:  # Only if OpenAI works
        results.append(("AI Cognition Response", test_ai_cognition_response()))
    else:
        logger.warning("Skipping AI Cognition test - OpenAI connection failed")
        results.append(("AI Cognition Response", False))

    # Test 3: Speech-to-Text (if audio files exist)
    logger.info("\n")
    results.append(("Speech-to-Text", test_speech_to_text_simulation()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name:30s} {status}")

    logger.info("-" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! AI cognition with OpenAI is working.")
    elif passed > 0:
        logger.info(f"\n⚠️  {passed} tests passed, {total - passed} failed.")
    else:
        logger.error("\n❌ All tests failed. Check your OpenAI API key and configuration.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)