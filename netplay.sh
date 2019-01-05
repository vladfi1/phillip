#!/usr/bin/env bash


#EXE=$OM2_USER/fm/dolphin-emu
EXE=$OM2_USER/fm-vlad-bin/dolphin-emu
#EXE=$OM2_USER/dolphin/BuildOM/Binaries/dolphin-emu
#EXE=$OM2_USER/dolphin/BuildLast5.3/Binaries/dolphin-emu

#$RUN $EXE -e SSBM.iso -v Null

xvfb-run -s '-screen 0 800x600x24' \
python -u phillip/run.py --exe $EXE --fm --gfx Null --start 0 \
--disk 1 --experience_length 600 \
--load agents/delay18/FalcoBF \
--epsilon 0 --reload 0 --speed 1 --dolphin --netplay $1 \
--predict_steps $2 --delay $2 \
--real_delay $3
