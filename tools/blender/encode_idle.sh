#!/bin/bash
cd "$(dirname "$0")"
c=$1; o=$2; D=/home/claude/afo-repo/assets/video; T=/tmp/idle-$c-$o.mp4
ffmpeg -y -loglevel error -framerate 12 -i out/$c-$o-idle/f%04d.png -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p" -c:v libx264 -crf 14 -preset fast $T
ffmpeg -y -loglevel error -i $T -filter_complex "[0:v]split[a][b];[a]trim=1:4,setpts=PTS-STARTPTS[m];[b]trim=0:1,setpts=PTS-STARTPTS[h];[m][h]xfade=transition=fade:duration=1:offset=2,format=yuv420p[v]" -map "[v]" -c:v libx264 -profile:v high -crf 26 -preset slow -g 24 -movflags +faststart -an $D/$c-idle-$o.mp4
ffmpeg -y -loglevel error -i $D/$c-idle-$o.mp4 -frames:v 1 -q:v 5 $D/$c-idle-$o.jpg
ffmpeg -y -loglevel error -i $D/$c-idle-$o.mp4 -c:v libvpx-vp9 -b:v 0 -crf 38 -row-mt 1 -deadline good -cpu-used 4 -an $D/$c-idle-$o.webm
ls -la $D/$c-idle-$o.*
