#!/bin/bash
# encode.sh clip orient  -> repo assets/video/<clip>-<o>.mp4 + .jpg poster
cd "$(dirname "$0")"
c=$1; o=$2; D=/home/claude/afo-repo/assets/video
ffmpeg -y -loglevel error -framerate 12 -i out/$c-$o/f%04d.png \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p" \
  -c:v libx264 -profile:v high -crf 26 -preset slow -g 24 -movflags +faststart -an $D/$c-$o.mp4
ffmpeg -y -loglevel error -i out/$c-$o/f0001.png -q:v 5 $D/$c-$o.jpg
ls -la $D/$c-$o.*
ffmpeg -y -loglevel error -i $D/$c-$o.mp4 -c:v libvpx-vp9 -b:v 0 -crf 38 -row-mt 1 -deadline good -cpu-used 4 -an $D/$c-$o.webm
ls -la $D/$c-$o.webm
