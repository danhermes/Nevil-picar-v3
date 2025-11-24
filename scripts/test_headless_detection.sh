#!/bin/bash
#
# Test Headless Detection and Network Setup
#
# This script tests the headless detection logic and network management
# without actually modifying the system.
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Nevil Headless Detection & Network Test            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Environment Detection
echo "─────────────────────────────────────────────────────────────"
echo "Test 1: Display Environment Detection"
echo "─────────────────────────────────────────────────────────────"

if [ -n "$DISPLAY" ]; then
    echo -e "${GREEN}✓${NC} DISPLAY is set: $DISPLAY"
else
    echo -e "${YELLOW}○${NC} DISPLAY is not set"
fi

if [ -n "$WAYLAND_DISPLAY" ]; then
    echo -e "${GREEN}✓${NC} WAYLAND_DISPLAY is set: $WAYLAND_DISPLAY"
else
    echo -e "${YELLOW}○${NC} WAYLAND_DISPLAY is not set"
fi

if [ -n "$SSH_CONNECTION" ]; then
    echo -e "${YELLOW}⚠${NC}  SSH_CONNECTION detected: $SSH_CONNECTION"
    IS_SSH=true
else
    echo -e "${GREEN}✓${NC} Not connected via SSH"
    IS_SSH=false
fi

# Test 2: Framebuffer Detection
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Test 2: Framebuffer Device Detection"
echo "─────────────────────────────────────────────────────────────"

if [ -e "/dev/fb0" ]; then
    echo -e "${GREEN}✓${NC} Framebuffer device exists: /dev/fb0"
    ls -l /dev/fb0
    HAS_FB=true
else
    echo -e "${RED}✗${NC} No framebuffer device found"
    HAS_FB=false
fi

# Test 3: Headless Mode Determination
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Test 3: Headless Mode Determination"
echo "─────────────────────────────────────────────────────────────"

HEADLESS=false

if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    HEADLESS=true
    echo -e "${YELLOW}→${NC} No display environment variables set"
fi

if [ "$IS_SSH" = true ] && [ -z "$DISPLAY" ]; then
    HEADLESS=true
    echo -e "${YELLOW}→${NC} SSH connection without display forwarding"
fi

if [ "$HEADLESS" = true ]; then
    echo -e "${YELLOW}━━━ RESULT: HEADLESS MODE ━━━${NC}"
    echo "   System is running without display (headless)"
    echo "   → Hotspot will be enabled if offline"
else
    echo -e "${GREEN}━━━ RESULT: DISPLAY MODE ━━━${NC}"
    echo "   System has display attached"
    echo "   → User can configure network manually"
fi

# Test 4: Network Status
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Test 4: Current Network Status"
echo "─────────────────────────────────────────────────────────────"

# General network state
NETWORK_STATE=$(nmcli -t -f STATE general 2>/dev/null || echo "unknown")
echo "Network state: $NETWORK_STATE"

if [ "$NETWORK_STATE" = "connected" ]; then
    echo -e "${GREEN}✓${NC} Network is connected"
else
    echo -e "${YELLOW}⚠${NC}  Network is not connected"
fi

# WiFi status
echo ""
echo "WiFi Connections:"
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device 2>/dev/null | grep "wifi" | while IFS=: read -r device type state connection; do
    if [ "$state" = "connected" ]; then
        echo -e "  ${GREEN}✓${NC} $device: $connection (connected)"
    else
        echo -e "  ${YELLOW}○${NC} $device: $state"
    fi
done

# Hotspot check
echo ""
if nmcli connection show "Nevil-AP" &>/dev/null; then
    echo -e "${GREEN}✓${NC} Hotspot profile 'Nevil-AP' exists"
    HOTSPOT_STATE=$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null | grep "Nevil-AP" || echo "inactive")
    if [ "$HOTSPOT_STATE" != "inactive" ]; then
        echo -e "${GREEN}✓${NC} Hotspot is currently ACTIVE"
    else
        echo -e "${YELLOW}○${NC} Hotspot profile exists but is INACTIVE"
    fi
else
    echo -e "${YELLOW}○${NC} Hotspot profile 'Nevil-AP' not created yet"
    echo "   (Will be created automatically when needed)"
fi

# Test 5: Python System Detection Module
echo ""
echo "─────────────────────────────────────────────────────────────"
echo "Test 5: Python System Detection Module"
echo "─────────────────────────────────────────────────────────────"

PYTHON_TEST=$(cat << 'PYEOF'
import sys
sys.path.insert(0, '/home/dan/Nevil-picar-v3')

from nevil_framework.utils.system_detection import SystemDetector

print("Headless detection:", SystemDetector.is_headless())
print("\nNetwork status:")
status = SystemDetector.get_network_status()
for key, value in status.items():
    print(f"  {key}: {value}")
PYEOF
)

if python3 -c "$PYTHON_TEST" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Python module test passed"
else
    echo -e "${RED}✗${NC} Python module test failed"
    echo "   Make sure system_detection.py is installed correctly"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                      Test Summary                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

if [ "$HEADLESS" = true ]; then
    echo -e "${YELLOW}Mode:${NC} HEADLESS"
    echo ""
    echo "When Nevil service starts in this mode:"
    echo "  1. Will attempt to connect to configured WiFi (summerdome)"
    echo "  2. If WiFi unavailable, will enable hotspot automatically"
    echo "  3. You can connect to: SSID=Nevil-Robot, Password=nevil2025"
    echo "  4. Access Nevil via hotspot IP (typically 10.42.0.1)"
else
    echo -e "${GREEN}Mode:${NC} DISPLAY ATTACHED"
    echo ""
    echo "When Nevil service starts in this mode:"
    echo "  1. Will attempt to connect to configured WiFi"
    echo "  2. No automatic hotspot (user can configure via desktop)"
    echo "  3. Network configuration available through GUI"
fi

echo ""
echo "─────────────────────────────────────────────────────────────"
echo "To test network setup script directly:"
echo "  sudo /home/dan/Nevil-picar-v3/scripts/network_setup.sh"
echo ""
echo "To view network setup logs:"
echo "  tail -f /home/dan/Nevil-picar-v3/logs/network_setup.log"
echo "─────────────────────────────────────────────────────────────"
echo ""
