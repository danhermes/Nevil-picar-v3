"""
VideoLibraryManager - Curated Video URL Library

AI calls videos by name instead of searching/generating URLs.
Reduces costs and provides curated, appropriate content.

AI calls: play_video(name="relaxing_nature")
Instead of: searching YouTube and picking random videos
"""

import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class VideoLibraryManager:
    """
    Manages curated library of video URLs for AI-driven playback.

    Approach: AI calls videos by name (like gestures and sounds).
    """

    # Video library definitions
    # Each video has: name, url, description, category, duration_estimate
    VIDEO_LIBRARY = {
        # === EDUCATIONAL ===
        "how_robots_work": {
            "category": "educational",
            "description": "Educational video about how robots work",
            "url": "https://www.youtube.com/watch?v=qXZLfOnCYQY",
            "duration": "5:30",
            "topics": ["robotics", "engineering", "technology"]
        },
        "ai_explained": {
            "category": "educational",
            "description": "Simple explanation of artificial intelligence",
            "url": "https://www.youtube.com/watch?v=2ePf9rue1Ao",
            "duration": "6:12",
            "topics": ["ai", "machine learning", "technology"]
        },

        # === MUSIC ===
        "relaxing_nature": {
            "category": "music",
            "description": "Relaxing music with nature sounds",
            "url": "https://www.youtube.com/watch?v=lTRiuFIWV54",
            "duration": "3:00:00",
            "topics": ["relaxation", "nature", "calm"]
        },
        "lofi_study": {
            "category": "music",
            "description": "Lo-fi hip hop music for studying/relaxing",
            "url": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
            "duration": "LIVE",
            "topics": ["lofi", "study", "chill"]
        },
        "classical_piano": {
            "category": "music",
            "description": "Beautiful classical piano music",
            "url": "https://www.youtube.com/watch?v=jgpJVI3tDbY",
            "duration": "2:00:00",
            "topics": ["classical", "piano", "elegant"]
        },

        # === ENTERTAINMENT ===
        "funny_robots": {
            "category": "entertainment",
            "description": "Compilation of funny robot moments",
            "url": "https://www.youtube.com/watch?v=fn3KWM1kuAw",
            "duration": "10:15",
            "topics": ["funny", "robots", "humor"]
        },
        "robot_dance": {
            "category": "entertainment",
            "description": "Amazing robot dance performance",
            "url": "https://www.youtube.com/watch?v=kHBcVlqpvZ8",
            "duration": "2:45",
            "topics": ["dance", "robots", "performance"]
        },

        # === NATURE/SCENERY ===
        "ocean_waves": {
            "category": "nature",
            "description": "Peaceful ocean waves for relaxation",
            "url": "https://www.youtube.com/watch?v=V1bFr2SWP1I",
            "duration": "3:00:00",
            "topics": ["ocean", "relaxation", "nature"]
        },
        "forest_sounds": {
            "category": "nature",
            "description": "Peaceful forest with bird sounds",
            "url": "https://www.youtube.com/watch?v=xNN7iTA57jM",
            "duration": "3:00:00",
            "topics": ["forest", "birds", "nature"]
        },

        # === INSPIRATION ===
        "robot_inspiration": {
            "category": "inspiration",
            "description": "Inspiring video about robotics future",
            "url": "https://www.youtube.com/watch?v=wE3fmFTtP9g",
            "duration": "5:42",
            "topics": ["robotics", "future", "inspiration"]
        },
    }

    def __init__(self, display_callback: Optional[Callable] = None):
        """
        Initialize video library manager.

        Args:
            display_callback: Callback to display video (opens URL in browser/player)
        """
        self.display_callback = display_callback

        # Currently playing video
        self.current_video = None

        logger.info(f"VideoLibraryManager initialized with {len(self.VIDEO_LIBRARY)} videos")

    def get_available_videos(self) -> Dict[str, Dict[str, Any]]:
        """Get all available videos in the library"""
        return self.VIDEO_LIBRARY

    def get_video_info(self, video_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific video.

        Args:
            video_name: Name of the video

        Returns:
            Video info dict or None if not found
        """
        return self.VIDEO_LIBRARY.get(video_name)

    def play_video(self, video_name: str) -> Dict[str, Any]:
        """
        Play a video from the library.

        Args:
            video_name: Name of the video to play

        Returns:
            Result dict with status and URL
        """
        # Get video info
        video_info = self.get_video_info(video_name)
        if not video_info:
            logger.error(f"Video not found: {video_name}")
            return {"status": "error", "message": f"Video '{video_name}' not found"}

        logger.info(f"📺 Playing video: {video_name} ({video_info['category']})")

        try:
            # Open video URL
            if self.display_callback:
                self.display_callback(video_info["url"])
            else:
                # Fallback: Open in default browser
                import webbrowser
                webbrowser.open(video_info["url"])

            self.current_video = video_name

            return {
                "status": "success",
                "message": f"Playing: {video_info['description']}",
                "url": video_info["url"],
                "duration": video_info["duration"]
            }

        except Exception as e:
            logger.error(f"Error playing video {video_name}: {e}")
            return {"status": "error", "message": str(e)}

    def get_videos_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all videos in a specific category.

        Args:
            category: Category name (educational, music, entertainment, etc.)

        Returns:
            Dict of videos in that category
        """
        return {
            name: info
            for name, info in self.VIDEO_LIBRARY.items()
            if info["category"] == category
        }

    def search_videos(self, query: str) -> Dict[str, Dict[str, Any]]:
        """
        Search videos by query (searches description and topics).

        Args:
            query: Search query

        Returns:
            Dict of matching videos
        """
        query_lower = query.lower()
        results = {}

        for name, info in self.VIDEO_LIBRARY.items():
            # Search in description and topics
            if (query_lower in info["description"].lower() or
                any(query_lower in topic.lower() for topic in info["topics"])):
                results[name] = info

        return results

    def get_ai_function_definitions(self) -> list:
        """
        Get function definitions for AI integration.

        Returns list of function definitions that AI can call.
        Similar to gesture and sound library pattern.
        """
        functions = []

        # Play video function
        functions.append({
            "type": "function",
            "name": "play_video",
            "description": (
                "Play a video from the curated library. "
                "Use this to show educational content, music videos, or entertainment. "
                "\n\nAvailable videos:\n" +
                "\n".join([
                    f"- {name}: {info['description']} ({info['category']}, {info['duration']})"
                    for name, info in self.VIDEO_LIBRARY.items()
                ])
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "video_name": {
                        "type": "string",
                        "enum": list(self.VIDEO_LIBRARY.keys()),
                        "description": "Name of the video to play"
                    }
                },
                "required": ["video_name"]
            }
        })

        # Search videos function (optional - for more flexibility)
        functions.append({
            "type": "function",
            "name": "search_videos",
            "description": "Search available videos by keyword (searches titles, descriptions, topics)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'relaxing', 'robots', 'educational')"
                    }
                },
                "required": ["query"]
            }
        })

        return functions

    def get_stats(self) -> Dict[str, Any]:
        """Get video library statistics"""
        return {
            "total_videos": len(self.VIDEO_LIBRARY),
            "current_video": self.current_video,
            "videos_by_category": {
                category: len(self.get_videos_by_category(category))
                for category in set(v["category"] for v in self.VIDEO_LIBRARY.values())
            }
        }


# Example integration
def example_usage():
    """Example of how to use VideoLibraryManager with AI"""

    # Create video library
    video_library = VideoLibraryManager()

    # Get AI function definitions (to add to AI's tools)
    ai_functions = video_library.get_ai_function_definitions()

    # AI calls function like:
    # play_video(video_name="relaxing_nature")

    # In your AI function handler:
    def execute_ai_function(function_name: str, args: Dict[str, Any]):
        if function_name == "play_video":
            return video_library.play_video(video_name=args["video_name"])
        elif function_name == "search_videos":
            results = video_library.search_videos(query=args["query"])
            return {
                "status": "success",
                "results": list(results.keys()),
                "count": len(results)
            }

    logger.info("Video library ready for AI integration")
