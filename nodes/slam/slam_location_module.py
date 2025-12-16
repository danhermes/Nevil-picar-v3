#!/usr/bin/env python3
"""
SLAM Location Module

Provides location awareness and navigation capabilities to Nevil's AI cognition.
Bridges SLAM navigation with voice commands and AI decision-making.
"""

import os
import sys
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from nodes.slam.room_database import RoomDatabase

load_dotenv()


class SLAMLocationModule:
    """
    Location awareness and navigation interface for AI cognition.

    Provides:
    - Current location detection
    - Room information queries
    - Navigation command generation
    - Location-based context for AI
    """

    def __init__(self):
        self.room_db = RoomDatabase()
        self.current_location = None
        self.last_pose = None

    def get_available_rooms(self) -> List[Dict]:
        """Get list of all known rooms"""
        return self.room_db.get_all_rooms()

    def get_room_by_name(self, room_name: str) -> Optional[Dict]:
        """Find room by name (case-insensitive, fuzzy match)"""
        room_name_lower = room_name.lower().strip()

        # Try exact match first
        room = self.room_db.get_room_by_name(room_name_lower)
        if room:
            return room

        # Try fuzzy match on label
        all_rooms = self.get_available_rooms()
        for room in all_rooms:
            if room_name_lower in room['label'].lower():
                return room
            if room_name_lower in room['name'].lower():
                return room

        return None

    def get_current_location(self, x: float, y: float) -> Optional[Dict]:
        """Determine which room contains the given position"""
        room = self.room_db.get_room_at_position(x, y)
        if room:
            self.current_location = room
        return room

    def update_pose(self, pose: Dict):
        """Update current pose from SLAM"""
        self.last_pose = pose

        # Update current location
        if pose.get('tracking_state') == 'Tracking':
            x, y = pose.get('x', 0.0), pose.get('y', 0.0)
            self.get_current_location(x, y)

    def get_location_context(self) -> str:
        """Get natural language description of current location for AI"""
        if not self.current_location:
            if self.last_pose and self.last_pose.get('tracking_state') == 'Lost':
                return "I'm not sure where I am right now - my tracking is lost."
            return "I don't know my current location yet."

        room_label = self.current_location.get('label', 'Unknown')
        x = self.last_pose.get('x', 0.0) if self.last_pose else 0.0
        y = self.last_pose.get('y', 0.0) if self.last_pose else 0.0

        return f"I'm currently in the {room_label} at position ({x:.2f}, {y:.2f})."

    def parse_navigation_command(self, user_input: str) -> Optional[Dict]:
        """
        Parse user input for navigation intent.

        Returns navigation command dict or None.

        Examples:
        - "go to the kitchen" -> {'action': 'navigate', 'room': 'kitchen'}
        - "take me to the office" -> {'action': 'navigate', 'room': 'office'}
        - "navigate to living room" -> {'action': 'navigate', 'room': 'living_room'}
        """
        user_input_lower = user_input.lower().strip()

        # Navigation trigger phrases
        nav_triggers = [
            "go to",
            "take me to",
            "navigate to",
            "move to",
            "drive to",
            "head to",
            "go into",
        ]

        for trigger in nav_triggers:
            if trigger in user_input_lower:
                # Extract room name after trigger
                parts = user_input_lower.split(trigger, 1)
                if len(parts) > 1:
                    room_name = parts[1].strip().strip("the").strip()

                    # Try to find matching room
                    room = self.get_room_by_name(room_name)
                    if room:
                        return {
                            'action': 'navigate',
                            'room': room['name'],
                            'room_label': room['label'],
                            'target_x': room['center_x'],
                            'target_y': room['center_y']
                        }

        # Location query triggers
        location_triggers = [
            "where am i",
            "what room",
            "my location",
            "current location",
        ]

        for trigger in location_triggers:
            if trigger in user_input_lower:
                return {
                    'action': 'query_location'
                }

        # List rooms trigger
        if "what rooms" in user_input_lower or "list rooms" in user_input_lower:
            return {
                'action': 'list_rooms'
            }

        return None

    def generate_navigation_response(self, command: Dict) -> str:
        """Generate natural language response for navigation actions"""
        action = command.get('action')

        if action == 'navigate':
            room_label = command.get('room_label', 'that room')
            return f"Okay, I'll navigate to the {room_label} now."

        elif action == 'query_location':
            return self.get_location_context()

        elif action == 'list_rooms':
            rooms = self.get_available_rooms()
            if not rooms:
                return "I don't have any rooms mapped yet."

            room_labels = [r['label'] for r in rooms]
            if len(room_labels) == 1:
                return f"I know about one room: {room_labels[0]}."
            elif len(room_labels) == 2:
                return f"I know about these rooms: {room_labels[0]} and {room_labels[1]}."
            else:
                rooms_str = ", ".join(room_labels[:-1])
                return f"I know about these rooms: {rooms_str}, and {room_labels[-1]}."

        return "I understood the navigation command."

    def get_room_list_for_ai(self) -> str:
        """Get formatted room list for AI system prompt"""
        rooms = self.get_available_rooms()
        if not rooms:
            return "No rooms available."

        room_info = []
        for room in rooms:
            room_info.append(f"  - {room['label']} ({room['name']})")

        return "\n".join(room_info)

    def close(self):
        """Cleanup"""
        if self.room_db:
            self.room_db.close()


# Singleton instance for easy import
_location_module = None

def get_location_module() -> SLAMLocationModule:
    """Get singleton location module instance"""
    global _location_module
    if _location_module is None:
        _location_module = SLAMLocationModule()
    return _location_module


if __name__ == '__main__':
    # Test the module
    module = SLAMLocationModule()

    print("Available rooms:")
    for room in module.get_available_rooms():
        print(f"  - {room['label']}: {room['name']} at ({room['center_x']:.2f}, {room['center_y']:.2f})")

    print("\nTesting navigation parsing:")
    test_commands = [
        "go to the kitchen",
        "take me to the office",
        "navigate to living room",
        "where am i",
        "what rooms do you know",
    ]

    for cmd in test_commands:
        result = module.parse_navigation_command(cmd)
        if result:
            print(f"  '{cmd}' -> {result['action']}")
            response = module.generate_navigation_response(result)
            print(f"    Response: {response}")
        else:
            print(f"  '{cmd}' -> No navigation intent")

    print("\nRoom list for AI:")
    print(module.get_room_list_for_ai())

    module.close()
