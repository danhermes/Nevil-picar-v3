# Extended Gestures Movement Redesign Plan
## All 106 Gestures - Keep Names, Change Movements

### OBSERVATION (15) - Should be STATIC or HEAD-ONLY
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 1 | look_left_then_right | Wiggle+tiny wheels | **HEAD ONLY** - Smooth pan sweep -35° to +35° |
| 2 | look_up_then_down | Wiggle+tiny wheels | **HEAD ONLY** - Tilt +30° to -30° |
| 3 | look_up | Wiggle+tiny wheels | **STATIC** - Just tilt camera up 35°, hold |
| 4 | inspect_floor | Wiggle+tiny wheels | **STATIC** - Tilt down -30°, slight forward 10cm |
| 5 | look_around_nervously | Wiggle+tiny wheels | **HEAD ONLY** - Quick pan snaps left-right-left |
| 6 | curious_peek | Wiggle+tiny wheels | **STATIC+HEAD** - Lean forward 10cm, tilt head 20° |
| 7 | reverse_peek | Wiggle+tiny wheels | **STATIC+HEAD** - Back 10cm, tilt head sideways |
| 8 | head_spin_survey | Wiggle+tiny wheels | **HEAD ONLY** - Slow 360° pan rotation |
| 9 | alert_scan | Wiggle+tiny wheels | **HEAD ONLY** - Fast pan -40° +40° -40° |
| 10 | search_pattern | Wiggle+tiny wheels | **HEAD+SLOW TURN** - Pan while slow 90° turn |
| 11 | scout_mode | Wiggle+tiny wheels | **FORWARD+HEAD** - Move 20cm forward, scan around |
| 12 | investigate_noise | Wiggle+tiny wheels | **HEAD ONLY** - Snap turn to one side, hold, listen |
| 13 | scan_environment | Wiggle+tiny wheels | **HEAD ONLY** - Methodical left-center-right scan |
| 14 | approach_object | Wiggle+tiny wheels | **FORWARD** - Smooth 15cm forward, look down |
| 15 | avoid_object | Wiggle+tiny wheels | **BACKWARD** - Quick 15cm back, turn 45° |

### MOVEMENT (16) - Should be REAL LOCOMOTION
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 16 | circle_dance | Wiggle+tiny wheels | **SPIN** - 360° turn at speed 20 |
| 17 | wiggle_and_wait | Wiggle+tiny wheels | **DANCE** - Side-to-side weight shift (differential) |
| 18 | bump_check | Wiggle+tiny wheels | **FORWARD-STOP** - 5cm fwd, pause, 3cm back |
| 19 | approach_gently | Wiggle+tiny wheels | **SLOW FORWARD** - 30cm at speed 12 |
| 20 | happy_spin | Wiggle+tiny wheels | **FAST SPIN** - 720° double rotation speed 25 |
| 21 | eager_start | Wiggle+tiny wheels | **BOUNCE** - Fwd 5cm, back 3cm, fwd 5cm, back 3cm |
| 22 | show_off | Wiggle+tiny wheels | **SPIN+STOP** - Quick 180° spin, pause, 180° back |
| 23 | zigzag | Wiggle+tiny wheels | **ZIGZAG** - Fwd 10cm turn left, fwd 10cm turn right |
| 24 | charge_forward | Wiggle+tiny wheels | **BURST** - 40cm forward at speed 35 |
| 25 | retreat_fast | Wiggle+tiny wheels | **BURST BACK** - 40cm backward at speed 30 |
| 26 | patrol_mode | Wiggle+tiny wheels | **PATROL** - Fwd 20cm, turn 90°, fwd 20cm |
| 27 | moonwalk | Wiggle+tiny wheels | **BACKWARD DANCE** - Smooth backward 25cm with sway |
| 28 | ballet_spin | Wiggle+tiny wheels | **GRACEFUL SPIN** - Slow 360° turn speed 15 |
| 29 | figure_eight | Wiggle+tiny wheels | **FIGURE 8** - Flowing S-curve path |
| 30 | crescent_arc_left | Wiggle+tiny wheels | **ARC LEFT** - Wide arc turn going forward |
| 31 | crescent_arc_right | Wiggle+tiny wheels | **ARC RIGHT** - Wide arc turn going forward |

### REACTIONS (13) - Should be QUICK/JERKY
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 32 | recoil_surprise | Wiggle+tiny wheels | **JERK BACK** - Quick 15cm back + head snap up |
| 33 | sad_turnaway | Wiggle+tiny wheels | **TURN AWAY** - Slow 90° turn, head down |
| 34 | confused_tilt | Wiggle+tiny wheels | **HEAD TILT** - Tilt head left, pause, tilt right |
| 35 | twitchy_nervous | Wiggle+tiny wheels | **JITTER** - Micro movements, random head snaps |
| 36 | angry_shake | Wiggle+tiny wheels | **SHAKE** - Rapid head shake + steering wiggle |
| 37 | playful_bounce | Wiggle+tiny wheels | **BOUNCE** - Fwd 5cm, back 5cm × 3 quick |
| 38 | backflip_attempt | Wiggle+tiny wheels | **ROCK BACK** - Back 8cm, pause, fwd lurch 12cm |
| 39 | defensive_curl | Wiggle+tiny wheels | **COIL** - Back 10cm, turn inward, head down |
| 40 | flinch | Wiggle+tiny wheels | **QUICK JERK** - Instant 5cm back, freeze |
| 41 | show_surprise | Wiggle+tiny wheels | **RECOIL+LOOK** - Back 8cm, head up 35° |
| 42 | show_joy | Wiggle+tiny wheels | **JUMP** - Quick fwd pulses × 4 |
| 43 | show_fear | Wiggle+tiny wheels | **SHRINK** - Slow back 15cm, head low, freeze |
| 44 | show_disgust | Wiggle+tiny wheels | **TURN AWAY** - Turn 45°, head away |

### SOCIAL (14) - Should be STATIC POSES or SEQUENCES
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 45 | bow_respectfully | Wiggle+tiny wheels | **BOW** - Forward lean, head down 30°, hold, up |
| 46 | bow_apologetically | Wiggle+tiny wheels | **DEEP BOW** - Lower head -40°, pause 1.5s, up |
| 47 | wave_head_no | Wiggle+tiny wheels | **HEAD NO** - Pan -30° +30° -30° +30° (shake) |
| 48 | wave_head_yes | Wiggle+tiny wheels | **HEAD YES** - Tilt -20° +10° × 3 (nod) |
| 49 | intro_pose | Wiggle+tiny wheels | **PRESENT** - Center, slight bow, look up |
| 50 | end_pose | Wiggle+tiny wheels | **FINISH** - Bow, hold 2s, return center |
| 51 | beckon_forward | Wiggle+tiny wheels | **BECKON** - Fwd 5cm, back 5cm, fwd 5cm (come here) |
| 52 | call_attention | Wiggle+tiny wheels | **WAVE** - Steering left-right-left quick |
| 53 | bashful_hide | Wiggle+tiny wheels | **HIDE** - Turn 45° away, head down, freeze |
| 54 | greet_wave | Wiggle+tiny wheels | **WAVE** - Steering +30° -30° +30° friendly |
| 55 | farewell_wave | Wiggle+tiny wheels | **WAVE** - Steering sway, slow head turn away |
| 56 | hello_friend | Wiggle+tiny wheels | **APPROACH+WAVE** - Fwd 15cm, steering wave |
| 57 | goodbye_friend | Wiggle+tiny wheels | **WAVE+RETREAT** - Steering wave, back 15cm |
| 58 | come_on_then | Wiggle+tiny wheels | **IMPATIENT** - Fwd 5cm back 5cm fwd 5cm |

### CELEBRATION (7) - Should be ENERGETIC
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 59 | spin_celebrate | Wiggle+tiny wheels | **SPIN BURST** - Fast 540° spin speed 30 |
| 60 | spin_reverse | Wiggle+tiny wheels | **REVERSE SPIN** - 360° opposite direction |
| 61 | jump_excited | Wiggle+tiny wheels | **JUMP SEQUENCE** - Fwd 8cm × 5 pulses rapid |
| 62 | cheer_wave | Wiggle+tiny wheels | **CHEER** - Steering wave + fwd bursts |
| 63 | celebrate_big | Wiggle+tiny wheels | **BIG SPIN** - 720° spin + head up celebration |
| 64 | applaud_motion | Wiggle+tiny wheels | **CLAP** - Steering left-right rapid × 6 |
| 65 | victory_pose | Wiggle+tiny wheels | **VICTORY** - Fwd 10cm, spin 180°, freeze proud |

### EMOTIONAL (15) - Should be SLOW/EXPRESSIVE
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 66 | show_curiosity | Wiggle+tiny wheels | **CURIOUS** - Head tilt 25°, pause, lean fwd 8cm |
| 67 | peekaboo | Wiggle+tiny wheels | **PEEK** - Turn away, pause, quick turn back |
| 68 | dance_happy | Wiggle+tiny wheels | **DANCE** - Side-to-side sway rhythm |
| 69 | dance_sad | Wiggle+tiny wheels | **SAD SWAY** - Slow side-to-side, head down |
| 70 | flirt | Wiggle+tiny wheels | **FLIRT** - Fwd 10cm, angle away coy, peek back |
| 71 | bored_idle | Wiggle+tiny wheels | **IDLE** - Long pause, head drift, sigh motion |
| 72 | think_long | Wiggle+tiny wheels | **THINK** - Head tilt up 20°, long pause 2s |
| 73 | ponder | Wiggle+tiny wheels | **PONDER** - Head angle 15°, freeze completely |
| 74 | dreamy_stare | Wiggle+tiny wheels | **DREAMY** - Slow head drift up-right, hold |
| 75 | ponder_and_nod | Wiggle+tiny wheels | **THINK+NOD** - Pause, then slow nod yes |
| 76 | show_confidence | Wiggle+tiny wheels | **CONFIDENT** - Head up 25°, chest out, still |
| 77 | show_shyness | Wiggle+tiny wheels | **SHY** - Turn 30° away, head down slightly |
| 78 | show_love | Wiggle+tiny wheels | **LOVE** - Lean forward gently, head tilt soft |
| 79 | show_thoughtfulness | Wiggle+tiny wheels | **THOUGHTFUL** - Head tilt, angle, long pause |
| 80 | idle_breath | Wiggle+tiny wheels | **BREATH** - Gentle forward-back micro-sway |

### FUNCTIONAL (12) - Should be CLEAR POSES
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 81 | sleep_mode | Wiggle+tiny wheels | **SLEEP** - Head down -35°, all center, freeze |
| 82 | wake_up | Wiggle+tiny wheels | **WAKE** - Head up, stretch upward, shake head |
| 83 | yawn | Wiggle+tiny wheels | **YAWN** - Slow head tilt back, pause 1.5s, forward |
| 84 | stretch | Wiggle+tiny wheels | **STRETCH** - Fwd 15cm slow, head up, back |
| 85 | look_proud | Wiggle+tiny wheels | **PROUD** - Head up 30°, chest position, still |
| 86 | sigh | Wiggle+tiny wheels | **SIGH** - Slow slump forward, pause, back |
| 87 | listen | Wiggle+tiny wheels | **LISTEN** - Head tilt 15° attentive, freeze |
| 88 | listen_close | Wiggle+tiny wheels | **LISTEN** - Head turn 30°, lean fwd 5cm, freeze |
| 89 | guard_pose | Wiggle+tiny wheels | **GUARD** - Center, head level, alert stance |
| 90 | ready_pose | Wiggle+tiny wheels | **READY** - Slight forward lean, head focused |
| 91 | charge_pose | Wiggle+tiny wheels | **CHARGE** - Low stance, head forward aggressive |
| 92 | wait_here | Wiggle+tiny wheels | **WAIT** - Center all, freeze completely |

### SIGNALING (10) - Should be DISTINCT CLEAR
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 93 | acknowledge_signal | Wiggle+tiny wheels | **ACK** - Single nod, clear and crisp |
| 94 | reject_signal | Wiggle+tiny wheels | **REJECT** - Head shake no, turn slightly away |
| 95 | error_shrug | Wiggle+tiny wheels | **SHRUG** - Steering wiggle uncertain |
| 96 | failure_pose | Wiggle+tiny wheels | **FAIL** - Head down low, slump, freeze |
| 97 | question_pose | Wiggle+tiny wheels | **QUESTION** - Head tilt 30°, freeze |
| 98 | affirm_pose | Wiggle+tiny wheels | **AFFIRM** - Confident nod, head up |
| 99 | signal_complete | Wiggle+tiny wheels | **DONE** - Return center, clear finish pose |
| 100 | signal_error | Wiggle+tiny wheels | **ERROR** - Head shake, steering shake |
| 101 | present_left | Wiggle+tiny wheels | **LEFT** - Turn 45° left, head point left |
| 102 | present_right | Wiggle+tiny wheels | **RIGHT** - Turn 45° right, head point right |

### ADVANCED (4) - Should be PRECISE MOVEMENT
| # | Gesture Name | Current | Should Be |
|---|--------------|---------|-----------|
| 103 | approach_slowly | Wiggle+tiny wheels | **SLOW APPROACH** - 30cm forward speed 10 |
| 104 | back_off_slowly | Wiggle+tiny wheels | **SLOW RETREAT** - 30cm backward speed 10 |
| 105 | quick_look_left | Wiggle+tiny wheels | **SNAP LEFT** - Instant head turn -40° |
| 106 | quick_look_right | Wiggle+tiny wheels | **SNAP RIGHT** - Instant head turn +40° |

## Summary of Changes Needed

**Remove Completely:**
- ❌ All micro wheel movements (speed 3-8)
- ❌ Random servo wiggles
- ❌ Everything-at-once pattern

**Add:**
- ✓ 30+ gestures with NO wheel movement (static poses)
- ✓ 20+ gestures with REAL forward/backward motion (20-40cm)
- ✓ 15+ gestures with REAL turns/spins
- ✓ 10+ gestures with rhythmic dance patterns
- ✓ Clear distinction between every gesture

**Movement Speed Guide:**
- Static gestures: 0 wheel speed
- Gentle: 10-15 speed, 20-30cm
- Normal: 20-25 speed, 30-50cm
- Energetic: 25-35 speed, 40-60cm
- Burst: 35-50 speed, brief moments
