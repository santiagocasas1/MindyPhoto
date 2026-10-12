#!/usr/bin/env bash
# Technical + visual QA for a delivered MP4.  Usage: bash tools/qa.sh ../output/AFM_BRAND_Reels_1080p.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
F="$1"
Q="../output/qa"
mkdir -p "$Q"
name=$(basename "$F" .mp4)

echo "== ffprobe"; ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,profile,level,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,color_space,color_primaries,color_transfer,color_range,sample_rate,channels,channel_layout,bit_rate,duration -of json "$F" | tee "$Q/${name}_ffprobe.json"

echo "== black frames (pix_th 0.10, min 0.1 s)"
ffmpeg -hide_banner -nostats -i "$F" -vf blackdetect=d=0.1:pix_th=0.10 -an -f null - 2>&1 | grep blackdetect || echo "none"

echo "== frozen picture (> 0.6 s)"
ffmpeg -hide_banner -nostats -i "$F" -vf freezedetect=n=0.0015:d=0.6 -an -f null - 2>&1 | grep -E "freeze_(start|end|duration)" || echo "none"

echo "== silence (< -50 dB for > 0.3 s)"
ffmpeg -hide_banner -nostats -i "$F" -af silencedetect=n=-50dB:d=0.3 -vn -f null - 2>&1 | grep -E "silence_(start|end)" || echo "none"

echo "== loudness / true peak"
ffmpeg -hide_banner -nostats -i "$F" -af ebur128=peak=true -vn -f null - 2>&1 | grep -A14 "Summary" | grep -E "I:|LRA:|Peak:"

echo "== contact sheets (every 0.5 s) and transition strips"
ffmpeg -hide_banner -loglevel error -y -i "$F" -vf "fps=2,scale=216:384,tile=10x6:padding=4:margin=4" -frames:v 1 "$Q/${name}_contact_0.5s.png"
for c in 3.40 3.90 7.40 7.95 8.85 10.30 17.85 21.00 25.50 25.95; do
  ffmpeg -hide_banner -loglevel error -y -ss "$c" -i "$F" -vf "fps=30,scale=216:384,tile=6x1:padding=4:margin=4" -frames:v 1 "$Q/${name}_transition_${c}.png"
done
ffmpeg -hide_banner -loglevel error -y -sseof -0.04 -i "$F" -frames:v 1 "$Q/${name}_last_frame.png"
ffmpeg -hide_banner -loglevel error -y -ss 0 -i "$F" -frames:v 1 "$Q/${name}_first_frame.png"

echo "== audio onsets at the scripted impacts (should sit within one video frame)"
python3 - "$F" <<'EOF'
import json, subprocess, sys, numpy as np
f = sys.argv[1]
T = json.load(open("config/timeline.json"))
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32)
sr = 48000
hop = 240  # 5 ms windows
e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(x) - hop, hop)])
db = 20 * np.log10(e)
for name, t in [("impactReveal", T["cues"]["impactReveal"]), ("drop", T["cues"]["drop"]), ("impactEnd", T["cues"]["impactEnd"])]:
    i = int(t * sr / hop)
    pre = np.median(db[i - 30:i - 10])          # level 50-150 ms before the cue
    k = i - 10
    while k < i + 40 and db[k] < pre + 6:       # first 5 ms window 6 dB above the bed
        k += 1
    onset = k * hop / sr
    print(f"{name:13s} scripted {t:6.3f}s  attack starts {onset:6.3f}s  offset {1000*(onset-t):+6.1f} ms  (bed {pre:5.1f} dBFS -> {db[k]:5.1f})")
print(f"audio length {len(x)/sr:.3f}s")
EOF
