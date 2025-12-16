#!/usr/bin/env python3
"""
Manual room setup - Define rooms when auto-clustering fails
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from nodes.slam.room_database import RoomDatabase

db = RoomDatabase()

# Clear existing
db.clear_all_rooms()

# Define the 4 rooms Nevil actually visited/saw
# Map bounds: X: -0.68 to 1.17m, Y: -0.56 to 0.61m

rooms = [
    {
        'name': 'hallway',
        'label': 'Hallway',
        'center_x': -0.3, 'center_y': 0.0,
        'min_x': -0.7, 'max_x': 0.0,
        'min_y': -0.4, 'max_y': 0.4,
    },
    {
        'name': 'office',
        'label': 'Office',
        'center_x': 0.3, 'center_y': -0.2,
        'min_x': 0.0, 'max_x': 0.6,
        'min_y': -0.6, 'max_y': 0.2,
    },
    {
        'name': 'living_room',
        'label': 'Living Room',
        'center_x': 0.6, 'center_y': 0.3,
        'min_x': 0.3, 'max_x': 0.9,
        'min_y': 0.0, 'max_y': 0.6,
    },
    {
        'name': 'kitchen',
        'label': 'Kitchen (visible only)',
        'center_x': 1.0, 'center_y': 0.0,
        'min_x': 0.8, 'max_x': 1.2,
        'min_y': -0.3, 'max_y': 0.3,
    },
]

for room in rooms:
    room_id = db.add_room(
        name=room['name'],
        label=room['label'],
        bounds=room
    )

    # Add waypoint at center
    db.add_waypoint(
        room_id=room_id,
        name=f"{room['name']}_center",
        x=room['center_x'],
        y=room['center_y']
    )

    print(f"✅ Created room: {room['label']} at ({room['center_x']:.2f}, {room['center_y']:.2f})")

print(f"\n🎉 Manually defined {len(rooms)} rooms")
print("\nTo navigate:")
print("  bus.publish('navigate_to_room', {'room': 'kitchen'})")

db.close()
