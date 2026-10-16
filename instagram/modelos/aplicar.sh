#!/bin/bash
# uso: aplicar.sh <video> <musica.mp3> <inicio_s> <saida>
ffmpeg -nostdin -v error -y -ss "$3" -t 18 -i "$2" -i "$1" -filter_complex \
 "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,afade=t=in:st=0:d=0.4,afade=t=out:st=16.3:d=1.7,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
 -map 1:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$4"
