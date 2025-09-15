# Nevil v3.0 - Lightweight Robot Framework

A simple, reliable robotics framework that preserves proven v1.0 audio components while providing modern node-based architecture.

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run the System
```bash
# Validate configuration
./nevil validate

# Start the system
./nevil start

# Stop with Ctrl+C
```

## Architecture

### Core Philosophy
- **Declarative Everything**: Configuration via `.nodes` and `.messages` YAML files
- **Simple Architecture = Working Robot**: Minimal complexity, maximum reliability
- **Preserve What Works**: v1.0 audio components integrated exactly as-is

### Key Components

#### Message Bus
- Simple pub/sub system using Python queues
- Automatic topic creation and subscription management
- Thread-safe operation with performance monitoring

#### NevilNode Base Class
- **Declarative messaging** via `init_messages()` - no manual subscribe() calls needed!
- Threading with graceful shutdown
- Enhanced logging with EST timestamps
- Health monitoring and error recovery

#### Configuration System
- **Individual `.messages` files**: Each node declares its messaging interface
- **Root `.nodes` file**: System-wide coordination
- Environment variable expansion
- Hot-reloading capabilities (Phase 2)

## Creating Nodes

### 1. Create Node Directory
```bash
mkdir -p nodes/my_node
```

### 2. Create `.messages` Configuration
```yaml
# nodes/my_node/.messages
node_name: "my_node"
version: "1.0"
description: "My custom node"

publishes:
  - topic: "my_output"
    message_type: "MyMessage"
    description: "Messages from my node"

subscribes:
  - topic: "my_input"
    callback: "on_my_input"
    description: "Input messages"
```

### 3. Create Node Implementation
```python
# nodes/my_node/my_node_node.py
from nevil_framework.base_node import NevilNode

class MyNodeNode(NevilNode):
    def __init__(self):
        super().__init__("my_node")  # Auto-loads .messages!

    def initialize(self):
        # Initialize your node components
        pass

    def main_loop(self):
        # Main processing loop
        self.publish("my_output", {"hello": "world"})

    def on_my_input(self, message):
        # Automatically configured callback
        self.logger.info(f"Received: {message.data}")

    def cleanup(self):
        # Cleanup resources
        pass
```

### 4. Run Your Node
```bash
./nevil start
```

The framework automatically discovers and starts your node!

## Development Status

**✅ Week 1 Complete: Core Framework**
- Message bus with pub/sub
- Declarative node system
- Configuration loading
- Node discovery and lifecycle

**🚧 Week 2 Planned: Audio Integration**
- Extract v1.0 audio components
- Speech recognition wrapper
- TTS synthesis wrapper
- Hardware abstraction layer

**🔮 Week 3 Planned: Node Implementation**
- Speech recognition node
- Speech synthesis node
- AI cognition node
- Inter-node communication

## Testing

The framework includes a test node for validation:

```bash
# Check test node configuration
cat nodes/test_node/.messages

# Run system with test node
./nevil start

# Watch logs
tail -f logs/test_node.log
```

## Documentation

Full technical specifications are available in `docs/nevil_v3/`:

- `01_technical_architecture_specification.md`
- `02_node_structure_threading_model.md`
- `03_configuration_file_formats.md`
- And 7 more detailed design documents

## Project Structure

```
nevil_v3/
├── nevil                          # CLI executable
├── .nodes                         # Root system config
├── nevil_framework/              # Core framework
│   ├── base_node.py              # Declarative messaging
│   ├── message_bus.py            # Pub/sub system
│   ├── config_loader.py          # YAML validation
│   └── launcher.py               # Node lifecycle
├── nodes/                        # Node implementations
│   └── test_node/               # Example node
├── audio/                        # v1.0 audio preservation (Week 2)
├── v1.0/                         # Original working implementation
├── v2.0/                         # ROS2 version (reference)
└── logs/                         # Runtime logs
```

## Philosophy

**"Simple architecture = working robot"**

Nevil v3.0 eliminates the complexity of ROS2 while preserving all the proven functionality from v1.0. The declarative configuration system means nodes define their behavior through YAML files rather than imperative code, making the system more maintainable and less error-prone.

The `init_messages()` method automatically configures all pub/sub relationships, eliminating a major source of bugs and configuration drift.

---

*Built with the principle of preserving what works while adding modern framework capabilities.*