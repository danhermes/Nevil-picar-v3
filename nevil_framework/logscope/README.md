# Nevil v3 LogScope

LogScope is an advanced desktop log monitoring dashboard for Nevil v3 that provides real-time log visualization, filtering, and analysis capabilities.

## Features

### Core Features
- **Real-time log streaming** with pause/resume functionality
- **Multi-pane view** (unified and per-node)
- **Advanced filtering** by log level and node type
- **Live search** with regex support and highlighting
- **Node health indicators** with visual status LEDs
- **Keyboard shortcuts** for efficient operation

### Special Modes
- **Crash Monitor Mode** - Focused error analysis showing only ERROR/CRITICAL logs and crash-related entries
- **Dialogue Mode** - Filter to show only speech TTS and STT related logs (NEW FEATURE!)
- **Performance metrics** and statistics display

### Dialogue Mode
The new Dialogue Mode filters logs to show only speech-related activities:
- Logs from `speech_recognition` and `speech_synthesis` nodes
- Messages containing speech-related keywords: 'speech', 'tts', 'stt', 'audio', 'voice', 'whisper', etc.
- Perfect for monitoring conversation flow and speech processing

## Installation

### System Requirements
- Python 3.9+
- PyQt6 (or PyQt5 as fallback)
- watchdog library for file monitoring

### Install Dependencies
```bash
# On Debian/Ubuntu systems:
sudo apt-get install python3-pyqt6 python3-watchdog

# Or using pip in a virtual environment:
pip install PyQt6 watchdog
```

## Usage

### GUI Application
Launch the full desktop GUI:
```bash
python3 -m nevil_framework.logscope.launcher --log-dir logs
```

**Command Line Options:**
- `--log-dir PATH` - Log directory to monitor (default: logs)
- `--max-entries INT` - Maximum entries in memory (default: 10000)
- `--theme [dark|light]` - UI theme (default: dark)

### CLI Tool (Headless)
For headless environments or quick log analysis:

**Real-time monitoring:**
```bash
python3 -m nevil_framework.logscope.cli --dialogue  # Dialogue mode
python3 -m nevil_framework.logscope.cli --crash     # Crash monitor mode
```

**Search existing logs:**
```bash
python3 -m nevil_framework.logscope.cli --search "TTS" --max-results 10 search
python3 -m nevil_framework.logscope.cli --dialogue --count search
python3 -m nevil_framework.logscope.cli --levels ERROR CRITICAL search
```

### Testing Parser
Test log parsing functionality:
```bash
python3 /home/dan/Nevil-picar-v3/nevil_framework/logscope/test_parser.py logs
```

## Keyboard Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+F` | Focus Search | Jump to search box |
| `Ctrl+1-5` | Toggle Log Levels | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `F1-F4` | Toggle Nodes | System, Speech Rec, Speech Syn, AI Cognition |
| `Space` or `P` | Pause/Resume | Toggle live log streaming |
| `A` | Auto-scroll | Toggle auto-scroll to bottom |
| `Ctrl+L` | Clear | Clear all visible log entries |
| `Ctrl+Shift+C` | Crash Monitor | Toggle Crash Monitor Mode |
| `Ctrl+Shift+D` | Dialogue Mode | Toggle Dialogue Mode (NEW!) |

## Architecture

LogScope implements a multi-threaded architecture:
```
File System → Watchdog Monitor → Queue → GUI Thread → Display Views
     ↓              ↓              ↓         ↓           ↓
   Log Files → File Events → Entry Queue → Processing → Multi-Tab UI
```

### Core Components
- **File Monitor**: Background thread using watchdog library
- **Log Parser**: Structured parsing of EST-formatted log entries
- **Filter Engine**: Multi-criteria filtering with special modes
- **GUI Controller**: PyQt-based interface with responsive updates
- **View Manager**: Tabbed interface for unified and node-specific views

## Integration with Nevil v3

LogScope automatically monitors the `logs/` directory where Nevil v3 writes log files:
- `system.log` - Framework and system-level messages
- `speech_recognition.log` - Audio input and recognition logs
- `speech_synthesis.log` - TTS and audio output logs
- `ai_cognition.log` - AI processing and decision logs
- `navigation.log` - Robot movement and action logs

## Log Format Support

LogScope parses logs in EST format:
```
[TIMESTAMP EST] [LEVEL] [NODE] [COMPONENT] MESSAGE
```

Example:
```
[2025-09-15 17:01:16,643 EST] [INFO] [speech_synthesis] [MainThread] Processing TTS: 'Hello!' (voice: onyx)
```

## Performance

- **Memory Management**: Configurable entry limit (default: 10,000)
- **Update Batching**: 50 entries per 100ms update cycle
- **Thread Safety**: Queue-based communication between monitor and GUI
- **Efficient Filtering**: Real-time filtering with minimal performance impact

## Troubleshooting

### Common Issues
1. **PyQt Not Found**: Install with `sudo apt-get install python3-pyqt6`
2. **Log Directory Not Found**: Ensure Nevil v3 has created log files first
3. **High Memory Usage**: Reduce `--max-entries` parameter
4. **Display Issues**: Use CLI mode for headless environments

### Debug Mode
```bash
LOGSCOPE_DEBUG=1 python3 -m nevil_framework.logscope.launcher
```

## Examples

### Monitor Only Speech Processing
```bash
# GUI with dialogue mode (use Ctrl+Shift+D hotkey)
python3 -m nevil_framework.logscope.launcher

# CLI dialogue mode
python3 -m nevil_framework.logscope.cli --dialogue

# Search for TTS activities
python3 -m nevil_framework.logscope.cli --search "TTS" search
```

### Focus on Errors and Crashes
```bash
# GUI with crash mode (use Ctrl+Shift+C hotkey)
python3 -m nevil_framework.logscope.launcher

# CLI crash mode
python3 -m nevil_framework.logscope.cli --crash

# Count error entries
python3 -m nevil_framework.logscope.cli --levels ERROR CRITICAL --count search
```

### Real-time Monitoring
```bash
# Monitor all logs in real-time
python3 -m nevil_framework.logscope.cli

# Monitor specific nodes
python3 -m nevil_framework.logscope.cli --nodes speech_recognition speech_synthesis
```

LogScope provides a powerful alternative to parsing monolithic system.log files, offering a modern GUI experience with comprehensive monitoring features for Nevil v3 development and debugging.