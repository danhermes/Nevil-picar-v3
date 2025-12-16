#!/usr/bin/env python3
"""
YouTube Library Integration Example

Shows how to integrate YouTube music library with AI node.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nevil_framework.youtube_library import YouTubeLibrary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_load_library():
    """Example 1: Load and explore the library"""
    logger.info("=== Example 1: Load Library ===\n")

    # Initialize library (loads from config/youtube_music.json)
    library = YouTubeLibrary()

    # Show statistics
    stats = library.get_stats()
    logger.info(f"Library Stats:")
    logger.info(f"  Total entries: {stats['total_entries']}")
    logger.info(f"  Categories: {stats['categories']}")
    logger.info(f"  Moods: {stats['moods']}")

    # Show all entries
    logger.info(f"\nAll Entries:")
    for entry in library.get_all():
        logger.info(f"  - {entry['name']}: {entry['description']}")


def example_search_and_filter():
    """Example 2: Search and filter entries"""
    logger.info("\n=== Example 2: Search and Filter ===\n")

    library = YouTubeLibrary()

    # Search by keyword
    logger.info("Search for 'calm':")
    results = library.search('calm')
    for entry in results:
        logger.info(f"  - {entry['name']}: {entry['description']}")

    # Filter by category
    logger.info("\nMusic category:")
    music_entries = library.get_by_category('music')
    for entry in music_entries:
        logger.info(f"  - {entry['name']}: {entry['description']}")

    # Filter by mood
    logger.info("\nPeaceful mood:")
    peaceful = library.get_by_mood('peaceful')
    for entry in peaceful:
        logger.info(f"  - {entry['name']}: {entry['description']}")


def example_ai_function_definition():
    """Example 3: Get AI function definition"""
    logger.info("\n=== Example 3: AI Function Definition ===\n")

    library = YouTubeLibrary()

    # Get function definition for AI
    func_def = library.get_ai_function_definition()

    logger.info(f"Function Name: {func_def['name']}")
    logger.info(f"Description: {func_def['description'][:100]}...")
    logger.info(f"Available options: {len(func_def['parameters']['properties']['name']['enum'])}")
    logger.info(f"Options: {func_def['parameters']['properties']['name']['enum']}")


def example_ai_integration():
    """Example 4: Simulate AI integration"""
    logger.info("\n=== Example 4: AI Integration Simulation ===\n")

    library = YouTubeLibrary()

    # Simulate AI function handler
    def execute_ai_function(function_name: str, args: dict):
        """This would be part of your AI node's _execute_function method"""

        logger.info(f"\n🤖 AI called: {function_name}({args})")

        if function_name == "stream_youtube_music":
            # Get the entry
            entry = library.get_by_name(args["name"])

            if entry:
                logger.info(f"   Would stream: {entry['description']}")
                logger.info(f"   URL: {entry['url']}")
                logger.info(f"   Mood: {entry['mood']}, Category: {entry['category']}")

                # Actual streaming (commented out for demo)
                # result = library.stream_audio(name=args["name"])
                # return result

                return {
                    "status": "success",
                    "message": f"Streaming: {entry['description']}",
                    "url": entry['url']
                }
            else:
                return {
                    "status": "error",
                    "message": f"Entry '{args['name']}' not found"
                }

    # Simulate AI conversations
    logger.info("--- Conversation 1: User needs focus ---")
    logger.info('User: "I need to focus on work"')
    logger.info('AI thinks: User needs calm, focused music → lofi_study')
    execute_ai_function("stream_youtube_music", {"name": "lofi_study"})

    logger.info("\n--- Conversation 2: User is stressed ---")
    logger.info('User: "I\'m feeling stressed"')
    logger.info('AI thinks: User needs calming → ocean_sounds')
    execute_ai_function("stream_youtube_music", {"name": "ocean_sounds"})

    logger.info("\n--- Conversation 3: User wants energy ---")
    logger.info('User: "Play something upbeat!"')
    logger.info('AI thinks: User wants energetic → upbeat_pop')
    execute_ai_function("stream_youtube_music", {"name": "upbeat_pop"})


def example_add_to_ai_node():
    """Example 5: Show integration with AI node"""
    logger.info("\n=== Example 5: AI Node Integration Code ===\n")

    code = '''
# In your ai_cognition_realtime_node.py:

from nevil_framework.youtube_library import YouTubeLibrary

class AICognitionRealtimeNode:
    def __init__(self):
        # ... existing initialization ...

        # Initialize YouTube library
        self.youtube_library = YouTubeLibrary()

        # Add to AI function definitions (alongside gestures)
        self.gesture_definitions.append(
            self.youtube_library.get_ai_function_definition()
        )

    def _execute_function(self, function_name: str, args: dict):
        """Execute AI function calls"""

        # ... existing gesture handling ...

        # Handle YouTube music streaming
        if function_name == "stream_youtube_music":
            return self.youtube_library.stream_audio(
                name=args["name"]
            )

        # ... rest of function handling ...
    '''

    logger.info(code)


def example_adding_custom_url():
    """Example 6: Show how to add custom URL"""
    logger.info("\n=== Example 6: Adding Custom URL ===\n")

    logger.info("To add a new YouTube URL, edit config/youtube_music.json:")
    logger.info("")

    new_entry = {
        "name": "my_custom_music",
        "description": "My favorite relaxing guitar music",
        "url": "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
        "category": "music",
        "mood": "peaceful"
    }

    logger.info(json.dumps(new_entry, indent=2))
    logger.info("")
    logger.info("Then restart Nevil to reload the library.")


def main():
    """Run all examples"""

    logger.info("🎵 YouTube Library Integration Examples 🎵")
    logger.info("=" * 60)

    try:
        example_load_library()
        example_search_and_filter()
        example_ai_function_definition()
        example_ai_integration()
        example_add_to_ai_node()
        example_adding_custom_url()

        logger.info("\n" + "=" * 60)
        logger.info("✅ All examples completed!")
        logger.info("\nNext steps:")
        logger.info("1. Edit config/youtube_music.json to add your URLs")
        logger.info("2. Integrate with ai_cognition_realtime_node.py")
        logger.info("3. Test with real conversations")

    except Exception as e:
        logger.error(f"Error in examples: {e}", exc_info=True)


if __name__ == "__main__":
    main()
