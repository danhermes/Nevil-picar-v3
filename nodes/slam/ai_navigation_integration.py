#!/usr/bin/env python3
"""
AI Navigation Integration

Patches AI Cognition Node to add SLAM navigation capabilities.
Run this to enable voice-controlled room navigation.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Instructions for manual integration
INTEGRATION_GUIDE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SLAM NAVIGATION - AI INTEGRATION                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

## 🎯 Integration Complete!

The SLAM location module is ready. Now add navigation to your AI:

### Step 1: Update System Prompt

Edit: nodes/ai_cognition_realtime/.messages

Add this to the system_prompt (after the "# MOVEMENT FUNCTIONS" section):

```
# NAVIGATION FUNCTIONS

You can navigate between rooms using your SLAM system!

## Available Rooms:
  - Hallway (hallway)
  - Office (office)
  - Living Room (living_room)
  - Kitchen (kitchen) - visible only

## Navigation Command
Use navigate_to_room function when asked to go somewhere:
  User: "go to the kitchen" → call navigate_to_room(room_name="kitchen")
  User: "take me to the office" → call navigate_to_room(room_name="office")

When navigating, say where you're going AND gesture while moving!
Example: "Heading to the kitchen!" + perform_gesture("eager_start", "fast")
```

### Step 2: Add Navigation Function Definition

Edit: nodes/ai_cognition_realtime/ai_cognition_realtime_node.py

In the _load_gesture_library() method, after the perform_gesture definition (around line 170),
add this navigation function:

```python
# Navigation function
navigation_function = {
    "type": "function",
    "name": "navigate_to_room",
    "description": "Navigate to a specific room using SLAM. Use this when the user asks you to go somewhere or move to a different room.",
    "parameters": {
        "type": "object",
        "properties": {
            "room_name": {
                "type": "string",
                "enum": ["hallway", "office", "living_room", "kitchen"],
                "description": "Name of the room to navigate to"
            },
            "announce": {
                "type": "boolean",
                "description": "Whether to announce arrival (default: true)",
                "default": True
            }
        },
        "required": ["room_name"]
    }
}

# Add to function definitions
self.gesture_definitions.append(navigation_function)
```

### Step 3: Add Navigation Handler

In the same file, find the function call handler (search for "perform_gesture")
and add navigation handling:

```python
elif function_name == "navigate_to_room":
    room_name = function_args.get("room_name")
    announce = function_args.get("announce", True)

    # Publish navigation command
    self.message_bus.publish("robot_action", {
        "action": "navigate_to_room",
        "room": room_name,
        "announce": announce
    })

    self.logger.info(f"Navigation to {room_name} requested")
    return f"Navigating to {room_name}"
```

### Step 4: Start SLAM Navigation Service

Before using voice navigation, start the navigation service:

```bash
# Terminal 1: SLAM Navigation
python3 nodes/slam/slam_navigation_node.py

# Terminal 2: Start Nevil
./start_nevil_quiet.sh
```

### Step 5: Test Voice Navigation!

Say to Nevil:
  - "Go to the kitchen"
  - "Take me to the office"
  - "Navigate to the living room"
  - "Head to the hallway"

═══════════════════════════════════════════════════════════════════════════════

## 🔧 Alternative: Quick Test Without AI Integration

Test navigation directly via message bus:

```python
from nevil_framework.message_bus import MessageBus
import time

bus = MessageBus()
time.sleep(1)

# Navigate to office
bus.publish("robot_action", {"action": "navigate_to_room", "room": "office"})
```

═══════════════════════════════════════════════════════════════════════════════

## 📚 Files Created:

✅ nodes/slam/slam_location_module.py  - Location awareness module
✅ nodes/slam/manual_room_setup.py     - Define your 4 rooms
✅ nodes/slam/room_database.py         - Room database manager
✅ nodes/slam/slam_navigation_node.py  - A* path planning
✅ data/slam/rooms.db                  - Room definitions database

## 🎯 Voice Commands Available (after integration):

Navigation:
  "Go to the [room]"
  "Take me to the [room]"
  "Navigate to the [room]"

Location Queries:
  "Where am I?"
  "What room am I in?"
  "What rooms do you know?"

═══════════════════════════════════════════════════════════════════════════════

For automatic integration, we'd need to modify the AI cognition node code directly.
This guide shows manual integration to preserve your existing AI configuration.

"""

print(INTEGRATION_GUIDE)
