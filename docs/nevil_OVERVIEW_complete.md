# NEVIL FRAMEWORK - OFFICIAL OVERVIEW
**Version 3.0**
**Document Date:** November 10, 2025
**Copyright Notice:** All rights reserved.

---

## CREATIVE OWNERSHIP & COPYRIGHT

This document serves as an official declaration of creative ownership for the Nevil Framework (hereinafter "the Framework"). The Framework, including all source code, architecture, documentation, and associated intellectual property, is the original creative work of **Daniel [Last Name]** (hereinafter "the Owner").

**Copyright Year:** 2025
**Owner:** Daniel [Last Name]
**Framework Name:** Nevil Framework v3.0
**Repository:** Nevil-picar-v3

The Framework constitutes a unique, original work of authorship encompassing custom software architecture, novel integration methodologies, proprietary gesture choreography, and distinctive AI personality systems. All rights, title, and interest in and to the Framework remain exclusively with the Owner.

---

## I. BUSINESS DESCRIPTION

### 1.1 Overview

The **Nevil Framework v3.0** is a proprietary robotics software platform designed to create AI-powered, personality-driven companion robots. The Framework transforms the PiCar-X hardware platform (Raspberry Pi-based robotic vehicle) into an autonomous interactive companion capable of natural conversation, expressive physical movement, and environment-aware behavior.

### 1.2 Business Value Proposition

**Core Value:** Delivering an engaging, personality-rich robotic companion that combines artificial intelligence cognition with expressive physical embodiment, creating meaningful human-robot interaction experiences.

**Key Differentiators:**
- **AI-Driven Autonomy:** 100% GPT-powered decision-making with no hardcoded behavioral sequences
- **Expressive Movement Library:** 106+ proprietary choreographed gestures enabling nuanced emotional expression
- **Personality Architecture:** 8 distinct mood states with configurable behavioral parameters
- **Maintainable Design:** Declarative configuration-based architecture replacing complex ROS2 dependencies
- **Voice Interaction:** Natural conversation capabilities using OpenAI Whisper and GPT-4o integration

### 1.3 Target Application

**Primary Use Case:** Desktop companion robot ("Nevil") providing entertainment, interaction, and personality-driven autonomous behavior for personal and educational environments.

**Market Position:** Custom companion robotics platform emphasizing personality expression and AI-driven behavior over pure utility functions.

### 1.4 Product Philosophy

*"Simple architecture = working robot"*

The Framework prioritizes reliability, maintainability, and expressive capability over architectural complexity. Version 3.0 represents a strategic architectural shift from ROS2-based v2.0 to a lightweight custom messaging system, while preserving proven audio components from v1.0.

---

## II. TECHNICAL ARCHITECTURE

### 2.1 System Architecture

**Architecture Pattern:** Node-based publish-subscribe messaging system with declarative configuration management.

**Core Framework Components:**
- **Message Bus** ([message_bus.py](nevil_framework/message_bus.py)) - Thread-safe pub/sub messaging using Python queues
- **Base Node Class** ([base_node.py](nevil_framework/base_node.py)) - Abstract node implementation with declarative messaging
- **Launcher** ([launcher.py](nevil_framework/launcher.py)) - Node lifecycle and dependency management
- **Configuration Loader** ([config_loader.py](nevil_framework/config_loader.py)) - YAML-based configuration with validation

**Key Architectural Principles:**
1. **Declarative Messaging:** Nodes define pub/sub relationships in `.messages` YAML files, eliminating imperative subscription code
2. **Process Isolation:** Independent node processes with multiprocessing queue-based communication
3. **Graceful Degradation:** Health monitoring and automatic recovery mechanisms
4. **Configuration-Driven:** YAML-based system configuration with environment variable expansion

### 2.2 Active Node System

The Framework implements six primary nodes:

#### 2.2.1 Speech Recognition Node ([nodes/speech_recognition/](nodes/speech_recognition/))
- **Function:** Voice input processing using OpenAI Whisper
- **Key Features:** Microphone mutex management, audio level monitoring, listening status broadcast
- **Integration:** Publishes `voice_command`, subscribes to `system_mode`, `speaking_status`, `navigation_status`

#### 2.2.2 Speech Synthesis Node ([nodes/speech_synthesis/](nodes/speech_synthesis/))
- **Function:** Text-to-speech output using OpenAI TTS-1-HD
- **Key Features:** Music() playback system (v1.0 proven), sound effect management, speaking status broadcast
- **Integration:** Publishes `speaking_status`, subscribes to `text_response`, `tts_request`, `sound_effect`

#### 2.2.3 AI Cognition Node ([nodes/ai_cognition/](nodes/ai_cognition/))
- **Function:** Conversational AI and behavioral decision-making using GPT-4o
- **Key Features:** 8-mood personality system, vision integration, gesture command generation
- **Integration:** Publishes `text_response`, `robot_action`, `mood_change`, subscribes to `voice_command`, `visual_data`

#### 2.2.4 Navigation Node ([nodes/navigation/](nodes/navigation/))
- **Function:** Movement execution, gesture choreography, autonomous behavior
- **Key Features:** 106+ extended gestures, obstacle avoidance, 3-speed modifiers (:slow, :med, :fast)
- **Integration:** Publishes `navigation_status`, `auto_mode_status`, subscribes to `robot_action`, `mood_change`

#### 2.2.5 Visual Node ([nodes/visual/](nodes/visual/))
- **Function:** Camera capture and image management
- **Integration:** Publishes `visual_data`, subscribes to `snap_pic`

#### 2.2.6 LED Indicator Node ([nodes/led_indicator/](nodes/led_indicator/))
- **Function:** Visual status indication via LED patterns
- **Integration:** Subscribes to `system_mode`, `speaking_status`, `listening_status`, `auto_mode_status`

### 2.3 Technology Stack

**Primary Platform:**
- Python 3.x on Raspberry Pi 4/5 (ARM/Linux)
- robot_hat library (SunFounder PiCar-X hardware control)

**AI Services:**
- OpenAI GPT-4o (conversation and autonomous decision-making)
- OpenAI Whisper (speech-to-text)
- OpenAI TTS-1-HD (text-to-speech)
- OpenAI Vision API (image analysis)

**Audio Stack:**
- pygame (audio playback via Music())
- pyaudio (microphone input)
- HiFiBerry DAC (audio output hardware)

**Dependencies:**
- PyYAML (configuration management)
- python-dateutil (timestamp utilities)

### 2.4 Hardware Integration

**PiCar-X Platform Components:**
- 2x DC motors (rear-wheel drive locomotion)
- 3x Servos (steering, camera pan, camera tilt)
- Ultrasonic distance sensor (obstacle detection)
- 3x Grayscale sensors (line following capability)
- Camera (PiCamera or USB webcam)
- USB microphone
- HiFiBerry DAC speaker
- Status LED

**Hardware Abstraction Layer:** [picarx.py](nodes/navigation/picarx.py) provides calibrated servo control, motor management, and sensor interface.

### 2.5 Proprietary Extended Gesture System

The Framework includes 106+ proprietary choreographed movements categorized as:

- **Observation** (15 gestures): look_left_then_right, inspect_floor, curious_peek, alert_scan, etc.
- **Movement** (16 gestures): circle_dance, zigzag, moonwalk, figure_eight, etc.
- **Reactions** (13 gestures): recoil_surprise, confused_tilt, show_surprise, etc.
- **Social** (14 gestures): bow_respectfully, greet_wave, hello_friend, etc.
- **Celebration** (7 gestures): spin_celebrate, jump_excited, victory_pose, etc.
- **Emotional** (15 gestures): show_curiosity, peekaboo, ponder, dreamy_stare, etc.
- **Functional** (12 gestures): sleep_mode, yawn, stretch, listen_close, etc.
- **Signaling** (10 gestures): acknowledge_signal, error_shrug, signal_complete, etc.
- **Advanced** (4 gestures): approach_slowly, quick_look_left, etc.

**Implementation:** [extended_gestures.py](nodes/navigation/extended_gestures.py) (3,349 lines)

Each gesture supports speed modifiers (:slow, :med, :fast) for behavioral nuance.

### 2.6 Personality Architecture

**8 Mood States with Behavioral Parameters:**

1. **playful** - Energetic, social, whimsical (90% energy, 60% speech rate)
2. **brooding** - Quiet, introspective, withdrawn (30% energy, 20% speech rate)
3. **curious** - Investigative, observational (60% energy, 50% speech rate)
4. **melancholic** - Slow, gentle, wistful (20% energy, 25% speech rate)
5. **zippy** - Fast, bouncy, impatient (95% energy, 65% speech rate)
6. **lonely** - Seeks interaction, patient (50% energy, 55% speech rate)
7. **mischievous** - Playful but sneaky (85% energy, 60% speech rate)
8. **sleepy** - Minimal activity, quiet (15% energy, 15% speech rate)

**Mood Persistence:** 15-30 behavioral cycles per mood for stable personality periods.

**Implementation:** [automatic.py](nodes/navigation/automatic.py) autonomous behavior system with mood-specific interaction patterns.

### 2.7 Microphone Mutex System

Proprietary audio resource management preventing audio feedback and servo noise interference:

- Speech synthesis **blocks** speech recognition (prevents self-talk)
- Navigation movement **blocks** speech recognition (blocks servo noise)
- Speech synthesis and navigation can run in parallel
- Automatic locking/unlocking via context managers

**Implementation:** [microphone_mutex.py](nevil_framework/microphone_mutex.py)

### 2.8 Message Bus Topics

**Primary Communication Topics:**
- `voice_command` - User speech input
- `text_response` - AI-generated responses
- `robot_action` - Movement/gesture commands
- `visual_data` - Camera images with metadata
- `snap_pic` - Camera capture requests
- `system_mode` - System state changes (listening, speaking, thinking, idle, error)
- `mood_change` - Personality state transitions
- `auto_mode_status` - Autonomous behavior state
- `sound_effect` - Audio effect playback requests
- `speaking_status` - TTS state broadcasts
- `listening_status` - STT state broadcasts
- `navigation_status` - Movement execution status

---

## III. INTELLECTUAL PROPERTY COMPONENTS

### 3.1 Original Creative Works

The following components constitute original creative works protected by copyright:

1. **Framework Architecture** - Custom node-based messaging system with declarative configuration
2. **Extended Gesture Choreography** - 106+ movement sequences with timing and servo coordination
3. **Personality System** - 8-mood behavioral architecture with quantified parameters
4. **Autonomous Behavior Logic** - AI-driven decision-making patterns and interaction flows
5. **Microphone Mutex System** - Audio resource management methodology
6. **Configuration Schema** - YAML-based declarative messaging and node configuration system
7. **Hardware Abstraction Layer** - Custom PiCar-X interface with calibration management

### 3.2 Third-Party Components

The Framework integrates the following third-party technologies under their respective licenses:

- **Python** (PSF License)
- **OpenAI API** (Commercial API service)
- **robot_hat library** (SunFounder, MIT License)
- **PyYAML** (MIT License)
- **pygame** (LGPL)
- **pyaudio** (MIT License)

The Owner retains all rights to original integration methodologies, configuration, and architectural implementations using these components.

---

## IV. SYSTEM CAPABILITIES

### 4.1 Core Capabilities

- Natural language conversation with personality-driven responses
- 106+ expressive physical gestures with speed variation
- Autonomous behavior with mood-based decision-making
- Voice-activated command processing
- Environment-aware navigation with obstacle avoidance
- Vision-integrated responses (70% usage when speaking, 35% when silent)
- Sound effect playback (vehicle, musical, spooky, alien, voice categories)
- LED status indication with pattern-based feedback

### 4.2 Operational Modes

- **Interactive Mode:** Voice-activated conversation with gesture responses
- **Autonomous Mode:** Self-directed behavior based on current mood state
- **Sleep Mode:** Minimal activity conservation state
- **Error Recovery:** Automatic node restart and health monitoring

---

## V. DOCUMENTATION STRUCTURE

**Primary Documentation:**
- [Architecture Overview](nevil_v3/ARCHITECTURE.md) - System design and component relationships
- [Message Bus Documentation](nevil_v3/message_bus.md) - Pub/sub messaging system
- [Node Development Guide](nevil_v3/node_guide.md) - Creating custom nodes
- [Gesture Reference](nevil_v3/extended_gestures.md) - Complete gesture catalog

**Repository Structure:**
- `/nevil_framework/` - Core framework implementation
- `/nodes/` - Active node implementations
- `/audio/` - Audio system components
- `/docs/` - Documentation and specifications
- `/.nodes` - System node configuration
- `/.env` - Environment configuration

---

## VI. VERSION HISTORY

**v3.0 (Current)** - Lightweight custom messaging architecture, 106+ gestures, 8-mood personality system
**v2.0** - ROS2-based architecture (deprecated due to complexity)
**v1.0** - Initial implementation with proven audio components

---

## VII. LEGAL NOTICES

### 7.1 Copyright Statement

Copyright (c) 2025 Daniel [Last Name]. All rights reserved.

This software and associated documentation files (the "Framework") are the proprietary and confidential intellectual property of the Owner. Unauthorized copying, modification, distribution, or use of this Framework, via any medium, is strictly prohibited without express written permission from the Owner.

### 7.2 Restrictions

No license, express or implied, by estoppel or otherwise, to any intellectual property rights is granted by this document. The Framework is provided "as is" without warranty of any kind, express or implied.

### 7.3 Attribution

Any authorized use of the Framework must include attribution to the Owner and reference to this overview document.

---

**END OF DOCUMENT**

*This overview serves as an official record of creative ownership and technical specification for the Nevil Framework v3.0. For inquiries regarding licensing, collaboration, or authorized use, contact the Owner at [contact information].*
