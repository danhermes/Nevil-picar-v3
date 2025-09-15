# Nevil v3.0 Obstacle Avoidance and Safety System

## Overview

This document defines the obstacle avoidance and safety system for Nevil v3.0, which operates as a separate node that monitors sensors and publishes safety signals to the navigation node.

## Architecture

The obstacle avoidance system operates independently from navigation, following the principle of separation of concerns:

```
Ultrasonic Sensor → Obstacle Detection Node → Safety Messages → Navigation Node
                                            ↘                ↗
                                              Emergency Stop
```

## Safety Parameters

From v1.0 action_helper.py calibration:
- **SafeDistance**: 30cm - Normal operation threshold
- **DangerDistance**: 15cm - Immediate caution/stop threshold
- **Emergency Stop Distance**: 10cm - Full stop required
- **Sensor Check Frequency**: 10Hz (every 100ms)

## Obstacle Detection Implementation

### Core Safety Node

```python
# nodes/obstacle_detection/obstacle_detection_node.py

class ObstacleDetectionNode(NevilNode):
    """
    Obstacle Detection and Safety Node for Nevil v3.0

    Monitors ultrasonic sensor and publishes safety status.
    """

    def __init__(self):
        super().__init__("obstacle_detection")

        # Safety thresholds
        self.safe_distance = 30  # cm
        self.danger_distance = 15  # cm
        self.emergency_distance = 10  # cm

        # Sensor state
        self.last_distance = None
        self.sensor_healthy = True

    def _check_obstacles(self) -> bool:
        """Check for obstacles and publish safety status"""
        if self.simulation_mode:
            return True

        try:
            distance = self.car.get_distance()

            if distance < self.emergency_distance:
                self._publish_safety_status("emergency_stop", distance)
                return False
            elif distance < self.danger_distance:
                self._publish_safety_status("caution", distance)
                return False
            elif distance < self.safe_distance:
                self._publish_safety_status("warning", distance)
                return True
            else:
                self._publish_safety_status("clear", distance)
                return True

        except Exception as e:
            self.logger.error(f"Obstacle sensor error: {e}")
            self._publish_safety_status("sensor_error", -1)
            return True  # Continue if sensor fails
```

### Safety Message Protocol

```yaml
# Published by obstacle_detection node
publishes:
  - topic: "safety_status"
    message_type: "SafetyStatus"
    description: "Obstacle detection and safety status"
    schema:
      status:
        type: "string"
        required: true
        enum: ["clear", "warning", "caution", "emergency_stop", "sensor_error"]
      distance:
        type: "float"
        required: true
        description: "Distance to obstacle in cm (-1 if error)"
      timestamp:
        type: "float"
        required: true
```

### Navigation Node Integration

The navigation node subscribes to safety messages and responds accordingly:

```python
# In navigation_node.py

def on_safety_status(self, message):
    """Handle safety status updates from obstacle detection"""
    status = message.data.get('status')
    distance = message.data.get('distance')

    if status == 'emergency_stop':
        self._emergency_stop()
        self.logger.error(f"EMERGENCY STOP - Obstacle at {distance}cm")
    elif status == 'caution':
        self._reduce_speed()
        self.logger.warning(f"Caution - Obstacle at {distance}cm")
    elif status == 'warning':
        self.logger.info(f"Warning - Obstacle at {distance}cm")
```

## Obstacle Avoidance Behaviors

### From v1.0 action_helper.py

The decorator pattern for obstacle checking:

```python
def with_obstacle_check(func):
    """Decorator to add obstacle checking to movement functions"""
    def wrapper(car, *args, **kwargs):
        def check_distance():
            distance = car.get_distance()
            if distance >= car.SafeDistance:
                return "safe"
            elif distance >= car.DangerDistance:
                car.set_dir_servo_angle(30)  # Turn to avoid
                return "caution"
            else:
                car.set_dir_servo_angle(-30)
                move_backward_this_way(car, 10, car.speed)
                sleep(0.5)
                return "danger"

        return func(car, *args, check_distance=check_distance, **kwargs)
    return wrapper
```

### Avoidance Strategies

1. **Clear Path** (>30cm):
   - Continue normal operation
   - Maintain current speed

2. **Warning Zone** (20-30cm):
   - Continue with monitoring
   - Prepare for avoidance

3. **Caution Zone** (15-20cm):
   - Reduce speed to 50%
   - Turn 30° to find clear path
   - Continue movement with caution

4. **Danger Zone** (<15cm):
   - Stop forward movement
   - Back up 10cm
   - Turn -30° and reassess

5. **Emergency Stop** (<10cm):
   - Immediate full stop
   - No movement until cleared

## Sensor Health Monitoring

```python
def _monitor_sensor_health(self):
    """Monitor ultrasonic sensor health"""
    if self.last_distance is None:
        return

    current_time = time.time()

    # Check for sensor timeout (no reading for 1 second)
    if current_time - self.last_reading_time > 1.0:
        self.sensor_healthy = False
        self._publish_sensor_health(False, "timeout")

    # Check for stuck readings
    elif self.last_5_readings.count(self.last_distance) == 5:
        self.sensor_healthy = False
        self._publish_sensor_health(False, "stuck_value")

    else:
        self.sensor_healthy = True
        self._publish_sensor_health(True, "operational")
```

## Testing Requirements

### Unit Tests
1. Distance threshold logic
2. Safety status message generation
3. Sensor failure detection
4. Avoidance behavior selection

### Integration Tests
1. Obstacle detection → Navigation stop
2. Emergency stop response time (<100ms)
3. Sensor failure fallback behavior
4. Multi-obstacle scenarios

### Hardware Tests
1. Ultrasonic sensor accuracy
2. Response time measurements
3. Moving obstacle detection
4. Different material detection (wood, fabric, glass)

## Performance Requirements

- **Sensor polling rate**: 10Hz minimum
- **Emergency stop latency**: <100ms from detection
- **Safety message latency**: <50ms
- **Sensor timeout detection**: 1 second
- **Minimum detectable object**: 2cm diameter

## Error Handling

1. **Sensor timeout**: Publish sensor_error, continue with last known state
2. **Invalid readings**: Filter outliers, use rolling average
3. **Stuck sensor**: Detect repeated values, flag as error
4. **Communication failure**: Navigation defaults to cautious mode

## Future Enhancements

1. **Multi-sensor fusion**: Combine ultrasonic with camera depth
2. **Predictive avoidance**: Anticipate moving obstacles
3. **Dynamic safety zones**: Adjust thresholds based on speed
4. **Learning**: Adapt to environment over time
5. **360° coverage**: Multiple ultrasonic sensors

## Conclusion

The obstacle avoidance system provides a critical safety layer that operates independently from navigation, ensuring safe operation even if other systems fail. By separating concerns, the system maintains modularity while providing robust collision avoidance.