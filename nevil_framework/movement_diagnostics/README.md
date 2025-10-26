# Movement Diagnostics

Simple diagnostic tools for testing PiCar-X movements.

## Head Movement Test

Tests pan/tilt servo actions from action_helper (10 basic gestures).

### Usage

```bash
cd /home/dan/Nevil-picar-v3
python3 nevil_framework/movement_diagnostics/head_movement_test.py
```

### What it does

Tests the following head movement actions, each performed 3 times:
1. shake_head - Pan servo movements
2. nod - Tilt servo movements
3. wave_hands - Steering and tilt servos
4. resist - Steering and pan servos
5. act_cute - Steering servo
6. rub_hands - Steering servo
7. think - Pan, tilt, and steering servos
8. keep_think - Pan, tilt, and steering servos
9. celebrate - Pan, tilt, and steering servos
10. depressed - Tilt servo movements

Each action is:
- Announced via quick TTS (espeak)
- Displayed on screen
- The car resets to neutral
- Runs 3 times
- Moves to the next action

---

## Extended Gestures Test

Tests all 106 extended gesture actions from extended_gestures.py.

### Usage

```bash
cd /home/dan/Nevil-picar-v3
python3 nevil_framework/movement_diagnostics/extended_gestures_test.py
```

### What it does

Tests all 106 extended gestures organized by category, each performed 2 times:

**Observation (15)**: look_left_then_right, look_up_then_down, inspect_floor, curious_peek, alert_scan, etc.

**Movement (16)**: circle_dance, happy_spin, zigzag, moonwalk, ballet_spin, figure_eight, etc.

**Reactions (13)**: recoil_surprise, confused_tilt, playful_bounce, show_surprise, show_joy, etc.

**Social (14)**: bow_respectfully, greet_wave, hello_friend, beckon_forward, etc.

**Celebration (7)**: spin_celebrate, jump_excited, cheer_wave, victory_pose, etc.

**Emotional (15)**: ponder, dreamy_stare, show_confidence, show_love, idle_breath, etc.

**Functional (12)**: sleep_mode, yawn, stretch, listen, guard_pose, ready_pose, etc.

**Signaling (10)**: acknowledge_signal, error_shrug, affirm_pose, signal_complete, etc.

**Advanced (4)**: approach_slowly, back_off_slowly, quick_look_left, quick_look_right

Each gesture is:
- Announced via quick TTS (espeak)
- Displayed on screen with progress counter
- The car resets to neutral
- Runs 2 times (optimized from 3x for faster testing)
- Moves to the next gesture

**Duration**: ~12-15 minutes for complete test (106 gestures × 2 iterations)

**Note**: Press Ctrl+C to interrupt if needed

---

## All Extended Gestures Diagnostic

Comprehensive test of all 106 extended gestures with enhanced formatting and category organization.

### Usage

```bash
cd /home/dan/Nevil-picar-v3
python3 nevil_framework/movement_diagnostics/all_extended_gestures_diagnostic.py
```

### What it does

Tests all 106 extended gestures with enhanced output formatting, each performed 2 times:

**Features:**
- Organized by 9 categories with section headers
- Clear progress counter `[X/106]`
- Synthesized voice announcements (espeak)
- Per-iteration status (✓ or ✗)
- Error handling with detailed messages
- Keyboard interrupt support (Ctrl+C)
- Auto-reset between gestures

**Categories tested:**
1. **OBSERVATION (15)**: Environmental scanning and inspection
2. **MOVEMENT (16)**: Locomotion and dynamic actions
3. **REACTION (13)**: Emotional and responsive gestures
4. **SOCIAL (14)**: Interpersonal communication gestures
5. **CELEBRATION (7)**: Victory and excitement expressions
6. **EMOTIONAL (15)**: Mood and feeling displays
7. **FUNCTIONAL (12)**: Utility and state gestures
8. **SIGNALING (10)**: Communication and status indicators
9. **ADVANCED (4)**: Complex navigation movements

**Duration**: ~12-15 minutes for complete test

**Output**: Clean, organized display with category sections and real-time status

**Safety**: Automatically resets to neutral on completion or interruption
