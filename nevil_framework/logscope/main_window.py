import sys
import threading
import queue
import re
from typing import Dict, List, Set, Optional
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from PyQt5.QtWidgets import *
        from PyQt5.QtCore import *
        from PyQt5.QtGui import *
        PYQT_AVAILABLE = True
    except ImportError:
        PYQT_AVAILABLE = False

class NevilLogScope(QMainWindow):
    """
    Advanced desktop log monitoring dashboard for Nevil v3.

    Features:
    - Multi-pane view (unified, per-node, system)
    - Real-time live streaming with pause/resume
    - Keystroke-based filtering (Ctrl+1-5 for levels, F1-F4 for nodes)
    - Live search with colored highlighting
    - Pause on scroll, resume on hotkey
    - Node health indicators
    - Performance metrics overlay
    """

    # Custom signals for thread-safe GUI updates
    new_log_entry = pyqtSignal(dict)
    node_status_changed = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()

        # Application state
        self.log_dir = Path("logs")
        self.running = False
        self.paused = False
        self.auto_scroll = True

        # Filtering state
        self.active_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        self.active_nodes = {'system', 'ai_cognition_realtime', 'speech_recognition_realtime', 'speech_synthesis_realtime', 'visual', 'navigation'}
        self.search_pattern = ""
        self.search_regex = None
        self.crash_monitor_mode = False  # Crash Monitor Mode
        self.dialogue_mode = False  # Dialogue Mode - filter to show only speech TTS and STT

        # Data storage
        self.log_entries = []  # All entries
        self.filtered_entries = []  # Currently visible entries
        self.max_entries = 10000  # Memory limit

        # Threading
        self.monitor_thread = None
        self.update_queue = queue.Queue()

        # UI components (initialize before creating UI)
        self.level_checkboxes = {}
        self.node_indicators = {}

        # Setup UI
        self.init_ui()
        self.init_hotkeys()
        self.init_monitoring()

        # Start log monitoring
        self.start_monitoring()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Nevil v3 LogScope - Real-time Log Monitor")
        self.setGeometry(100, 100, 1600, 1000)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins

        # Compact toolbar
        self.create_compact_toolbar(main_layout)

        # Create horizontal splitter for main content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Compact control panel (minimal width)
        self.create_compact_control_panel(main_splitter)

        # Log displays - uses most of the screen
        self.create_log_panels(main_splitter)

        # Set proportions - sufficient space for controls, maximum for messages
        main_splitter.setSizes([250, 1350])  # 250px for controls, 1350px for logs

        # Compact status bar
        self.create_status_bar()

    def create_compact_toolbar(self, layout):
        """Create compact toolbar with essential controls"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)  # Better spacing for visibility

        # Search box (smaller)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.on_search_changed)
        self.search_box.returnPressed.connect(self.focus_next_match)

        # Set tooltip style for all widgets
        QApplication.instance().setStyleSheet("""
            QToolTip {
                background-color: #f8f8f8;
                color: #999999;
                border: none;
                padding: 4px;
                font-size: 12px;
            }
        """)

        # Compact mode buttons with text labels
        self.dialogue_mode_button = QPushButton("Talk")
        self.dialogue_mode_button.setToolTip("Dialogue Mode - Show only speech/TTS/STT (Ctrl+Shift+D)")
        self.dialogue_mode_button.clicked.connect(self.toggle_dialogue_mode)
        self.dialogue_mode_button.setStyleSheet(self.get_button_style())

        self.crash_monitor_button = QPushButton("Err")
        self.crash_monitor_button.setToolTip("Crash Monitor - Show errors only (Ctrl+Shift+C)")
        self.crash_monitor_button.clicked.connect(self.toggle_crash_monitor_mode)
        self.crash_monitor_button.setStyleSheet(self.get_button_style())

        self.live_button = QPushButton("||")
        self.live_button.setToolTip("Pause/Resume live updates (Space)")
        self.live_button.clicked.connect(self.toggle_pause)
        self.live_button.setStyleSheet(self.get_button_style())

        self.clear_button = QPushButton("CLR")
        self.clear_button.setToolTip("Clear all logs (Ctrl+L)")
        self.clear_button.clicked.connect(self.clear_logs)
        self.clear_button.setStyleSheet(self.get_button_style())

        # Auto-scroll button
        self.auto_scroll_button = QPushButton("Auto")
        self.auto_scroll_button.setToolTip("Toggle auto-scroll (A)")
        self.auto_scroll_button.clicked.connect(self.toggle_auto_scroll)
        self.auto_scroll_button.setStyleSheet(self.get_active_button_style() if self.auto_scroll else self.get_button_style())

        # Stats label (compact)
        self.stats_label = QLabel("Entries: 0 | Filtered: 0")
        self.stats_label.setStyleSheet("font-family: monospace; font-size: 10px; color: #888;")

        # Layout with all buttons
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_box)
        toolbar_layout.addWidget(self.dialogue_mode_button)
        toolbar_layout.addWidget(self.crash_monitor_button)
        toolbar_layout.addWidget(self.live_button)
        toolbar_layout.addWidget(self.auto_scroll_button)
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.stats_label)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        toolbar_widget.setMaximumHeight(50)  # Slightly taller for better button visibility
        toolbar_widget.setStyleSheet("background-color: #2a2a2a; border-bottom: 2px solid #555;")
        layout.addWidget(toolbar_widget)

    def create_toolbar(self, layout):
        """Create top toolbar with search and controls"""
        toolbar_layout = QHBoxLayout()

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search logs... (Ctrl+F)")
        self.search_box.textChanged.connect(self.on_search_changed)
        self.search_box.returnPressed.connect(self.focus_next_match)

        # Search controls
        self.search_case_sensitive = QCheckBox("Case Sensitive")
        self.search_regex_mode = QCheckBox("Regex")

        # Live controls
        self.live_button = QPushButton("⏸️ Pause" if not self.paused else "▶️ Resume")
        self.live_button.clicked.connect(self.toggle_pause)

        self.auto_scroll_button = QPushButton("📜 Auto-scroll ON" if self.auto_scroll else "📜 Auto-scroll OFF")
        self.auto_scroll_button.clicked.connect(self.toggle_auto_scroll)

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_logs)

        self.crash_monitor_button = QPushButton("🚨 Crash Monitor OFF")
        self.crash_monitor_button.clicked.connect(self.toggle_crash_monitor_mode)
        self.crash_monitor_button.setStyleSheet("QPushButton { font-weight: bold; }")

        self.dialogue_mode_button = QPushButton("💬 Dialogue Mode OFF")
        self.dialogue_mode_button.clicked.connect(self.toggle_dialogue_mode)
        self.dialogue_mode_button.setStyleSheet("QPushButton { font-weight: bold; }")

        # Add to layout
        toolbar_layout.addWidget(QLabel("Search:"))
        toolbar_layout.addWidget(self.search_box)
        toolbar_layout.addWidget(self.search_case_sensitive)
        toolbar_layout.addWidget(self.search_regex_mode)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.crash_monitor_button)
        toolbar_layout.addWidget(self.dialogue_mode_button)
        toolbar_layout.addWidget(self.live_button)
        toolbar_layout.addWidget(self.auto_scroll_button)
        toolbar_layout.addWidget(self.clear_button)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        layout.addWidget(toolbar_widget)

    def create_control_panel(self, splitter):
        """Create left control panel"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Node status indicators
        control_layout.addWidget(QLabel("Node Status:"))
        self.node_indicators = {}

        for node in ['system', 'ai_cognition_realtime', 'speech_recognition_realtime', 'speech_synthesis_realtime', 'visual', 'navigation']:
            indicator_layout = QHBoxLayout()

            # Status LED
            status_led = QLabel("🟢")  # Green by default
            status_led.setFixedSize(20, 20)
            self.node_indicators[node] = status_led

            # Node name and checkbox
            checkbox = QCheckBox(node.replace('_', ' ').title())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, n=node: self.toggle_node_filter(n, state))

            # Hotkey label
            hotkey_map = {'system': 'F1', 'ai_cognition_realtime': 'F2', 'speech_recognition_realtime': 'F3', 'speech_synthesis_realtime': 'F4', 'visual': 'F5', 'navigation': 'F6'}
            hotkey_label = QLabel(f"({hotkey_map[node]})")
            hotkey_label.setStyleSheet("color: gray; font-size: 10px;")

            indicator_layout.addWidget(status_led)
            indicator_layout.addWidget(checkbox)
            indicator_layout.addStretch()
            indicator_layout.addWidget(hotkey_label)

            control_layout.addLayout(indicator_layout)

        control_layout.addWidget(QLabel(""))  # Spacer

        # Log level filters
        control_layout.addWidget(QLabel("Log Levels:"))
        self.level_checkboxes = {}

        level_colors = {
            'DEBUG': '#00FFFF',    # Cyan
            'INFO': '#00FF00',     # Green
            'WARNING': '#FFFF00',  # Yellow
            'ERROR': '#FF0000',    # Red
            'CRITICAL': '#FF00FF'  # Magenta
        }

        hotkey_nums = {'DEBUG': '1', 'INFO': '2', 'WARNING': '3', 'ERROR': '4', 'CRITICAL': '5'}

        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            level_layout = QHBoxLayout()

            checkbox = QCheckBox(level)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, l=level: self.toggle_level_filter(l, state))
            checkbox.setStyleSheet(f"color: {level_colors[level]}; font-weight: bold;")
            self.level_checkboxes[level] = checkbox

            hotkey_label = QLabel(f"(Ctrl+{hotkey_nums[level]})")
            hotkey_label.setStyleSheet("color: gray; font-size: 10px;")

            level_layout.addWidget(checkbox)
            level_layout.addStretch()
            level_layout.addWidget(hotkey_label)

            control_layout.addLayout(level_layout)

        control_layout.addStretch()

        splitter.addWidget(control_widget)

    def create_compact_control_panel(self, splitter):
        """Create compact control panel for maximum message space"""
        control_widget = QWidget()
        control_widget.setMaximumWidth(250)  # Wider to fit node names
        control_layout = QVBoxLayout(control_widget)
        control_layout.setSpacing(3)  # Tight spacing

        # Node filters (compact checkboxes)
        control_layout.addWidget(QLabel("Nodes:"))
        for node in ['system', 'ai_cognition_realtime', 'speech_recognition_realtime', 'speech_synthesis_realtime', 'visual', 'navigation']:
            checkbox = QCheckBox(node.replace('_', ' ').title())  # Full names, properly capitalized
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, n=node: self.toggle_node_filter(n, state))
            checkbox.setStyleSheet("font-size: 10px;")
            control_layout.addWidget(checkbox)

        control_layout.addWidget(QLabel(""))  # Small spacer

        # Level filters (compact)
        control_layout.addWidget(QLabel("Levels:"))
        level_colors = {
            'DEBUG': '#00FFFF', 'INFO': '#00FF00', 'WARNING': '#FFFF00',
            'ERROR': '#FF0000', 'CRITICAL': '#FF00FF'
        }

        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            checkbox = QCheckBox(level[:4])  # Shortened to 4 chars
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, l=level: self.toggle_level_filter(l, state))
            checkbox.setStyleSheet(f"color: {level_colors[level]}; font-size: 9px; font-weight: bold;")
            self.level_checkboxes[level] = checkbox
            control_layout.addWidget(checkbox)

        control_layout.addStretch()
        splitter.addWidget(control_widget)

    def create_log_panels(self, splitter):
        """Create main log display panels"""
        # Right side - tabbed log views
        self.tab_widget = QTabWidget()

        # Unified view - all logs merged
        self.unified_view = self.create_log_view("All Logs")
        self.tab_widget.addTab(self.unified_view, "🔄 Unified")

        # Per-node views
        self.node_views = {}
        node_tabs = [
            ("system", "🖥️ System"),
            ("ai_cognition_realtime", "🧠 AI Realtime"),
            ("speech_recognition_realtime", "🎤 STT Realtime"),
            ("speech_synthesis_realtime", "🔊 TTS Realtime"),
            ("visual", "📷 Visual"),
            ("navigation", "🧭 Navigation")
        ]

        for node_key, tab_name in node_tabs:
            view = self.create_log_view(f"{node_key} logs")
            self.node_views[node_key] = view
            self.tab_widget.addTab(view, tab_name)

        splitter.addWidget(self.tab_widget)

    def create_log_view(self, view_name):
        """Create a single log view widget"""
        view = QTextEdit()
        view.setReadOnly(True)
        view.setFont(QFont("Consolas", 10))  # Monospace font
        view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
            }
        """)

        # Enable scroll-to-pause functionality
        scrollbar = view.verticalScrollBar()
        scrollbar.valueChanged.connect(lambda: self.on_scroll_changed(view))

        return view

    def init_hotkeys(self):
        """Initialize keyboard shortcuts"""
        # Search
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)

        # Level filters (Ctrl+1-5)
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for i, level in enumerate(levels, 1):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self, lambda l=level: self.toggle_level_hotkey(l))

        # Node filters (F1-F6)
        nodes = ['system', 'ai_cognition_realtime', 'speech_recognition_realtime', 'speech_synthesis_realtime', 'visual', 'navigation']
        for i, node in enumerate(nodes, 1):
            QShortcut(QKeySequence(f"F{i}"), self, lambda n=node: self.toggle_node_hotkey(n))

        # Crash Monitor Mode
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, self.toggle_crash_monitor_mode)

        # Dialogue Mode
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, self.toggle_dialogue_mode)

        # Pause/Resume
        QShortcut(QKeySequence("Space"), self, self.toggle_pause)
        QShortcut(QKeySequence("P"), self, self.toggle_pause)

        # Clear
        QShortcut(QKeySequence("Ctrl+L"), self, self.clear_logs)

        # Auto-scroll
        QShortcut(QKeySequence("A"), self, self.toggle_auto_scroll)

    def init_monitoring(self):
        """Initialize log file monitoring"""
        # Connect signals
        self.new_log_entry.connect(self.add_log_entry)
        self.node_status_changed.connect(self.update_node_status)

        # Timer for GUI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_update_queue)
        self.update_timer.start(100)  # Update every 100ms

    def start_monitoring(self):
        """Start log file monitoring in background thread"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
        self.monitor_thread.start()

    def _monitor_logs(self):
        """Background thread for monitoring log files"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            print("Warning: watchdog not available, using polling mode")
            self._monitor_logs_polling()
            return

        class LogEventHandler(FileSystemEventHandler):
            def __init__(self, logscope):
                self.logscope = logscope
                self.file_positions = {}

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.log'):
                    self.process_log_file(event.src_path)

            def process_log_file(self, file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        last_pos = self.file_positions.get(file_path, 0)
                        f.seek(last_pos)

                        new_lines = f.readlines()
                        if new_lines:
                            self.file_positions[file_path] = f.tell()

                            for line in new_lines:
                                entry = self.parse_log_line(file_path, line.strip())
                                if entry:
                                    self.logscope.update_queue.put(('log', entry))

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

            def parse_log_line(self, file_path, line):
                """Parse log line into structured entry"""
                # Enhanced pattern for EST format
                pattern = re.compile(
                    r'\[(?P<timestamp>[^\]]+) EST\] \[(?P<level>[^\]]+)\] '
                    r'\[(?P<node>[^\]]+)\] (?:\[(?P<component>[^\]]+)\] )?'
                    r'(?P<message>.*)'
                )

                match = pattern.match(line)
                if not match:
                    return None

                return {
                    'timestamp': match.group('timestamp').strip(),
                    'level': match.group('level').strip(),
                    'node': match.group('node').strip(),
                    'component': match.group('component').strip() if match.group('component') else '',
                    'message': match.group('message').strip(),
                    'file_path': file_path,
                    'raw_line': line
                }

        observer = Observer()
        handler = LogEventHandler(self)
        observer.schedule(handler, str(self.log_dir), recursive=False)
        observer.start()

        # Load existing log content on startup (last 1000 lines from each file)
        try:
            for log_file in self.log_dir.glob("*.log"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Read last 1000 lines
                        lines = f.readlines()
                        start_line = max(0, len(lines) - 1000)

                        for line in lines[start_line:]:
                            entry = handler.parse_log_line(str(log_file), line.strip())
                            if entry:
                                self.update_queue.put(('log', entry))

                        # Set file position to end
                        handler.file_positions[str(log_file)] = f.tell()
                except Exception as e:
                    print(f"Error loading existing content from {log_file}: {e}")
        except Exception as e:
            print(f"Error loading existing logs: {e}")

        try:
            while self.running:
                threading.Event().wait(1)
        finally:
            observer.stop()
            observer.join()

    def _monitor_logs_polling(self):
        """Fallback polling mode for log monitoring"""
        import time
        file_positions = {}

        # Load existing log content on startup (last 1000 lines from each file)
        try:
            log_files = list(self.log_dir.glob("*.log"))
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        # Read last 1000 lines
                        lines = f.readlines()
                        start_line = max(0, len(lines) - 1000)

                        for line in lines[start_line:]:
                            entry = self._parse_log_line_simple(str(log_file), line.strip())
                            if entry:
                                self.update_queue.put(('log', entry))

                        # Set file position to end
                        file_positions[str(log_file)] = f.tell()
                except Exception as e:
                    print(f"Error loading existing content from {log_file}: {e}")
        except Exception as e:
            print(f"Error loading existing logs: {e}")

        while self.running:
            try:
                log_files = list(self.log_dir.glob("*.log"))
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            last_pos = file_positions.get(str(log_file), 0)
                            f.seek(last_pos)

                            new_lines = f.readlines()
                            if new_lines:
                                file_positions[str(log_file)] = f.tell()

                                for line in new_lines:
                                    entry = self._parse_log_line_simple(str(log_file), line.strip())
                                    if entry:
                                        self.update_queue.put(('log', entry))
                    except Exception as e:
                        print(f"Error processing {log_file}: {e}")

                time.sleep(1)  # Poll every second
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(5)

    def _parse_log_line_simple(self, file_path, line):
        """Simple log line parser"""
        # Use same regex pattern as watchdog handler for consistency
        pattern = re.compile(
            r'\[(?P<timestamp>[^\]]+) EST\] \[(?P<level>[^\]]+)\] '
            r'\[(?P<node>[^\]]+)\] (?:\[(?P<component>[^\]]+)\] )?'
            r'(?P<message>.*)'
        )

        match = pattern.match(line)
        if not match:
            return None

        return {
            'timestamp': match.group('timestamp').strip(),
            'level': match.group('level').strip(),
            'node': match.group('node').strip(),
            'component': match.group('component').strip() if match.group('component') else '',
            'message': match.group('message').strip(),
            'file_path': file_path,
            'raw_line': line
        }

    def process_update_queue(self):
        """Process queued updates from monitoring thread"""
        processed = 0
        while not self.update_queue.empty() and processed < 50:  # Limit batch size
            try:
                update_type, data = self.update_queue.get_nowait()
                if update_type == 'log':
                    self.new_log_entry.emit(data)
                processed += 1
            except queue.Empty:
                break

    def add_log_entry(self, entry):
        """Add new log entry to displays"""
        if self.paused:
            return

        # Add to storage
        self.log_entries.append(entry)

        # Trim if too many entries
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]

        # Check if entry passes filters
        if self.passes_filters(entry):
            self.filtered_entries.append(entry)

            # Add to appropriate views
            formatted_line = self.format_log_entry(entry)

            # Unified view
            self.append_to_view(self.unified_view, formatted_line, entry)

            # Node-specific view
            if entry['node'] in self.node_views:
                self.append_to_view(self.node_views[entry['node']], formatted_line, entry)

        # Update statistics
        self.update_statistics()

    def format_log_entry(self, entry):
        """Format log entry for display with colors"""
        timestamp = entry['timestamp']
        level = entry['level']
        node = entry['node']
        component = entry['component']
        message = entry['message']

        # Color codes
        level_colors = {
            'DEBUG': '#00FFFF',    # Cyan
            'INFO': '#00FF00',     # Green
            'WARNING': '#FFFF00',  # Yellow
            'ERROR': '#FF0000',    # Red
            'CRITICAL': '#FF00FF'  # Magenta
        }

        node_colors = {
            'system': '#0080FF',                    # Blue
            'ai_cognition_realtime': '#FF80FF',     # Light Magenta
            'speech_recognition_realtime': '#40FFFF', # Light Cyan
            'speech_synthesis_realtime': '#80FF80',   # Light Green
            'visual': '#FFB347',                    # Peach/Orange
            'navigation': '#9370DB',                # Medium Purple
        }

        level_color = level_colors.get(level, '#FFFFFF')
        node_color = node_colors.get(node, '#FFFFFF')

        # Build formatted line
        formatted = f'<span style="color: #AAAAAA;">[{timestamp} EST]</span> '
        formatted += f'<span style="color: {level_color}; font-weight: bold;">[{level:8}]</span> '
        formatted += f'<span style="color: {node_color};">[{node:15}]</span> '
        if component:
            formatted += f'<span style="color: #CCCCCC;">[{component:20}]</span> '
        formatted += f'<span style="color: #FFFFFF;">{message}</span>'

        return formatted

    def append_to_view(self, view, formatted_line, entry):
        """Append formatted line to a view with search highlighting"""
        if self.search_pattern and self.search_regex:
            # Highlight search matches
            highlighted = self.highlight_search_matches(formatted_line, entry)
            view.append(highlighted)
        else:
            view.append(formatted_line)

        # Auto-scroll if enabled and view is active
        if self.auto_scroll:
            scrollbar = view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def highlight_search_matches(self, formatted_line, entry):
        """Highlight search matches in the formatted line"""
        if not self.search_regex:
            return formatted_line

        try:
            # Search in the raw message for matches
            message = entry['message']
            matches = list(self.search_regex.finditer(message))

            if matches:
                # Highlight matches with yellow background
                highlighted_message = message
                offset = 0
                for match in matches:
                    start, end = match.span()
                    start += offset
                    end += offset

                    replacement = f'<span style="background-color: #FFFF00; color: #000000;">{message[match.start():match.end()]}</span>'
                    highlighted_message = highlighted_message[:start] + replacement + highlighted_message[end:]
                    offset += len(replacement) - (end - start)

                # Replace message in formatted line
                return formatted_line.replace(f'>{message}</span>', f'>{highlighted_message}</span>')

        except Exception as e:
            print(f"Search highlighting error: {e}")

        return formatted_line

    def passes_filters(self, entry):
        """Check if entry passes current filters"""
        # Crash Monitor Mode - overrides other filters
        if self.crash_monitor_mode:
            return self._is_crash_related(entry)

        # Dialogue Mode - filter to show only speech-related entries
        if self.dialogue_mode:
            return self._is_dialogue_related(entry)

        # Level filter
        if entry['level'] not in self.active_levels:
            return False

        # Node filter
        if entry['node'] not in self.active_nodes:
            return False

        # Search filter
        if self.search_pattern and self.search_regex:
            try:
                if not self.search_regex.search(entry['message']):
                    return False
            except Exception:
                return False

        return True

    def _is_crash_related(self, entry):
        """Check if entry is crash/error related"""
        # Check log level first
        if entry['level'] in ['ERROR', 'CRITICAL']:
            return True

        # Check message content for crash-related keywords
        message = entry['message'].lower()
        crash_keywords = [
            'error', 'failure', 'crash', 'unsuccessful', 'failed',
            'exception', 'traceback', 'fatal', 'abort', 'panic',
            'timeout', 'refused', 'unavailable', 'corrupted',
            'invalid', 'missing', 'not found', 'access denied',
            'connection lost', 'segmentation fault', 'memory error'
        ]

        return any(keyword in message for keyword in crash_keywords)

    def _is_dialogue_related(self, entry):
        """Check if entry is dialogue/speech related"""
        # Check if it's from speech-related nodes
        if entry['node'] in ['speech_recognition_realtime', 'speech_synthesis_realtime', 'ai_cognition_realtime']:
            return True

        # Check message content for speech/dialogue keywords
        message = entry['message'].lower()
        dialogue_keywords = [
            'speech', 'tts', 'stt', 'audio', 'voice', 'speak', 'listen',
            'microphone', 'recognition', 'synthesis', 'utterance', 'transcript',
            'dialogue', 'conversation', 'whisper', 'openai', 'azure', 'pyttsx3',
            'pygame', 'recording', 'playback', 'say', 'hear', 'sound', 'realtime'
        ]

        return any(keyword in message for keyword in dialogue_keywords)

    # Event handlers and utility methods
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        self.live_button.setText(">" if self.paused else "||")
        self.live_button.setToolTip("Resume (Space)" if self.paused else "Pause (Space)")

        # Update button style for visual feedback
        if self.paused:
            self.live_button.setStyleSheet(self.get_active_button_style("#ff8844"))
        else:
            self.live_button.setStyleSheet(self.get_button_style())

    def toggle_auto_scroll(self):
        """Toggle auto-scroll"""
        self.auto_scroll = not self.auto_scroll
        self.auto_scroll_button.setText("Auto" if self.auto_scroll else "Man")
        self.auto_scroll_button.setToolTip("Auto-scroll ON (A)" if self.auto_scroll else "Auto-scroll OFF - Manual mode (A)")

        # Update button style for visual feedback
        if self.auto_scroll:
            self.auto_scroll_button.setStyleSheet(self.get_active_button_style("#44aa44"))
        else:
            self.auto_scroll_button.setStyleSheet(self.get_button_style())

    def toggle_crash_monitor_mode(self):
        """Toggle Crash Monitor Mode"""
        self.crash_monitor_mode = not self.crash_monitor_mode

        if self.crash_monitor_mode:
            self.crash_monitor_button.setStyleSheet(self.get_active_button_style("#ff4444"))
            self.crash_monitor_button.setToolTip("Crash Monitor ON - Showing errors only (Ctrl+Shift+C)")
        else:
            self.crash_monitor_button.setStyleSheet(self.get_button_style())
            self.crash_monitor_button.setToolTip("Crash Monitor OFF - Click to show errors only (Ctrl+Shift+C)")

        # Refresh view with new filter
        self.refresh_all_views()

    def toggle_dialogue_mode(self):
        """Toggle Dialogue Mode"""
        self.dialogue_mode = not self.dialogue_mode

        if self.dialogue_mode:
            self.dialogue_mode_button.setStyleSheet(self.get_active_button_style("#4444ff"))
            self.dialogue_mode_button.setToolTip("Dialogue Mode ON - Showing speech/TTS/STT only (Ctrl+Shift+D)")
        else:
            self.dialogue_mode_button.setStyleSheet(self.get_button_style())
            self.dialogue_mode_button.setToolTip("Dialogue Mode OFF - Click to show speech only (Ctrl+Shift+D)")

        # Refresh view with new filter
        self.refresh_all_views()

    def toggle_level_filter(self, level, state):
        """Toggle level filter"""
        if state:
            self.active_levels.add(level)
        else:
            self.active_levels.discard(level)
        self.refresh_all_views()

    def toggle_node_filter(self, node, state):
        """Toggle node filter"""
        if state:
            self.active_nodes.add(node)
        else:
            self.active_nodes.discard(node)
        self.refresh_all_views()

    def toggle_level_hotkey(self, level):
        """Toggle level filter via hotkey"""
        checkbox = self.level_checkboxes.get(level)
        if checkbox:
            checkbox.setChecked(not checkbox.isChecked())

    def toggle_node_hotkey(self, node):
        """Toggle node filter via hotkey"""
        # Find the checkbox for this node
        for widget in self.findChildren(QCheckBox):
            if widget.text().lower().replace(' ', '_') == node:
                widget.setChecked(not widget.isChecked())
                break

    def focus_search(self):
        """Focus search box"""
        self.search_box.setFocus()

    def focus_next_match(self):
        """Focus next search match (placeholder)"""
        pass

    def clear_logs(self):
        """Clear all log entries"""
        self.log_entries.clear()
        self.filtered_entries.clear()
        self.unified_view.clear()
        for view in self.node_views.values():
            view.clear()
        self.update_statistics()

    def on_search_changed(self, text):
        """Handle search text changes"""
        self.search_pattern = text
        if text:
            try:
                # Check if search checkboxes exist (full toolbar mode)
                flags = re.IGNORECASE  # Default to case-insensitive
                if hasattr(self, 'search_case_sensitive') and self.search_case_sensitive.isChecked():
                    flags = 0

                # Check if regex mode enabled
                if hasattr(self, 'search_regex_mode') and self.search_regex_mode.isChecked():
                    self.search_regex = re.compile(text, flags)
                else:
                    self.search_regex = re.compile(re.escape(text), flags)
            except re.error:
                self.search_regex = None
        else:
            self.search_regex = None

        self.refresh_all_views()

    def on_scroll_changed(self, view):
        """Handle scroll changes for pause-on-scroll"""
        scrollbar = view.verticalScrollBar()
        # If user scrolled up from bottom, pause auto-scroll
        if scrollbar.value() < scrollbar.maximum() - 10:
            if self.auto_scroll:
                self.auto_scroll = False

    def refresh_all_views(self):
        """Refresh all views with current filters"""
        # Clear views
        self.unified_view.clear()
        for view in self.node_views.values():
            view.clear()

        # Re-filter and display entries
        self.filtered_entries = []
        for entry in self.log_entries:
            if self.passes_filters(entry):
                self.filtered_entries.append(entry)
                formatted_line = self.format_log_entry(entry)

                self.append_to_view(self.unified_view, formatted_line, entry)
                if entry['node'] in self.node_views:
                    self.append_to_view(self.node_views[entry['node']], formatted_line, entry)

        self.update_statistics()

    def update_statistics(self):
        """Update statistics display"""
        total = len(self.log_entries)
        filtered = len(self.filtered_entries)

        # Calculate rate (entries per second over last 60 seconds)
        rate = 0.0  # Simplified for now

        # Compact stats format
        self.stats_label.setText(f"Entries: {total} | Filtered: {filtered} | Rate: {rate:.1f}/s")

    def update_node_status(self, node, status):
        """Update node status indicator"""
        if node in self.node_indicators:
            indicator = self.node_indicators[node]
            if status == "healthy":
                indicator.setText("🟢")
            elif status == "warning":
                indicator.setText("🟡")
            elif status == "error":
                indicator.setText("🔴")
            else:
                indicator.setText("⚫")

    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("LogScope ready - monitoring logs directory")

    def get_button_style(self):
        """Get normal button style"""
        return """
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                font-size: 18px;
                min-width: 45px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """

    def get_active_button_style(self, color="#5555ff"):
        """Get active/pressed button style"""
        return f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #aaa;
                border-radius: 5px;
                padding: 5px;
                font-size: 18px;
                min-width: 45px;
                min-height: 35px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: {color};
                border: 2px solid #ccc;
            }}
        """

    def closeEvent(self, event):
        """Handle application close"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        event.accept()