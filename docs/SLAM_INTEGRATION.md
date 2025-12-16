# SLAM Integration Guide

## Overview

Nevil now supports room-to-room autonomous navigation using **stella_vslam** for localization and mapping. This integration enables:

- **Real-time localization** - Know where Nevil is at all times
- **Room detection** - Automatically cluster map landmarks into rooms
- **Path planning** - A* pathfinding to navigate between rooms
- **Natural language navigation** - "Nevil, go to the kitchen"

## Architecture

```
┌─────────────────────────────────────────────┐
│ External: stella_vslam                      │
│ Location: /home/dan/Documents/openvslam    │
│ - Executables: run_image_slam, etc.        │
│ - Map database: my_map.msg (2150 landmarks)│
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│ Nevil SLAM Nodes (Bridge)                   │
│                                             │
│ 1. slam_localization_node.py               │
│    - Runs stella_vslam as subprocess        │
│    - Publishes pose to message bus          │
│                                             │
│ 2. slam_room_mapping_node.py               │
│    - Clusters landmarks into rooms (DBSCAN)│
│    - Stores in rooms.db                     │
│                                             │
│ 3. slam_navigation_node.py                 │
│    - A* path planning                       │
│    - Waypoint generation                    │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│ Existing: navigation_node.py               │
│ - Executes waypoints                        │
│ - Motor control with SLAM feedback          │
└─────────────────────────────────────────────┘
```

## Prerequisites

### 1. stella_vslam Installation

stella_vslam must be installed separately in `/home/dan/Documents/openvslam`:

```bash
# stella_vslam should already be installed
ls /home/dan/Documents/stella_vslam_examples/build/
# Should see: run_image_slam, run_camera_slam, etc.
```

### 2. Map Database

You need a pre-built SLAM map (`my_map.msg`):

```bash
# Check if map exists
ls -lh /home/dan/Documents/openvslam/my_map.msg
# Should show ~5MB file with 2150 landmarks

# Check map metadata
python3 /home/dan/Documents/openvslam/inspect_map.py
```

### 3. Dependencies

Install Python packages:

```bash
cd /home/dan/Nevil-picar-v3
pip install scikit-learn scipy numpy
```

## Configuration

All SLAM settings are in `.env`:

```bash
# SLAM Configuration (External stella_vslam)
SLAM_EXECUTABLE_DIR=/home/dan/Documents/stella_vslam_examples/build
SLAM_ROOT=/home/dan/Documents/openvslam
SLAM_MAP_FILE=/home/dan/Documents/openvslam/my_map.msg
SLAM_MAP_JSON=/home/dan/Documents/openvslam/my_map.json
SLAM_CAMERA_CONFIG=/home/dan/Documents/openvslam/pi_camera_640x480.yaml
SLAM_VOCAB_FILE=/home/dan/vocab/orb_vocab.fbow
SLAM_ROOMS_DB=/home/dan/Nevil-picar-v3/data/slam/rooms.db
SLAM_UPDATE_RATE=10
SLAM_GRID_RESOLUTION=0.05
SLAM_ROBOT_RADIUS=0.15
SLAM_WAYPOINT_THRESHOLD=0.2
```

## Enabling SLAM

### Step 1: Enable SLAM Nodes

Edit `.nodes` configuration:

```yaml
slam:
  enabled: true  # Change from false to true
```

### Step 2: Generate Room Map

Run room mapping to cluster landmarks:

```bash
cd /home/dan/Nevil-picar-v3
python3 nodes/slam/room_mapping_node.py
```

This will:
- Load 2150 landmarks from `my_map.json`
- Cluster into rooms using DBSCAN
- Save to `data/slam/rooms.db`

Expected output:
```
[RoomMapping] Found 3 room clusters
[RoomMapping] Room 0:
  Landmarks: 850
  Center: (0.47, 0.45)
  Size: 1.85m x 1.17m
```

### Step 3: Inspect Rooms

Check detected rooms:

```bash
sqlite3 data/slam/rooms.db "SELECT * FROM rooms"
```

### Step 4: Start Nevil with SLAM

```bash
# Start all nodes including SLAM
python3 launcher.py
```

## Usage

### Command Examples

Once SLAM is running, you can use natural language navigation:

**User:** "Nevil, go to room 0"

**User:** "Nevil, navigate to the kitchen"
*(Requires manual room labeling first)*

**User:** "Nevil, where are you?"
**Nevil:** "I'm at position (0.5, 0.3) in room_1"

### Manual Room Labeling

After initial clustering, label rooms manually:

```bash
sqlite3 data/slam/rooms.db

# Label room 0 as kitchen
UPDATE rooms SET label = 'kitchen' WHERE room_id = 0;

# Label room 1 as living room
UPDATE rooms SET label = 'living room' WHERE room_id = 1;
```

### Message Bus Topics

**SLAM publishes:**
- `slam_pose` - Current robot pose (10 Hz)
  ```python
  {
    'x': 0.5, 'y': 0.3, 'z': 0.0,
    'qx': 0.0, 'qy': 0.0, 'qz': 0.0, 'qw': 1.0,
    'timestamp': 1234567890.123,
    'tracking_state': 'Tracking'
  }
  ```

- `slam_rooms_updated` - Room list after clustering
- `navigation_complete` - Path execution finished
- `navigation_failed` - Path planning failed

**SLAM subscribes to:**
- `navigate_to_room` - Navigate to room by name
  ```python
  {'room': 'kitchen'}
  ```

- `slam_cancel_navigation` - Stop navigation

- `slam_remap_rooms` - Re-cluster landmarks

### Programmatic Usage

From AI cognition node:

```python
# Navigate to a room
self.message_bus.publish('navigate_to_room', {'room': 'kitchen'})

# Get current pose
self.message_bus.subscribe('slam_pose', self._handle_pose)

def _handle_pose(self, pose):
    x, y = pose['x'], pose['y']
    print(f"Current position: ({x:.2f}, {y:.2f})")
```

## Troubleshooting

### Problem: "stella_vslam executable not found"

**Solution:**
```bash
# Check stella_vslam installation
ls /home/dan/Documents/stella_vslam_examples/build/run_image_slam
# If missing, rebuild stella_vslam
```

### Problem: "Map file not found"

**Solution:**
```bash
# Verify map exists
ls -lh /home/dan/Documents/openvslam/my_map.msg

# If missing, create new map using picar_slam_live.py
cd /home/dan/Documents/openvslam
python3 picar_slam_live.py
# Drive around, press 'R' to record, then process frames
```

### Problem: "No rooms detected"

**Possible causes:**
1. Map too small - Current map is 1.85m x 1.17m, may be only one room
2. Clustering parameters too strict

**Solution:**
```python
# Adjust in room_mapping_node.py
self.clustering_eps = 0.5  # Increase from 0.3
self.clustering_min_samples = 30  # Decrease from 50
```

### Problem: "Tracking Lost"

**Solution:**
- Ensure good lighting
- Move slowly for feature tracking
- Check camera is working: `python3 nodes/visual/visual_node.py`

### Problem: "No path found"

**Possible causes:**
1. Start/goal in obstacle
2. No valid path exists
3. Grid resolution too coarse

**Solution:**
```bash
# Check grid settings in .env
SLAM_GRID_RESOLUTION=0.03  # Decrease from 0.05 for finer grid
SLAM_ROBOT_RADIUS=0.10     # Decrease from 0.15 if too conservative
```

## Advanced Features

### Expanding the Map

To map additional rooms:

1. **Record new frames:**
   ```bash
   cd /home/dan/Documents/openvslam
   python3 picar_slam_live.py
   # Drive to new room, press 'R' to record
   ```

2. **Extend existing map:**
   ```bash
   cd /home/dan/Documents/stella_vslam_examples/build
   ./run_image_slam \
     -v ~/vocab/orb_vocab.fbow \
     -d /tmp/picar_slam_NEW_TIMESTAMP \
     -c ~/Documents/openvslam/pi_camera_640x480.yaml \
     -i ~/Documents/openvslam/my_map.msg \
     -o ~/Documents/openvslam/my_map_extended.msg
   ```

3. **Re-cluster rooms:**
   ```bash
   python3 nodes/slam/room_mapping_node.py
   ```

### Custom Room Boundaries

Manually define room boundaries:

```python
from nodes.slam.room_database import RoomDatabase

db = RoomDatabase()

# Add custom room
db.add_room(
    name='office',
    label='Office',
    bounds={
        'min_x': 0.0, 'max_x': 2.0,
        'min_y': 0.0, 'max_y': 1.5,
        'min_z': 0.0, 'max_z': 2.0,
        'center_x': 1.0, 'center_y': 0.75, 'center_z': 1.0
    }
)

# Add waypoint
db.add_waypoint(room_id=1, name='desk', x=1.5, y=0.5, heading=0.0)
```

### Visualization

Export path for visualization:

```python
# In slam_navigation_node.py, add:
import matplotlib.pyplot as plt

def visualize_path(self, path):
    grid = self.grid.grid
    plt.imshow(grid, cmap='gray')

    path_x = [self.grid.world_to_grid(x, y)[0] for x, y in path]
    path_y = [self.grid.world_to_grid(x, y)[1] for x, y in path]

    plt.plot(path_x, path_y, 'r-', linewidth=2)
    plt.savefig('/tmp/nevil_path.png')
```

## Files Reference

### Created by Integration

```
Nevil-picar-v3/
├── nodes/slam/
│   ├── __init__.py
│   ├── slam_localization_node.py    # stella_vslam bridge
│   ├── room_mapping_node.py         # Room clustering
│   ├── slam_navigation_node.py      # A* path planning
│   └── room_database.py             # Room database manager
│
├── data/slam/
│   ├── maps/                        # (Empty - references external)
│   └── rooms.db                     # Room definitions (auto-generated)
│
├── .env                             # SLAM configuration added
└── docs/SLAM_INTEGRATION.md         # This file
```

### External Dependencies

```
/home/dan/Documents/openvslam/       # stella_vslam installation (KEEP SEPARATE)
├── my_map.msg                       # SLAM map database (2150 landmarks)
├── my_map.json                      # JSON export of map
├── pi_camera_640x480.yaml           # Camera calibration
└── build/
    ├── run_image_slam               # SLAM executable
    └── run_camera_slam              # Live SLAM executable

/home/dan/vocab/
└── orb_vocab.fbow                   # ORB vocabulary for SLAM
```

## Performance Tips

### Raspberry Pi Optimization

1. **Lower update rate:**
   ```bash
   SLAM_UPDATE_RATE=5  # From 10 Hz to 5 Hz
   ```

2. **Coarser grid:**
   ```bash
   SLAM_GRID_RESOLUTION=0.10  # From 0.05 to 0.10
   ```

3. **Disable mapping mode** (always use localization-only):
   - Localization mode is already enabled by default when `my_map.msg` exists

### Memory Usage

- stella_vslam process: ~200-300 MB
- Occupancy grid: ~40 KB (200x200 @ 1 byte/cell)
- Room database: <1 MB

## Next Steps

1. **Test basic navigation:**
   ```bash
   python3 nodes/slam/slam_navigation_node.py
   # In another terminal:
   python3 -c "
   from nevil_framework.message_bus import MessageBus
   bus = MessageBus()
   bus.publish('navigate_to_room', {'room': 'room_0'})
   "
   ```

2. **Integrate with AI cognition:**
   - Add intent recognition for navigation commands
   - "go to [room]", "navigate to [room]", "take me to [room]"

3. **Add room labeling with GPT-4V:**
   - Capture image at room center
   - Ask GPT-4V: "What type of room is this?"
   - Auto-update room labels

4. **Multi-floor support:**
   - Add `floor_id` to room database
   - Separate maps per floor

## Reference

- **stella_vslam docs:** `/home/dan/Documents/openvslam/README.md`
- **SLAM guide:** `/home/dan/Documents/openvslam/SLAM_NAVIGATION_PLANNING_GUIDE.md`
- **Map inspection:** `python3 /home/dan/Documents/openvslam/inspect_map_detailed.py`

---

**Status:** SLAM integration complete. Nodes are disabled by default. Enable when ready to test navigation.
