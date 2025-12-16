#!/usr/bin/env python3
"""
SLAM Navigation Node

Provides path planning from current pose to goal room using A* algorithm.
Uses SLAM landmarks as obstacles and generates waypoints for navigation_node.
"""

import os
import sys
import time
import math
import numpy as np
from collections import deque
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
import heapq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from nevil_framework.message_bus import MessageBus
from nodes.slam.room_database import RoomDatabase

load_dotenv()


class OccupancyGrid:
    """2D occupancy grid for path planning"""

    def __init__(self, resolution: float = 0.05, width: int = 200, height: int = 200):
        self.resolution = resolution  # meters per cell
        self.width = width
        self.height = height
        self.origin_x = -width * resolution / 2  # Center grid at (0, 0)
        self.origin_y = -height * resolution / 2

        # Grid: 0 = free, 1 = occupied
        self.grid = np.zeros((height, width), dtype=np.uint8)

    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid cell"""
        grid_x = int((x - self.origin_x) / self.resolution)
        grid_y = int((y - self.origin_y) / self.resolution)
        return grid_x, grid_y

    def grid_to_world(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid cell to world coordinates"""
        x = self.origin_x + grid_x * self.resolution
        y = self.origin_y + grid_y * self.resolution
        return x, y

    def is_valid(self, grid_x: int, grid_y: int) -> bool:
        """Check if grid cell is within bounds"""
        return 0 <= grid_x < self.width and 0 <= grid_y < self.height

    def is_free(self, grid_x: int, grid_y: int) -> bool:
        """Check if grid cell is free (not occupied)"""
        if not self.is_valid(grid_x, grid_y):
            return False
        return self.grid[grid_y, grid_x] == 0

    def set_obstacle(self, grid_x: int, grid_y: int):
        """Mark grid cell as occupied"""
        if self.is_valid(grid_x, grid_y):
            self.grid[grid_y, grid_x] = 1

    def inflate_obstacles(self, robot_radius: float):
        """Inflate obstacles by robot radius for safety"""
        inflate_cells = int(robot_radius / self.resolution)

        # Create structuring element (circular footprint)
        from scipy.ndimage import binary_dilation

        footprint = np.zeros((inflate_cells * 2 + 1, inflate_cells * 2 + 1), dtype=bool)
        center = inflate_cells
        for i in range(footprint.shape[0]):
            for j in range(footprint.shape[1]):
                if (i - center)**2 + (j - center)**2 <= inflate_cells**2:
                    footprint[i, j] = True

        # Dilate obstacles
        self.grid = binary_dilation(self.grid, structure=footprint).astype(np.uint8)


class AStarPlanner:
    """A* path planning algorithm"""

    def __init__(self, grid: OccupancyGrid):
        self.grid = grid

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic"""
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def get_neighbors(self, node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring cells (8-connected)"""
        x, y = node
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy

                if self.grid.is_free(nx, ny):
                    neighbors.append((nx, ny))

        return neighbors

    def plan(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        A* pathfinding from start to goal (grid coordinates)
        Returns list of grid cells forming path, or None if no path found
        """
        if not self.grid.is_free(*start):
            print(f"[A*] ERROR: Start position {start} is occupied")
            return None

        if not self.grid.is_free(*goal):
            print(f"[A*] ERROR: Goal position {goal} is occupied")
            return None

        # Priority queue: (f_score, counter, node)
        counter = 0
        open_set = [(0, counter, start)]
        came_from = {}

        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        visited = set()

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current in visited:
                continue

            visited.add(current)

            # Goal reached
            if current == goal:
                return self._reconstruct_path(came_from, current)

            # Explore neighbors
            for neighbor in self.get_neighbors(current):
                # Cost to neighbor (diagonal = sqrt(2), straight = 1)
                dx = abs(neighbor[0] - current[0])
                dy = abs(neighbor[1] - current[1])
                step_cost = math.sqrt(2) if (dx + dy == 2) else 1.0

                tentative_g = g_score[current] + step_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)

                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))

        print(f"[A*] No path found from {start} to {goal}")
        return None

    def _reconstruct_path(self, came_from: Dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct path from came_from chain"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path


class SLAMNavigationNode:
    """Path planning and navigation coordination using SLAM"""

    def __init__(self):
        self.message_bus = MessageBus()
        self.room_db = RoomDatabase()

        # Load configuration
        self.grid_resolution = float(os.getenv('SLAM_GRID_RESOLUTION', '0.05'))
        self.robot_radius = float(os.getenv('SLAM_ROBOT_RADIUS', '0.15'))
        self.waypoint_threshold = float(os.getenv('SLAM_WAYPOINT_THRESHOLD', '0.2'))

        # Occupancy grid
        self.grid = OccupancyGrid(resolution=self.grid_resolution, width=200, height=200)

        # Current state
        self.current_pose = None
        self.current_path = None
        self.navigation_active = False

        # Load landmarks into grid
        self._load_landmarks_to_grid()

    def _load_landmarks_to_grid(self):
        """Load SLAM landmarks as obstacles in occupancy grid"""
        import json

        map_json = os.getenv('SLAM_MAP_JSON', '/home/dan/Documents/openvslam/my_map.json')

        if not os.path.exists(map_json):
            print(f"[SLAMNav] WARNING: Map file not found: {map_json}")
            return

        print(f"[SLAMNav] Loading landmarks into occupancy grid...")

        with open(map_json, 'r') as f:
            map_data = json.load(f)

        landmarks = map_data.get('landmarks', [])
        if isinstance(landmarks, dict):
            landmarks = list(landmarks.values())

        # Mark landmarks as obstacles
        obstacle_count = 0
        for lm in landmarks:
            if isinstance(lm, dict) and 'pos_w' in lm:
                pos = lm['pos_w']
                if len(pos) >= 3:
                    x, y, z = pos[0], pos[1], pos[2]

                    # Only use ground-level landmarks (0.0m to 2.0m height)
                    if 0.0 <= z <= 2.0:
                        grid_x, grid_y = self.grid.world_to_grid(x, y)
                        self.grid.set_obstacle(grid_x, grid_y)
                        obstacle_count += 1

        print(f"[SLAMNav] Loaded {obstacle_count} obstacles into grid")

        # Inflate obstacles by robot radius
        print(f"[SLAMNav] Inflating obstacles by robot radius: {self.robot_radius}m")
        self.grid.inflate_obstacles(self.robot_radius)

        occupied_cells = np.sum(self.grid.grid)
        total_cells = self.grid.width * self.grid.height
        occupancy_percent = (occupied_cells / total_cells) * 100
        print(f"[SLAMNav] Grid occupancy: {occupancy_percent:.1f}% ({occupied_cells}/{total_cells} cells)")

    def start(self):
        """Start navigation node"""
        print("[SLAMNav] Starting SLAM Navigation Node...")

        # Subscribe to topics
        self.message_bus.subscribe('slam_pose', self._handle_pose_update)
        self.message_bus.subscribe('navigate_to_room', self._handle_navigate_to_room)
        self.message_bus.subscribe('slam_cancel_navigation', self._handle_cancel_navigation)

        print("[SLAMNav] Navigation node ready")

        # Keep alive
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[SLAMNav] Shutdown requested")

    def _handle_pose_update(self, pose_data):
        """Update current pose from SLAM"""
        self.current_pose = pose_data

    def _handle_navigate_to_room(self, data):
        """Handle navigation request to a room"""
        room_name = data.get('room')

        if not room_name:
            print("[SLAMNav] ERROR: No room name provided")
            return

        print(f"[SLAMNav] Navigation request to room: {room_name}")

        # Get room from database
        room = self.room_db.get_room_by_name(room_name)

        if not room:
            print(f"[SLAMNav] ERROR: Room '{room_name}' not found")
            self.message_bus.publish('navigation_failed', {'reason': 'room_not_found', 'room': room_name})
            return

        # Get goal position (room center)
        goal_x = room['center_x']
        goal_y = room['center_y']

        print(f"[SLAMNav] Goal: ({goal_x:.2f}, {goal_y:.2f})")

        # Get current position
        if not self.current_pose:
            print("[SLAMNav] ERROR: No current pose available from SLAM")
            self.message_bus.publish('navigation_failed', {'reason': 'no_pose'})
            return

        start_x = self.current_pose['x']
        start_y = self.current_pose['y']

        print(f"[SLAMNav] Current: ({start_x:.2f}, {start_y:.2f})")

        # Plan path
        path = self._plan_path(start_x, start_y, goal_x, goal_y)

        if path:
            print(f"[SLAMNav] Path found with {len(path)} waypoints")
            self.current_path = path
            self.navigation_active = True

            # Send path to navigation_node
            self._execute_path(path)
        else:
            print("[SLAMNav] Path planning failed")
            self.message_bus.publish('navigation_failed', {'reason': 'no_path'})

    def _plan_path(self, start_x: float, start_y: float, goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """Plan path using A* algorithm"""
        print(f"[SLAMNav] Planning path from ({start_x:.2f}, {start_y:.2f}) to ({goal_x:.2f}, {goal_y:.2f})")

        # Convert to grid coordinates
        start_grid = self.grid.world_to_grid(start_x, start_y)
        goal_grid = self.grid.world_to_grid(goal_x, goal_y)

        print(f"[SLAMNav] Grid coords: start={start_grid}, goal={goal_grid}")

        # Check if positions are valid
        if not self.grid.is_free(*start_grid):
            print("[SLAMNav] WARNING: Start position is in obstacle, finding nearest free cell")
            start_grid = self._find_nearest_free_cell(start_grid)

        if not self.grid.is_free(*goal_grid):
            print("[SLAMNav] WARNING: Goal position is in obstacle, finding nearest free cell")
            goal_grid = self._find_nearest_free_cell(goal_grid)

        # Run A* planner
        planner = AStarPlanner(self.grid)
        grid_path = planner.plan(start_grid, goal_grid)

        if not grid_path:
            return None

        # Convert grid path to world coordinates
        world_path = [self.grid.grid_to_world(gx, gy) for gx, gy in grid_path]

        # Simplify path (remove redundant waypoints on straight lines)
        simplified_path = self._simplify_path(world_path)

        return simplified_path

    def _find_nearest_free_cell(self, start: Tuple[int, int], max_search_radius: int = 20) -> Tuple[int, int]:
        """Find nearest free cell using breadth-first search"""
        visited = set()
        queue = deque([start])

        while queue:
            cell = queue.popleft()

            if cell in visited:
                continue

            visited.add(cell)

            if self.grid.is_free(*cell):
                return cell

            # Add neighbors to queue
            x, y = cell
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    neighbor = (x + dx, y + dy)
                    if self.grid.is_valid(*neighbor) and neighbor not in visited:
                        queue.append(neighbor)

        print("[SLAMNav] ERROR: Could not find free cell")
        return start

    def _simplify_path(self, path: List[Tuple[float, float]], angle_threshold: float = 0.1) -> List[Tuple[float, float]]:
        """Remove redundant waypoints on straight segments"""
        if len(path) <= 2:
            return path

        simplified = [path[0]]

        for i in range(1, len(path) - 1):
            prev = np.array(path[i - 1])
            curr = np.array(path[i])
            next_pt = np.array(path[i + 1])

            # Calculate angle change
            v1 = curr - prev
            v2 = next_pt - curr

            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                v1_norm = v1 / np.linalg.norm(v1)
                v2_norm = v2 / np.linalg.norm(v2)

                angle_change = np.arccos(np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0))

                # Keep waypoint if significant direction change
                if angle_change > angle_threshold:
                    simplified.append(tuple(curr))

        simplified.append(path[-1])

        return simplified

    def _execute_path(self, path: List[Tuple[float, float]]):
        """Send waypoints to navigation_node for execution"""
        print(f"[SLAMNav] Executing path with {len(path)} waypoints")

        for i, (x, y) in enumerate(path):
            print(f"[SLAMNav] Waypoint {i+1}/{len(path)}: ({x:.2f}, {y:.2f})")

            # Send waypoint to navigation_node
            self.message_bus.publish('robot_action', {
                'action': 'navigate_to_waypoint',
                'x': x,
                'y': y,
                'threshold': self.waypoint_threshold
            })

            # Wait for waypoint completion (simplified - needs proper feedback)
            # In production, navigation_node should publish waypoint_reached
            time.sleep(2)  # Placeholder

        print("[SLAMNav] Path execution complete")
        self.navigation_active = False
        self.message_bus.publish('navigation_complete', {'success': True})

    def _handle_cancel_navigation(self, data):
        """Cancel ongoing navigation"""
        if self.navigation_active:
            print("[SLAMNav] Canceling navigation")
            self.navigation_active = False
            self.current_path = None
            self.message_bus.publish('robot_action', {'action': 'stop'})


if __name__ == '__main__':
    node = SLAMNavigationNode()
    try:
        node.start()
    except KeyboardInterrupt:
        print("\n[SLAMNav] Shutting down...")
