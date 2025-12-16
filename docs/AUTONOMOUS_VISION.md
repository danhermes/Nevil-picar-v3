# Autonomous Vision System

## Overview

Nevil takes snapshots of his surroundings to maintain environmental awareness. Following an **80/20 philosophy**: 80% of vision happens during interactions, 20% unsolicited.

### Vision Trigger Types

1. **Direct requests** (Type 1): User explicitly asks "what do you see?"
2. **Context-aware** (Type 2): Conversation mentions surroundings/location
3. **Autonomous random** (Type 3): Occasional unsolicited snapshots every ~1.5-4.5 minutes

**Design Philosophy**: Vision is primarily **interaction-driven**. Nevil looks around when you talk about his environment, not constantly. Autonomous snapshots are infrequent "curiosity checks" during idle time.

## Implementation

### Three Trigger Types

#### 1. Direct Vision Requests (ai_node22.py:1067-1082)

**Triggers**: Explicit vision keywords
- "what do you see"
- "look at"
- "describe what you see"
- etc.

**Behavior**:
- Waits for vision data before responding
- User gets immediate visual description
- High priority

#### 2. Context-Aware Triggers (ai_node22.py:1084-1088)

**Triggers**: Surroundings discussion keywords
- "where are you"
- "what's around"
- "what room"
- "describe your location"
- "environment"
- "surroundings"

**Behavior**:
- Triggers vision in background
- Conversation continues immediately
- Vision data available for context in response

**Example**:
```
User: "Where are you right now?"
  ↓ [Context keyword detected: "where are you"]
  ↓ [Trigger vision in background]
  ↓ [Immediately start responding]
  ↓ [Vision data arrives mid-response]
Nevil: "I'm in the living room! [sees desk] I can see my desk with the laptop..."
```

#### 3. Autonomous Random Vision (ai_node22.py:1313-1337)

**Triggers**: **Infrequent random intervals** (base: 180s ± 50% = 90-270 seconds = **1.5-4.5 minutes**)

**Behavior**:
- Runs in main_loop() with randomized timing
- Each snapshot schedules next one at random interval
- **Infrequent** - only ~20% of total vision activity
- Occasional "curiosity checks" during idle periods
- Provides context for follow-up questions

**80/20 Philosophy**:
- **80% vision**: During interactions (Type 1 & 2 triggers)
- **20% vision**: Unsolicited autonomous (Type 3)
- Nevil looks around when you talk, not constantly

**Randomization**:
- Base interval: **180 seconds (3 minutes)** (configurable)
- Randomness: ±50% (so 180s ± 90s = 90-270 seconds = 1.5-4.5 minutes)
- Natural, unpredictable timing
- Not constantly photographing

**Example**:
```
[Random interval: 3.2 minutes]
  ↓ [Autonomous vision triggers]
  ↓ [Camera captures environment]
  ↓ [Vision API analyzes: "Living room with couch..."]
  ↓ [Stored in conversation context]
  ↓ [Next random interval scheduled: 2.1 minutes]

[Later when user interacts...]
User: "What's around you?"
Nevil: "I'm in the living room with a couch and coffee table..." [uses recent vision]
```

## Throttling & Spam Prevention

### Smart Throttling (ai_node22.py:1301-1327)

**Minimum interval**: 15 seconds between ANY snapshots

```python
# Throttle check
time_since_last = current_time - self.last_vision_time
if time_since_last < 15:  # seconds
    return False  # Skip this snapshot
```

**Prevents**:
- Rapid-fire vision requests draining API quota
- Unnecessary duplicate snapshots
- Cost explosion

**Example**:
```
User: "What do you see?"
  ↓ [Vision triggered at t=0]
User: "Look around!"
  ↓ [t=5s - THROTTLED, too soon]
User: "What's in front of you?"
  ↓ [t=20s - ALLOWED, >15s elapsed]
```

## Configuration

### Environment Variables

```bash
# Enable/disable autonomous vision
export NEVIL_AUTONOMOUS_VISION=true   # Default: true

# Base interval for random autonomous vision (seconds)
export NEVIL_VISION_INTERVAL=180      # Default: 180 seconds (3 minutes)
                                      # Actual intervals will be ±50% random
                                      # (180s ± 90s = 90-270s = 1.5-4.5 minutes)
                                      # 80/20 philosophy: most vision during interactions

# Minimum time between ANY snapshots (prevents spam)
# (Hardcoded in code: 15 seconds)
```

### Adjust Intervals

**Default (80/20 balance)**:
```bash
export NEVIL_VISION_INTERVAL=180  # 3 min base (actual: 1.5-4.5 min random)
                                  # Most vision during interactions
```

**More frequent autonomous vision** (50/50 balance):
```bash
export NEVIL_VISION_INTERVAL=60  # 1 min base (actual: 30-90s random)
```

**Very infrequent** (95/5 - almost only interactions):
```bash
export NEVIL_VISION_INTERVAL=300  # 5 min base (actual: 2.5-7.5 min random)
```

**Disable autonomous vision** (100% interaction-driven):
```bash
export NEVIL_AUTONOMOUS_VISION=false
```

### Adjust Randomness

Edit `ai_node22.py` line 104:

```python
self.autonomous_vision_randomness = 0.5   # ±50% (default)
# self.autonomous_vision_randomness = 0.3  # ±30% (less random)
# self.autonomous_vision_randomness = 0.7  # ±70% (more random)
```

### Adjust Throttling

Edit `ai_node22.py` line 107:

```python
self.min_vision_interval = 15  # Change to 20, 30, etc.
```

## Vision Context Injection

All vision data (regardless of trigger type) is injected the same way:

```
[SYSTEM: Your camera is showing you this view: {description}]
```

This stays in conversation history, providing context for future responses.

## Cost Analysis

### Cost per Snapshot
- **Vision API call**: ~$0.005 (low detail)

### Estimated Daily Usage

**Scenario 1: Active use (8 hours/day, 80/20 balance)**
```
During interactions (Type 1 & 2): ~80 snapshots (80%)
Autonomous random (Type 3): ~20 snapshots (20%)
Total: ~100 snapshots/day × $0.005 = $0.50/day
Monthly: ~$15/month
```

**Scenario 2: 24/7 operation (80/20 balance)**
```
During interactions (Type 1 & 2): ~50 snapshots/day (assuming some interaction)
Autonomous random (Type 3): ~180 snapshots/day (every ~3 min average)
Total: ~230 snapshots/day × $0.005 = $1.15/day
Monthly: ~$35/month
```

**Scenario 3: High interaction use (lots of conversation)**
```
During interactions (Type 1 & 2): ~150 snapshots/day (conversations about environment)
Autonomous random (Type 3): ~20 snapshots/day
Total: ~170 snapshots/day × $0.005 = $0.85/day
Monthly: ~$26/month
```

**Scenario 4: Disabled autonomous (100% interaction-driven)**
```
Context triggers: ~20 snapshots/day
Direct requests: ~30 snapshots/day
Total: ~50 snapshots/day × $0.005 = $0.25/day
Monthly: ~$7.50
```

### Cost Optimization

**Balance awareness vs cost**:
- 45s interval = Good awareness, moderate cost
- 90s interval = Less cost, still aware
- 120s+ interval = Minimal cost, delayed awareness

## Statistics Tracking

```python
stats = ai_node.get_stats()
print(stats)

# Output:
{
    "vision_call_count": 150,           # Total vision calls
    "autonomous_vision_count": 120,     # How many were autonomous
    "vision_error_count": 2,            # Failed calls
    "autonomous_vision_enabled": True,  # Is autonomous enabled?
    "autonomous_vision_interval": 45    # Interval in seconds
}
```

## Monitoring

### Log Messages

**Autonomous trigger** (infrequent - 20% of vision activity):
```
🤖 AUTONOMOUS VISION - Random interval (198.5s), taking snapshot
📸 Vision snapshot triggered (source: autonomous_random)
🔮 Next autonomous vision in ~156.3s
```

**Context trigger**:
```
🌍 SURROUNDINGS CONTEXT detected - triggering autonomous vision
📸 Vision snapshot triggered (source: context_surroundings)
```

**Direct trigger**:
```
🎥 DIRECT VISION REQUEST - triggering camera
📸 Vision snapshot triggered (source: voice_direct)
⏸️ Waiting for vision data before responding...
```

**Throttled**:
```
⏸️ Vision throttled (8.3s < 15s)
```

## Behavior Examples

### Example 1: Idle Random Autonomous Vision (20% of total)
```
[Nevil idle, random timer: 3.2 minutes]
  ↓ [Autonomous vision triggers]
  ↓ [Captures: "Living room with TV and couch"]
  ↓ [Stored in conversation context]
  ↓ [Next random interval: 2.7 minutes]

[Later when user talks...]
User: "What room are you in?"
Nevil: "I'm in the living room! I can see the TV and couch over there."
  [Uses recent autonomous snapshot from 2 minutes ago]
```

### Example 2: Context-Aware Discussion
```
User: "Describe your environment"
  ↓ [Context keyword: "environment"]
  ↓ [Vision triggered in background]
  ↓ [Nevil starts responding immediately]
  ↓ [Vision data arrives: "Kitchen with table..."]
Nevil: "Well, I'm in the kitchen area. I can see a table with some chairs and a window..."
```

### Example 3: Direct + Throttle
```
User: "What do you see?"
  ↓ [t=0s - Vision triggered]
Nevil: "I see a desk with a laptop..."

User: "What else?"
  ↓ [t=5s - THROTTLED, reuses recent vision]
Nevil: "From what I saw a moment ago, there's also a red mug and some papers..."

User: "Look around again"
  ↓ [t=20s - NEW vision triggered, >15s elapsed]
Nevil: "Taking another look... I can now see there's a window on the left side..."
```

## 80/20 Balance Rationale

**Why interaction-first?**
- **Natural conversation flow**: Vision happens when relevant
- **Cost efficient**: Most snapshots are immediately useful
- **Privacy friendly**: Not constantly photographing
- **Context appropriate**: Vision triggered by discussion topic

**Why some autonomous?**
- **Idle awareness**: Maintains context during quiet periods
- **Fresh context**: Updates environment when things change
- **Surprise factor**: Nevil can notice changes unprompted
- **Fallback data**: Recent vision available when needed

## Future Enhancements

1. **Vision caching**: Reuse recent vision descriptions for similar questions
2. **Motion-triggered vision**: Take snapshot when robot moves
3. **Change detection**: Compare vision over time, note changes
4. **Multi-angle vision**: Take multiple snapshots from different angles
5. **Selective detail**: Use high-detail vision for specific objects on request
6. **Adaptive frequency**: More autonomous vision when user is away, less when active

## Troubleshooting

### Too Many Vision Calls
**Solution**: Increase interval or disable autonomous
```bash
export NEVIL_VISION_INTERVAL=90  # Less frequent
# or
export NEVIL_AUTONOMOUS_VISION=false  # Disable
```

### Vision Not Triggering
**Check**:
1. `NEVIL_AUTONOMOUS_VISION=true` is set
2. Check logs for throttling messages
3. Verify main_loop() is running

### Stale Vision Context
**Issue**: Vision description is old
**Solution**: Vision auto-refreshes every 45s (or configured interval)

### Cost Too High
**Solutions**:
1. Increase `NEVIL_VISION_INTERVAL` (reduce frequency)
2. Disable autonomous vision (manual only)
3. Increase `min_vision_interval` (more aggressive throttling)

## Related Files

- `ai_node22.py:96-107` - Autonomous vision configuration
- `ai_node22.py:1049-1088` - Vision intent detection
- `ai_node22.py:1287-1295` - Autonomous vision main loop
- `ai_node22.py:1301-1327` - Vision snapshot trigger with throttling
- `/docs/INTENT_BASED_VISION.md` - Intent detection architecture
- `/docs/VISION_INTEGRATION.md` - Complete vision system
