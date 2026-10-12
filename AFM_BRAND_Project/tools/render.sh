#!/usr/bin/env bash
# Render the commercial and encode the delivery MP4.
#   bash tools/render.sh 1080   -> ../output/AFM_BRAND_Reels_1080p.mp4   (1080x1920, real render)
#   bash tools/render.sh 4k     -> ../output/AFM_BRAND_Cinematic_4K.mp4  (2160x3840, real render at 2x device scale)
# Frames are rendered losslessly (PNG) by Remotion, then encoded once by FFmpeg with
# explicit BT.709 conversion and tags (SDR Rec.709, limited range), H.264 High, CFR 30 fps,
# AAC-LC 48 kHz stereo.
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-1080}"
BROWSER="${AFM_BROWSER:-}"
CONC="${AFM_CONCURRENCY:-2}"
OUT_DIR="../output"
mkdir -p "$OUT_DIR" out

[ -f public/audio/soundtrack.wav ] || python3 audio/compose.py

if [ "$MODE" = "4k" ]; then
  SCALE=2; FRAMES=out/frames_4k; FILE="$OUT_DIR/AFM_BRAND_Cinematic_4K.mp4"
  VOPTS=(-profile:v high -level:v 5.1 -b:v 45M -maxrate 60M -bufsize 90M)
else
  SCALE=1; FRAMES=out/frames_1080; FILE="$OUT_DIR/AFM_BRAND_Reels_1080p.mp4"
  VOPTS=(-profile:v high -level:v 4.2 -b:v 16M -maxrate 22M -bufsize 32M)
fi

rm -rf "$FRAMES"
npx remotion render src/index.ts AFMCommercial "$FRAMES" \
  --sequence --image-format=png --scale="$SCALE" --concurrency="$CONC" --gl=swangle \
  ${BROWSER:+--browser-executable="$BROWSER"} --log=info

# Remotion names frames element-000.png … element-899.png
PATTERN="$FRAMES/element-%03d.png"
COUNT=$(ls "$FRAMES"/element-*.png | wc -l)
[ "$COUNT" -eq 900 ] || { echo "expected 900 frames, got $COUNT" >&2; exit 1; }

ENC=(-framerate 30 -i "$PATTERN" -i public/audio/soundtrack.wav
  -map 0:v:0 -map 1:a:0
  -vf "scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p,noise=c0s=5:c0f=t+u"
  -c:v libx264 -preset slow "${VOPTS[@]}" -pix_fmt yuv420p -g 60 -keyint_min 30 -bf 2
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv
  -r 30 -fps_mode cfr
  -c:a aac -b:a 320k -ar 48000 -ac 2
  -t 30 -movflags +faststart)

ffmpeg -hide_banner -y "${ENC[@]}" -pass 1 -an -f mp4 /dev/null
ffmpeg -hide_banner -y "${ENC[@]}" -pass 2 "$FILE"
rm -f ffmpeg2pass-0.log ffmpeg2pass-0.log.mbtree
echo "wrote $FILE"
