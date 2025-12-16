"""
YouTube Music Library - Simple curated list of YouTube URLs

AI reads this list and chooses which videos to stream.
Add/edit URLs in config/youtube_music.json
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class YouTubeLibrary:
    """
    Loads and manages YouTube music/video URLs from config file.

    AI can choose from curated list to stream audio.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize YouTube library.

        Args:
            config_file: Path to youtube_music.json (default: config/youtube_music.json)
        """
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                "..",
                "config",
                "youtube_music.json"
            )

        self.config_file = config_file
        self.library = []
        self.load_library()

    def load_library(self) -> None:
        """Load YouTube library from config file"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"YouTube library not found: {self.config_file}")
                return

            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.library = data.get('library', [])

            logger.info(f"Loaded {len(self.library)} YouTube music entries")

        except Exception as e:
            logger.error(f"Error loading YouTube library: {e}")
            self.library = []

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all entries in the library"""
        return self.library

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get entry by name.

        Args:
            name: Name of the entry

        Returns:
            Entry dict or None if not found
        """
        for entry in self.library:
            if entry.get('name') == name:
                return entry
        return None

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all entries in a category.

        Args:
            category: Category name (music, ambient, etc.)

        Returns:
            List of matching entries
        """
        return [
            entry for entry in self.library
            if entry.get('category') == category
        ]

    def get_by_mood(self, mood: str) -> List[Dict[str, Any]]:
        """
        Get entries matching a mood.

        Args:
            mood: Mood name (calm, energetic, peaceful, etc.)

        Returns:
            List of matching entries
        """
        return [
            entry for entry in self.library
            if entry.get('mood') == mood
        ]

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search library by query (searches name, description, category, mood).

        Args:
            query: Search query

        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        results = []

        for entry in self.library:
            if (query_lower in entry.get('name', '').lower() or
                query_lower in entry.get('description', '').lower() or
                query_lower in entry.get('category', '').lower() or
                query_lower in entry.get('mood', '').lower()):
                results.append(entry)

        return results

    def stream_audio(
        self,
        name: Optional[str] = None,
        category: Optional[str] = None,
        mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stream audio from YouTube URL.

        Can select by:
        - name: Specific song name
        - category: Pick random from category (music, ambient, etc.)
        - mood: Pick random from mood (calm, festive, etc.)
        - category + mood: Pick random matching both

        Args:
            name: Specific entry name (exact match)
            category: Category to pick from
            mood: Mood to pick from

        Returns:
            Result dict with status
        """
        import random

        entry = None

        # Method 1: Direct name lookup
        if name:
            entry = self.get_by_name(name)
            if not entry:
                return {
                    "status": "error",
                    "message": f"YouTube entry '{name}' not found"
                }

        # Method 2: Category and/or mood based selection
        else:
            candidates = self.library

            # Filter by category if provided
            if category:
                candidates = [e for e in candidates if e.get('category') == category]

            # Filter by mood if provided
            if mood:
                candidates = [e for e in candidates if e.get('mood') == mood]

            if not candidates:
                return {
                    "status": "error",
                    "message": f"No music found for category='{category}', mood='{mood}'"
                }

            # Pick random from candidates
            entry = random.choice(candidates)
            logger.info(f"🎲 Selected '{entry['name']}' from {len(candidates)} options")

        logger.info(f"🎵 Streaming: {entry['description']}")

        try:
            # Use existing youtube_music.py script
            from scripts.youtube_music import YouTubeMusicStreamer

            streamer = YouTubeMusicStreamer()
            success = streamer.stream_audio(entry['url'])

            if success:
                return {
                    "status": "success",
                    "message": f"Streaming: {entry['description']}",
                    "url": entry['url'],
                    "name": entry['name']
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to stream audio"
                }

        except Exception as e:
            logger.error(f"Error streaming: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def get_ai_function_definition(self) -> Dict[str, Any]:
        """
        Get AI function definition for streaming YouTube music.

        Uses category/mood-based selection to minimize tokens.
        AI picks category or mood, system randomly selects from that category.

        Returns:
            Function definition dict for AI
        """
        # Get unique categories and moods
        categories = set(entry.get('category', 'music') for entry in self.library)
        moods = set(entry.get('mood', 'calm') for entry in self.library)

        # Build summary of what's available
        stats = self.get_stats()
        summary = f"Library: {stats['total_entries']} songs. "
        summary += f"Categories: {', '.join(categories)}. "
        summary += f"Moods: {', '.join(moods)}."

        return {
            "type": "function",
            "name": "stream_youtube_music",
            "description": (
                f"**THIS IS HOW YOU PLAY MUSIC/SOUNDS.** You CAN play music - use this function! "
                f"{summary}\n\n"
                "When user asks for music, sounds, songs, or audio - use this function. "
                "Choose by category (music/ambient) or mood (calm/energetic/festive/peaceful/etc). "
                "System will pick appropriate song from that category/mood.\n\n"
                "Examples:\n"
                "- User: 'play music' → stream_youtube_music(category='music')\n"
                "- User: 'play Christmas music' → stream_youtube_music(mood='festive')\n"
                "- User: 'I need to relax' → stream_youtube_music(mood='calm')\n"
                "- User: 'play sounds' → stream_youtube_music(category='ambient')"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": list(categories),
                        "description": "Category of music (music, ambient, etc.)"
                    },
                    "mood": {
                        "type": "string",
                        "enum": list(moods),
                        "description": "Mood/feeling (calm, energetic, festive, peaceful, etc.)"
                    }
                },
                "description": "Provide category OR mood (or both for more specific selection)"
            }
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        categories = {}
        moods = {}

        for entry in self.library:
            cat = entry.get('category', 'unknown')
            mood = entry.get('mood', 'unknown')

            categories[cat] = categories.get(cat, 0) + 1
            moods[mood] = moods.get(mood, 0) + 1

        return {
            "total_entries": len(self.library),
            "categories": categories,
            "moods": moods,
            "config_file": self.config_file
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load library
    library = YouTubeLibrary()

    # Show stats
    print("\nLibrary Stats:")
    print(json.dumps(library.get_stats(), indent=2))

    # Show all entries
    print("\nAll Entries:")
    for entry in library.get_all():
        print(f"  - {entry['name']}: {entry['description']}")

    # Search example
    print("\nSearch 'calm':")
    results = library.search('calm')
    for entry in results:
        print(f"  - {entry['name']}: {entry['description']}")

    # Get AI function
    print("\nAI Function Definition:")
    func = library.get_ai_function_definition()
    print(f"  Name: {func['name']}")
    print(f"  Options: {len(func['parameters']['properties']['name']['enum'])}")
