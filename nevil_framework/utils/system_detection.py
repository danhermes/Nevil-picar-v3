"""
System Detection Utilities for Nevil

Detects headless mode and network connectivity for offline behavior management.
"""

import os
import subprocess
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SystemDetector:
    """Detect system state including headless mode and network connectivity."""

    @staticmethod
    def is_headless() -> bool:
        """
        Detect if system is running in headless mode.

        Checks multiple indicators:
        - DISPLAY/WAYLAND_DISPLAY environment variables
        - Framebuffer device existence
        - SSH connection status

        Returns:
            True if running headless (no display attached), False otherwise
        """
        # Check for display environment variables
        has_display = bool(
            os.environ.get('DISPLAY') or
            os.environ.get('WAYLAND_DISPLAY')
        )

        # Check for framebuffer device (display hardware)
        has_framebuffer = os.path.exists('/dev/fb0')

        # Check if connected via SSH
        is_ssh = bool(os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_CLIENT'))

        # Headless if: no display env vars AND (no framebuffer OR is SSH)
        # Note: SSH with X11 forwarding would have DISPLAY set
        headless = not has_display or (is_ssh and not has_display)

        logger.info(
            f"Headless detection - Display env: {has_display}, "
            f"Framebuffer: {has_framebuffer}, SSH: {is_ssh}, "
            f"Result: {'HEADLESS' if headless else 'DISPLAY ATTACHED'}"
        )

        return headless

    @staticmethod
    def get_network_status() -> Dict[str, any]:
        """
        Get current network connectivity status.

        Returns:
            Dictionary with network status information:
            - connected: bool - overall connectivity
            - wifi_connected: bool - WiFi connection status
            - wifi_ssid: str - connected WiFi SSID if available
            - hotspot_active: bool - whether hotspot is running
        """
        status = {
            'connected': False,
            'wifi_connected': False,
            'wifi_ssid': None,
            'hotspot_active': False,
            'interface': None
        }

        try:
            # Check general connectivity
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'STATE', 'general'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                state = result.stdout.strip()
                status['connected'] = state in ['connected', 'connected (local only)']

            # Check WiFi connection
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE,CONNECTION', 'device'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split(':')
                    if len(parts) >= 4:
                        device, dev_type, state, connection = parts[:4]

                        if dev_type == 'wifi' and state == 'connected':
                            status['wifi_connected'] = True
                            status['wifi_ssid'] = connection
                            status['interface'] = device

                        # Check for hotspot (AP mode connection)
                        if 'hotspot' in connection.lower() or 'nevil-ap' in connection.lower():
                            status['hotspot_active'] = True

            logger.info(f"Network status: {status}")

        except Exception as e:
            logger.error(f"Error checking network status: {e}")

        return status

    @staticmethod
    def wait_for_network(timeout: int = 30, wifi_required: bool = False) -> bool:
        """
        Wait for network connectivity.

        Args:
            timeout: Maximum time to wait in seconds
            wifi_required: If True, wait specifically for WiFi connection

        Returns:
            True if network is available, False if timeout
        """
        import time

        start_time = time.time()

        while (time.time() - start_time) < timeout:
            status = SystemDetector.get_network_status()

            if wifi_required:
                if status['wifi_connected']:
                    logger.info(f"WiFi connected to {status['wifi_ssid']}")
                    return True
            else:
                if status['connected']:
                    logger.info("Network connectivity established")
                    return True

            time.sleep(2)

        logger.warning(f"Network timeout after {timeout}s")
        return False


class NetworkManager:
    """Manage network connections including hotspot fallback."""

    HOTSPOT_NAME = "Nevil-AP"
    HOTSPOT_SSID = "Nevil-Robot"
    HOTSPOT_PASSWORD = "nevil2025"  # Change this for production

    @staticmethod
    def enable_hotspot() -> bool:
        """
        Enable WiFi hotspot for direct connection to Nevil.

        Returns:
            True if hotspot enabled successfully, False otherwise
        """
        try:
            logger.info("Enabling Nevil hotspot...")

            # Check if hotspot connection already exists
            result = subprocess.run(
                ['nmcli', 'connection', 'show', NetworkManager.HOTSPOT_NAME],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # Create hotspot connection
                logger.info(f"Creating hotspot profile: {NetworkManager.HOTSPOT_NAME}")
                result = subprocess.run([
                    'nmcli', 'device', 'wifi', 'hotspot',
                    'ifname', 'wlan0',
                    'con-name', NetworkManager.HOTSPOT_NAME,
                    'ssid', NetworkManager.HOTSPOT_SSID,
                    'password', NetworkManager.HOTSPOT_PASSWORD
                ], capture_output=True, text=True, timeout=10)

                if result.returncode != 0:
                    logger.error(f"Failed to create hotspot: {result.stderr}")
                    return False
            else:
                # Activate existing hotspot connection
                logger.info(f"Activating existing hotspot: {NetworkManager.HOTSPOT_NAME}")
                result = subprocess.run(
                    ['nmcli', 'connection', 'up', NetworkManager.HOTSPOT_NAME],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    logger.error(f"Failed to activate hotspot: {result.stderr}")
                    return False

            logger.info(f"Hotspot enabled: SSID={NetworkManager.HOTSPOT_SSID}")
            return True

        except Exception as e:
            logger.error(f"Error enabling hotspot: {e}")
            return False

    @staticmethod
    def disable_hotspot() -> bool:
        """Disable WiFi hotspot."""
        try:
            logger.info("Disabling Nevil hotspot...")
            result = subprocess.run(
                ['nmcli', 'connection', 'down', NetworkManager.HOTSPOT_NAME],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info("Hotspot disabled")
                return True
            else:
                logger.warning(f"Hotspot disable failed (may not be active): {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error disabling hotspot: {e}")
            return False

    @staticmethod
    def connect_wifi(ssid: str, timeout: int = 20) -> bool:
        """
        Connect to a WiFi network.

        Args:
            ssid: WiFi network name
            timeout: Connection timeout in seconds

        Returns:
            True if connected, False otherwise
        """
        try:
            logger.info(f"Connecting to WiFi: {ssid}")

            result = subprocess.run(
                ['nmcli', 'connection', 'up', ssid],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                logger.info(f"Connected to {ssid}")
                return True
            else:
                logger.warning(f"Failed to connect to {ssid}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error connecting to WiFi: {e}")
            return False
