#!/bin/bash

# Ultimate ALSA Suppression Script
# Uses unbuffered output and real-time filtering to eliminate ALL ALSA messages

# Export ALSA suppression environment variables
export ALSA_VERBOSITY=0
export ALSA_LOG_LEVEL=0
export LIBASOUND_DEBUG=0
export HIDE_ALSA_LOGGING=true

# Suppress all ALSA-related stderr output using stdbuf + sed
stdbuf -oL -eL python3 -m nevil_framework.launcher "$@" 2> >(
    stdbuf -oL sed -u \
        -e '/ALSA lib/d' \
        -e '/alsa_/d' \
        -e '/snd_/d' \
        -e '/pcm_/d' \
        -e '/confmisc/d' \
        -e '/Cannot get card index/d' \
        -e '/Unknown PCM/d' \
        -e '/cannot find card/d' \
        -e '/Invalid field card/d' \
        -e '/Device or resource busy/d' \
        -e '/No such file or directory/d' \
        -e '/Unable to find definition/d' \
        -e '/function.*returned error/d' \
        -e '/Evaluate error/d' \
        -e '/Cannot open device/d' \
        -e '/dmix plugin supports only/d' \
        -e '/unable to open slave/d' \
        -e '/a52 is only for playback/d' \
        >&2
)