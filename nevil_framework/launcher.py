"""
Nevil v3.0 Node Launcher

Simple launcher that discovers nodes, manages their lifecycle, and coordinates startup/shutdown.
"""

import os
import sys
import time
import signal
import importlib.util
import multiprocessing
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
from datetime import datetime
import subprocess
import tempfile

from .config_loader import ConfigLoader
from .message_bus import MessageBus
from .base_node import NevilNode


class NodeProcess:
    """Represents a node running in its own process"""

    def __init__(self, node_name: str, node_class: type, config: Dict[str, Any]):
        self.node_name = node_name
        self.node_class = node_class
        self.config = config
        self.process = None
        self.start_time = None

    def start(self, message_bus: MessageBus):
        """Start the node process"""
        try:
            print(f"[Launcher] Starting node: {self.node_name}")

            # For now, run in-process for simplicity (Phase 1)
            # Phase 2 will implement true process isolation
            self.node_instance = self.node_class()

            # Set message bus BEFORE starting the node
            self.node_instance.set_message_bus(message_bus)

            # Start the node in a separate thread
            # CRITICAL: Use daemon=True so threads don't block process exit
            self.process = threading.Thread(
                target=self._run_node,
                name=f"Node_{self.node_name}",
                daemon=True
            )
            self.process.start()
            self.start_time = time.time()

            print(f"[Launcher] Node {self.node_name} started successfully")
            return True

        except Exception as e:
            print(f"[Launcher] Failed to start node {self.node_name}: {e}")
            return False

    def _run_node(self):
        """Run the node instance"""
        try:
            self.node_instance.start()
        except Exception as e:
            print(f"[Launcher] Node {self.node_name} crashed: {e}")

    def stop(self, timeout: float = 10.0):
        """Stop the node process"""
        try:
            if hasattr(self, 'node_instance'):
                print(f"[Launcher] Stopping node: {self.node_name}")
                self.node_instance.stop(timeout)

            if self.process and self.process.is_alive():
                self.process.join(timeout)

            print(f"[Launcher] Node {self.node_name} stopped")
            return True

        except Exception as e:
            print(f"[Launcher] Error stopping node {self.node_name}: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the node process is running"""
        return self.process and self.process.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """Get node status information"""
        return {
            "node_name": self.node_name,
            "running": self.is_running(),
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0
        }


class NevilLauncher:
    """
    Main launcher for Nevil v3.0 system.

    Features:
    - Automatic node discovery
    - Configuration loading and validation
    - Node lifecycle management
    - Message bus coordination
    - System health monitoring
    """

    def __init__(self, root_path: str = "."):
        self.root_path = root_path

        # Setup system-wide logging
        self._setup_system_logging()

        # Load .env file if it exists
        self._load_env_file()

        self.config_loader = ConfigLoader(root_path)
        self.message_bus = MessageBus()

        self.nodes = {}  # node_name -> NodeProcess
        self.system_config = {}
        self.running = False
        self.shutdown_requested = False

        # Set up signal handlers for clean shutdown - MUST be in main thread
        # These will override any handlers set by child threads
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info(f"Nevil v3.0 launcher initialized in {root_path}")

    def _setup_system_logging(self):
        """Setup system-wide logging to system.log"""
        # Create logs directory
        log_dir = os.path.join(self.root_path, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Setup system logger
        self.logger = logging.getLogger("system")
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.logger.handlers = []

        # Create file handler for system.log
        system_log_path = os.path.join(log_dir, "system.log")
        file_handler = logging.FileHandler(system_log_path)
        file_handler.setLevel(logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)-8s] [%(name)-20s] [%(threadName)-15s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %Z'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log startup
        self.logger.info("=" * 60)
        self.logger.info("Nevil v3.0 System Starting")
        self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Working Directory: {os.getcwd()}")
        self.logger.info("=" * 60)

    def _load_env_file(self):
        """Load environment variables from .env file"""
        env_path = os.path.join(self.root_path, '.env')
        if os.path.exists(env_path):
            self.logger.info(f"Loading environment from {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                        # Don't log API keys for security
                        if 'KEY' in key.upper() or 'SECRET' in key.upper():
                            self.logger.info(f"Set {key}=<REDACTED>")
                        else:
                            self.logger.info(f"Set {key}={value}")
        else:
            self.logger.warning(f"No .env file found at {env_path}")

    def discover_and_load_nodes(self) -> bool:
        """Discover nodes and load their classes"""
        try:
            # Load system configuration
            self.system_config = self.config_loader.load_nodes_config()

            # Get nodes to actually start from configuration
            nodes_to_start = []
            if 'launch' in self.system_config and 'startup_order' in self.system_config['launch']:
                nodes_to_start = self.system_config['launch']['startup_order']
            else:
                # Fallback to discovering all nodes
                nodes_to_start = self.config_loader.discover_nodes()

            if not nodes_to_start:
                print("[Launcher] No nodes configured to start")
                return True  # Not an error, just no nodes to run

            print(f"[Launcher] Loading {len(nodes_to_start)} nodes: {nodes_to_start}")

            # Load only the nodes we're going to start
            for node_name in nodes_to_start:
                print(f"[Launcher] Loading node: {node_name}...")
                if self._load_node(node_name):
                    print(f"[Launcher] Successfully loaded node: {node_name}")
                else:
                    print(f"[Launcher] Failed to load node: {node_name}")
                    return False

            return True

        except Exception as e:
            print(f"[Launcher] Error during node discovery: {e}")
            return False

    def _load_node(self, node_name: str) -> bool:
        """Load a specific node class from its module"""
        try:
            # Load node .messages configuration
            node_config = self.config_loader.load_node_messages_config(node_name)

            # Construct path to node module
            node_dir = os.path.join(self.root_path, "nodes", node_name)
            node_file = os.path.join(node_dir, f"{node_name}_node.py")

            if not os.path.exists(node_file):
                print(f"[Launcher] Node file not found: {node_file}")
                return False

            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(f"{node_name}_node", node_file)
            if spec is None or spec.loader is None:
                print(f"[Launcher] Could not load module spec for {node_file}")
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the node class (should be named {NodeName}Node)
            class_name = ''.join(word.capitalize() for word in node_name.split('_')) + 'Node'
            node_class = getattr(module, class_name, None)

            if node_class is None:
                print(f"[Launcher] Node class '{class_name}' not found in {node_file}")
                return False

            if not issubclass(node_class, NevilNode):
                print(f"[Launcher] Class '{class_name}' is not a subclass of NevilNode")
                return False

            # Create node process wrapper
            self.nodes[node_name] = NodeProcess(node_name, node_class, node_config)
            return True

        except Exception as e:
            print(f"[Launcher] Error loading node {node_name}: {e}")
            return False

    def configure_audio_devices(self) -> bool:
        """
        Dynamically configure ALSA audio devices using i2samp approach.
        Finds the HiFiBerry DAC card and generates proper asound.conf.
        """
        try:
            self.logger.info("Configuring audio devices...")

            # Target audio card name (from i2samp script)
            audio_card_name = "sndrpihifiberry"
            asound_conf_path = os.path.expanduser("~/.asoundrc")

            # Find the card number for HiFiBerry DAC
            self.logger.debug("Searching for HiFiBerry DAC card...")
            try:
                # Run aplay -l and parse output to find card number
                result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, check=True)
                card_num = None

                for line in result.stdout.split('\n'):
                    if audio_card_name in line:
                        # Extract card number from line like "card 2: sndrpihifiberry"
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'card' and i + 1 < len(parts):
                                card_num = parts[i + 1].rstrip(':')
                                break
                        break

                if card_num is None:
                    self.logger.warning(f"Audio card '{audio_card_name}' not found, using default audio")
                    return True  # Not an error, just use system default

                self.logger.info(f"Found HiFiBerry DAC at card {card_num}")

            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to run aplay -l: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Error finding audio card: {e}")
                return False

            # Generate ALSA configuration (based on i2samp auto_sound_card script)
            asound_config = f"""pcm.speakerbonnet {{
    type hw card {card_num}
}}

pcm.dmixer {{
    type dmix
    ipc_key 1024
    ipc_perm 0666
    slave {{
        pcm "speakerbonnet"
        period_time 0
        period_size 1024
        buffer_size 8192
        rate 44100
        channels 2
    }}
}}

ctl.dmixer {{
    type hw card {card_num}
}}

pcm.softvol {{
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card {card_num}
}}

ctl.softvol {{
    type hw card {card_num}
}}

pcm.!default {{
    type             plug
    slave.pcm       "softvol"
}}
"""

            # Backup existing configuration
            if os.path.exists(asound_conf_path):
                backup_path = f"{asound_conf_path}.backup"
                try:
                    with open(asound_conf_path, 'r') as src, open(backup_path, 'w') as dst:
                        dst.write(src.read())
                    self.logger.info(f"Backed up existing .asoundrc to {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Could not backup .asoundrc: {e}")

            # Write new configuration
            try:
                with open(asound_conf_path, 'w') as f:
                    f.write(asound_config)
                self.logger.info(f"Generated new ALSA configuration at {asound_conf_path}")
            except Exception as e:
                self.logger.error(f"Failed to write ALSA configuration: {e}")
                return False

            # Enable speaker switch (pin 20)
            try:
                self.logger.debug("Enabling speaker switch (pin 20)...")
                subprocess.run(['pinctrl', 'set', '20', 'op', 'dh'], check=True,
                             capture_output=True)
                self.logger.info("Speaker switch enabled")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"Failed to enable speaker switch: {e}")
                # Not a fatal error, continue

            # Restart any audio services that depend on ALSA config
            self._restart_audio_services()

            self.logger.info("Audio device configuration completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error configuring audio devices: {e}")
            return False

    def _restart_audio_services(self):
        """
        Restart audio-related services to pick up new ALSA configuration.
        Based on i2samp script approach.
        """
        try:
            # Restart aplay service if it exists (from i2samp setup)
            self.logger.debug("Checking for aplay service...")
            result = subprocess.run(['systemctl', 'is-active', 'aplay.service'],
                                  capture_output=True, text=True)

            if result.returncode == 0 and 'active' in result.stdout:
                self.logger.info("Restarting aplay service...")
                subprocess.run(['sudo', 'systemctl', 'restart', 'aplay.service'],
                             check=False, capture_output=True)

            # Force reload of ALSA configuration in current process
            self._reload_alsa_in_process()

        except Exception as e:
            self.logger.warning(f"Error restarting audio services: {e}")

    def _reload_alsa_in_process(self):
        """
        Force the current process to reload ALSA configuration.
        This ensures pygame/robot_hat Music() will use the new settings.
        """
        try:
            # Clear any ALSA configuration cache
            # This forces ALSA to re-read configuration files
            import ctypes
            import ctypes.util

            # Try to load ALSA library and call snd_config_update
            alsa_lib = ctypes.util.find_library('asound')
            if alsa_lib:
                libasound = ctypes.CDLL(alsa_lib)
                if hasattr(libasound, 'snd_config_update_free_global'):
                    libasound.snd_config_update_free_global()
                    self.logger.debug("Cleared ALSA configuration cache")

                if hasattr(libasound, 'snd_config_update'):
                    result = libasound.snd_config_update()
                    if result == 0:
                        self.logger.debug("Reloaded ALSA configuration")
                    else:
                        self.logger.warning(f"ALSA config reload returned: {result}")

            # Also try environment variable approach
            # Force ALSA to re-read config by clearing cache
            if 'ALSA_CONFIG_DIR' not in os.environ:
                os.environ['ALSA_CONFIG_DIR'] = '/usr/share/alsa'

            self.logger.info("ALSA configuration reload attempted")

        except Exception as e:
            self.logger.warning(f"Could not reload ALSA in process: {e}")
            self.logger.info("Audio configuration will take effect on next restart")

    def start_system(self) -> bool:
        """Start the entire Nevil system"""
        try:
            print("[Launcher] Starting Nevil v3.0 system...")

            # Configure audio devices first (before starting audio nodes)
            self.logger.info("Configuring audio devices...")
            if not self.configure_audio_devices():
                self.logger.warning("Audio configuration failed, continuing with defaults")

            # Discover and load nodes
            if not self.discover_and_load_nodes():
                print("[Launcher] Failed to discover/load nodes")
                return False

            if not self.nodes:
                print("[Launcher] No nodes to start")
                return True

            # Start nodes in order
            startup_order = self._get_startup_order()

            for node_name in startup_order:
                if node_name in self.nodes:
                    if not self.nodes[node_name].start(self.message_bus):
                        print(f"[Launcher] Failed to start node: {node_name}")
                        return False

                    # Brief delay between node starts
                    time.sleep(1.0)

            self.running = True
            print(f"[Launcher] System started successfully with {len(self.nodes)} nodes")
            print(f"[Launcher] Returning from start_system() with True")
            return True

        except Exception as e:
            print(f"[Launcher] Error starting system: {e}")
            return False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals with v2.0 aggressive cleanup pattern"""
        # Simple, clean message
        if signum == signal.SIGINT:
            print("\n\nShutting down Nevil v3.0...")

        # Don't even try graceful shutdown - just kill everything immediately
        import subprocess
        import os

        # Kill EVERYTHING related to this session silently
        try:
            # Get our own PID
            my_pid = os.getpid()

            # Kill all child processes first with -9 to prevent their output
            subprocess.run(['pkill', '-9', '-P', str(my_pid)], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Then kill all nevil-related processes
            subprocess.run(['pkill', '-9', '-f', 'nevil'], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', '-f', 'speech'], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', '-f', 'ai_cognition'], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-9', '-f', 'test_node'], check=False,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

        # Most aggressive exit possible - bypasses EVERYTHING
        os._exit(0)

    def stop_system(self, timeout: float = 30.0) -> bool:
        """Stop the entire Nevil system with v2.0 cleanup pattern"""
        if not self.running:
            return True  # Already stopped

        try:
            print("[Launcher] Stopping Nevil v3.0 system...")
            self.running = False
            self.shutdown_requested = True

            # Stop nodes in reverse order
            startup_order = self._get_startup_order()
            shutdown_order = list(reversed(startup_order))

            success = True
            for node_name in shutdown_order:
                if node_name in self.nodes:
                    if not self.nodes[node_name].stop(timeout / len(self.nodes)):
                        print(f"[Launcher] Failed to stop node: {node_name}")
                        success = False

            # Shutdown message bus
            self.message_bus.shutdown()

            # v2.0 pattern: Force cleanup stubborn audio processes
            print("[Launcher] Cleaning up stubborn processes...")
            import subprocess
            stubborn_patterns = [
                "speech_recognition_node",
                "speech_synthesis_node",
                "ai_cognition_node"
            ]

            for pattern in stubborn_patterns:
                try:
                    # Get PIDs first
                    result = subprocess.run(['pgrep', '-f', pattern],
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        pids = result.stdout.strip().split('\n')
                        print(f"[Launcher] Force killing {pattern} processes: {pids}")
                        for pid in pids:
                            if pid.strip():
                                subprocess.run(['kill', '-9', pid.strip()],
                                             capture_output=True, check=False)
                except Exception:
                    pass

            print("[Launcher] System stopped")
            return success

        except Exception as e:
            print(f"[Launcher] Error stopping system: {e}")
            return False

    def _get_startup_order(self) -> List[str]:
        """Get the order in which nodes should be started"""
        # Use startup_order from configuration if available
        if 'launch' in self.system_config and 'startup_order' in self.system_config['launch']:
            configured_order = self.system_config['launch']['startup_order']
            # Only include nodes that are actually loaded and configured to start
            return [node for node in configured_order if node in self.nodes]

        # Fallback to alphabetical order if no configuration
        return sorted(self.nodes.keys())

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        node_statuses = {}
        for node_name, node_process in self.nodes.items():
            node_statuses[node_name] = node_process.get_status()

        return {
            "running": self.running,
            "total_nodes": len(self.nodes),
            "running_nodes": sum(1 for node in self.nodes.values() if node.is_running()),
            "message_bus_stats": self.message_bus.get_stats(),
            "nodes": node_statuses
        }

    def wait_for_shutdown(self):
        """Wait for system shutdown (useful for main process)"""
        try:
            while self.running and not self.shutdown_requested:
                time.sleep(0.1)  # Shorter sleep for more responsive shutdown

            # If shutdown was requested, actually stop the system
            if self.shutdown_requested:
                self.stop_system()
        except KeyboardInterrupt:
            print("\n[Launcher] Keyboard interrupt received")
            self.shutdown_requested = True
            self.stop_system()


def main():
    """Main entry point for the launcher"""
    launcher = NevilLauncher()

    try:
        if launcher.start_system():
            print("[Launcher] System running. Press Ctrl+C to stop.")
            launcher.wait_for_shutdown()
        else:
            print("[Launcher] Failed to start system")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down...")
    finally:
        launcher.stop_system()


if __name__ == "__main__":
    main()