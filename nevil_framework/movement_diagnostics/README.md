# Movement Diagnostics

Simple diagnostic tools for testing PiCar-X movements.

## Head Movement Test

Tests pan/tilt servo actions from action_helper.

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
