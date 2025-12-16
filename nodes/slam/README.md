# SLAM Nodes

These nodes provide room-to-room navigation using external stella_vslam.

## Running SLAM Nodes

SLAM nodes are **run separately** from the main launcher, as they are optional features.

### Step 1: Generate Room Map

First, cluster your SLAM landmarks into rooms:

```bash
cd /home/dan/Nevil-picar-v3
python3 nodes/slam/room_mapping_node.py
```

This will:
- Load 2150 landmarks from `/home/dan/Documents/openvslam/my_map.json`
- Cluster into rooms using DBSCAN
- Save to `data/slam/rooms.db`

Expected output:
```
[RoomMapping] Loading landmarks from /home/dan/Documents/openvslam/my_map.json
[RoomMapping] Loaded 2150 landmarks
[RoomMapping] Found 3 room clusters
[RoomMapping] Room 0: 850 landmarks, center (0.47, 0.45), size 1.85m x 1.17m
```

### Step 2: Start Navigation Node

Start the path planning service:

```bash
python3 nodes/slam/slam_navigation_node.py
```

This loads the occupancy grid and waits for navigation commands.

### Step 3: Start Localization (Optional)

For real-time pose tracking:

```bash
python3 nodes/slam/slam_localization_node.py
```

This runs stella_vslam in localization mode and publishes pose to message bus.

## Testing Navigation

Send a navigation command via message bus:

```bash
python3 -c "
from nevil_framework.message_bus import MessageBus
bus = MessageBus()
bus.publish('navigate_to_room', {'room': 'room_0'})
"
```

## Inspecting Rooms

Check detected rooms:

```bash
sqlite3 data/slam/rooms.db "SELECT room_id, name, label, num_landmarks FROM rooms"
```

Label rooms manually:

```bash
sqlite3 data/slam/rooms.db "UPDATE rooms SET label='kitchen' WHERE room_id=0"
```

## Architecture

```
nodes/slam/
├── room_mapping_node.py       # Run once to cluster landmarks
├── slam_navigation_node.py    # Path planning service (keep running)
├── slam_localization_node.py  # Real-time pose (optional)
└── room_database.py           # Database utilities
```

## Files

- **Input:** `/home/dan/Documents/openvslam/my_map.json` (external)
- **Output:** `data/slam/rooms.db` (generated)
- **Config:** `.env` (SLAM_* variables)

## Documentation

See **docs/SLAM_INTEGRATION.md** for complete guide.

## Why Separate?

SLAM nodes are:
- **Optional** - Not needed for basic operation
- **Resource-intensive** - Run only when navigation is needed
- **Manual** - Typically used for specific tasks, not continuous operation

This keeps the main launcher lightweight and fast.
