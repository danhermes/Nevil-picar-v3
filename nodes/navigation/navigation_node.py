"""
Navigation Node for Nevil v3.0

Executes movement commands and expressive actions from AI responses.
Uses proven v1.0 action_helper for all movement implementations.
"""

import time
import threading
import queue
import json
import os
import sys
from typing import Dict, Any, List, Optional
from nevil_framework.base_node import NevilNode
from robot_hat import reset_mcu
# Hardware interface - use local picarx.py
# try:
#     from .calibration import servos_reset
# except ImportError:
#     # For dynamic loading, import directly
#     import importlib.util
#     calibration_path = os.path.join(os.path.dirname(__file__), 'calibration.py')
#     spec = importlib.util.spec_from_file_location("calibration", calibration_path)
#     calibration_module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(calibration_module)
#     Picarx = calibration_module.servos_reset

# Import v1.0 action functions
try:
    from .action_helper import actions_dict
    print(f"[NAVIGATION DEBUG] Imported actions_dict with relative import: {len(actions_dict)} actions")
except ImportError as e1:
    print(f"[NAVIGATION DEBUG] Relative import failed: {e1}")
    try:
        from action_helper import actions_dict
        print(f"[NAVIGATION DEBUG] Imported actions_dict with direct import: {len(actions_dict)} actions")
    except ImportError as e2:
        print(f"[NAVIGATION DEBUG] Direct import failed: {e2}")
        # Dynamic import using absolute path
        try:
            import importlib.util
            import sys

            # First add navigation directory to path so utils can be found
            nav_dir = os.path.dirname(__file__)
            if nav_dir not in sys.path:
                sys.path.insert(0, nav_dir)

            action_helper_path = os.path.join(nav_dir, 'action_helper.py')
            print(f"[NAVIGATION DEBUG] Trying dynamic import from: {action_helper_path}")
            spec = importlib.util.spec_from_file_location("action_helper", action_helper_path)
            action_helper_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(action_helper_module)
            actions_dict = action_helper_module.actions_dict
            print(f"[NAVIGATION DEBUG] Dynamic import SUCCESS: {len(actions_dict)} actions")
        except Exception as e3:
            print(f"[NAVIGATION DEBUG] Dynamic import failed: {e3}")
            # Fallback if action_helper not available
            actions_dict = {}
            print(f"[NAVIGATION DEBUG] Using empty actions_dict fallback")

# Hardware interface - use local picarx.py
try:
    from .picarx import Picarx
except ImportError:
    # For dynamic loading, import directly
    import importlib.util
    picarx_path = os.path.join(os.path.dirname(__file__), 'picarx.py')
    spec = importlib.util.spec_from_file_location("picarx", picarx_path)
    picarx_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(picarx_module)
    Picarx = picarx_module.Picarx


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

        # Action processing
        self.action_queue = queue.PriorityQueue(maxsize=50)
        self.current_action = None
        self.action_lock = threading.Lock()

        # Movement configuration
        self.default_speed = 30

        # Import v1.0 action functions
        self.action_functions = actions_dict
        print(f"[NAVIGATION DEBUG] self.action_functions set to: {len(self.action_functions)} actions")
        if self.action_functions:
            print(f"[NAVIGATION DEBUG] Available actions: {list(self.action_functions.keys())[:10]}")

        # Processing state
        self.actions_processed = 0
        self.last_action_time = 0

    def initialize(self):
        """Initialize navigation and hardware"""
        print(f"[NAVIGATION DEBUG] initialize() called - logger available: {hasattr(self, 'logger')}")
        self.logger.info("Initializing Navigation Node...")
        print(f"[NAVIGATION DEBUG] After logger.info call")


        # Initialize PiCar-X hardware - REQUIRED
        if not Picarx:
            raise RuntimeError("PiCar-X hardware not available - navigation requires real hardware")

        print(f"[NAVIGATION DEBUG] Creating Picarx object...")
        self.car = Picarx()
        print(f"[NAVIGATION DEBUG] Picarx object created")

        # Set default speed
        self.car.speed = self.default_speed
        print(f"[NAVIGATION DEBUG] Default speed set to {self.default_speed}")

        # Motion initialization - reset to known state
        #servos_reset() #from calibration.py - NOT DEFINED YET
        print(f"[NAVIGATION DEBUG] Calling reset_mcu()...")
        reset_mcu() # from robot-hat
        print(f"[NAVIGATION DEBUG] reset_mcu() complete")
        time.sleep(.2)
        print(f"[NAVIGATION DEBUG] Calling car.reset()...")
        self.car.reset()  # Reset all servos to center
        print(f"[NAVIGATION DEBUG] car.reset() complete")
        time.sleep(0.5)   # Allow hardware to settle
        print(f"[NAVIGATION DEBUG] Hardware settle delay complete")

        # Set default positions (v1.0 pattern)
        self.car.set_dir_servo_angle(0)    # Wheels straight
        self.car.set_cam_pan_angle(0)      # Camera center
        self.car.set_cam_tilt_angle(20)    # Head up (v1.0 DEFAULT_HEAD_TILT)

        self.logger.info("PiCar-X hardware initialized and motion reset complete")

        # Start action processing thread
        self.action_thread = threading.Thread(
            target=self._action_processing_loop,
            daemon=True
        )
        self.action_thread.start()

        self.logger.info("Navigation Node initialization complete")

    def main_loop(self):
        """Main navigation processing loop"""
        try:
            # Just keep the node alive - actual work done in background thread
            time.sleep(1.0)

        except Exception as e:
            self.logger.error(f"Error in navigation main loop: {e}")
            time.sleep(5.0)

    def _action_processing_loop(self):
        """Background action processing loop"""
        while not self.shutdown_event.is_set():
            try:
                # Get action from queue with timeout
                try:
                    priority, timestamp, action_sequence = self.action_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Process the action sequence
                self._process_action_sequence(action_sequence)

                # Mark task as done
                self.action_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error in action processing loop: {e}")
                time.sleep(0.5)

    def _process_action_sequence(self, action_sequence: Dict[str, Any]):
        """Process a sequence of actions"""
        try:
            actions = action_sequence.get('actions', [])
            source_text = action_sequence.get('source_text', '')
            mood = action_sequence.get('mood', 'neutral')

            self.logger.info(f"🎬 STARTING ACTION SEQUENCE: {len(actions)} actions from '{source_text[:40]}...' (mood: {mood})")
            self.logger.info(f"🎯 ACTION LIST: {actions}")

            # Publish navigation status - executing
            self.publish("navigation_status", {
                "status": "executing",
                "current_action": actions[0] if actions else "",
                "actions_remaining": len(actions),
                "timestamp": time.time()
            })

            for i, action_str in enumerate(actions, 1):
                if self.shutdown_event.is_set():
                    self.logger.warning(f"❌ Action sequence stopped at {i}/{len(actions)}")
                    break

                self.logger.info(f"🎬 [{i}/{len(actions)}] Executing: '{action_str}'")

                # Parse and execute action
                action_data = self._parse_action(action_str)
                if action_data:
                    start_time = time.time()
                    self._execute_action(action_data)
                    execution_time = time.time() - start_time
                    self.logger.info(f"✅ [{i}/{len(actions)}] Completed '{action_str}' in {execution_time:.2f}s")
                else:
                    self.logger.error(f"❌ [{i}/{len(actions)}] Failed to parse action: '{action_str}'")

                # Brief pause between actions
                time.sleep(0.1)

            self.logger.info(f"🏁 ACTION SEQUENCE COMPLETE: {len(actions)} actions finished")

            # Publish navigation status - completed
            self.publish("navigation_status", {
                "status": "completed",
                "current_action": "",
                "actions_remaining": 0,
                "timestamp": time.time()
            })

            self.actions_processed += 1
            self.last_action_time = time.time()

        except Exception as e:
            self.logger.error(f"Error processing action sequence: {e}")

    def _parse_action(self, action_str: str) -> Optional[Dict[str, Any]]:
        """Parse an action string into function and parameters"""
        try:
            parts = action_str.split()
            action_name = parts[0]

            # Handle parameterized movement actions
            if action_name in ['forward', 'backward']:
                distance = int(parts[1]) if len(parts) > 1 else 10
                speed = int(parts[2]) if len(parts) > 2 else self.default_speed

                return {
                    'function': self.action_functions.get(action_name),
                    'params': {'distance_cm': distance, 'speed': speed},
                    'name': f"{action_name} {distance}cm @ {speed}"
                }

            # Handle simple actions
            elif action_name in self.action_functions:
                return {
                    'function': self.action_functions[action_name],
                    'params': {},
                    'name': action_name
                }

            # Handle compound action names
            else:
                # Try joining parts for multi-word actions like "shake head"
                full_action = ' '.join(parts)
                if full_action in self.action_functions:
                    return {
                        'function': self.action_functions[full_action],
                        'params': {},
                        'name': full_action
                    }

                # Try converting underscores to spaces for AI-generated action names
                underscore_to_space = action_str.replace('_', ' ')
                if underscore_to_space in self.action_functions:
                    return {
                        'function': self.action_functions[underscore_to_space],
                        'params': {},
                        'name': underscore_to_space
                    }

            self.logger.warning(f"Unknown action: {action_str}")
            return None

        except Exception as e:
            self.logger.error(f"Error parsing action '{action_str}': {e}")
            return None

    def _execute_action(self, action_data: Dict[str, Any]):
        """Execute a parsed action"""
        self.logger.info(f"[NAVIGATION DEBUG] Executing action: {action_data}")
        if not action_data or not action_data['function']:
            return

        try:
            func = action_data['function']
            params = action_data['params']
            name = action_data['name']

            # Execute on real hardware
            self.logger.info(f"🚗 [HARDWARE] func: {func} {name} - params: {params}")
            if params:
                func(self.car, **params)
            else:
                func(self.car)

        except Exception as e:
            self.logger.error(f"Action execution error: {e}")

    def on_robot_action(self, message):
        """Handle robot action messages from AI cognition"""
        self.logger.info(f"Received robot action message: {message}")
        try:
            data = message.data
            actions = data.get('actions', [])
            priority = data.get('priority', 100)
            source_text = data.get('source_text', '')

            if not actions:
                self.logger.debug("No actions in robot_action message")
                return

            # Create action sequence
            action_sequence = {
                'actions': actions,
                'source_text': source_text,
                'mood': data.get('mood', 'neutral'),
                'timestamp': time.time(),
                'action_id': message.message_id if hasattr(message, 'message_id') else f"action_{int(time.time())}"
            }

            # Add to priority queue
            self.action_queue.put((priority, time.time(), action_sequence))

            self.logger.info(f"📥 RECEIVED ACTIONS: {len(actions)} actions queued from AI")
            self.logger.info(f"📝 SOURCE: '{source_text}'")
            self.logger.info(f"📋 ACTIONS: {actions}")
            self.logger.info(f"🎭 MOOD: {data.get('mood', 'neutral')}")
            self.logger.info(f"📊 QUEUE SIZE: {self.action_queue.qsize()}")

        except Exception as e:
            self.logger.error(f"Error handling robot action: {e}")

    def on_mood_change(self, message):
        """Handle mood change messages from AI cognition"""
        try:
            mood = message.data.get('mood', 'neutral')
            source = message.data.get('source', 'unknown')

            self.logger.info(f"Mood changed to: {mood} (from {source})")

            # TODO: Implement mood-influenced behavior
            # - Adjust movement speed based on mood
            # - Modify action timing/intensity
            # - Select different expression variants

        except Exception as e:
            self.logger.error(f"Error handling mood change: {e}")

    def get_navigation_stats(self):
        """Get navigation statistics"""
        return {
            "actions_processed": self.actions_processed,
            "last_action_time": self.last_action_time,
            "queue_size": self.action_queue.qsize(),
            "available_actions": len(self.action_functions)
        }

    def cleanup(self):
        """Cleanup navigation resources"""
        self.logger.info("Cleaning up Navigation Node...")

        # Stop action processing
        if hasattr(self, 'action_thread') and self.action_thread.is_alive():
            self.action_thread.join(timeout=2.0)

        # Reset hardware
        if self.car:
            try:
                self.car.stop()
                self.car.set_dir_servo_angle(0)
                self.car.set_cam_pan_angle(0)
                self.car.set_cam_tilt_angle(0)
                self.logger.info("Hardware reset complete")
            except Exception as e:
                self.logger.warning(f"Error resetting hardware: {e}")

        self.logger.info(f"Navigation stopped after {self.actions_processed} action sequences")