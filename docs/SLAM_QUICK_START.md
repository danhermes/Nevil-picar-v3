# SLAM Quick Start Guide

## ✅ What's Installed

SLAM integration is complete! Here's what you have:

```
✅ External stella_vslam: /home/dan/Documents/openvslam (kept separate)
✅ SLAM nodes: /home/dan/Nevil-picar-v3/nodes/slam/
✅ Configuration: .env (SLAM_* variables)
✅ Documentation: docs/SLAM_INTEGRATION.md
```

Your existing map:
- **2150 landmarks** from my_map.msg
- **99 keyframes**
- **Coverage:** ~1.85m × 1.17m space

## 🚀 How to Use SLAM for Room Navigation

### Option 1: Quick Test (Room Mapping)

Generate rooms from your existing map:

```bash
cd /home/dan/Nevil-picar-v3

# Cluster landmarks into rooms
python3 nodes/slam/room_mapping_node.py
```

**Expected output:**
```
[RoomMapping] Loaded 2150 landmarks
[RoomMapping] Found 3 room clusters
[RoomMapping] Room 0: 850 landmarks, center (0.47, 0.45)
[RoomMapping] Saved to data/slam/rooms.db
```

Check detected rooms:
```bash
sqlite3 data/slam/rooms.db "SELECT room_id, name, label, num_landmarks FROM rooms"
```

### Option 2: Full Navigation System

Run all SLAM services:

```bash
# Terminal 1: Room mapping (run once)
python3 nodes/slam/room_mapping_node.py

# Terminal 2: Path planning service
python3 nodes/slam/slam_navigation_node.py

# Terminal 3: Send navigation command
python3 -c "
from nevil_framework.message_bus import MessageBus
bus = MessageBus()
bus.publish('navigate_to_room', {'room': 'room_0'})
"
```

### Option 3: With Real-time Localization

For live pose tracking during navigation:

```bash
# Terminal 1: SLAM localization
python3 nodes/slam/slam_localization_node.py

# Terminal 2: Navigation
python3 nodes/slam/slam_navigation_node.py

# Terminal 3: Monitor pose
python3 -c "
from nevil_framework.message_bus import MessageBus
bus = MessageBus()

def show_pose(pose):
    print(f\"Position: ({pose['x']:.2f}, {pose['y']:.2f}) - {pose['tracking_state']}\")

bus.subscribe('slam_pose', show_pose)
import time
while True: time.sleep(0.5)
"
```

## 📝 Labeling Rooms

After generating rooms, give them meaningful names:

```bash
sqlite3 data/slam/rooms.db

UPDATE rooms SET label='Kitchen' WHERE room_id=0;
UPDATE rooms SET label='Living Room' WHERE room_id=1;
UPDATE rooms SET label='Bedroom' WHERE room_id=2;

.quit
```

Then navigate using natural names:
```python
bus.publish('navigate_to_room', {'room': 'Kitchen'})
```

## 🗺️ Map Info

Check your current map:

```bash
# View map metadata
python3 /home/dan/Documents/openvslam/inspect_map.py

# Detailed inspection
python3 /home/dan/Documents/openvslam/inspect_map_detailed.py
```

## 🔧 Troubleshooting

### "No rooms detected"

Your current map (1.85m × 1.17m) might be small. Adjust clustering:

```python
# Edit nodes/slam/room_mapping_node.py
self.clustering_eps = 0.5  # Increase from 0.3
self.clustering_min_samples = 30  # Decrease from 50
```

### "stella_vslam not found"

Check installation:
```bash
ls /home/dan/Documents/stella_vslam_examples/build/run_image_slam
```

If missing, rebuild stella_vslam.

### "Map file not found"

Verify map exists:
```bash
ls -lh /home/dan/Documents/openvslam/my_map.{msg,json}
```

If missing, create new map:
```bash
cd /home/dan/Documents/openvslam
python3 picar_slam_live.py
# Drive around, press 'R' to record frames
# Then run save_slam_map.sh
```

## 📚 Architecture

```
External: stella_vslam (/home/dan/Documents/openvslam)
    ↓
Nevil SLAM Nodes:
    1. room_mapping_node.py    - Cluster landmarks → rooms
    2. slam_navigation_node.py  - A* path planning
    3. slam_localization_node.py - Real-time pose (optional)
    ↓
Existing: navigation_node.py   - Execute waypoints
```

## 💡 Tips

1. **Start simple:** Just run `room_mapping_node.py` first to see rooms
2. **Manual mode:** SLAM nodes run independently, not in launcher
3. **Keep separate:** stella_vslam stays in Documents/openvslam
4. **Map expansion:** Record new areas, extend map, re-cluster

## 📖 Full Documentation

See **docs/SLAM_INTEGRATION.md** for:
- Complete API reference
- Message bus topics
- Advanced features
- Visualization
- Performance tuning

## 🎯 Next Steps

1. ✅ Run `room_mapping_node.py` to see your rooms
2. Label rooms with meaningful names
3. Test navigation to a room
4. Integrate with AI cognition for voice commands:
   - "Nevil, go to the kitchen"
   - "Nevil, navigate to the bedroom"

---

**Status:** ✅ SLAM integration complete and tested. Ready to use!
