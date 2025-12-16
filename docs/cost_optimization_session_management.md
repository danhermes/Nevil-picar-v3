# Session Management & Cost Tracking

## Problem
1. **No session timeout** - WebSocket stays open indefinitely even during idle
2. **No usage tracking** - Can't monitor costs or identify expensive operations
3. **No cost alerts** - Can't detect runaway costs before they happen

## Solution 1: Idle Session Timeout

### Implementation in realtime_connection_manager.py

```python
class RealtimeConnectionManager:
    def __init__(self, ...):
        # ... existing code ...

        # Session timeout configuration
        self.idle_timeout = 300.0  # 5 minutes of inactivity
        self.last_activity_time = time.time()
        self.idle_check_interval = 30.0  # Check every 30 seconds

    def start(self):
        """Start connection and idle monitoring"""
        # ... existing code ...

        # Start idle monitor thread
        self.idle_monitor_thread = Thread(
            target=self._idle_monitor_loop,
            daemon=True,
            name="IdleMonitor"
        )
        self.idle_monitor_thread.start()

    def _idle_monitor_loop(self):
        """Monitor for idle timeout and disconnect if inactive"""
        while self.running:
            time.sleep(self.idle_check_interval)

            if self.state == ConnectionState.CONNECTED:
                idle_duration = time.time() - self.last_activity_time

                if idle_duration > self.idle_timeout:
                    logger.info(f"Session idle for {idle_duration:.1f}s - disconnecting to save costs")
                    asyncio.run_coroutine_threadsafe(
                        self._async_disconnect("Idle timeout"),
                        self.loop
                    )

    def _update_activity(self):
        """Update last activity timestamp"""
        self.last_activity_time = time.time()

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message and update activity"""
        self._update_activity()
        # ... existing send code ...

    async def _handle_message(self, data: Union[str, bytes]) -> None:
        """Handle message and update activity"""
        self._update_activity()
        # ... existing handle code ...
```

### Auto-Reconnect on Next User Input
```python
# In ai_cognition_realtime_node.py
def on_voice_command(self, message):
    """Handle voice command - auto-reconnect if needed"""
    # Check if disconnected due to idle timeout
    if not self.connection_manager.is_connected():
        logger.info("Auto-reconnecting after idle timeout")
        self.connection_manager.start()
        # Wait for connection
        for _ in range(10):  # 5 second timeout
            if self.connection_manager.is_connected():
                break
            time.sleep(0.5)

    # Process command as normal
    # ... existing code ...
```

## Solution 2: Usage Tracking & Cost Monitoring

### Create UsageTracker Class

```python
# nevil_framework/realtime/usage_tracker.py

import json
import time
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class UsageStats:
    """Real-time usage statistics"""
    # Audio usage (in seconds)
    audio_input_seconds: float = 0.0
    audio_output_seconds: float = 0.0

    # Text usage (in tokens)
    text_input_tokens: int = 0
    text_output_tokens: int = 0

    # Session metrics
    total_sessions: int = 0
    total_duration_seconds: float = 0.0
    function_calls: int = 0

    # Cost estimates (USD)
    estimated_cost_usd: float = 0.0

class UsageTracker:
    """Track and estimate API usage costs"""

    # OpenAI Realtime API pricing (per 1M tokens)
    PRICING = {
        "audio_input_per_second": 0.00001111,  # $100/1M tokens ÷ (1M/3600/2.5) tokens per second
        "audio_output_per_second": 0.00002222,  # $200/1M tokens ÷ (1M/3600/2.5)
        "text_input_per_token": 0.000005,       # $5/1M tokens
        "text_output_per_token": 0.00002        # $20/1M tokens
    }

    def __init__(self, stats_file: Path = None):
        self.stats = UsageStats()
        self.stats_file = stats_file or Path("/home/dan/Nevil-picar-v3/logs/realtime_usage.json")
        self.session_start_time = time.time()

        # Load previous stats if available
        self._load_stats()

    def track_audio_input(self, duration_seconds: float):
        """Track audio input usage"""
        self.stats.audio_input_seconds += duration_seconds
        cost = duration_seconds * self.PRICING["audio_input_per_second"]
        self.stats.estimated_cost_usd += cost

    def track_audio_output(self, duration_seconds: float):
        """Track audio output usage"""
        self.stats.audio_output_seconds += duration_seconds
        cost = duration_seconds * self.PRICING["audio_output_per_second"]
        self.stats.estimated_cost_usd += cost

    def track_text_input(self, token_count: int):
        """Track text input tokens"""
        self.stats.text_input_tokens += token_count
        cost = token_count * self.PRICING["text_input_per_token"]
        self.stats.estimated_cost_usd += cost

    def track_text_output(self, token_count: int):
        """Track text output tokens"""
        self.stats.text_output_tokens += token_count
        cost = token_count * self.PRICING["text_output_per_token"]
        self.stats.estimated_cost_usd += cost

    def track_function_call(self):
        """Track function calls"""
        self.stats.function_calls += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return asdict(self.stats)

    def get_session_cost(self) -> float:
        """Get cost for current session only"""
        session_duration = time.time() - self.session_start_time
        return self.stats.estimated_cost_usd

    def save_stats(self):
        """Save statistics to file"""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.stats_file, 'w') as f:
            json.dump(asdict(self.stats), f, indent=2)

    def _load_stats(self):
        """Load previous statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                self.stats = UsageStats(**data)

    def reset_session(self):
        """Reset session-specific counters"""
        self.session_start_time = time.time()
        self.stats.total_sessions += 1
        self.save_stats()
```

### Integration with RealtimeConnectionManager

```python
# In realtime_connection_manager.py

from nevil_framework.realtime.usage_tracker import UsageTracker

class RealtimeConnectionManager:
    def __init__(self, ...):
        # ... existing code ...

        # Usage tracking
        self.usage_tracker = UsageTracker()

    async def _handle_message(self, data: Union[str, bytes]) -> None:
        """Process incoming message and track usage"""
        # ... existing parsing code ...

        event_type = event.get('type')

        # Track audio usage
        if event_type == 'response.audio.delta':
            # Estimate duration from delta size
            delta = event.get('delta', '')
            audio_bytes = base64.b64decode(delta)
            # 24kHz PCM16 = 48000 bytes/second
            duration = len(audio_bytes) / 48000.0
            self.usage_tracker.track_audio_output(duration)

        elif event_type == 'input_audio_buffer.speech_stopped':
            # Track input audio duration (if provided by API)
            pass

        # Track text tokens (if API provides usage data)
        elif event_type == 'response.done':
            usage = event.get('usage', {})
            if 'output_tokens' in usage:
                self.usage_tracker.track_text_output(usage['output_tokens'])
            if 'input_tokens' in usage:
                self.usage_tracker.track_text_input(usage['input_tokens'])

        # ... existing event handling ...

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return self.usage_tracker.get_stats()

    def get_estimated_cost(self) -> float:
        """Get estimated cost in USD"""
        return self.usage_tracker.stats.estimated_cost_usd
```

## Solution 3: Cost Alerts

```python
# In ai_cognition_realtime_node.py

class AiNode22(NevilNode):
    def __init__(self):
        # ... existing code ...

        # Cost alert thresholds
        self.cost_alert_threshold = 1.0  # Alert at $1.00
        self.cost_warning_threshold = 0.50  # Warn at $0.50
        self.last_cost_check = 0.0

    def main_loop(self):
        """Main loop with cost monitoring"""
        time.sleep(0.1)

        # Check costs every 10 seconds
        if time.time() - self.last_cost_check > 10.0:
            self._check_costs()
            self.last_cost_check = time.time()

    def _check_costs(self):
        """Monitor costs and alert if threshold exceeded"""
        if not self.connection_manager:
            return

        current_cost = self.connection_manager.get_estimated_cost()

        if current_cost > self.cost_alert_threshold:
            self.logger.error(f"🚨 COST ALERT: ${current_cost:.2f} spent this session!")
            # Optional: auto-disconnect to prevent runaway costs
            # self.connection_manager.stop("Cost threshold exceeded")

        elif current_cost > self.cost_warning_threshold:
            self.logger.warning(f"⚠️ Cost warning: ${current_cost:.2f} spent this session")

    def get_stats(self) -> Dict[str, Any]:
        """Include usage stats in node stats"""
        stats = super().get_stats()

        if self.connection_manager:
            stats["usage"] = self.connection_manager.get_usage_stats()
            stats["estimated_cost_usd"] = self.connection_manager.get_estimated_cost()

        return stats
```

## Usage Dashboard (Optional)

```python
# scripts/show_realtime_usage.py

import json
from pathlib import Path

def show_usage_dashboard():
    """Display real-time usage dashboard"""
    stats_file = Path("/home/dan/Nevil-picar-v3/logs/realtime_usage.json")

    if not stats_file.exists():
        print("No usage data available yet")
        return

    with open(stats_file) as f:
        stats = json.load(f)

    print("=" * 60)
    print("OpenAI Realtime API Usage Dashboard")
    print("=" * 60)
    print(f"Audio Input:  {stats['audio_input_seconds']:.1f}s")
    print(f"Audio Output: {stats['audio_output_seconds']:.1f}s")
    print(f"Text Input:   {stats['text_input_tokens']:,} tokens")
    print(f"Text Output:  {stats['text_output_tokens']:,} tokens")
    print(f"Function Calls: {stats['function_calls']}")
    print(f"Total Sessions: {stats['total_sessions']}")
    print("-" * 60)
    print(f"Estimated Cost: ${stats['estimated_cost_usd']:.4f} USD")
    print("=" * 60)

if __name__ == "__main__":
    show_usage_dashboard()
```

Run with:
```bash
python scripts/show_realtime_usage.py
```

## Expected Savings
- **Idle timeout**: 10-15% (prevents paying for idle connections)
- **Cost awareness**: 5-10% (catch expensive operations early)
- **Total**: 15-25% cost reduction

## Implementation Checklist
- [ ] Add idle timeout to RealtimeConnectionManager
- [ ] Implement UsageTracker class
- [ ] Integrate usage tracking in event handlers
- [ ] Add cost alerts to ai_node22
- [ ] Create usage dashboard script
- [ ] Set appropriate alert thresholds
- [ ] Monitor usage for 48 hours
- [ ] Adjust thresholds based on usage patterns
