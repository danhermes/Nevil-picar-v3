#!/usr/bin/env python3
"""
SLAM Localization Node - Bridge to External stella_vslam

This node runs the external stella_vslam executable and provides
real-time pose estimation by parsing its output.

stella_vslam installation: /home/dan/Documents/openvslam (kept separate)
"""

import os
import sys
import time
import subprocess
import json
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from threading import Thread, Event
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from nevil_framework.message_bus import MessageBus

# Load environment variables
load_dotenv()


class SLAMLocalizationNode:
    """Bridges external stella_vslam to Nevil's message bus"""

    def __init__(self):
        self.message_bus = MessageBus()
        self.running = False
        self.slam_process = None
        self.pose_thread = None
        self.shutdown_event = Event()

        # Load configuration from .env
        self.slam_executable = os.path.join(
            os.getenv('SLAM_EXECUTABLE_DIR', '/home/dan/Documents/stella_vslam_examples/build'),
            'run_image_slam'
        )
        self.vocab_file = os.getenv('SLAM_VOCAB_FILE', '/home/dan/vocab/orb_vocab.fbow')
        self.map_file = os.getenv('SLAM_MAP_FILE', '/home/dan/Documents/openvslam/my_map.msg')
        self.camera_config = os.getenv('SLAM_CAMERA_CONFIG', '/home/dan/Documents/openvslam/pi_camera_640x480.yaml')
        self.update_rate = float(os.getenv('SLAM_UPDATE_RATE', '10'))

        # Current state
        self.current_pose = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'qx': 0.0,
            'qy': 0.0,
            'qz': 0.0,
            'qw': 1.0,
            'timestamp': 0.0,
            'tracking_state': 'Unknown'
        }

        # Working directory for SLAM output
        self.slam_work_dir = Path('/tmp/nevil_slam_session')
        self.slam_work_dir.mkdir(exist_ok=True)

        # Frame capture directory (updated by visual node)
        self.frame_dir = None

        # Validate external dependencies
        self._validate_dependencies()

    def _validate_dependencies(self):
        """Check that stella_vslam is installed and accessible"""
        if not os.path.exists(self.slam_executable):
            print(f"[SLAM] ERROR: stella_vslam executable not found at {self.slam_executable}")
            print(f"[SLAM] Please install stella_vslam in /home/dan/Documents/openvslam")
            sys.exit(1)

        if not os.path.exists(self.vocab_file):
            print(f"[SLAM] ERROR: ORB vocabulary not found at {self.vocab_file}")
            sys.exit(1)

        if not os.path.exists(self.map_file):
            print(f"[SLAM] WARNING: Map file not found at {self.map_file}")
            print(f"[SLAM] SLAM will run in mapping mode (creating new map)")
        else:
            print(f"[SLAM] Map file found: {self.map_file}")

        print(f"[SLAM] stella_vslam validated at {self.slam_executable}")

    def start(self):
        """Start the SLAM localization node"""
        print("[SLAM] Starting SLAM Localization Node...")
        self.running = True

        # Subscribe to frame capture updates from visual node
        self.message_bus.subscribe('slam_frame_dir', self._handle_frame_dir_update)

        # Subscribe to navigation queries
        self.message_bus.subscribe('slam_get_pose', self._handle_pose_request)

        # Start pose publishing thread
        self.pose_thread = Thread(target=self._pose_publisher_loop, daemon=True)
        self.pose_thread.start()

        print(f"[SLAM] Localization node ready (update rate: {self.update_rate} Hz)")
        print("[SLAM] Waiting for frame directory from visual node...")

        # Keep alive
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[SLAM] Shutdown requested")
        finally:
            self.stop()

    def _handle_frame_dir_update(self, data):
        """Visual node signals new frame directory for SLAM processing"""
        self.frame_dir = data.get('directory')
        print(f"[SLAM] Frame directory updated: {self.frame_dir}")

        # If SLAM is not running, start it
        if self.slam_process is None or self.slam_process.poll() is not None:
            self._start_slam_process()

    def _start_slam_process(self):
        """Launch stella_vslam as external subprocess"""
        if not self.frame_dir or not os.path.exists(self.frame_dir):
            print(f"[SLAM] ERROR: Frame directory not valid: {self.frame_dir}")
            return

        print(f"[SLAM] Starting stella_vslam process...")

        # Build command
        cmd = [
            self.slam_executable,
            '-v', self.vocab_file,
            '-d', self.frame_dir,
            '-c', self.camera_config,
        ]

        # Add map file if exists (localization mode)
        if os.path.exists(self.map_file):
            cmd.extend(['-i', self.map_file, '--disable-mapping'])
            print(f"[SLAM] Running in LOCALIZATION mode with map: {self.map_file}")
        else:
            print(f"[SLAM] Running in MAPPING mode (creating new map)")

        # Set working directory for trajectory output
        os.chdir(self.slam_work_dir)

        try:
            self.slam_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            print(f"[SLAM] stella_vslam started (PID: {self.slam_process.pid})")

            # Start thread to parse SLAM output
            Thread(target=self._parse_slam_output, daemon=True).start()

        except Exception as e:
            print(f"[SLAM] ERROR starting stella_vslam: {e}")
            self.slam_process = None

    def _parse_slam_output(self):
        """Parse pose data from SLAM stdout"""
        print("[SLAM] Parsing SLAM output for pose data...")

        try:
            for line in self.slam_process.stdout:
                if not self.running:
                    break

                # Look for tracking state messages
                # stella_vslam outputs: "Tracking: OK" or "Tracking: LOST"
                if "Tracking:" in line:
                    if "OK" in line or "SUCCESS" in line:
                        self.current_pose['tracking_state'] = 'Tracking'
                    elif "LOST" in line or "FAIL" in line:
                        self.current_pose['tracking_state'] = 'Lost'
                    elif "INIT" in line:
                        self.current_pose['tracking_state'] = 'Initializing'

                # Parse pose if available in output
                # (stella_vslam may output pose in specific format)
                # This is a simplified parser - adjust based on actual output
                pose_match = re.search(r'pose:\s*\[([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\]', line)
                if pose_match:
                    self.current_pose['x'] = float(pose_match.group(1))
                    self.current_pose['y'] = float(pose_match.group(2))
                    self.current_pose['z'] = float(pose_match.group(3))
                    self.current_pose['timestamp'] = time.time()

        except Exception as e:
            print(f"[SLAM] Error parsing output: {e}")

    def _read_trajectory_file(self):
        """
        Read latest pose from trajectory file (fallback method)
        stella_vslam outputs frame_trajectory.txt in KITTI format
        """
        traj_file = self.slam_work_dir / 'frame_trajectory.txt'

        if not traj_file.exists():
            return None

        try:
            # Read last line (most recent pose)
            with open(traj_file, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return None

                last_line = lines[-1].strip()
                # KITTI format: r11 r12 r13 tx r21 r22 r23 ty r31 r32 r33 tz
                values = [float(v) for v in last_line.split()]

                if len(values) == 12:
                    # Extract translation
                    tx, ty, tz = values[3], values[7], values[11]

                    # Extract rotation matrix and convert to quaternion
                    R = np.array([
                        [values[0], values[1], values[2]],
                        [values[4], values[5], values[6]],
                        [values[8], values[9], values[10]]
                    ])
                    quat = self._rotation_matrix_to_quaternion(R)

                    return {
                        'x': tx,
                        'y': ty,
                        'z': tz,
                        'qx': quat[0],
                        'qy': quat[1],
                        'qz': quat[2],
                        'qw': quat[3],
                        'timestamp': time.time()
                    }
        except Exception as e:
            print(f"[SLAM] Error reading trajectory: {e}")

        return None

    @staticmethod
    def _rotation_matrix_to_quaternion(R):
        """Convert 3x3 rotation matrix to quaternion [qx, qy, qz, qw]"""
        trace = np.trace(R)

        if trace > 0:
            s = 0.5 / np.sqrt(trace + 1.0)
            qw = 0.25 / s
            qx = (R[2, 1] - R[1, 2]) * s
            qy = (R[0, 2] - R[2, 0]) * s
            qz = (R[1, 0] - R[0, 1]) * s
        else:
            if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
                s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
                qw = (R[2, 1] - R[1, 2]) / s
                qx = 0.25 * s
                qy = (R[0, 1] + R[1, 0]) / s
                qz = (R[0, 2] + R[2, 0]) / s
            elif R[1, 1] > R[2, 2]:
                s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
                qw = (R[0, 2] - R[2, 0]) / s
                qx = (R[0, 1] + R[1, 0]) / s
                qy = 0.25 * s
                qz = (R[1, 2] + R[2, 1]) / s
            else:
                s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
                qw = (R[1, 0] - R[0, 1]) / s
                qx = (R[0, 2] + R[2, 0]) / s
                qy = (R[1, 2] + R[2, 1]) / s
                qz = 0.25 * s

        return [qx, qy, qz, qw]

    def _pose_publisher_loop(self):
        """Periodically publish current pose to message bus"""
        update_interval = 1.0 / self.update_rate

        while self.running:
            # Try to get latest pose from trajectory file
            pose_from_file = self._read_trajectory_file()
            if pose_from_file:
                self.current_pose.update(pose_from_file)

            # Publish pose
            self.message_bus.publish('slam_pose', self.current_pose.copy())

            time.sleep(update_interval)

    def _handle_pose_request(self, data):
        """Handle synchronous pose requests"""
        self.message_bus.publish('slam_pose_response', self.current_pose.copy())

    def stop(self):
        """Shutdown SLAM node and cleanup"""
        print("\n[SLAM] Shutting down...")
        self.running = False
        self.shutdown_event.set()

        # Stop SLAM process
        if self.slam_process and self.slam_process.poll() is None:
            print("[SLAM] Terminating stella_vslam process...")
            self.slam_process.terminate()
            try:
                self.slam_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("[SLAM] Force killing stella_vslam...")
                self.slam_process.kill()

        print("[SLAM] Shutdown complete")


if __name__ == '__main__':
    node = SLAMLocalizationNode()
    try:
        node.start()
    except KeyboardInterrupt:
        node.stop()
