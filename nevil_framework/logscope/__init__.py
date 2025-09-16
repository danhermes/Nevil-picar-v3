"""
Nevil v3 LogScope - Advanced Log Monitoring Dashboard

LogScope provides a comprehensive desktop GUI for monitoring Nevil v3 system logs
in real-time with advanced filtering, search, and visualization capabilities.

Key Features:
- Real-time log streaming with pause/resume
- Multi-pane view (unified and per-node)
- Advanced filtering by log level and node type
- Live search with regex support and highlighting
- Crash Monitor Mode for focused error analysis
- Dialogue Mode for speech-related logs only
- Node health indicators
- Keyboard shortcuts for efficient operation

Usage:
    python -m nevil_framework.logscope.launcher
"""

__version__ = "3.0.0"
__author__ = "Nevil Framework Team"

from .main_window import NevilLogScope

__all__ = ['NevilLogScope']