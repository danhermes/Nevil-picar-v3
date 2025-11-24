#!/bin/bash
# Install or update Nevil systemd service with proper audio dependencies

set -e

echo "Installing Nevil systemd service..."

# Get the script's directory (where nevil project is)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"

# Create the service file
sudo tee /etc/systemd/system/nevil.service > /dev/null << EOF
[Unit]
Description=Nevil Robot System
After=network.target sound.target auto_sound_card.service
Wants=network.target auto_sound_card.service

[Service]
Type=simple
User=dan
Group=dan
# Include supplementary groups for hardware access
SupplementaryGroups=audio video gpio i2c spi input render

WorkingDirectory=$PROJECT_DIR
# Pre-start: Configure hardware and network
ExecStartPre=/usr/bin/pinctrl set 20 op dh
ExecStartPre=/usr/bin/amixer -c 3 set Mic 16
ExecStart=$PROJECT_DIR/nevil start
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Environment variables for user session access
Environment=HOME=/home/dan
Environment=USER=dan
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=ALSA_VERBOSITY=0
Environment=HIDE_ALSA_LOGGING=true

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created at /etc/systemd/system/nevil.service"

# Reload systemd
sudo systemctl daemon-reload
echo "✓ Systemd configuration reloaded"

# Enable the service
sudo systemctl enable nevil.service
echo "✓ Nevil service enabled"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Nevil service installed successfully!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Service configuration:"
echo "  • Waits for: auto_sound_card.service (ensures audio configured first)"
echo "  • Waits for: sound.target, network.target"
echo "  • Pre-start: Network setup (intelligent WiFi selection)"
echo "  • Pre-start: GPIO/audio hardware configuration"
echo "  • Runs as: dan (with audio/video/gpio groups)"
echo "  • Auto-restart: on-failure"
echo ""
echo "Network behavior:"
echo "  • Scans for known WiFi networks and selects best available"
echo "  • Priority: summerdome > LinkedSys7 > LinkedSys7_EXT"
echo "  • Headless fallback: Connects to iPhone hotspot if no WiFi available"
echo "  • Display mode: User configures network manually if needed"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start nevil"
echo "  Stop:    sudo systemctl stop nevil"
echo "  Status:  sudo systemctl status nevil"
echo "  Logs:    journalctl -u nevil -f"
echo ""
echo "Note: Service will auto-start on boot"
echo ""
