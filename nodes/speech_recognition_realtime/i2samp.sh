#!/bin/bash

: <<'DISCLAIMER'

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

This script is licensed under the terms of the MIT license.
Unless otherwise noted, code reproduced herein
was written for this script.

- The Pimoroni Crew - (modified by Adafruit!)

DISCLAIMER

# script control variables
# =================================================================
productname="i2s amplifier" # the name of the product to install
scriptname="i2samp" # the name of this script
spacereq=1 # minimum size required on root partition in MB
debugmode="no" # whether the script should use debug routines
debuguser="none" # optional test git user to use in debug mode
debugpoint="none" # optional git repo branch or tag to checkout
forcesudo="no" # whether the script requires to be ran with root privileges
promptreboot="no" # whether the script should always prompt user to reboot
mininstall="no" # whether the script enforces minimum install routine
customcmd="yes" # whether to execute commands specified before exit
armv6="yes" # whether armv6 processors are supported
armv7="yes" # whether armv7 processors are supported
armv8="yes" # whether armv8 processors are supported
arm64="yes" # whether arm64 processors are supported
raspbianonly="no" # whether the script is allowed to run on other OSes
osreleases=( "Raspbian" ) # list os-releases supported
oswarning=( "Debian" "Kano" "Mate" "PiTop" "Ubuntu" ) # list experimental os-releases
osdeny=( "Darwin" "Kali" ) # list os-releases specifically disallowed

FORCE=$1
NO_APLAY=false
DEVICE_TREE=true
ASK_TO_REBOOT=false
CURRENT_SETTING=false
UPDATE_DB=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        -y)
            FORCE='-y'
            ;;
        -n|--no-aplay)
            NO_APLAY=true
            ;;
        -yn|-ny)
            FORCE='-y'
            NO_APLAY=true
            ;;
    esac
done

BOOTCMD=/boot/firmware/cmdline.txt
CONFIG=/boot/firmware/config.txt
APTSRC=/etc/apt/sources.list
INITABCONF=/etc/inittab
BLACKLIST=/etc/modprobe.d/raspi-blacklist.conf
LOADMOD=/etc/modules
DTBODIR=/boot/overlays

AUTO_SOUND_CARD=/usr/local/bin/auto_sound_card

# Fall back to old location
if ! test -f $CONFIG; then
    CONFIG=/boot/config.txt
fi

# function define
# =================================================================
confirm() {
    if [ "$FORCE" == '-y' ]; then
        true
    else
        read -r -p "$1 [y/N] " response < /dev/tty
        if [[ $response =~ ^(yes|y|Y)$ ]]; then
            true
        else
            false
        fi
    fi
}

prompt() {
        read -r -p "$1 [y/N] " response < /dev/tty
        if [[ $response =~ ^(yes|y|Y)$ ]]; then
            true
        else
            false
        fi
}

success() {
    echo -e "$(tput setaf 2)$1$(tput sgr0)"
}

inform() {
    echo -e "$(tput setaf 6)$1$(tput sgr0)"
}

warning() {
    echo -e "$(tput setaf 1)$1$(tput sgr0)"
}

newline() {
    echo ""
}

progress() {
    count=0
    until [ $count -eq $1 ]; do
        echo -n "..." && sleep 1
        ((count++))
    done
    echo
}
sudocheck() {
    if [ $(id -u) -ne 0 ]; then
        echo -e "Install must be run as root. Try 'sudo ./$scriptname'\n"
        exit 1
    fi
}

sysclean() {
    sudo apt-get clean && sudo apt-get autoclean
    sudo apt-get -y autoremove &> /dev/null
}

sysupdate() {
    if ! $UPDATE_DB; then
        echo "Updating apt indexes..." && progress 3 &
        sudo apt-get update 1> /dev/null || { warning "Apt failed to update indexes!" && exit 1; }
        echo "Reading package lists..."
        progress 3 && UPDATE_DB=true
    fi
}

sysupgrade() {
    sudo apt-get upgrade
    sudo apt-get clean && sudo apt-get autoclean
    sudo apt-get -y autoremove &> /dev/null
}

sysreboot() {
    warning "Some changes made to your system require"
    warning "your computer to reboot to take effect."
    newline
    if prompt "Would you like to reboot now?"; then
        sync && sudo reboot
    fi
}

arch_check() {
    IS_ARM64=false
    IS_ARMHF=false
    IS_ARMv6=false

    if uname -m | grep "aarch64" > /dev/null; then
        IS_ARM64=true
    fi
    if uname -m | grep "armv.l" > /dev/null; then
        IS_ARMHF=true
        if uname -m | grep "armv6l" > /dev/null; then
            IS_ARMv6=true
        fi
    fi
}

os_check() {
    IS_RASPBIAN=false
    IS_MACOSX=false
    IS_SUPPORTED=false
    IS_EXPERIMENTAL=false

    if [ -f /etc/os-release ]; then
        if cat /etc/os-release | grep "Raspbian" > /dev/null; then
            IS_RASPBIAN=true && IS_SUPPORTED=true
        fi
        if command -v apt-get > /dev/null; then
            for os in ${osreleases[@]}; do
                if cat /etc/os-release | grep $os > /dev/null; then
                    IS_SUPPORTED=true && IS_EXPERIMENTAL=false
                fi
            done
            for os in ${oswarning[@]}; do
                if cat /etc/os-release | grep $os > /dev/null; then
                    IS_SUPPORTED=false && IS_EXPERIMENTAL=true
                fi
            done
            for os in ${osdeny[@]}; do
                if cat /etc/os-release | grep $os > /dev/null; then
                    IS_SUPPORTED=false && IS_EXPERIMENTAL=false
                fi
            done
        fi
    fi
    if [ -d ~/.kano-settings ] || [ -d ~/.kanoprofile ]; then
        IS_RASPBIAN=false
        for os in ${oswarning[@]}; do
            if [ $os == "Kano" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=true
            fi
        done
        for os in ${osdeny[@]}; do
            if [ $os == "Kano" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=false
            fi
        done
    fi
    if [ -f ~/.pt-dashboard-config ] || [ -d ~/.pt-dashboard ] || [ -d ~/.pt-os-dashboard ]; then
        IS_RASPBIAN=false
        for os in ${oswarning[@]}; do
            if [ $os == "PiTop" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=true
            fi
        done
        for os in ${osdeny[@]}; do
            if [ $os == "PiTop" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=false
            fi
        done
    fi
    if [ -d ~/.config/ubuntu-mate ]; then
        for os in ${osdeny[@]}; do
            if [ $os == "Mate" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=false
            fi
        done
    fi
    if uname -s | grep "Darwin" > /dev/null; then
        IS_MACOSX=true
        for os in ${osdeny[@]}; do
            if [ $os == "Darwin" ]; then
                IS_SUPPORTED=false && IS_EXPERIMENTAL=false
            fi
        done
    fi
}

raspbian_check() {
    IS_SUPPORTED=false
    IS_EXPERIMENTAL=false

    if [ -f /etc/os-release ]; then
        if cat /etc/os-release | grep "/sid" > /dev/null; then
            IS_SUPPORTED=false && IS_EXPERIMENTAL=true
        elif cat /etc/os-release | grep "bookworm" > /dev/null; then
            IS_SUPPORTED=false && IS_EXPERIMENTAL=true
        elif cat /etc/os-release | grep "bullseye" > /dev/null; then
            IS_SUPPORTED=false && IS_EXPERIMENTAL=true
        elif cat /etc/os-release | grep "buster" > /dev/null; then
            IS_SUPPORTED=false && IS_EXPERIMENTAL=true
        elif cat /etc/os-release | grep "stretch" > /dev/null; then
            IS_SUPPORTED=false && IS_EXPERIMENTAL=false
        elif cat /etc/os-release | grep "jessie" > /dev/null; then
            IS_SUPPORTED=true && IS_EXPERIMENTAL=false
        elif cat /etc/os-release | grep "wheezy" > /dev/null; then
            IS_SUPPORTED=true && IS_EXPERIMENTAL=false
        else
            IS_SUPPORTED=false && IS_EXPERIMENTAL=false
        fi
    fi
}

# main
# =================================================================
: <<'MAINSTART'

Perform all global variables declarations as well as function definition
above this section for clarity, thanks!

MAINSTART

# check platform
#=======================
arch_check
os_check

if [ $debugmode != "no" ]; then
    echo "USER_HOME is $USER_HOME" && newline
    echo "IS_RASPBIAN is $IS_RASPBIAN"
    echo "IS_MACOSX is $IS_MACOSX"
    echo "IS_SUPPORTED is $IS_SUPPORTED"
    echo "IS_EXPERIMENTAL is $IS_EXPERIMENTAL"
    newline
fi

if ! $IS_ARMHF && ! $IS_ARM64; then
    warning "This hardware is not supported, sorry!"
    warning "Config files have been left untouched"
    newline && exit 1
fi

if $IS_ARM64 && [ $arm64 == "no" ]; then
    warning "Sorry, your CPU is not supported by this installer"
    newline && exit 1
elif $IS_ARMv8 && [ $armv8 == "no" ]; then
    warning "Sorry, your CPU is not supported by this installer"
    newline && exit 1
elif $IS_ARMv7 && [ $armv7 == "no" ]; then
    warning "Sorry, your CPU is not supported by this installer"
    newline && exit 1
elif $IS_ARMv6 && [ $armv6 == "no" ]; then
    warning "Sorry, your CPU is not supported by this installer"
    newline && exit 1
fi

if [ $raspbianonly == "yes" ] && ! $IS_RASPBIAN;then
        warning "This script is intended for Raspbian on a Raspberry Pi!"
        newline && exit 1
fi

if $IS_RASPBIAN; then
    raspbian_check
    if ! $IS_SUPPORTED && ! $IS_EXPERIMENTAL; then
        newline && warning "--- Warning ---" && newline
        echo "The $productname installer"
        echo "does not work on this version of Raspbian."
        echo "Check https://github.com/$gitusername/$gitreponame"
        echo "for additional information and support"
        newline && exit 1
    fi
fi

if ! $IS_SUPPORTED && ! $IS_EXPERIMENTAL; then
        warning "Your operating system is not supported, sorry!"
        newline && exit 1
fi

if $IS_EXPERIMENTAL; then
    warning "Support for your operating system is experimental. Please visit"
    warning "forums.adafruit.com if you experience issues with this product."
    newline
fi

if [ $forcesudo == "yes" ]; then
    sudocheck
fi

newline
echo "This script will install everything needed to use"
echo "$productname"
newline
warning "--- Warning ---"
newline
echo "Always be careful when running scripts and commands"
echo "copied from the internet. Ensure they are from a"
echo "trusted source."
newline
echo "If you want to see what this script does before"
echo "running it, you should run:"
echo "    \curl -sS github.com/adafruit/Raspberry-Pi-Installer-Scripts/$scriptname"
newline

# ask whether to continue
#=======================
if ! confirm "Do you wish to continue?"; then
    newline
    echo "Aborting..."
    newline
    exit 0
fi

# config dtoverlay
#=======================
newline
echo "Checking hardware requirements..."

if [ -e $CONFIG ] && grep -q "^device_tree=$" $CONFIG; then
    DEVICE_TREE=false
fi

if $DEVICE_TREE; then

    newline
    echo "Adding Device Tree Entry to $CONFIG"

    if [ -e $CONFIG ] && grep -q "^dtoverlay=hifiberry-dac$" $CONFIG; then
        echo "dtoverlay already active"
    else
        echo "dtoverlay=hifiberry-dac" | sudo tee -a $CONFIG
        ASK_TO_REBOOT=true
    fi

    if [ -e $CONFIG ] && grep -q "^dtoverlay=i2s-mmap$" $CONFIG; then
        echo "i2s mmap dtoverlay already active"
    else
        echo "dtoverlay=i2s-mmap" | sudo tee -a $CONFIG
        ASK_TO_REBOOT=true
    fi

    if [ -e $BLACKLIST ]; then
        newline
        echo "Commenting out Blacklist entry in "
        echo "$BLACKLIST"
        sudo sed -i -e "s|^blacklist[[:space:]]*i2c-bcm2708.*|#blacklist i2c-bcm2708|" \
                    -e "s|^blacklist[[:space:]]*snd-soc-pcm512x.*|#blacklist snd-soc-pcm512x|" \
                    -e "s|^blacklist[[:space:]]*snd-soc-wm8804.*|#blacklist snd-soc-wm8804|" $BLACKLIST &> /dev/null
    fi
else
    newline
    echo "No Device Tree Detected, not supported"
    newline
    exit 1
fi

# install alsa-utils 
#=======================
sudo apt install alsa-utils -y

# aplay from /dev/zero at system start
#=======================
# DISABLED: This service blocks the HiFiBerry DAC exclusively and prevents other audio from playing
# If you need this for click/pop reduction, consider using dmix for shared access instead
# newline
# echo "Installing aplay systemd unit"
# sudo sh -c 'cat > /etc/systemd/system/aplay.service' << 'EOL'
# [Unit]
# Description=Invoke aplay from /dev/zero at system start.
#
# [Service]
# ExecStart=/usr/bin/aplay -D default -t raw -r 44100 -c 2 -f S16_LE /dev/zero
#
# [Install]
# WantedBy=multi-user.target
# EOL
#
# sudo systemctl daemon-reload
# sudo systemctl disable aplay
# newline
#
# if ! $NO_APLAY; then
#     echo "You can optionally activate '/dev/zero' playback in"
#     echo "the background at boot. This will remove all"
#     echo "popping/clicking but does use some processor time."
#     newline
#     if confirm "Activate '/dev/zero' playback in background? [RECOMMENDED]"; then
#     newline
#     sudo systemctl enable aplay
#     ASK_TO_REBOOT=true
#     fi
# else
#     echo "Skipping aplay /dev/zero background playback (--no-aplay flag set)"
#     newline
# fi

# config asound
#=======================
newline
echo "Configuring sound output"
# backup file
if [ -e /etc/asound.conf ]; then
    if [ -e /etc/asound.conf.old ]; then
        sudo rm -f /etc/asound.conf.old
    fi
    sudo cp /etc/asound.conf /etc/asound.conf.old
fi

# auto_sound_card scripts
# This script will be installed to: /usr/local/bin/auto_sound_card
# Logs the last 10 calls with BEFORE/AFTER state to: /var/log/auto_sound_card.log
# To view log: cat /var/log/auto_sound_card.log
# Each log entry shows:
#   - BEFORE: Current asound.conf card, running card states, open audio devices
#   - AFTER: Target configuration (card, volumes, mic settings)

sudo cat > /usr/local/bin/auto_sound_card << '-EOF'
#!/bin/bash

ASOUND_CONF=/etc/asound.conf
AUDIO_CARD_NAME="sndrpihifiberry"
LOG_FILE=/var/log/auto_sound_card.log

# Function to log calls with timestamp, card_num, card_name, mic info, and volumes
# Maintains only the last 10 calls in /var/log/auto_sound_card.log
# Log format: [YYYY-MM-DD HH:MM:SS] auto_sound_card called with card_num=N card_name=NAME speaker_vol=X% mic_card=M mic_device=D mic_name=MIC_NAME mic_vol=Y%
log_call() {
    local card_num=$1
    local card_name=$2
    local speaker_vol=$3
    local mic_card=$4
    local mic_device=$5
    local mic_name=$6
    local mic_vol=$7
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Log what was CURRENTLY in use before changes
    echo "[$timestamp] === BEFORE CHANGES ===" >> $LOG_FILE

    # Check current asound.conf card
    if [ -f "$ASOUND_CONF" ]; then
        current_card=$(grep "type hw card" $ASOUND_CONF 2>/dev/null | awk '{print $4}' | head -1)
        if [ -n "$current_card" ]; then
            current_card_name=$(aplay -l 2>/dev/null | grep "^card $current_card:" | awk -F'[\\[\\]]' '{print $2}')
            echo "[$timestamp] Current asound.conf: card=$current_card name=$current_card_name" >> $LOG_FILE
        else
            echo "[$timestamp] Current asound.conf: not configured or invalid" >> $LOG_FILE
        fi
    else
        echo "[$timestamp] Current asound.conf: does not exist" >> $LOG_FILE
    fi

    # Check which card devices are currently OPEN/RUNNING
    for card in 0 1 2 3; do
        if [ -f "/proc/asound/card$card/pcm0p/sub0/status" ]; then
            card_state=$(grep "state:" /proc/asound/card$card/pcm0p/sub0/status 2>/dev/null | awk '{print $2}')
            if [ "$card_state" = "RUNNING" ] || [ "$card_state" = "PREPARED" ]; then
                card_info=$(aplay -l 2>/dev/null | grep "^card $card:" | awk -F'[\\[\\]]' '{print $2}')
                echo "[$timestamp] Card $card ($card_info) state: $card_state" >> $LOG_FILE
            fi
        fi
    done

    # Check which processes have audio devices open
    lsof_out=$(lsof /dev/snd/pcmC*D0p 2>/dev/null | tail -n +2)
    if [ -n "$lsof_out" ]; then
        echo "[$timestamp] Open audio devices:" >> $LOG_FILE
        echo "$lsof_out" | while read line; do
            echo "[$timestamp]   $line" >> $LOG_FILE
        done
    else
        echo "[$timestamp] No audio devices currently open" >> $LOG_FILE
    fi

    echo "[$timestamp] === AFTER CHANGES (TARGET) ===" >> $LOG_FILE
    echo "[$timestamp] Setting to: card_num=$card_num card_name=$card_name speaker_vol=$speaker_vol mic_card=$mic_card mic_device=$mic_device mic_name=$mic_name mic_vol=$mic_vol" >> $LOG_FILE

    # Keep only last 10 entries (increased from 5 due to multi-line logging)
    tail -n 10 $LOG_FILE > $LOG_FILE.tmp && mv $LOG_FILE.tmp $LOG_FILE
}

# Detect output sound card (speaker/DAC)
card_num=$(sudo aplay -l |grep $AUDIO_CARD_NAME |awk '{print $2}'|tr -d ':')
card_name=$(sudo aplay -l |grep $AUDIO_CARD_NAME |awk -F'[\\[\\]]' '{print $2}')
echo "card_num=$card_num"
echo "card_name=$card_name"

# Get speaker volume (PCM control on the output card)
if [ -n "$card_num" ]; then
    speaker_vol=$(amixer -c $card_num get PCM 2>/dev/null | grep -oP '\d+%' | head -1)
    if [ -z "$speaker_vol" ]; then
        speaker_vol="N/A"
    fi
else
    speaker_vol="N/A"
fi
echo "speaker_vol=$speaker_vol"

# Detect microphone input device
# Look for USB microphone first, then other input devices
mic_info=$(sudo arecord -l 2>/dev/null | grep -E "card [0-9]:" | head -1)
if [ -n "$mic_info" ]; then
    mic_card=$(echo "$mic_info" | awk '{print $2}' | tr -d ':')
    mic_device=$(echo "$mic_info" | awk '{print $6}' | tr -d ':')
    mic_name=$(echo "$mic_info" | awk -F'[\\[\\]]' '{print $2}')

    # Get microphone volume/capture level
    # Try common capture control names: Mic, Capture, PCM Capture
    mic_vol=$(amixer -c $mic_card get Mic 2>/dev/null | grep -oP '\d+%' | head -1)
    if [ -z "$mic_vol" ]; then
        mic_vol=$(amixer -c $mic_card get Capture 2>/dev/null | grep -oP '\d+%' | head -1)
    fi
    if [ -z "$mic_vol" ]; then
        mic_vol="N/A"
    fi
else
    mic_card="none"
    mic_device="none"
    mic_name="none"
    mic_vol="N/A"
fi
echo "mic_card=$mic_card"
echo "mic_device=$mic_device"
echo "mic_name=$mic_name"
echo "mic_vol=$mic_vol"

# Log this call with both output and input info including volumes
log_call "$card_num" "$card_name" "$speaker_vol" "$mic_card" "$mic_device" "$mic_name" "$mic_vol"
if [ -n "$card_num" ]; then
    cat > $ASOUND_CONF << EOF
pcm.speakerbonnet {
    type hw card $card_num
}

pcm.dmixer {
    type dmix
    ipc_key 1024
    ipc_perm 0666
    slave {
        pcm "speakerbonnet"
        period_time 0
        period_size 1024
        buffer_size 8192
        rate 44100
        channels 2
    }
}

ctl.dmixer {
    type hw card $card_num
}

pcm.softvol {
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card $card_num
}

ctl.softvol {
    type hw card $card_num
}

pcm.!default {
    type             plug
    slave.pcm       "softvol"
}
EOF
    # DO NOT restart aplay.service - it blocks audio playback
    # echo "systemctl restart aplay.service"
    # sudo systemctl restart aplay.service

    if [ -n $1 ] && [ $1 -gt 0 ]; then
        echo "set volume to $1"
        amixer -c $card_num sset PCM $1%
    fi

fi

exit 0
-EOF

sudo chmod +x /usr/local/bin/auto_sound_card

# stop and disable existing service if it exists
if systemctl is-enabled --quiet auto_sound_card.service 2>/dev/null; then
    echo "Stopping and disabling existing auto_sound_card service..."
    sudo systemctl stop auto_sound_card.service
    sudo systemctl disable auto_sound_card.service
fi

# execute the script once
sudo /usr/local/bin/auto_sound_card 100

# add auto_sound_card start on boot
sudo cat > /etc/systemd/system/auto_sound_card.service << EOF
[Unit]
Description=Auto config als sound card num at system start.

[Service]
Type=oneshot
User=dan
Group=dan
SupplementaryGroups=audio
ExecStart=/usr/local/bin/auto_sound_card

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable auto_sound_card

#=======================
newline
echo "We can now test your $productname"
warning "Set your speakers if possible!"
if confirm "Do you wish to test your system now?"; then
    echo "Testing..."
    pinctrl set 20 op dh
    speaker-test -l5 -c2 -t wav
fi
newline
success "All done!"
newline
echo "Enjoy your new $productname!"
newline

if [ $promptreboot == "yes" ] || $ASK_TO_REBOOT; then
    sysreboot
fi

# end
# =======================
exit 0
