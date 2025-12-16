#!/usr/bin/env python3
"""
Room Database Manager

Manages room definitions, boundaries, and semantic labels.
Uses SQLite for storage with spatial data support.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()


class RoomDatabase:
    """Manages room definitions and spatial queries"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.getenv('SLAM_ROOMS_DB', '/home/dan/Nevil-picar-v3/data/slam/rooms.db')

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Rooms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                label TEXT,
                center_x REAL,
                center_y REAL,
                center_z REAL,
                min_x REAL,
                max_x REAL,
                min_y REAL,
                max_y REAL,
                min_z REAL,
                max_z REAL,
                num_landmarks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Landmarks associated with rooms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_landmarks (
                landmark_id INTEGER PRIMARY KEY,
                room_id INTEGER,
                pos_x REAL,
                pos_y REAL,
                pos_z REAL,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            )
        ''')

        # Waypoints for navigation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waypoints (
                waypoint_id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                name TEXT,
                pos_x REAL,
                pos_y REAL,
                heading REAL,
                FOREIGN KEY (room_id) REFERENCES rooms(room_id)
            )
        ''')

        # Room connections (adjacency)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_connections (
                from_room_id INTEGER,
                to_room_id INTEGER,
                connection_type TEXT DEFAULT 'doorway',
                PRIMARY KEY (from_room_id, to_room_id),
                FOREIGN KEY (from_room_id) REFERENCES rooms(room_id),
                FOREIGN KEY (to_room_id) REFERENCES rooms(room_id)
            )
        ''')

        self.conn.commit()
        print(f"[RoomDB] Database initialized at {self.db_path}")

    def add_room(self, name: str, label: str = None, bounds: Dict = None, landmarks: List = None) -> int:
        """Add a new room to the database"""
        cursor = self.conn.cursor()

        # Calculate center and bounds from landmarks if provided
        if landmarks and bounds is None:
            import numpy as np
            positions = np.array([[lm['x'], lm['y'], lm['z']] for lm in landmarks])
            bounds = {
                'min_x': float(positions[:, 0].min()),
                'max_x': float(positions[:, 0].max()),
                'min_y': float(positions[:, 1].min()),
                'max_y': float(positions[:, 1].max()),
                'min_z': float(positions[:, 2].min()),
                'max_z': float(positions[:, 2].max()),
                'center_x': float(positions[:, 0].mean()),
                'center_y': float(positions[:, 1].mean()),
                'center_z': float(positions[:, 2].mean()),
            }

        # Insert room
        cursor.execute('''
            INSERT INTO rooms (name, label, center_x, center_y, center_z,
                              min_x, max_x, min_y, max_y, min_z, max_z, num_landmarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            label or name,
            bounds.get('center_x', 0.0) if bounds else 0.0,
            bounds.get('center_y', 0.0) if bounds else 0.0,
            bounds.get('center_z', 0.0) if bounds else 0.0,
            bounds.get('min_x', 0.0) if bounds else 0.0,
            bounds.get('max_x', 0.0) if bounds else 0.0,
            bounds.get('min_y', 0.0) if bounds else 0.0,
            bounds.get('max_y', 0.0) if bounds else 0.0,
            bounds.get('min_z', 0.0) if bounds else 0.0,
            bounds.get('max_z', 0.0) if bounds else 0.0,
            len(landmarks) if landmarks else 0
        ))

        room_id = cursor.lastrowid

        # Insert landmarks
        if landmarks:
            for i, lm in enumerate(landmarks):
                cursor.execute('''
                    INSERT INTO room_landmarks (landmark_id, room_id, pos_x, pos_y, pos_z)
                    VALUES (?, ?, ?, ?, ?)
                ''', (i, room_id, lm['x'], lm['y'], lm['z']))

        self.conn.commit()
        print(f"[RoomDB] Added room '{name}' (ID: {room_id}) with {len(landmarks) if landmarks else 0} landmarks")
        return room_id

    def get_room_by_name(self, name: str) -> Optional[Dict]:
        """Get room by name"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms WHERE name = ?', (name,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_room_by_id(self, room_id: int) -> Optional[Dict]:
        """Get room by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_all_rooms(self) -> List[Dict]:
        """Get all rooms"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM rooms ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]

    def get_room_at_position(self, x: float, y: float, z: float = None) -> Optional[Dict]:
        """Find which room contains a given position"""
        cursor = self.conn.cursor()

        if z is not None:
            cursor.execute('''
                SELECT * FROM rooms
                WHERE ? BETWEEN min_x AND max_x
                  AND ? BETWEEN min_y AND max_y
                  AND ? BETWEEN min_z AND max_z
                LIMIT 1
            ''', (x, y, z))
        else:
            cursor.execute('''
                SELECT * FROM rooms
                WHERE ? BETWEEN min_x AND max_x
                  AND ? BETWEEN min_y AND max_y
                LIMIT 1
            ''', (x, y))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def add_waypoint(self, room_id: int, name: str, x: float, y: float, heading: float = 0.0) -> int:
        """Add a navigation waypoint to a room"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO waypoints (room_id, name, pos_x, pos_y, heading)
            VALUES (?, ?, ?, ?, ?)
        ''', (room_id, name, x, y, heading))

        self.conn.commit()
        return cursor.lastrowid

    def get_room_waypoints(self, room_id: int) -> List[Dict]:
        """Get all waypoints in a room"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM waypoints WHERE room_id = ?', (room_id,))
        return [dict(row) for row in cursor.fetchall()]

    def add_room_connection(self, from_room_id: int, to_room_id: int, connection_type: str = 'doorway'):
        """Mark two rooms as connected"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO room_connections (from_room_id, to_room_id, connection_type)
            VALUES (?, ?, ?)
        ''', (from_room_id, to_room_id, connection_type))

        # Add reverse connection
        cursor.execute('''
            INSERT OR REPLACE INTO room_connections (from_room_id, to_room_id, connection_type)
            VALUES (?, ?, ?)
        ''', (to_room_id, from_room_id, connection_type))

        self.conn.commit()

    def get_connected_rooms(self, room_id: int) -> List[Dict]:
        """Get rooms connected to a given room"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.* FROM rooms r
            JOIN room_connections rc ON r.room_id = rc.to_room_id
            WHERE rc.from_room_id = ?
        ''', (room_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_room_label(self, room_id: int, label: str):
        """Update room's semantic label"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE rooms SET label = ?, updated_at = CURRENT_TIMESTAMP
            WHERE room_id = ?
        ''', (label, room_id))
        self.conn.commit()

    def clear_all_rooms(self):
        """Clear all rooms (use with caution)"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM room_landmarks')
        cursor.execute('DELETE FROM waypoints')
        cursor.execute('DELETE FROM room_connections')
        cursor.execute('DELETE FROM rooms')
        self.conn.commit()
        print("[RoomDB] All rooms cleared")

    def export_to_json(self, filepath: str):
        """Export room database to JSON"""
        rooms = self.get_all_rooms()

        export_data = []
        for room in rooms:
            room_data = dict(room)
            room_data['waypoints'] = self.get_room_waypoints(room['room_id'])
            room_data['connections'] = self.get_connected_rooms(room['room_id'])
            export_data.append(room_data)

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"[RoomDB] Exported {len(export_data)} rooms to {filepath}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    # Test the database
    db = RoomDatabase()
    print(f"Room database ready: {db.db_path}")
    print(f"Total rooms: {len(db.get_all_rooms())}")
