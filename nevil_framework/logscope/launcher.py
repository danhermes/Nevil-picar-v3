import sys
import argparse
from pathlib import Path

def main():
    """Launch Nevil LogScope desktop application"""
    parser = argparse.ArgumentParser(description="Nevil v3 LogScope - Desktop Log Monitor")
    parser.add_argument("--log-dir", "-d", default="logs", help="Log directory to monitor")
    parser.add_argument("--max-entries", "-m", type=int, default=10000, help="Maximum entries to keep in memory")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="UI theme")

    args = parser.parse_args()

    # Check if PyQt is available
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        pyqt_version = "PyQt6"
    except ImportError:
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            pyqt_version = "PyQt5"
        except ImportError:
            print("Error: PyQt6 or PyQt5 required for LogScope GUI")
            print("Install with: pip install PyQt6")
            sys.exit(1)

    # Validate log directory
    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"Warning: Log directory '{log_dir}' does not exist")
        print("LogScope will wait for log files to appear...")

    # Import main window after PyQt check
    from .main_window import NevilLogScope

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Nevil LogScope")
    app.setApplicationVersion("3.0")

    print(f"Starting Nevil LogScope v3.0 using {pyqt_version}")
    print(f"Monitoring log directory: {log_dir.absolute()}")

    # Create and show main window
    window = NevilLogScope()
    window.log_dir = log_dir
    window.max_entries = args.max_entries
    window.show()

    # Run application
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nShutting down LogScope...")
        window.running = False
        sys.exit(0)

if __name__ == "__main__":
    main()