# Nevil Network Setup - Headless Mode & Hotspot

## Overview

Nevil automatically detects when running in headless mode (no display) and enables a WiFi hotspot for offline access. In normal operation with HDMI connected, WiFi works as expected.

## How It Works

### 1. Headless Detection

**The service detects headless mode by checking:**
- No `DISPLAY` or `WAYLAND_DISPLAY` environment variables
- Running via systemd (no display session)
- SSH connection without X11 forwarding

**99.9% of the time:** HDMI is connected → Uses WiFi normally

### 2. Network Priority (Headless Mode Only)

When headless and service starts:

```
1. Try to connect to configured WiFi (summerdome)
   ↓ (if fails)
2. Enable WiFi hotspot automatically
   - SSID: Nevil-Robot
   - Password: nevil2025
   - IP: 10.42.0.1 (typically)
```

### 3. Service Startup Sequence

```
network.target → network_setup.sh → GPIO/audio config → nevil start
```

## Files Created

### Core Modules

**`nevil_framework/utils/system_detection.py`**
- `SystemDetector.is_headless()` - Detect headless mode
- `SystemDetector.get_network_status()` - Check WiFi/network state
- `NetworkManager.enable_hotspot()` - Enable WiFi AP mode
- `NetworkManager.connect_wifi()` - Connect to WiFi network

### Scripts

**`scripts/network_setup.sh`**
- Runs before Nevil service starts
- Detects headless mode
- Connects to WiFi or enables hotspot
- Logs to `logs/network_setup.log`

**`scripts/test_headless_detection.sh`**
- Test headless detection logic
- Show current network status
- Verify Python modules

**`scripts/install_nevil_service.sh`**
- Updated to include network setup pre-start
- Creates systemd service with network checks

## Usage

### Test Headless Detection

```bash
# Run detection test
./scripts/test_headless_detection.sh

# Check if currently headless
python3 -c "
from nevil_framework.utils.system_detection import SystemDetector
print('Headless:', SystemDetector.is_headless())
"
```

### Manual Network Operations

```bash
# Check network status
python3 -c "
from nevil_framework.utils.system_detection import SystemDetector
status = SystemDetector.get_network_status()
print(status)
"

# Manually enable hotspot
python3 -c "
from nevil_framework.utils.system_detection import NetworkManager
NetworkManager.enable_hotspot()
"

# Manually connect to WiFi
python3 -c "
from nevil_framework.utils.system_detection import NetworkManager
NetworkManager.connect_wifi('summerdome')
"
```

### Service Management

```bash
# Install/update service with network setup
sudo ./scripts/install_nevil_service.sh

# Start service (runs network setup automatically)
sudo systemctl start nevil

# View network setup logs
tail -f logs/network_setup.log

# View service logs
journalctl -u nevil -f
```

### Check Hotspot Status

```bash
# List all connections
nmcli connection show

# Check if hotspot is active
nmcli connection show --active | grep Nevil-AP

# Manually activate hotspot
nmcli connection up Nevil-AP

# Manually deactivate hotspot
nmcli connection down Nevil-AP
```

## Configuration

### Change Hotspot Credentials

Edit `nevil_framework/utils/system_detection.py`:

```python
class NetworkManager:
    HOTSPOT_NAME = "Nevil-AP"
    HOTSPOT_SSID = "Nevil-Robot"
    HOTSPOT_PASSWORD = "nevil2025"  # ← Change this
```

Edit `scripts/network_setup.sh`:

```bash
HOTSPOT_SSID="Nevil-Robot"
HOTSPOT_PASSWORD="nevil2025"  # ← Change this
```

### Change Default WiFi Network

Edit `scripts/network_setup.sh`:

```bash
WIFI_SSID="summerdome"  # ← Change this
```

### Adjust WiFi Timeout

Edit `scripts/network_setup.sh`:

```bash
WIFI_TIMEOUT=15  # seconds to wait for WiFi
```

## Typical Scenarios

### Scenario 1: HDMI Connected (99.9% of the time)

```
1. Service starts
2. Network setup runs
3. Connects to WiFi (summerdome)
4. Nevil starts normally
```

**Headless detection:** False (display attached)
**Network:** WiFi

### Scenario 2: Truly Headless (Remote/Offline Operation)

```
1. Service starts (no display)
2. Network setup detects headless mode
3. Tries WiFi → fails (out of range)
4. Enables hotspot automatically
5. User connects to Nevil-Robot hotspot
6. Access Nevil via 10.42.0.1
```

**Headless detection:** True (no display)
**Network:** Hotspot fallback

### Scenario 3: SSH with Display Forwarding

```
SSH with X11: Detected as NOT headless (DISPLAY var set)
SSH without X11: Detected as headless
```

## Integration with Launcher

The Python modules can be imported into any node:

```python
from nevil_framework.utils.system_detection import SystemDetector, NetworkManager

# In your node's startup
if SystemDetector.is_headless():
    logger.info("Running in headless mode")
    # Adjust behavior for headless operation

# Check if offline
status = SystemDetector.get_network_status()
if not status['wifi_connected']:
    logger.warning("No WiFi - running offline")
```

## Logs

### Network Setup Log
```bash
tail -f logs/network_setup.log
```

Example output:
```
[2025-11-22 20:15:30] === Nevil Network Setup Starting ===
[2025-11-22 20:15:30] Running in HEADLESS mode
[2025-11-22 20:15:30] No network connection detected
[2025-11-22 20:15:31] Attempting to connect to WiFi: summerdome
[2025-11-22 20:15:33] Failed to connect to WiFi: summerdome
[2025-11-22 20:15:33] WiFi connection unavailable
[2025-11-22 20:15:33] Headless mode detected - enabling hotspot for offline access
[2025-11-22 20:15:35] Hotspot enabled: SSID=Nevil-Robot
[2025-11-22 20:15:38] Hotspot is active and accessible
[2025-11-22 20:15:38] === Network Setup Complete (Hotspot Mode) ===
```

### System Log
```bash
tail -f logs/system.log
```

### Service Log
```bash
journalctl -u nevil -f
```

## Troubleshooting

### Hotspot Not Working

```bash
# Check NetworkManager status
systemctl status NetworkManager

# Check WiFi interface
nmcli device status

# Manually create hotspot
nmcli device wifi hotspot ifname wlan0 ssid Nevil-Robot password nevil2025

# Check network setup logs
tail -20 logs/network_setup.log
```

### WiFi Not Connecting

```bash
# List available networks
nmcli device wifi list

# Check connection details
nmcli connection show summerdome

# Manually connect
nmcli connection up summerdome

# Check wpa_supplicant
systemctl status wpa_supplicant
```

### Headless Detection Issues

```bash
# Run test script
./scripts/test_headless_detection.sh

# Check environment when service runs
systemctl show nevil -p Environment

# Check manually
echo "DISPLAY=$DISPLAY"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
echo "SSH_CONNECTION=$SSH_CONNECTION"
```

## Security Notes

- **Change default hotspot password** in production
- Hotspot uses WPA2 encryption
- Only enabled when headless and offline
- Automatically disabled when WiFi reconnects (manual override needed)

## Future Enhancements

Possible additions:
- Auto-switch back to WiFi when in range
- Multiple WiFi network fallback
- Hotspot bandwidth limiting
- Captive portal for configuration
- Network diagnostics dashboard
