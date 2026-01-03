# Nevil Gesture & Action Architecture

**Last Updated:** 2026-01-02
**Status:** Production - Fully Functional
**GPT Control:** ❌ **NO** - Pattern matching only

---

## Executive Summary

**GPT-4 Realtime API does NOT control gestures.** All gestures are generated via fast pattern-matching code that analyzes speech transcripts and injects 3-6 context-appropriate gestures from a library of 135 available gestures.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GPT-4 Realtime API                       │
│              (Speech Generation ONLY)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  Speech Synthesis Node       │
          │  - Receives audio + transcript│
          │  - Injects gestures via       │
          │    pattern matching (<1ms)    │
          └──────────┬───────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│  Audio Output   │    │ robot_action     │
│  (speaker)      │    │ (message bus)    │
└─────────────────┘    └────────┬─────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │ Navigation Node  │
                      │ - Queues actions │
                      │ - Executes on    │
                      │   PiCar-X        │
                      └──────────────────┘
```

---

## What GPT Controls

### ✅ GPT Controls Speech ONLY

- **Conversational responses** - GPT generates intelligent dialogue
- **Voice output** - Streaming audio via OpenAI Realtime API
- **Context awareness** - Maintains conversation memory
- **Personality** - "Laid-back SoCal surfer dude" tone

### ❌ GPT Does NOT Control Gestures

GPT-4 Realtime API's function calling is fundamentally unreliable:
- Rarely calls `perform_gesture()` function despite explicit prompts
- Known limitation of Realtime API (not regular GPT-4)
- We attempted multiple fixes - all failed
- **Solution:** Fast pattern-matching fallback system

---

## Gesture Injection System

### Location
- **Main logic:** `/home/dan/Nevil-picar-v3/nevil_framework/gesture_injector.py`
- **Integration:** `/home/dan/Nevil-picar-v3/nodes/speech_synthesis_realtime/speech_synthesis_realtime_node.py:363-386`
- **Execution:** `/home/dan/Nevil-picar-v3/nodes/navigation/navigation_node.py`

### How It Works

1. **Speech synthesis receives transcript** from GPT Realtime API
2. **Pattern matching analyzes text** (sentiment, keywords, context)
3. **Selects 3-6 gestures** from appropriate categories
4. **Publishes to `robot_action` topic** on message bus
5. **Navigation node receives and queues** gestures
6. **Executes gestures in parallel** with speech playback

**Performance:** <1ms pattern matching, zero added latency

---

## The 135 Gesture Library

All gestures organized into 9 categories with 106 extended gestures + 29 base gestures:

### 1. OBSERVATION (15 gestures)
**Usage:** Questions, curiosity, investigation

Examples: `look_left_then_right`, `scan_up_down`, `curious_peek`, `alert_scan`, `pan_360`

### 2. MOVEMENT (16 gestures)
**Usage:** Locomotion, driving, positioning

Examples: `approach_slowly`, `dodge_left`, `figure_eight`, `serpentine`, `zigzag_approach`

### 3. REACTIONS (13 gestures)
**Usage:** Quick responses, thinking, confusion

Examples: `flinch`, `shocked_jerk`, `confused_tilt`, `think`, `ponder`, `double_take`

### 4. SOCIAL (14 gestures)
**Usage:** Greetings, farewells, acknowledgment

Examples: `greet_wave`, `hello_friend`, `farewell_wave`, `bow_respectfully`, `nod`

### 5. CELEBRATION (7 gestures)
**Usage:** Happy, excited, victorious moments

Examples: `happy_spin`, `celebrate_big`, `victory_spin`, `jump_excited`, `circle_dance`

### 6. EMOTIONAL (15 gestures)
**Usage:** Expressive feelings, moods

Examples: `show_joy`, `dance_happy`, `sad_turnaway`, `angry_shake`, `shy_retreat`

### 7. FUNCTIONAL (12 gestures)
**Usage:** Ready states, poses, patterns

Examples: `ready_pose`, `guard_pose`, `search_pattern`, `idle_breath`, `patrol_mode`

### 8. SIGNALING (10 gestures)
**Usage:** Pointing, directing attention

Examples: `call_attention`, `point_forward`, `signal_stop`, `wave_come_here`, `thumbs_up`

### 9. ADVANCED (4 gestures)
**Usage:** Complex choreography

Examples: `ballet_spin`, `backflip_attempt`, `moonwalk`, `matrix_dodge`

---

## Pattern Matching Logic

### Context-Aware Category Selection

The system analyzes transcript text and selects gestures from appropriate categories:

| Pattern | Selected Categories | Example |
|---------|---------------------|---------|
| Greetings (`hi`, `hello`) | Social | `greet_wave`, `hello_friend` |
| Questions (`?`, `what`, `why`) | Observation + Reactions | `curious_peek`, `think` |
| Excitement (`awesome`, `great`) | Celebration + Movement | `happy_spin`, `charge_forward` |
| Thinking (`hmm`, `ponder`) | Reactions + Observation | `think`, `scan_up_down` |
| Happy (`glad`, `joyful`) | Celebration + Emotional | `celebrate_big`, `show_joy` |
| Movement (`go`, `forward`) | Movement | `approach_slowly`, `dodge_left` |

### Speed Detection

Gestures auto-adjust speed based on sentiment:

- **FAST** - Excited, urgent keywords → `gesture:fast`
- **MED** - Default, neutral → `gesture:med`
- **SLOW** - Calm, thoughtful keywords → `gesture:slow`

### Anti-Repetition System

- Tracks last 20 gestures used
- Filters them from selection pool
- Ensures maximum variety across responses

---

## Message Flow

### 1. Speech Synthesis Injects Gestures

```python
# speech_synthesis_realtime_node.py:363-386
if transcript:
    injector = get_gesture_injector()
    auto_gestures = injector.analyze_and_inject(
        transcript,
        min_gestures=3,
        max_gestures=6
    )

    if auto_gestures:
        self.publish("robot_action", {
            "actions": auto_gestures,  # e.g., ['greet_wave:med', 'curious_peek:med', 'nod:fast']
            "source_text": transcript[:50],
            "mood": "neutral",
            "priority": 100,
            "timestamp": time.time()
        })
```

### 2. Navigation Receives & Queues

```python
# navigation_node.py
def on_robot_action(self, message):
    actions = message.data['actions']
    priority = message.data.get('priority', 50)

    action_sequence = {
        'actions': actions,
        'mood': message.data.get('mood', 'neutral'),
        'timestamp': time.time()
    }

    self.action_queue.put((priority, timestamp, action_sequence))
```

### 3. Execution Thread Processes Queue

```python
# navigation_node.py - action processing loop
while True:
    priority, timestamp, action_sequence = self.action_queue.get()

    for action_str in action_sequence['actions']:
        # Parse: 'greet_wave:med' → gesture='greet_wave', speed='med'
        gesture, speed = self._parse_action(action_str)

        # Execute on hardware
        function = self.action_functions.get(gesture)
        function(self.car, speed=speed)
```

---

## Direct Command Bypass

**User can directly command gestures:**

Say "forward", "move your head", "spin" → Speech recognition detects these patterns and publishes directly to `robot_action`, bypassing GPT entirely.

**Location:** `/home/dan/Nevil-picar-v3/nodes/speech_recognition_realtime/speech_recognition_realtime_node.py`

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **GPT speech latency** | 200-400ms |
| **Pattern matching** | <1ms |
| **Gesture selection** | <1ms |
| **Total added latency** | ~0ms (parallel execution) |
| **Gestures per response** | 3-6 |
| **Available gesture pool** | 135 |
| **Anti-repetition window** | 20 gestures |

---

## Future Enhancements

### Potential Improvements (Not Implemented)

1. **GPT-4 Planning (Rejected)** - Would add 200-500ms latency
   - Could use regular GPT-4 API to intelligently select gestures
   - Decision: Keep speed over intelligence

2. **Local LLM Integration** - Possible future enhancement
   - Run small model for gesture selection
   - Needs evaluation of latency impact

3. **Sentiment Analysis** - Could expand beyond regex
   - More sophisticated emotion detection
   - Currently: Fast regex patterns work well

---

## Troubleshooting

### No Gestures Executing

1. Check `robot_action` topic declared in `.messages` file
2. Verify gesture_injector import: `from nevil_framework.gesture_injector import get_gesture_injector`
3. Check logs for "🎭 Injecting N gestures"
4. Verify navigation node is receiving: grep "robot_action" in logs

### Wrong Gestures

1. Check pattern matching in `gesture_injector.py:pattern_categories`
2. Add/modify regex patterns for better context matching
3. Adjust category assignments

### Repetitive Gestures

1. Increase `maxlen` in `recent_gestures` deque (currently 20)
2. Check that anti-repetition logic is working in logs

---

## Key Files Reference

| File | Purpose | Lines of Interest |
|------|---------|-------------------|
| `nevil_framework/gesture_injector.py` | Pattern matching & gesture selection | 155-219 (analyze_and_inject) |
| `nodes/speech_synthesis_realtime/speech_synthesis_realtime_node.py` | Injection point | 363-386 |
| `nodes/speech_synthesis_realtime/.messages` | Topic permissions | 60-84 (robot_action) |
| `nodes/navigation/navigation_node.py` | Gesture execution | 285-450 (action processing) |
| `nodes/navigation/extended_gestures.py` | 106 extended gestures | Full file (32k tokens) |
| `nodes/navigation/action_helper.py` | 29 base gestures | Full file |

---

## Summary

**Current State:**
- ✅ Fast, responsive gesture system
- ✅ 135 gestures with context-aware selection
- ✅ Zero latency overhead (pattern matching <1ms)
- ✅ Simultaneous speech and motion
- ✅ Anti-repetition ensures variety
- ❌ GPT does NOT control gestures (Realtime API limitation)

**Trade-off:**
- **Chose:** Speed + responsiveness (pattern matching)
- **Over:** GPT intelligence (adds 200-500ms latency)

The system prioritizes **real-time responsiveness** over AI-controlled gesture selection, resulting in a fast, expressive robot that feels alive.
