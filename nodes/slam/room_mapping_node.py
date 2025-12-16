#!/usr/bin/env python3
"""
Room Mapping Node

Loads SLAM landmarks from my_map.json and clusters them into semantic rooms.
Uses spatial clustering (DBSCAN) and optional GPT-4V labeling.
"""

import os
import sys
import json
import math
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from nevil_framework.message_bus import MessageBus
from nodes.slam.room_database import RoomDatabase

load_dotenv()


class RoomMappingNode:
    """Clusters SLAM landmarks into semantic rooms"""

    def __init__(self):
        self.message_bus = MessageBus()
        self.room_db = RoomDatabase()

        # Load configuration
        self.map_json_path = os.getenv('SLAM_MAP_JSON', '/home/dan/Documents/openvslam/my_map.json')
        self.z_filter_min = 0.0  # Ground level
        self.z_filter_max = 6.0  # meters (increased to capture all landmarks)

        # Clustering parameters (tuned for multi-room detection)
        self.clustering_eps = 0.5  # Grid cell size (meters) - larger to group room areas
        self.clustering_min_samples = 100  # Minimum landmarks per room - higher threshold

        # Map data
        self.landmarks = []
        self.rooms = []

    def load_map_landmarks(self):
        """Load landmarks from SLAM map JSON"""
        print(f"[RoomMapping] Loading landmarks from {self.map_json_path}")

        if not os.path.exists(self.map_json_path):
            print(f"[RoomMapping] ERROR: Map file not found: {self.map_json_path}")
            return False

        try:
            with open(self.map_json_path, 'r') as f:
                map_data = json.load(f)

            metadata = map_data.get('metadata', {})
            print(f"[RoomMapping] Map metadata:")
            print(f"  Total keyframes: {metadata.get('num_keyframes', 0)}")
            print(f"  Total landmarks: {metadata.get('num_landmarks', 0)}")

            # Extract landmarks (convert from dict to list if needed)
            landmarks_data = map_data.get('landmarks', [])

            if isinstance(landmarks_data, dict):
                # Convert dict to list
                landmarks_data = list(landmarks_data.values())

            print(f"[RoomMapping] Processing {len(landmarks_data)} landmarks...")

            # Filter and extract positions
            for lm in landmarks_data:
                if isinstance(lm, dict) and 'position' in lm:
                    pos = lm['position']
                    if len(pos) >= 3:
                        x, y, z = pos[0], pos[1], pos[2]

                        # Filter by height (ground level features only for 2D navigation)
                        if self.z_filter_min <= z <= self.z_filter_max:
                            self.landmarks.append({
                                'id': lm.get('id', len(self.landmarks)),
                                'x': x,
                                'y': y,
                                'z': z,
                                'num_observations': lm.get('num_visible', 0)
                            })

            print(f"[RoomMapping] Loaded {len(self.landmarks)} landmarks (after z-filter)")
            return True

        except Exception as e:
            print(f"[RoomMapping] ERROR loading map: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cluster_into_rooms(self):
        """Simple grid-based clustering (no sklearn required)"""
        if len(self.landmarks) < self.clustering_min_samples:
            print(f"[RoomMapping] WARNING: Not enough landmarks for clustering ({len(self.landmarks)} < {self.clustering_min_samples})")
            # Create single room with all landmarks
            self._create_single_room()
            return

        print(f"[RoomMapping] Clustering landmarks into rooms...")
        print(f"  Algorithm: Grid-based clustering")
        print(f"  Grid size: {self.clustering_eps}m")
        print(f"  Min samples: {self.clustering_min_samples}")

        # Simple grid-based clustering
        labels = self._simple_clustering()

        # Group landmarks by cluster
        unique_labels = set(labels)
        num_clusters = len(unique_labels - {-1})  # Exclude noise label
        num_noise = labels.count(-1)

        print(f"[RoomMapping] Found {num_clusters} room clusters ({num_noise} noise points)")

        # Create room groups
        for cluster_id in sorted(unique_labels):
            if cluster_id == -1:  # Skip noise
                continue

            cluster_landmarks = [
                lm for lm, label in zip(self.landmarks, labels)
                if label == cluster_id
            ]

            if len(cluster_landmarks) >= self.clustering_min_samples:
                # Calculate room bounds
                xs = [lm['x'] for lm in cluster_landmarks]
                ys = [lm['y'] for lm in cluster_landmarks]
                zs = [lm['z'] for lm in cluster_landmarks]

                room_data = {
                    'cluster_id': cluster_id,
                    'name': f'room_{cluster_id}',
                    'label': f'Room {cluster_id}',
                    'landmarks': cluster_landmarks,
                    'bounds': {
                        'min_x': min(xs),
                        'max_x': max(xs),
                        'min_y': min(ys),
                        'max_y': max(ys),
                        'min_z': min(zs),
                        'max_z': max(zs),
                        'center_x': sum(xs) / len(xs),
                        'center_y': sum(ys) / len(ys),
                        'center_z': sum(zs) / len(zs),
                    }
                }

                self.rooms.append(room_data)

                print(f"[RoomMapping] Room {cluster_id}:")
                print(f"  Landmarks: {len(cluster_landmarks)}")
                print(f"  Center: ({room_data['bounds']['center_x']:.2f}, {room_data['bounds']['center_y']:.2f})")
                print(f"  Size: {room_data['bounds']['max_x'] - room_data['bounds']['min_x']:.2f}m x {room_data['bounds']['max_y'] - room_data['bounds']['min_y']:.2f}m")

        # If no clusters found, create single room
        if not self.rooms:
            self._create_single_room()

    def _simple_clustering(self):
        """Simple grid-based clustering without sklearn"""
        # Assign each landmark to a grid cell
        grid_assignments = {}

        for i, lm in enumerate(self.landmarks):
            # Grid cell coordinates
            grid_x = int(lm['x'] / self.clustering_eps)
            grid_y = int(lm['y'] / self.clustering_eps)
            grid_cell = (grid_x, grid_y)

            if grid_cell not in grid_assignments:
                grid_assignments[grid_cell] = []
            grid_assignments[grid_cell].append(i)

        # Merge adjacent cells into clusters
        visited = set()
        labels = [-1] * len(self.landmarks)
        cluster_id = 0

        for cell in grid_assignments.keys():
            if cell in visited:
                continue

            # Flood fill to find connected cells
            cluster_cells = self._flood_fill(cell, grid_assignments, visited)

            # Count total landmarks in this cluster
            cluster_indices = []
            for c in cluster_cells:
                cluster_indices.extend(grid_assignments[c])

            # Assign cluster label if enough landmarks
            if len(cluster_indices) >= self.clustering_min_samples:
                for idx in cluster_indices:
                    labels[idx] = cluster_id
                cluster_id += 1

        return labels

    def _flood_fill(self, start_cell, grid_assignments, visited):
        """Find all connected grid cells"""
        stack = [start_cell]
        cluster = []

        while stack:
            cell = stack.pop()

            if cell in visited or cell not in grid_assignments:
                continue

            visited.add(cell)
            cluster.append(cell)

            # Check 8 neighbors
            x, y = cell
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (x + dx, y + dy)
                    if neighbor not in visited:
                        stack.append(neighbor)

        return cluster

    def _create_single_room(self):
        """Create a single room containing all landmarks"""
        if not self.landmarks:
            print("[RoomMapping] ERROR: No landmarks available to create room")
            return

        print("[RoomMapping] Creating single room with all landmarks")

        xs = [lm['x'] for lm in self.landmarks]
        ys = [lm['y'] for lm in self.landmarks]
        zs = [lm['z'] for lm in self.landmarks]

        room_data = {
            'cluster_id': 0,
            'name': 'room_0',
            'label': 'Main Room',
            'landmarks': self.landmarks,
            'bounds': {
                'min_x': min(xs),
                'max_x': max(xs),
                'min_y': min(ys),
                'max_y': max(ys),
                'min_z': min(zs),
                'max_z': max(zs),
                'center_x': sum(xs) / len(xs),
                'center_y': sum(ys) / len(ys),
                'center_z': sum(zs) / len(zs),
            }
        }

        self.rooms.append(room_data)
        print(f"[RoomMapping] Main Room: {len(self.landmarks)} landmarks")

    def save_rooms_to_database(self):
        """Save detected rooms to database"""
        print(f"[RoomMapping] Saving {len(self.rooms)} rooms to database...")

        # Clear existing rooms (optional - comment out to preserve manual edits)
        # self.room_db.clear_all_rooms()

        for room in self.rooms:
            try:
                # Check if room already exists
                existing = self.room_db.get_room_by_name(room['name'])

                if existing:
                    print(f"[RoomMapping] Room '{room['name']}' already exists, skipping")
                    continue

                # Add new room
                room_id = self.room_db.add_room(
                    name=room['name'],
                    label=room['label'],
                    bounds=room['bounds'],
                    landmarks=room['landmarks']
                )

                # Add default waypoint at room center
                self.room_db.add_waypoint(
                    room_id=room_id,
                    name=f"{room['name']}_center",
                    x=room['bounds']['center_x'],
                    y=room['bounds']['center_y'],
                    heading=0.0
                )

            except Exception as e:
                print(f"[RoomMapping] Error saving room {room['name']}: {e}")

        print(f"[RoomMapping] Room database updated")

    def label_rooms_with_gpt4v(self):
        """Use GPT-4V to semantically label rooms (optional enhancement)"""
        # This would:
        # 1. Request camera capture at each room center
        # 2. Send image to GPT-4V with prompt: "What type of room is this? (kitchen, bedroom, etc)"
        # 3. Update room label in database

        # For now, just use default labels
        print("[RoomMapping] GPT-4V labeling not yet implemented (using default labels)")
        pass

    def start(self):
        """Main room mapping workflow"""
        print("[RoomMapping] Starting Room Mapping Node...")

        # Run mapping once and exit (standalone mode)
        if self.load_map_landmarks():
            self.cluster_into_rooms()
            self.save_rooms_to_database()

        print("[RoomMapping] Room mapping complete")
        print(f"[RoomMapping] Available rooms:")
        for room in self.room_db.get_all_rooms():
            print(f"  - {room['name']}: {room['label']} ({room['num_landmarks']} landmarks)")

        self.room_db.close()

    def _handle_remap_request(self, data):
        """Handle request to re-cluster rooms"""
        print("[RoomMapping] Remapping rooms...")
        self.rooms = []
        if self.load_map_landmarks():
            self.cluster_into_rooms()
            self.save_rooms_to_database()

    def _handle_room_query(self, data):
        """Handle room lookup queries"""
        room_name = data.get('name')
        x, y = data.get('x'), data.get('y')

        if room_name:
            room = self.room_db.get_room_by_name(room_name)
            if room:
                self.message_bus.publish('slam_room_response', room)
        elif x is not None and y is not None:
            room = self.room_db.get_room_at_position(x, y)
            if room:
                self.message_bus.publish('slam_room_response', room)


if __name__ == '__main__':
    node = RoomMappingNode()
    try:
        node.start()
    except KeyboardInterrupt:
        print("\n[RoomMapping] Shutting down...")
        node.room_db.close()
