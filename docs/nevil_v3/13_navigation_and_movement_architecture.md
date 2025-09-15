# Nevil v3.0 Navigation and Movement Architecture

## Overview

This document defines the navigation and movement system for Nevil v3.0, combining the proven v1.0 action_helper.py movement implementation with the AI-driven action parsing system. The navigation node receives parsed actions from AI responses and executes them on the PiCar-X hardware.

## Critical Implementation Note

**The v1.0 action_helper.py will be used VERBATIM as it contains the optimal movement mappings for the PiCar-X robot.** This has been thoroughly tested and calibrated for this specific hardware platform.

## Action Flow Architecture

```
User Voice Command → AI Cognition → JSON Response with Actions → Action Parser → Navigation Node → PiCar-X Hardware
```

### AI Response Format (from nevil_prompt.txt)

The AI generates responses in JSON format containing both text and actions:

```json
{
    "answer": "Let me check that out!",
    "actions": ["keep_think", "forward 30", "left"],
    "mood": "curious"
}
```

### Available Actions

#### Movement Actions (Parameterized)
- `forward [distance_cm] [speed]` - Move forward with optional distance (cm) and speed (0-50)
- `backward [distance_cm] [speed]` - Move backward with optional distance and speed
- `left` - Turn left (compound movement)
- `right` - Turn right (compound movement)
- `stop` - Stop all movement
- `twist left` - Turn wheels left in place
- `twist right` - Turn wheels right in place

#### Expression Actions
- `shake_head` - Pan camera side to side
- `nod` - Tilt camera up and down
- `wave_hands` - Wiggle steering servos
- `resist` - Resistance movement pattern
- `act_cute` - Cute behavior pattern
- `rub_hands` - Small steering movements
- `think` - Thinking gesture
- `keep_think` - Continue thinking gesture
- `twist_body` - Body twist movement
- `celebrate` - Celebration pattern
- `depressed` - Sad gesture

#### Sound Actions
- `honk` - Play horn sound
- `start_engine` - Play engine sound

## Navigation Node Implementation

### Core Components

```python
# nodes/navigation/navigation_node.py

import time
import threading
import queue
import json
from typing import Dict, Any, List, Optional
from nevil_framework.base_node import NevilNode
from v1.0.helpers.action_helper import actions_dict  # Use v1.0 verbatim
from picarx import Picarx  # Hardware interface

class NavigationNode(NevilNode):
    """
    Navigation Node for Nevil v3.0

    Executes movement commands and expressive actions from AI responses.
    Uses proven v1.0 action_helper for all movement implementations.
    """

    def __init__(self):
        super().__init__("navigation")

        # Hardware interface
        self.car = None
        self.simulation_mode = False

        # Action processing
        self.action_queue = queue.PriorityQueue(maxsize=50)
        self.current_action = None
        self.action_lock = threading.Lock()

        # Movement configuration
        self.default_speed = 30

        # Import v1.0 action functions
        self.action_functions = actions_dict

    def initialize(self):
        """Initialize navigation and hardware"""
        try:
            # Initialize PiCar-X hardware
            self.car = Picarx()
            self.car.set_dir_servo_angle(0)
            self.car.set_cam_pan_angle(0)
            self.car.set_cam_tilt_angle(0)

            # Set default speed
            self.car.speed = self.default_speed

            self.logger.info("PiCar-X hardware initialized")

        except Exception as e:
            self.logger.warning(f"Hardware init failed: {e}, using simulation")
            self.simulation_mode = True

        # Start action processing thread
        self.action_thread = threading.Thread(
            target=self._action_processing_loop,
            daemon=True
        )
        self.action_thread.start()
```

### Action Message Handler

```python
    def on_robot_action(self, message):
        """Handle robot action messages from AI cognition"""
        try:
            data = message.data
            actions = data.get('actions', [])
            priority = data.get('priority', 100)
            source_text = data.get('source_text', '')

            if not actions:
                return

            # Create action sequence
            action_sequence = {
                'actions': actions,
                'source_text': source_text,
                'timestamp': time.time(),
                'action_id': message.message_id
            }

            # Add to priority queue
            self.action_queue.put((priority, time.time(), action_sequence))

            self.logger.info(f"Queued {len(actions)} actions from: '{source_text[:50]}...'")

        except Exception as e:
            self.logger.error(f"Error handling robot action: {e}")
```

### Action Parser and Executor

```python
    def _parse_action(self, action_str: str) -> Dict[str, Any]:
        """Parse an action string into function and parameters"""
        parts = action_str.split()
        action_name = parts[0]

        # Handle parameterized movement actions
        if action_name in ['forward', 'backward']:
            distance = int(parts[1]) if len(parts) > 1 else 10
            speed = int(parts[2]) if len(parts) > 2 else self.default_speed

            return {
                'function': self.action_functions.get(action_name),
                'params': {'distance_cm': distance, 'speed': speed}
            }

        # Handle simple actions
        elif action_name in self.action_functions:
            return {
                'function': self.action_functions[action_name],
                'params': {}
            }

        # Handle compound action names
        else:
            # Try joining parts for multi-word actions like "shake head"
            full_action = ' '.join(parts)
            if full_action in self.action_functions:
                return {
                    'function': self.action_functions[full_action],
                    'params': {}
                }

        self.logger.warning(f"Unknown action: {action_str}")
        return None

    def _execute_action(self, action_data: Dict[str, Any]):
        """Execute a parsed action"""
        if not action_data or not action_data['function']:
            return

        try:
            func = action_data['function']
            params = action_data['params']

            if self.simulation_mode:
                self.logger.info(f"[SIM] Executing: {func.__name__}({params})")
                time.sleep(0.5)  # Simulate execution time
            else:
                # Execute on real hardware
                if params:
                    func(self.car, **params)
                else:
                    func(self.car)

        except Exception as e:
            self.logger.error(f"Action execution error: {e}")
```

## AI Cognition Integration

### Response Parser in AI Cognition Node

```python
# In ai_cognition_node.py

def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
    """Parse AI response to extract text and actions"""
    try:
        # AI responses should be in JSON format
        response_data = json.loads(response_text)

        return {
            'answer': response_data.get('answer', ''),
            'actions': response_data.get('actions', []),
            'mood': response_data.get('mood', 'neutral')
        }

    except json.JSONDecodeError:
        # Fallback for non-JSON responses
        return {
            'answer': response_text,
            'actions': [],
            'mood': 'neutral'
        }

def _publish_actions(self, actions: List[str], source_text: str):
    """Publish robot actions to navigation node"""
    if not actions:
        return

    action_data = {
        'actions': actions,
        'source_text': source_text,
        'priority': 100,
        'timestamp': time.time()
    }

    self.publish("robot_action", action_data)
```

## Message Specifications

### robot_action Topic

```yaml
# nodes/navigation/.messages

subscribes:
  - topic: "robot_action"
    message_type: "RobotAction"
    callback: "on_robot_action"
    description: "Movement and expression commands from AI"
    schema:
      actions:
        type: "array"
        required: true
        description: "List of action commands to execute"
        items:
          type: "string"
      source_text:
        type: "string"
        required: false
        description: "Original user command that triggered actions"
      priority:
        type: "integer"
        required: false
        default: 100
        description: "Execution priority (lower = higher priority)"
```

## Movement Calibration

### Distance and Speed Mapping

From v1.0 action_helper.py:
- **Distance calibration**: `distance_cm = distance_cm * 3` (hardware-specific)
- **Speed to cm/sec**: 0.7 (needs fine-tuning per robot)
- **Speed range**: 0-50 (optimal: 5-40)
- **Turn angles**: ±30 degrees for steering servo

### Movement Parameters

- **Default speed**: 30 (range: 0-50)
- **Minimum move distance**: 5cm
- **Maximum continuous move**: 100cm

## Testing Strategy

### Unit Tests
1. Action parsing for all command formats
2. Queue management and prioritization
3. Hardware interface mocking

### Integration Tests
1. AI response → Action execution flow
2. Multiple action sequences
3. Interrupt and priority handling

### Hardware Tests
1. Movement calibration verification
2. Expression action timing
3. Sound playback functionality

## Performance Requirements

- **Action parsing latency**: < 50ms
- **Movement start delay**: < 200ms
- **Expression action timing**: Exact as defined in action_helper.py
- **Queue processing rate**: 10Hz minimum
## Error Handling

1. **Invalid actions**: Log warning, skip action, continue sequence
2. **Hardware failures**: Fall back to simulation mode
3. **Queue overflow**: Drop lowest priority actions

## Future Enhancements

1. **Path planning**: Waypoint navigation system
2. **SLAM integration**: Mapping and localization
3. **Visual servoing**: Camera-based navigation
4. **Multi-robot coordination**: Swarm behaviors
5. **Learning**: Adaptive movement patterns

## Conclusion

The navigation node bridges AI intelligence with physical robot capabilities, using the proven v1.0 movement implementations while adding v3.0 message-based architecture. The system focuses on accurate movement execution and expressive robotic behaviors that enhance user interaction.