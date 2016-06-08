#!/usr/bin/env sh
squeue -u $USER -o "%i %j" | grep $1 | cut -d ' ' -f 1 | xargs scancel
