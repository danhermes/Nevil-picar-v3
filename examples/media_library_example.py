#!/usr/bin/env python3
"""
Media Library Integration Example

Shows how to integrate sound and video libraries with AI and existing AudioOutput.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nevil_framework.sound_library_manager import SoundLibraryManager
from nevil_framework.video_library_manager import VideoLibraryManager
from audio.audio_output import AudioOutput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_standalone_usage():
    """Example 1: Using sound and video libraries standalone"""

    logger.info("=== Example 1: Standalone Usage ===")

    # Initialize libraries
    sound_library = SoundLibraryManager()
    video_library = VideoLibraryManager()

    # List available sounds
    logger.info("\nAvailable sounds:")
    for name, info in sound_library.get_available_sounds().items():
        logger.info(f"  - {name}: {info['description']}")

    # List available videos
    logger.info("\nAvailable videos:")
    for name, info in video_library.get_available_videos().items():
        logger.info(f"  - {name}: {info['description']} ({info['duration']})")

    # Play a sound (will fail gracefully without audio hardware)
    result = sound_library.play_sound("calm_music", volume=0.3)
    logger.info(f"\nPlay sound result: {result}")

    # Play a video (opens in browser)
    result = video_library.play_video("relaxing_nature")
    logger.info(f"\nPlay video result: {result}")

    # Search videos
    results = video_library.search_videos("relaxing")
    logger.info(f"\nSearch 'relaxing' found: {list(results.keys())}")


def example_with_audio_output():
    """Example 2: Integration with AudioOutput"""

    logger.info("\n=== Example 2: With AudioOutput Integration ===")

    # Initialize audio output (requires hardware)
    try:
        audio_output = AudioOutput()

        # Initialize sound library with audio callback
        sound_library = SoundLibraryManager(
            audio_output_callback=audio_output.music
        )

        logger.info("Sound library integrated with AudioOutput")

        # Play sound through AudioOutput
        result = sound_library.play_sound("beep", volume=0.5)
        logger.info(f"Play result: {result}")

    except Exception as e:
        logger.error(f"AudioOutput not available: {e}")
        logger.info("(This is normal if not running on Raspberry Pi hardware)")


def example_ai_function_definitions():
    """Example 3: Get AI function definitions"""

    logger.info("\n=== Example 3: AI Function Definitions ===")

    sound_library = SoundLibraryManager()
    video_library = VideoLibraryManager()

    # Get function definitions for AI
    sound_functions = sound_library.get_ai_function_definitions()
    video_functions = video_library.get_ai_function_definitions()

    logger.info(f"\nSound functions for AI: {len(sound_functions)}")
    for func in sound_functions:
        logger.info(f"  - {func['name']}: {func['description'][:50]}...")

    logger.info(f"\nVideo functions for AI: {len(video_functions)}")
    for func in video_functions:
        logger.info(f"  - {func['name']}: {func['description'][:50]}...")


def example_ai_integration():
    """Example 4: How AI would call these functions"""

    logger.info("\n=== Example 4: AI Integration Pattern ===")

    # Initialize libraries
    sound_library = SoundLibraryManager()
    video_library = VideoLibraryManager()

    # Simulate AI function handler
    def execute_ai_function(function_name: str, args: dict):
        """
        This would be part of your AI node's function handler.
        Similar to gesture handling in ai_cognition_realtime_node.py
        """

        logger.info(f"\n🤖 AI called: {function_name}({args})")

        # Handle sound functions
        if function_name == "play_sound":
            result = sound_library.play_sound(
                sound_name=args["sound_name"],
                volume=args.get("volume")
            )
            logger.info(f"   Result: {result}")
            return result

        elif function_name == "stop_sound":
            result = sound_library.stop_sound()
            logger.info(f"   Result: {result}")
            return result

        # Handle video functions
        elif function_name == "play_video":
            result = video_library.play_video(
                video_name=args["video_name"]
            )
            logger.info(f"   Result: {result}")
            return result

        elif function_name == "search_videos":
            results = video_library.search_videos(
                query=args["query"]
            )
            result = {
                "status": "success",
                "results": list(results.keys()),
                "count": len(results)
            }
            logger.info(f"   Found: {result['results']}")
            return result

        else:
            return {"status": "error", "message": f"Unknown function: {function_name}"}

    # Simulate AI conversations
    logger.info("\n--- Simulated Conversation 1: User is stressed ---")
    logger.info("User: 'I'm feeling stressed'")
    execute_ai_function("play_sound", {"sound_name": "rain", "volume": 0.2})
    logger.info("AI: 'I've started some gentle rain sounds to help you relax.'")

    logger.info("\n--- Simulated Conversation 2: User wants music ---")
    logger.info("User: 'Play some music'")
    execute_ai_function("play_sound", {"sound_name": "youtube_lofi", "volume": 0.3})
    logger.info("AI: 'Sure! Playing some lo-fi hip hop for you.'")

    logger.info("\n--- Simulated Conversation 3: User wants video ---")
    logger.info("User: 'Show me something about robots'")
    execute_ai_function("play_video", {"video_name": "how_robots_work"})
    logger.info("AI: 'Here's an interesting video about how robots work!'")

    logger.info("\n--- Simulated Conversation 4: Search request ---")
    logger.info("User: 'Find relaxing videos'")
    execute_ai_function("search_videos", {"query": "relaxing"})
    logger.info("AI: 'I found 3 relaxing videos. Would you like ocean waves, forest sounds, or nature music?'")


def example_statistics():
    """Example 5: Get library statistics"""

    logger.info("\n=== Example 5: Library Statistics ===")

    sound_library = SoundLibraryManager()
    video_library = VideoLibraryManager()

    # Get stats
    sound_stats = sound_library.get_stats()
    video_stats = video_library.get_stats()

    logger.info(f"\nSound Library Stats:")
    logger.info(f"  Total sounds: {sound_stats['total_sounds']}")
    logger.info(f"  By type: {sound_stats['sounds_by_type']}")

    logger.info(f"\nVideo Library Stats:")
    logger.info(f"  Total videos: {video_stats['total_videos']}")
    logger.info(f"  By category: {video_stats['videos_by_category']}")


def main():
    """Run all examples"""

    logger.info("🎵 Media Library Integration Examples 🎥")
    logger.info("=" * 60)

    try:
        example_standalone_usage()
        example_with_audio_output()
        example_ai_function_definitions()
        example_ai_integration()
        example_statistics()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All examples completed!")
        logger.info("\nNext steps:")
        logger.info("1. Add sound files to sounds/ directory")
        logger.info("2. Integrate with ai_cognition_realtime_node.py")
        logger.info("3. Test with real AI conversations")

    except Exception as e:
        logger.error(f"Error in examples: {e}", exc_info=True)


if __name__ == "__main__":
    main()
