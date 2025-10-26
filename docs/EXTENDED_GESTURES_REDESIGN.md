# Extended Gestures Redesign - Adding Real Variety

## Problem
Current extended gestures are virtually identical - they all do tiny wheel spins (3-10 speed) with simultaneous head/steering wiggles. No real character or distinction.

## Design Principles for Variety

### 1. **STATIC Gestures** (No wheel movement - body language only)
- Head movements only
- Steering only (front wheels turning)
- Combined servo poses
- Pure expression through positioning

Examples:
- `look_up` - Just tilt camera up, no wheels
- `ponder` - Head tilted, steering angled, completely still
- `guard_pose` - Assertive pose, no movement
- `dreamy_stare` - Head tilted up-right, soft angle
- `question_pose` - Head tilted, one wheel turn
- `bashful_hide` - Turn away, look down, still

### 2. **HEAD-FOCUSED Gestures** (Head movement is primary)
- Scanning patterns
- Nodding/shaking
- Looking around
- Expressive head positions

Examples:
- `look_left_then_right` - Smooth pan sweep, no wheels
- `head_spin_survey` - 360° pan rotation, slow
- `confused_tilt` - Head tilt side to side, minimal wheels
- `alert_scan` - Quick pan left-right-left, no wheels
- `investigate_noise` - Head turns to listen, body still

### 3. **DANCE Gestures** (Rhythmic, musical, choreographed)
- Synced movements
- Repeated patterns
- Rhythmic timing
- Musical quality

Examples:
- `ballet_spin` - Smooth 360° turn, graceful
- `moonwalk` - Backwards with steering oscillation
- `figure_eight` - Continuous flowing path
- `dance_happy` - Bounce pattern with head bobs
- `wiggle_and_wait` - Side-to-side weight shift rhythm

### 4. **LOCOMOTION Gestures** (Real movement focused)
- Forward/backward motion
- Turning and spinning
- Approaching/retreating
- Spatial navigation

Examples:
- `charge_forward` - Fast forward burst (20-30 speed)
- `retreat_fast` - Quick backward (20-30 speed)
- `zigzag` - Alternating turns while moving
- `circle_dance` - Complete circle with steering
- `approach_slowly` - Gentle forward advance (5-10 speed)
- `patrol_mode` - Forward, turn, forward pattern

### 5. **BOUNCE/PULSE Gestures** (Vertical energy)
- Quick forward-back pulses
- Weight shifting
- Springy movements
- Energy bursts

Examples:
- `playful_bounce` - Quick fwd-back-fwd-back pulses
- `jump_excited` - Series of forward pulses
- `eager_start` - Anticipatory rocking motion
- `twitchy_nervous` - Jittery micro-movements

### 6. **SLOW/GRADUAL Gestures** (Patient, deliberate)
- Slow positioning
- Gradual turns
- Gentle approaches
- Contemplative movements

Examples:
- `dreamy_stare` - Slow head drift upward
- `think_long` - Gradual head tilt, pause
- `sigh` - Slow slump forward then back
- `stretch` - Slow extension movements
- `yawn` - Slow camera tilt with pause

### 7. **ARTICULATED Gestures** (Complex sequencing)
- Multi-part choreography
- Storytelling through movement
- Pose sequences
- Expressive combinations

Examples:
- `bow_respectfully` - Look down, forward tilt, back up
- `peekaboo` - Hide (turn away), quick peek back
- `flirt` - Approach, angle away coy, peek back
- `backflip_attempt` - Rock back, forward lurch, reset
- `intro_pose` - Sequence: center, slight bow, look up

## Gesture Categories with Variety Guidelines

### OBSERVATION (15) - Mostly STATIC + HEAD-FOCUSED
- ✓ No wheel movement for most
- ✓ Camera/head is primary tool
- ✓ Subtle steering angles okay
- ✗ No tiny motor pulses

### MOVEMENT (16) - LOCOMOTION + DANCE
- ✓ Real wheel speeds (15-30)
- ✓ Actual distance covered
- ✓ Flowing choreography
- ✗ No static poses here

### REACTIONS (13) - BOUNCE + QUICK movements
- ✓ Sudden movements
- ✓ Expressive jerks
- ✓ Quick recoils
- ✓ Energy bursts

### SOCIAL (14) - ARTICULATED + STATIC
- ✓ Pose sequences
- ✓ Communicative gestures
- ✓ Head + steering combinations
- ✗ Minimal wheel spinning

### CELEBRATION (7) - DANCE + BOUNCE
- ✓ Energetic movements
- ✓ Spinning and jumping
- ✓ Rhythmic patterns
- ✓ High energy

### EMOTIONAL (15) - STATIC + SLOW
- ✓ Expressive poses
- ✓ Gradual movements
- ✓ Contemplative stillness
- ✗ No hyperactive movements

### FUNCTIONAL (12) - STATIC + POSE
- ✓ Clear readable positions
- ✓ Minimal movement
- ✓ Purposeful placement
- ✗ No dancing around

### SIGNALING (10) - STATIC + CLEAR
- ✓ Distinct poses
- ✓ Unambiguous positions
- ✓ Clear communication
- ✗ No wiggling

### ADVANCED (4) - LOCOMOTION + PRECISION
- ✓ Controlled movement
- ✓ Spatial awareness
- ✓ Smooth execution
- ✓ Real distance covered

## Speed Ranges

### Motor Speeds:
- **Micro movements (deprecated)**: 3-8 - TOO SUBTLE, REMOVE THESE
- **Slow deliberate**: 10-15 - For gentle approaches, creeping
- **Normal movement**: 15-25 - Standard locomotion
- **Energetic**: 25-35 - Excited, urgent movements
- **Burst**: 35-50 - Maximum speed for short moments

### Sleep/Pause Timing:
- **Micro pauses**: 0.1-0.2s - Between rapid movements
- **Beat pauses**: 0.3-0.5s - Rhythmic timing
- **Contemplative**: 0.8-1.5s - Thoughtful pauses
- **Long holds**: 2.0-3.0s - Dramatic stillness

## Examples of Good Variety

### GOOD - Static Observation:
```python
def look_up(car, speed='med'):
    """Pure camera movement, no wheels"""
    car.set_cam_tilt_angle(35, smooth=True)
    _sleep(0.8, speed)
    # Leave it there - no reset, no wheels
```

### GOOD - Real Movement:
```python
def charge_forward(car, speed='med'):
    """Actual forward motion with energy"""
    car.set_motor_speed(1, 30)
    car.set_motor_speed(2, 30)
    _sleep(0.4, speed)
    car.stop()
```

### GOOD - Dance Choreography:
```python
def ballet_spin(car, speed='med'):
    """Graceful 360° turn"""
    car.set_motor_speed(1, 20)
    car.set_motor_speed(2, -20)  # Differential for spin
    _sleep(0.8, speed)  # Full rotation
    car.stop()
```

### GOOD - Articulated Sequence:
```python
def bow_respectfully(car, speed='med'):
    """Multi-part bow gesture"""
    # 1. Look forward
    car.set_cam_pan_angle(0)
    _sleep(0.3, speed)
    # 2. Tilt down (bow)
    car.set_cam_tilt_angle(-30)
    _sleep(0.6, speed)
    # 3. Hold
    _sleep(0.8, speed)
    # 4. Rise back up
    car.set_cam_tilt_angle(0)
    _sleep(0.4, speed)
```

### BAD - Everything at once (current problem):
```python
def generic_wiggle(car, speed='med'):
    """AVOID THIS PATTERN"""
    car.set_cam_pan_angle(-15)
    car.set_cam_tilt_angle(10)
    car.set_dir_servo_angle(-10)
    car.set_motor_speed(1, 5)  # Useless tiny movement
    car.set_motor_speed(2, 5)
    _sleep(0.2)
    # ...repeat with different angles
```

## Implementation Priority

1. **First**: Fix gestures that should be STATIC (observation, emotional, signaling)
2. **Second**: Add real LOCOMOTION to movement gestures (use 20-35 speed)
3. **Third**: Create DANCE patterns with rhythm and flow
4. **Fourth**: Build ARTICULATED sequences with storytelling
5. **Fifth**: Add BOUNCE/PULSE patterns with energy

## Testing Strategy

Run diagnostic and watch for:
- ❌ All gestures look the same
- ❌ Nothing actually moves anywhere
- ❌ Can't tell gestures apart
- ✓ Clear visual distinction between gestures
- ✓ Some gestures are completely still
- ✓ Some gestures move significantly
- ✓ Variety in rhythm, speed, and character

## Next Steps

1. Categorize current 106 gestures into the variety types
2. Redesign each gesture to match its type
3. Remove all "wiggle while tiny motor spin" patterns
4. Add true choreography and expression
5. Test and verify distinctiveness
