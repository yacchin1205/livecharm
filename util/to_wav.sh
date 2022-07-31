#!/bin/bash

#ffmpeg -i $1 -ac 1 -ar 8000 -acodec pcm_u8 $2
#  -acodec pcm_u8
ffmpeg -i $1 -ac 1 -acodec pcm_s16le -bitexact -ar 16000 $2
