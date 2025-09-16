# LogScope Quick Usage Guide

**✨ NEW: Whole-screen layout maximizes message display area!**
- Compact toolbar and minimal side panel
- Messages use ~90% of screen space
- Same powerful features in space-efficient design

## 🚀 Quick Start

### GUI Mode (Recommended)
```bash
python3 -m nevil_framework.logscope.launcher
```

### CLI Mode (Headless)
```bash
python3 -m nevil_framework.logscope.cli
```

## 🎯 Common Use Cases

### Monitor Speech Processing
```bash
# GUI: Press Ctrl+Shift+D or click "💬 Dialogue Mode" button
python3 -m nevil_framework.logscope.cli --dialogue
```

### Find Errors/Crashes
```bash
# GUI: Press Ctrl+Shift+C or click "🚨 Crash Monitor" button
python3 -m nevil_framework.logscope.cli --crash
```

### Search Logs
```bash
# Search for specific text
python3 -m nevil_framework.logscope.cli --search "OpenAI" search

# Count matching entries
python3 -m nevil_framework.logscope.cli --search "TTS" --count search
```

### Filter by Level/Node
```bash
# Show only errors
python3 -m nevil_framework.logscope.cli --levels ERROR CRITICAL

# Monitor specific nodes
python3 -m nevil_framework.logscope.cli --nodes speech_recognition ai_cognition
```

## ⌨️ GUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Shift+D` | **Dialogue Mode** (speech only) |
| `Ctrl+Shift+C` | **Crash Monitor** (errors only) |
| `Ctrl+F` | Focus search box |
| `Ctrl+1-5` | Toggle log levels (DEBUG→CRITICAL) |
| `F1-F4` | Toggle nodes (System/Speech/AI/Nav) |
| `Space` or `P` | Pause/resume live stream |
| `Ctrl+L` | Clear logs |

## 🔍 Search Examples

```bash
# Find TTS activities
python3 -m nevil_framework.logscope.cli --search "TTS" search

# Find API errors
python3 -m nevil_framework.logscope.cli --search "API.*error" search

# Count speech recognition events
python3 -m nevil_framework.logscope.cli --nodes speech_recognition --count search

# Monitor errors in real-time
python3 -m nevil_framework.logscope.cli --levels ERROR CRITICAL
```

## 🎛️ GUI Features

### Compact Toolbar (Maximizes Message Area)
- **💬** - Dialogue Mode (speech/TTS/STT only)
- **🚨** - Crash Monitor (errors only)
- **⏸️** - Pause/Resume live updates
- **🗑️** - Clear current display
- **Search box** - Live filtering
- **Stats** - Entry counts and rate

### Tabs
- **🔄 Unified** - All logs merged chronologically
- **🖥️ System** - Framework logs
- **🎤 Speech Rec** - Speech recognition logs
- **🔊 Speech Syn** - Text-to-speech logs
- **🧠 AI Cognition** - AI processing logs

### Compact Side Panel (Minimal Width)
- **Node checkboxes** - System, Speech..., Speech..., Ai Cogn...
- **Level checkboxes** - DEBU, INFO, WARN, ERRO, CRIT
- **Hover tooltips** - Full names and hotkeys
- **Color coding** - Level-based colors

## 🔧 Command Options

### GUI Launcher
```bash
python3 -m nevil_framework.logscope.launcher [OPTIONS]

--log-dir PATH       Log directory (default: logs)
--max-entries INT    Memory limit (default: 10000)
--theme dark|light   UI theme (default: dark)
```

### CLI Tool
```bash
python3 -m nevil_framework.logscope.cli [OPTIONS] [COMMAND]

--log-dir PATH           Log directory
--levels LEVEL [...]     Filter: DEBUG INFO WARNING ERROR CRITICAL
--nodes NODE [...]       Filter: system speech_recognition speech_synthesis ai_cognition
--search TEXT            Search in messages
--dialogue               Show only speech-related logs
--crash                  Show only error/crash logs
--no-color              Disable colored output
--count                 Count matches only
--max-results INT       Limit results

COMMANDS:
  tail     Monitor in real-time (default)
  search   Search existing logs
```

## 💡 Pro Tips

1. **Use Dialogue Mode** to focus on conversation flow
2. **Pause on scroll** - scrolling up auto-pauses updates
3. **Combine filters** - use levels + nodes + search together
4. **CLI for automation** - integrate into scripts and monitoring
5. **Search with regex** - enable regex mode for complex patterns

## 🐛 Quick Troubleshooting

```bash
# Test if parsing works
python3 nevil_framework/logscope/test_parser.py logs

# Check dependencies
python3 -c "import PyQt6; import watchdog; print('Dependencies OK')"

# Run in headless mode
python3 -m nevil_framework.logscope.cli --count search
```

## Examples for Your Nevil Robot

### Monitor Conversation Flow
```bash
# See all speech activity
python3 -m nevil_framework.logscope.cli --dialogue

# Find specific phrases
python3 -m nevil_framework.logscope.cli --search "Hello" --dialogue search
```

### Debug Robot Issues
```bash
# Check for hardware errors
python3 -m nevil_framework.logscope.cli --nodes navigation --crash

# Monitor AI responses
python3 -m nevil_framework.logscope.cli --nodes ai_cognition --levels INFO
```

### System Health Check
```bash
# Count recent errors
python3 -m nevil_framework.logscope.cli --crash --count search

# Monitor live system status
python3 -m nevil_framework.logscope.cli --levels WARNING ERROR CRITICAL
```