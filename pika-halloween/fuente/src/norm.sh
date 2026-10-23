#!/bin/bash
# usage: norm.sh in.wav out.wav  -> loudness-normalise to -14 LUFS
I=$(ffmpeg -hide_banner -i "$1" -af ebur128 -f null - 2>&1 | grep -A3 Summary | grep "I:" | awk '{print $2}')
G=$(python3 -c "print(-14-($I))")
ffmpeg -v error -y -i "$1" -af "volume=${G}dB" "$2"
ffmpeg -hide_banner -i "$2" -af ebur128=peak=true -f null - 2>&1 | grep -A20 Summary | grep -E "I:|Peak:" | tr -s ' '
