#!/bin/bash

# Nevil v3.0 Launcher with ALSA Suppression
# This script suppresses ALSA messages at the shell level

# Export ALSA suppression environment variables
export ALSA_VERBOSITY=0
export ALSA_LOG_LEVEL=0
export LIBASOUND_DEBUG=0
export HIDE_ALSA_LOGGING=true

# Nuclear ALSA suppression - filter ALL ALSA-related output
exec 2> >(
    while IFS= read -r line; do
        # Block ALL ALSA/audio-related messages
        if [[ ! "$line" =~ (ALSA|alsa|snd_|pcm_|confmisc|_snd_|mixer|audio|Invalid card|cannot find|control element|Unknown PCM|Broken pipe|Input/output error|Device or resource busy) ]]; then
            echo "$line" >&2
        fi
    done
)

python3 -m nevil_framework.launcher "$@"