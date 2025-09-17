# Nevil Boot Service Setup

This document explains how to configure Nevil to automatically start when the Raspberry Pi boots up, running headlessly without requiring a display or keyboard.

## Overview

Nevil uses systemd to automatically start on boot. The system will:
- Start Nevil after network and audio services are ready
- Run headlessly (no display/keyboard needed)
- Automatically use built-in speaker when no HDMI display is connected
- Restart Nevil if it crashes
- Provide proper logging and management capabilities

## Service Configuration

The systemd service file is located at `/etc/systemd/system/nevil.service`:

```ini
[Unit]
Description=Nevil Robot System
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/dan/Nevil-picar-v3
ExecStart=/home/dan/Nevil-picar-v3/nevil start
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Environment
Environment=HOME=/home/dan
Environment=USER=dan

[Install]
WantedBy=multi-user.target
```

## Installation Commands

To set up the auto-boot service:

```bash
# Copy service file to system location
sudo cp nevil.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable nevil
```

## Management Commands

### Check Service Status
```bash
sudo systemctl status nevil
```

### Start/Stop Service Manually
```bash
sudo systemctl start nevil   # Start now
sudo systemctl stop nevil    # Stop now
```

### View Logs
```bash
journalctl -u nevil -f       # Follow live logs
journalctl -u nevil          # View all logs
journalctl -u nevil --since today  # Today's logs
```

### Disable Auto-Boot
```bash
sudo systemctl disable nevil
```

## Audio Configuration

The Raspberry Pi OS automatically handles audio routing:
- When HDMI display is connected: Audio goes to HDMI
- When no HDMI display: Audio automatically switches to built-in speaker/headphone jack
- No manual configuration needed

## Headless Operation

Once configured, Nevil will:
1. Start automatically when Pi boots
2. Run without requiring display/keyboard
3. Use built-in speaker automatically
4. Be accessible via SSH if needed
5. Restart automatically if crashed

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status nevil

# Check detailed logs
journalctl -u nevil --no-pager
```

### Permission Issues
Ensure the `dan` user has proper permissions for:
- Nevil directory and files
- Audio devices
- GPIO access (if using hardware)

### Network Dependencies
The service waits for network to be ready before starting. If network issues occur, check:
```bash
systemctl status network.target
```

## File Locations

- Service file: `/etc/systemd/system/nevil.service`
- Nevil executable: `/home/dan/Nevil-picar-v3/nevil`
- Working directory: `/home/dan/Nevil-picar-v3/`
- Logs: Available via `journalctl -u nevil`

## Why Systemd vs Alternatives

**Systemd advantages over cron/rc.local:**
- Proper dependency management (waits for network/audio)
- Automatic restart on failure
- Better logging integration
- Clean shutdown handling
- Easy service management
- Resource monitoring

This setup provides a robust, production-ready auto-boot configuration for Nevil.