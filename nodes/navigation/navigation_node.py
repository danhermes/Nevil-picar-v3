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
from nevil_framework.busy_state import busy_state
from nevil_framework.microphone_mutex import microphone_mutex
# COMMENTED OUT: Using original SpeechAnimationManager instead
# from nevil_framework.speech_idle_animator import SpeechIdleAnimator
from robot_hat import reset_mcu

# Import Automatic module for autonomous behavior
try:
    from .automatic import Automatic
except ImportError:
    try:
        from automatic import Automatic
    except ImportError:
        import importlib.util
        automatic_path = os.path.join(os.path.dirname(__file__), 'automatic.py')
        spec = importlib.util.spec_from_file_location("automatic", automatic_path)
        automatic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(automatic_module)
        Automatic = automatic_module.Automatic

# Hardware interface - use local picarx.py
try:
   from .calibration import servos_reset
except ImportError:
    # For dynamic loading, import directly
    import importlib.util
    calibration_path = os.path.join(os.path.dirname(__file__), 'calibration.py')
    spec = importlib.util.spec_from_file_location("calibration", calibration_path)
    calibration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calibration_module)
    servos_reset = calibration_module.servos_reset

# Import v1.0 action functions using importlib directly (no sys.path pollution)
import importlib.util
nav_dir = os.path.dirname(__file__)
action_helper_path = os.path.join(nav_dir, 'action_helper.py')

try:
    spec = importlib.util.spec_from_file_location("action_helper", action_helper_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {action_helper_path}")

    action_helper_module = importlib.util.module_from_spec(spec)
    # Set __package__ so relative imports (.utils) work correctly
    action_helper_module.__package__ = 'nodes.navigation'
    spec.loader.exec_module(action_helper_module)
    actions_dict = action_helper_module.actions_dict
    print(f"[NAVIGATION] Imported actions_dict: {len(actions_dict)} actions")
except Exception as e:
    print(f"[NAVIGATION ERROR] Failed to import action_helper: {e}")
    import traceback
    traceback.print_exc()
    # Fallback if action_helper not available
    actions_dict = {}
    print(f"[NAVIGATION WARNING] Using empty actions_dict fallback")

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

        # Camera positioning (v1.0 pattern)
        self.DEFAULT_HEAD_TILT = 10  # Slightly higher for better field of view

        # Import v1.0 action functions
        self.action_functions = actions_dict
        print(f"[NAVIGATION DEBUG] self.action_functions set to: {len(self.action_functions)} actions")
        if self.action_functions:
            print(f"[NAVIGATION DEBUG] Available actions: {list(self.action_functions.keys())[:10]}")

        # Processing state
        self.actions_processed = 0
        self.last_action_time = 0

        # Automatic mode
        self.automatic = None
        self.auto_enabled = False
        self.auto_thread = None
        self.shutdown_event = threading.Event()

        # Autonomous mode GPT response handling
        self.auto_response_queue = queue.Queue(maxsize=1)
        self.auto_conversation_id = None
        self.auto_pending_response = {}  # Store text_response and robot_action until both received
        self.auto_response_lock = threading.Lock()

        # Speech idle animator - provides subtle movement while talking
        # COMMENTED OUT: Using original SpeechAnimationManager instead
        # self.idle_animator = SpeechIdleAnimator(get_car_callback=lambda: self.car)
        # self.idle_animator.set_animation_intensity("expressive")  # More animated while talking

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
        # Add reference to navigation node so actions can publish messages
        self.car.nav_node = self
        print(f"[NAVIGATION DEBUG] Picarx object created with nav_node reference")

        # Set default speed
        self.car.speed = self.default_speed
        print(f"[NAVIGATION DEBUG] Default speed set to {self.default_speed}")

        # Motion initialization - reset to known state
        # NOTE: reset_mcu() is already called inside Picarx.__init__()
        # Calling it again here can scramble GPIO/servo assignments!
        # print(f"[NAVIGATION DEBUG] Calling reset_mcu()...")
        # reset_mcu() # from robot-hat - REMOVED: Already called in Picarx.__init__
        # print(f"[NAVIGATION DEBUG] reset_mcu() complete")
        time.sleep(.2)
        servos_reset(self.car) #from calibration.py - pass shared instance
        print(f"[NAVIGATION DEBUG] servos_reset() complete")
        print(f"[NAVIGATION DEBUG] Calling car.reset()...")
        self.car.reset()  # Reset all servos to center
        print(f"[NAVIGATION DEBUG] car.reset() complete")
        time.sleep(0.5)   # Allow hardware to settle
        print(f"[NAVIGATION DEBUG] Hardware settle delay complete")

        # Set default positions (v1.0 pattern)
        #self.car.set_dir_servo_angle(0)                    # Wheels straight
        #self.car.set_cam_pan_angle(0)                      # Camera center
        self.car.set_cam_tilt_angle(self.DEFAULT_HEAD_TILT) # Head up for better view

        self.logger.info("PiCar-X hardware initialized and motion reset complete")

        # Start action processing thread
        self.action_thread = threading.Thread(
            target=self._action_processing_loop,
            daemon=True
        )
        self.action_thread.start()

        # Initialize Automatic module with a mock nevil object
        # The automatic module needs access to certain methods
        class MockNevil:
            def __init__(self, nav_node):
                self.nav = nav_node
                self.auto_enabled = False
                self.action_lock = threading.Lock()
                self.speech_lock = threading.Lock()
                self.actions_to_be_done = []
                self.action_status = None
                self.speech_loaded = False
                self.sound_effects_queue = []
                self.tts_file = None

            def handle_TTS_generation(self, message):
                """Queue TTS for speech node"""
                self.nav.logger.info(f"[AUTO] TTS: {message}")
                self.nav.publish("tts_request", {
                    "text": message,
                    "priority": 50
                })

            def call_GPT(self, prompt, use_image=False):
                """Call GPT for auto mode responses via AI cognition node"""
                try:
                    self.nav.logger.info(f"[AUTO GPT] Calling AI with prompt (vision={use_image}): {prompt[:100]}")

                    # Generate a unique conversation ID for this autonomous request
                    import uuid
                    conversation_id = f"auto_{uuid.uuid4().hex[:8]}"
                    self.nav.auto_conversation_id = conversation_id

                    # Clear any old response in queue
                    while not self.nav.auto_response_queue.empty():
                        try:
                            self.nav.auto_response_queue.get_nowait()
                        except queue.Empty:
                            break

                    # Request snapshot if vision is needed
                    if use_image:
                        self.nav.logger.info(f"[AUTO GPT] Requesting camera snapshot for vision")
                        snap_data = {
                            "requested_by": "autonomous_mode",
                            "timestamp": time.time()
                        }
                        self.nav.publish("snap_pic", snap_data)
                        # Brief delay to allow camera capture
                        time.sleep(0.3)

                    # Publish voice_command message to trigger AI cognition
                    voice_command_data = {
                        "text": prompt,
                        "confidence": 1.0,  # Autonomous mode has perfect confidence
                        "timestamp": time.time(),
                        "conversation_id": conversation_id
                    }

                    if not self.nav.publish("voice_command", voice_command_data):
                        self.nav.logger.error("[AUTO GPT] Failed to publish voice_command")
                        return [], ""

                    # Wait for response from AI cognition (via on_robot_action callback)
                    # Timeout after 10 seconds
                    try:
                        response = self.nav.auto_response_queue.get(timeout=10.0)
                        actions = response.get('actions', [])
                        answer = response.get('answer', '')
                        self.nav.logger.info(f"[AUTO GPT] Got response: actions={actions}, answer='{answer}'")
                        return actions, answer

                    except queue.Empty:
                        self.nav.logger.warning("[AUTO GPT] Timeout waiting for AI response")
                        return [], ""

                except Exception as e:
                    self.nav.logger.error(f"[AUTO GPT] Error calling GPT: {e}")
                    import traceback
                    self.nav.logger.error(f"[AUTO GPT] Traceback: {traceback.format_exc()}")
                    return [], ""

            def parse_action(self, action_str):
                """Parse action string"""
                parts = action_str.split()
                if parts:
                    return parts[0], parts[1:]
                return None, []

        self.mock_nevil = MockNevil(self)
        self.automatic = Automatic(self.mock_nevil)

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
        self.logger.info("🔄 [QUEUE] Action processing loop started")

        while not self.shutdown_event.is_set():
            try:
                self.logger.debug(f"🔄 [QUEUE] Checking queue (size: {self.action_queue.qsize()})")

                # Get action from queue with timeout
                try:
                    priority, timestamp, action_sequence = self.action_queue.get(timeout=1.0)
                    self.logger.info(f"📦 [QUEUE] Retrieved action sequence - Priority: {priority}, Timestamp: {timestamp}")
                    self.logger.debug(f"📦 [QUEUE] Action sequence: {action_sequence}")

                except queue.Empty:
                    # Log every 30 seconds in debug mode to show we're alive
                    if int(time.time()) % 30 == 0:
                        self.logger.debug(f"🔄 [QUEUE] Queue empty, waiting... (queue size: {self.action_queue.qsize()})")
                    continue

                # Process the action sequence
                self.logger.info(f"🚀 [QUEUE] Starting to process action sequence")
                self._process_action_sequence(action_sequence)
                self.logger.info(f"✅ [QUEUE] Completed processing action sequence")

                # Mark task as done
                self.action_queue.task_done()
                self.logger.debug(f"📝 [QUEUE] Marked queue task as done")

            except Exception as e:
                self.logger.error(f"❌ [QUEUE] Error in action processing loop: {e}")
                time.sleep(0.5)

        self.logger.info("🛑 [QUEUE] Action processing loop stopped")

    def _process_action_sequence(self, action_sequence: Dict[str, Any]):
        """Process a sequence of actions"""
        actions = action_sequence.get('actions', [])
        source_text = action_sequence.get('source_text', '')
        mood = action_sequence.get('mood', 'neutral')

        self.logger.info(f"📝 SOURCE: '{source_text}'")

        # Acquire busy state for entire action sequence - actions are interruptible
        self.logger.debug("Acquiring busy state for navigation...")
        if not busy_state.acquire("acting", interruptible=True):
            self.logger.error("Could not acquire busy state for navigation, aborting action sequence")
            return

        # Acquire microphone mutex - prevents speech recognition during servo noise
        microphone_mutex.acquire_noisy_activity("navigation")

        # Delay 0.5s before starting movement to better sync with speech
        time.sleep(0.5)

        try:
            self.logger.info(f"🎬 STARTING ACTION SEQUENCE: {len(actions)} actions from '{source_text[:40]}...' (mood: {mood})")

            # Publish navigation status - executing
            self.publish("navigation_status", {
                "status": "executing",
                "current_action": actions[0] if actions else "",
                "actions_remaining": len(actions),
                "timestamp": time.time()
            })

            for i, action_str in enumerate(actions, 1):
                # Check for shutdown or interrupt
                if self.shutdown_event.is_set():
                    self.logger.warning(f"❌ Action sequence stopped at {i}/{len(actions)}")
                    break

                # Check if TTS wants to interrupt
                if busy_state.should_interrupt():
                    self.logger.warning(f"🚨 Action sequence interrupted by TTS at {i}/{len(actions)}")
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

                # Pause between actions to allow servos to complete physical movement
                # v1.0 used 0.5s - servos need time to physically finish moving
                time.sleep(0.5)

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

        finally:
            # Always release busy state
            busy_state.release()
            self.logger.debug("Released busy state after navigation")

            # Release microphone mutex
            microphone_mutex.release_noisy_activity("navigation")

    def _parse_action(self, action_str: str) -> Optional[Dict[str, Any]]:
        """Parse an action string into function and parameters"""
        self.logger.info(f"🔍 [PARSE] Parsing action: '{action_str}'")
        self.logger.debug(f"🔍 [PARSE] Available action functions: {len(self.action_functions)} total")
        self.logger.debug(f"🔍 [PARSE] Action functions keys (first 10): {list(self.action_functions.keys())[:10]}")

        try:
            # First, check for speed modifier (e.g., "happy_spin:fast" or "ponder:slow")
            gesture_speed = 'med'  # default
            if ':' in action_str:
                action_str, speed_part = action_str.rsplit(':', 1)
                if speed_part.strip() in ['slow', 'med', 'fast']:
                    gesture_speed = speed_part.strip()
                    self.logger.debug(f"🔍 [PARSE] Detected speed modifier: {gesture_speed}")

            parts = action_str.split()
            self.logger.debug(f"🔍 [PARSE] Split into parts: {parts}")

            if not parts:
                self.logger.error(f"🔍 [PARSE] Empty action string after split")
                return None

            action_name = parts[0]
            self.logger.debug(f"🔍 [PARSE] Primary action name: '{action_name}'")

            # Handle parameterized movement actions
            if action_name in ['forward', 'backward']:
                self.logger.info(f"🔍 [PARSE] Processing parameterized movement: {action_name}")
                distance = int(parts[1]) if len(parts) > 1 else 10
                speed = int(parts[2]) if len(parts) > 2 else self.default_speed

                function = self.action_functions.get(action_name)
                self.logger.info(f"🔍 [PARSE] Movement function found: {function is not None}")
                self.logger.debug(f"🔍 [PARSE] Distance: {distance}cm, Speed: {speed}")

                result = {
                    'function': function,
                    'params': {'distance_cm': distance, 'speed': speed},
                    'name': f"{action_name} {distance}cm @ {speed}"
                }
                self.logger.info(f"✅ [PARSE] Parameterized action parsed: {result['name']}")
                return result

            # Handle parameterized sound actions
            elif action_name == 'play_sound' and len(parts) > 1:
                self.logger.info(f"🔍 [PARSE] Processing parameterized sound: {action_name}")
                sound_name = parts[1]
                volume = int(parts[2]) if len(parts) > 2 else 100

                function = self.action_functions.get(action_name)
                self.logger.info(f"🔍 [PARSE] Sound function found: {function is not None}")
                self.logger.debug(f"🔍 [PARSE] Sound: {sound_name}, Volume: {volume}")

                result = {
                    'function': function,
                    'params': {'sound_name': sound_name, 'volume': volume},
                    'name': f"{action_name} {sound_name} @ {volume}%"
                }
                self.logger.info(f"✅ [PARSE] Parameterized sound parsed: {result['name']}")
                return result

            # Handle simple actions
            elif action_name in self.action_functions:
                self.logger.info(f"🔍 [PARSE] Processing simple action: {action_name}")
                function = self.action_functions[action_name]
                result = {
                    'function': function,
                    'params': {'speed': gesture_speed},
                    'name': f"{action_name}:{gesture_speed}" if gesture_speed != 'med' else action_name
                }
                self.logger.info(f"✅ [PARSE] Simple action parsed: {result['name']}")
                return result

            # Handle compound action names
            else:
                self.logger.info(f"🔍 [PARSE] Trying compound action matching for: {action_name}")

                # Try joining parts for multi-word actions like "shake head"
                full_action = ' '.join(parts)
                self.logger.debug(f"🔍 [PARSE] Trying full action: '{full_action}'")

                if full_action in self.action_functions:
                    self.logger.info(f"🔍 [PARSE] Found full action match: '{full_action}'")
                    function = self.action_functions[full_action]
                    result = {
                        'function': function,
                        'params': {'speed': gesture_speed},
                        'name': f"{full_action}:{gesture_speed}" if gesture_speed != 'med' else full_action
                    }
                    self.logger.info(f"✅ [PARSE] Compound action parsed: {result['name']}")
                    return result

                # Try converting underscores to spaces for AI-generated action names
                underscore_to_space = action_str.replace('_', ' ')
                self.logger.debug(f"🔍 [PARSE] Trying underscore conversion: '{underscore_to_space}'")

                if underscore_to_space in self.action_functions:
                    self.logger.info(f"🔍 [PARSE] Found underscore match: '{underscore_to_space}'")
                    function = self.action_functions[underscore_to_space]
                    result = {
                        'function': function,
                        'params': {'speed': gesture_speed},
                        'name': f"{underscore_to_space}:{gesture_speed}" if gesture_speed != 'med' else underscore_to_space
                    }
                    self.logger.info(f"✅ [PARSE] Underscore action parsed: {result['name']}")
                    return result

            self.logger.warning(f"❌ [PARSE] Unknown action: '{action_str}' - not found in action_functions")
            self.logger.debug(f"❌ [PARSE] Available actions: {list(self.action_functions.keys())}")
            return None

        except Exception as e:
            self.logger.error(f"❌ [PARSE] Error parsing action '{action_str}': {e}")
            return None

    def _execute_action(self, action_data: Dict[str, Any]):
        """Execute a parsed action"""
        self.logger.info(f"⚡ [EXEC] Starting action execution")
        self.logger.debug(f"⚡ [EXEC] Full action data: {action_data}")

        if not action_data:
            self.logger.error(f"❌ [EXEC] No action data provided")
            return

        if not action_data.get('function'):
            self.logger.error(f"❌ [EXEC] No function in action data: {action_data}")
            return

        try:
            func = action_data['function']
            params = action_data['params']
            name = action_data['name']

            self.logger.info(f"⚡ [EXEC] Action: {name}")
            self.logger.debug(f"⚡ [EXEC] Function: {func}")
            self.logger.debug(f"⚡ [EXEC] Parameters: {params}")
            self.logger.debug(f"⚡ [EXEC] Car object: {self.car}")

            # Execute on real hardware
            self.logger.info(f"🚗 [HARDWARE] Calling action_helper function: {func.__name__ if hasattr(func, '__name__') else str(func)}")
            self.logger.debug(f"🚗 [HARDWARE] With car: {self.car} and params: {params}")

            start_time = time.time()

            if params:
                self.logger.debug(f"🚗 [HARDWARE] Calling with params: func(car, **{params})")
                # Check if function accepts speed parameter
                import inspect
                sig = inspect.signature(func)
                if 'speed' in params and 'speed' not in sig.parameters:
                    # Function doesn't accept speed, remove it from params
                    self.logger.debug(f"🚗 [HARDWARE] Function doesn't accept 'speed' parameter, removing it")
                    params = {k: v for k, v in params.items() if k != 'speed'}

                if params:
                    func(self.car, **params)
                else:
                    func(self.car)
            else:
                self.logger.debug(f"🚗 [HARDWARE] Calling without params: func(car)")
                func(self.car)

            execution_time = time.time() - start_time
            self.logger.info(f"✅ [EXEC] Action '{name}' completed successfully in {execution_time:.3f}s")

        except Exception as e:
            self.logger.error(f"❌ [EXEC] Action execution error for '{action_data.get('name', 'unknown')}': {e}")
            self.logger.error(f"❌ [EXEC] Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(f"❌ [EXEC] Full traceback: {traceback.format_exc()}")

    def on_text_response(self, message):
        """Handle text response messages from AI cognition (for autonomous mode)"""
        try:
            conversation_id = message.data.get('conversation_id', '')
            text = message.data.get('text', '')

            # Check if this is for autonomous mode
            if conversation_id and conversation_id == self.auto_conversation_id:
                self.logger.info(f"[AUTO GPT] Received text_response for autonomous mode: '{text}'")

                with self.auto_response_lock:
                    # Store the text response
                    if conversation_id not in self.auto_pending_response:
                        self.auto_pending_response[conversation_id] = {}
                    self.auto_pending_response[conversation_id]['answer'] = text

                    # Check if we have both text and actions
                    if 'actions' in self.auto_pending_response[conversation_id]:
                        # We have complete response, send it to queue
                        complete_response = self.auto_pending_response[conversation_id]
                        self.logger.info(f"[AUTO GPT] Complete response ready: {complete_response}")
                        self.auto_response_queue.put(complete_response)
                        # Clean up
                        del self.auto_pending_response[conversation_id]

        except Exception as e:
            self.logger.error(f"Error handling text response: {e}")

    def on_robot_action(self, message):
        """Handle robot action messages from AI cognition"""
        self.logger.info(f"📨 [MESSAGE] RECEIVED robot action message")

        # Check for auto mode triggers in source text
        source_text = message.data.get('source_text', '').lower()

        # DEBUG: Log what we're checking
        self.logger.info(f"🔍 [AUTO CHECK] Checking source_text for triggers: '{source_text}'")

        # Auto mode triggers
        auto_triggers = ['start auto', 'go play', 'seeya nevil', 'see ya nevil',
                        'auto mode', 'automatic mode', 'go have fun', 'go explore',
                        'entertain yourself', 'do your thing']
        stop_triggers = ['stop auto', 'stop playing', 'come back', 'stop automatic',
                        'manual mode', 'stop exploring']

        # Check for auto mode commands
        for trigger in auto_triggers:
            if trigger in source_text:
                self.logger.info(f"🤖 [AUTO] Auto mode triggered by: '{trigger}'")
                self.start_auto_mode()
                # Still process any immediate actions before going auto
                break

        for trigger in stop_triggers:
            if trigger in source_text:
                self.logger.info(f"🛑 [AUTO] Auto mode stopped by: '{trigger}'")
                self.stop_auto_mode()
                break
        self.logger.debug(f"📨 [MESSAGE] Full message object: {message}")
        self.logger.debug(f"📨 [MESSAGE] Message type: {type(message)}")
        self.logger.debug(f"📨 [MESSAGE] Message attributes: {dir(message)}")

        try:
            data = message.data
            self.logger.info(f"📨 [MESSAGE] Message data: {data}")
            self.logger.debug(f"📨 [MESSAGE] Data type: {type(data)}")

            actions = data.get('actions', [])
            priority = data.get('priority', 100)
            source_text = data.get('source_text', '')
            conversation_id = data.get('conversation_id', '')

            self.logger.info(f"📨 [MESSAGE] Extracted actions: {actions}")
            self.logger.info(f"📨 [MESSAGE] Priority: {priority}")
            self.logger.info(f"📨 [MESSAGE] Source text: '{source_text}'")

            # Check if this is for autonomous mode
            if conversation_id and conversation_id == self.auto_conversation_id:
                self.logger.info(f"[AUTO GPT] Received robot_action for autonomous mode")

                with self.auto_response_lock:
                    # Store the actions
                    if conversation_id not in self.auto_pending_response:
                        self.auto_pending_response[conversation_id] = {}
                    self.auto_pending_response[conversation_id]['actions'] = actions

                    # Check if we have both text and actions
                    if 'answer' in self.auto_pending_response[conversation_id]:
                        # We have complete response, send it to queue
                        complete_response = self.auto_pending_response[conversation_id]
                        self.logger.info(f"[AUTO GPT] Complete response ready: {complete_response}")
                        self.auto_response_queue.put(complete_response)
                        # Clean up
                        del self.auto_pending_response[conversation_id]
                    else:
                        # No text_response yet - wait briefly for it
                        # If it doesn't arrive, assume empty answer (silence)
                        import threading
                        def check_for_text_response():
                            time.sleep(0.5)  # Wait 500ms for text_response
                            with self.auto_response_lock:
                                if conversation_id in self.auto_pending_response and 'answer' not in self.auto_pending_response[conversation_id]:
                                    # Still no answer after waiting - assume silent response
                                    self.logger.info(f"[AUTO GPT] No text_response received - assuming silent response")
                                    self.auto_pending_response[conversation_id]['answer'] = ''
                                    complete_response = self.auto_pending_response[conversation_id]
                                    self.auto_response_queue.put(complete_response)
                                    del self.auto_pending_response[conversation_id]

                        threading.Thread(target=check_for_text_response, daemon=True).start()

                # For autonomous mode, don't queue the actions here - they'll be handled by automatic.py
                return

            if not actions:
                self.logger.warning(f"📨 [MESSAGE] No actions in robot_action message - data: {data}")
                return

            # Create action sequence
            action_sequence = {
                'actions': actions,
                'source_text': source_text,
                'mood': data.get('mood', 'neutral'),
                'timestamp': time.time(),
                'action_id': message.message_id if hasattr(message, 'message_id') else f"action_{int(time.time())}"
            }

            self.logger.info(f"📨 [MESSAGE] Created action sequence: {action_sequence}")

            # Add to priority queue
            self.logger.info(f"📨 [MESSAGE] Adding to queue with priority {priority}")
            self.action_queue.put((priority, time.time(), action_sequence))
            self.logger.info(f"📨 [MESSAGE] Successfully added to queue")

            self.logger.info(f"📥 RECEIVED ACTIONS: {len(actions)} actions queued from AI")
            self.logger.info(f"📝 SOURCE: '{source_text}'")
            self.logger.info(f"📋 ACTIONS: {actions}")
            self.logger.info(f"🎭 MOOD: {data.get('mood', 'neutral')}")
            self.logger.info(f"📊 QUEUE SIZE: {self.action_queue.qsize()}")

        except Exception as e:
            self.logger.error(f"❌ [MESSAGE] Error handling robot action: {e}")
            self.logger.error(f"❌ [MESSAGE] Exception type: {type(e).__name__}")
            import traceback
            self.logger.debug(f"❌ [MESSAGE] Full traceback: {traceback.format_exc()}")

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

    # COMMENTED OUT: Using original SpeechAnimationManager instead
    # def on_speaking_status(self, message):
    #     """
    #     Handle speaking status messages to trigger idle animations during speech.
    #
    #     When Nevil starts speaking, we trigger subtle movements (head, wheels) to make
    #     him appear more lifelike and animated. When speech ends, we stop the animations.
    #     """
    #     try:
    #         is_speaking = message.data.get('speaking', False)
    #         text = message.data.get('text', '')
    #
    #         self.logger.info(f"📨 Received speaking_status: speaking={is_speaking}, text='{text[:30]}'...")
    #         self.logger.info(f"🤖 Car available: {self.car is not None}")
    #         self.logger.info(f"🎬 Animator status: is_animating={self.idle_animator.is_animating}")
    #
    #         if is_speaking:
    #             self.logger.info(f"🎬 STARTING idle animations for speech: '{text[:50]}'...")
    #             try:
    #                 self.idle_animator.start_animation()
    #                 self.logger.info(f"✅ Idle animation started successfully")
    #             except Exception as start_err:
    #                 self.logger.error(f"❌ Failed to start idle animation: {start_err}", exc_info=True)
    #         else:
    #             self.logger.info(f"🛑 STOPPING idle animations (speech ended)")
    #             try:
    #                 self.idle_animator.stop_animation()
    #                 self.logger.info(f"✅ Idle animation stopped successfully")
    #             except Exception as stop_err:
    #                 self.logger.error(f"❌ Failed to stop idle animation: {stop_err}", exc_info=True)
    #
    #     except Exception as e:
    #         self.logger.error(f"❌ Error handling speaking status: {e}", exc_info=True)

    def get_navigation_stats(self):
        """Get navigation statistics"""
        stats = {
            "actions_processed": self.actions_processed,
            "last_action_time": self.last_action_time,
            "queue_size": self.action_queue.qsize(),
            "available_actions": len(self.action_functions),
            "action_functions_loaded": list(self.action_functions.keys()) if self.action_functions else [],
            "car_initialized": self.car is not None,
            "hardware_available": bool(self.car),
            "status": self.status.value if hasattr(self, 'status') else "unknown"
        }

        self.logger.info(f"📊 [STATS] Navigation statistics:")
        self.logger.info(f"📊 [STATS] Actions processed: {stats['actions_processed']}")
        self.logger.info(f"📊 [STATS] Queue size: {stats['queue_size']}")
        self.logger.info(f"📊 [STATS] Available actions: {stats['available_actions']}")
        self.logger.info(f"📊 [STATS] Car initialized: {stats['car_initialized']}")

        if self.action_functions:
            self.logger.info(f"📊 [STATS] Action functions: {list(self.action_functions.keys())}")
        else:
            self.logger.warning(f"📊 [STATS] No action functions loaded!")

        return stats

    # NOTE: start_auto_mode() and stop_auto_mode() are defined below at lines 977+
    # to avoid duplication and ensure proper error handling

    def run_auto(self):
        """Run autonomous behavior loop"""
        self.logger.info("[AUTO] Autonomous thread started")

        # Wait for any in-progress AI response to complete
        # (e.g., if user said "Can you go play?" - let AI respond to that first, THEN start auto mode)
        self.logger.info("[AUTO] Waiting for any in-progress AI response to complete...")
        max_wait = 15  # Maximum 15 seconds to wait
        waited = 0
        while waited < max_wait:
            # Check if AI is busy (this is a simple heuristic - could be improved)
            # For now, just wait 5 seconds which should be enough for most responses
            if waited >= 5:
                break
            time.sleep(1)
            waited += 1
            self.logger.debug(f"[AUTO] Waited {waited}s for AI response...")

        self.logger.info("[AUTO] Starting autonomous behavior cycles")

        while self.auto_enabled and not self.shutdown_event.is_set():
            try:
                # Update last interaction time when we get messages
                self.automatic.last_interaction_time = self.last_action_time

                # Run one autonomous behavior cycle
                self.logger.info(f"[AUTO] Running autonomous behavior cycle (mood: {self.automatic.current_mood_name})")

                self.automatic.run_idle_loop(1)

                # Process any actions queued by automatic
                with self.mock_nevil.action_lock:
                    if self.mock_nevil.actions_to_be_done:
                        actions = self.mock_nevil.actions_to_be_done
                        self.mock_nevil.actions_to_be_done = []

                        # Queue actions for execution
                        action_sequence = {
                            'actions': actions,
                            'source_text': f'Auto mode ({self.automatic.current_mood_name})',
                            'mood': self.automatic.current_mood_name,
                            'timestamp': time.time()
                        }
                        self.action_queue.put((50, time.time(), action_sequence))

                        # Wait for actions to complete before running next behavior
                        self.logger.info("[AUTO] Waiting for actions to complete...")
                        while not self.action_queue.empty() and self.auto_enabled:
                            time.sleep(0.5)
                        self.logger.info("[AUTO] Actions completed, ready for next cycle")

                # Mood-based listening window duration
                # Higher sociability = longer window (wants interaction)
                # Lower energy = longer window (patient, not rushing)
                # Higher energy = shorter window (impatient, wants to keep moving)
                mood = self.automatic.current_mood
                sociability = mood.get('sociability', 50)
                energy = mood.get('energy', 50)

                # Calculate listening window: 5-20 seconds (FULL 15s range)
                # Normalize actual mood values (60-95 energy, 10-90 soc) to 5-20s range
                # Use weighted formula that maps our actual mood ranges to desired output
                # Formula: ((sociability - 10) * 0.1875) + (((100-energy) - 5) * 0.1875) + 5
                # This maps: low end (soc:10, nrg:95) = 0 + 0 + 5 = 5s
                #            high end (soc:90, nrg:10) = 15 + 16.875 + 5 = ~37s → clamped to 20s
                # Actual examples:
                #   zippy (soc:60, nrg:95) = (50*0.1875) + (0*0.1875) + 5 = 9.375 + 0 + 5 = 14.4s
                #   Let's use simpler: map normalized (soc + (100-nrg)) to 5-20 range
                #   Range of (soc + inverted_nrg): zippy (60+5)=65, lonely (80+50)=130
                #   Map 65-130 to 5-20: duration = 5 + ((value - 65) / (130-65)) * 15
                combined = sociability + (100 - energy)
                # Normalize combined score (ranges from ~65 for zippy to ~140 for low-energy moods)
                # Map 60-150 to 5-20s
                listen_duration = 5.0 + ((combined - 60.0) / 90.0) * 15.0
                listen_duration = max(5.0, min(20.0, listen_duration))  # Clamp to 5-20 range

                self.logger.info(f"[AUTO] 👂 Listening window: {listen_duration:.1f}s (sociability:{sociability}, energy:{energy})")

                # Signal listening window with head gesture
                if self.auto_enabled and self.car:
                    # Tilt head way back and look right
                    #self.car.set_cam_tilt_angle(30)  # Tilt way back
                    #self.car.set_cam_pan_angle(30)   # Look right
                    time.sleep(0.3)  # Hold pose briefly

                    # Speech recognition window (mood-dependent)
                    time.sleep(listen_duration)

                    # Return to center position
                    #self.car.set_cam_pan_angle(0)    # Center
                    #self.car.set_cam_tilt_angle(10)  # Normal tilt
                else:
                    # Just the delay if no hardware
                    time.sleep(listen_duration)

            except Exception as e:
                self.logger.error(f"[AUTO] Error in auto loop: {e}")
                time.sleep(1.0)

        self.logger.info("[AUTO] Autonomous thread stopped")

    def on_auto_mode_command(self, message):
        """Handle direct auto mode commands from speech recognition"""
        try:
            self.logger.info(f"🎯 [AUTO COMMAND DEBUG] Message received! Type: {type(message)}")
            self.logger.info(f"🎯 [AUTO COMMAND DEBUG] Message data: {message.data}")

            command = message.data.get('command', '')
            trigger = message.data.get('trigger', '')
            original_text = message.data.get('original_text', '')

            self.logger.info(f"🎯 [AUTO COMMAND] Received: {command} (trigger: '{trigger}', text: '{original_text}')")

            if command == 'start':
                self.logger.info("🚀 [AUTO COMMAND] Calling start_auto_mode()")
                # TTS announcement is now in start_auto_mode() itself
                self.start_auto_mode()
            elif command == 'stop':
                self.logger.info("🛑 [AUTO COMMAND] Calling stop_auto_mode()")
                self.stop_auto_mode()
            else:
                self.logger.warning(f"Unknown auto mode command: {command}")

        except Exception as e:
            self.logger.error(f"Error handling auto mode command: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def on_mood_command(self, message):
        """Handle mood change commands"""
        try:
            # Extract mood from message
            text = message.data.get('text', '').lower()

            # Check for mood commands
            moods = ['playful', 'brooding', 'curious', 'melancholic',
                    'zippy', 'lonely', 'mischievous', 'sleepy']

            for mood in moods:
                if mood in text:
                    if self.automatic and self.automatic.set_mood(mood):
                        self.logger.info(f"[AUTO] Mood changed to: {mood}")
                        self.publish("tts_request", {
                            "text": f"Feeling {mood} now!",
                            "priority": 10
                        })
                    break

        except Exception as e:
            self.logger.error(f"Error handling mood command: {e}")

    def start_auto_mode(self):
        """Start automatic mode"""
        try:
            # Check if already running AND thread is alive
            if self.auto_enabled and hasattr(self, 'auto_thread') and self.auto_thread.is_alive():
                self.logger.info("[AUTO] Already in automatic mode (thread alive)")
                return

            # If flag was set but thread died, log it
            if self.auto_enabled:
                self.logger.warning("[AUTO] Flag was set but thread died - restarting")

            # Console announcement
            print("\n" + "="*70)
            print("🤖 [AUTOMATIC MODE] ACTIVATING...")
            print(f"🎭 Current Mood: {self.automatic.current_mood_name.upper()}")
            print("📝 Commands:")
            print("  • Say 'Stop auto' or 'Come back' to exit")
            print("  • Say 'Set mood [playful/curious/sleepy/etc]' to change personality")
            print("="*70 + "\n")

            self.logger.info("🚀 [AUTO] Starting automatic mode...")
            self.auto_enabled = True
            self.mock_nevil.auto_enabled = True

            # TTS announcement FIRST - "Okay, I'll go play now!"
            # Do this BEFORE starting the thread so user knows immediately
            self.publish("tts_request", {
                "text": "Okay, I'll go play now!",
                "priority": 1  # HIGHEST PRIORITY
            })
            self.logger.info("🔊 [AUTO] Announcing activation...")

            # Brief delay to let TTS start
            time.sleep(0.5)

            # Start autonomous thread
            self.auto_thread = threading.Thread(target=self.run_auto, daemon=True)
            self.auto_thread.start()

            # Publish status update
            self.publish("auto_mode_status", {
                "active": True,
                "mood": self.automatic.current_mood_name,
                "behavior": "starting",
                "timestamp": time.time()
            })

            self.logger.info("✅ [AUTO] Automatic mode started successfully")

        except Exception as e:
            self.logger.error(f"[AUTO] Error starting automatic mode: {e}")
            import traceback
            self.logger.error(f"[AUTO] Traceback: {traceback.format_exc()}")

    def stop_auto_mode(self):
        """Stop automatic mode"""
        try:
            if not self.auto_enabled:
                self.logger.info("[AUTO] Automatic mode not running")
                return

            # Console announcement
            print("\n" + "="*60)
            print("🛑 [AUTOMATIC MODE] DEACTIVATING...")
            print("Returning to manual control")
            print("="*60 + "\n")

            self.logger.info("🛑 [AUTO] Stopping automatic mode...")

            # TTS announcement FIRST - "I'm back!"
            self.publish("tts_request", {
                "text": "I'm back!",
                "priority": 1  # HIGHEST PRIORITY
            })
            self.logger.info("🔊 [AUTO] Announcing deactivation...")

            self.auto_enabled = False
            self.mock_nevil.auto_enabled = False

            # Wait for thread to finish
            if self.auto_thread and self.auto_thread.is_alive():
                self.auto_thread.join(timeout=3.0)

            # Publish status update
            self.publish("auto_mode_status", {
                "active": False,
                "mood": self.automatic.current_mood_name,
                "behavior": "stopped",
                "timestamp": time.time()
            })

            self.logger.info("✅ [AUTO] Automatic mode stopped successfully")

        except Exception as e:
            self.logger.error(f"[AUTO] Error stopping automatic mode: {e}")

    def cleanup(self):
        """Cleanup navigation resources"""
        self.logger.info("Cleaning up Navigation Node...")

        # Signal shutdown to all threads
        self.shutdown_event.set()

        # Stop auto mode if running
        if self.auto_enabled:
            self.stop_auto_mode()

        # Stop action processing
        if hasattr(self, 'action_thread') and self.action_thread.is_alive():
            self.action_thread.join(timeout=2.0)

        # Stop idle animator
        # COMMENTED OUT: Using original SpeechAnimationManager instead
        # if hasattr(self, 'idle_animator'):
        #     try:
        #         self.idle_animator.cleanup()
        #         self.logger.info("Idle animator stopped")
        #     except Exception as e:
        #         self.logger.warning(f"Error stopping idle animator: {e}")

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