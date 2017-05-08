#!/bin/sh

export vblank_mode=0

# from http://wiki.ros.org/docker/Tutorials/GUI
sudo docker run -it --rm \
--user=$(id -u) \
--env="DISPLAY" \
--volume="/etc/group:/etc/group:ro" \
--volume="/etc/passwd:/etc/passwd:ro" \
--volume="/etc/shadow:/etc/shadow:ro" \
--volume="/etc/sudoers.d:/etc/sudoers.d:ro" \
--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
--volume="/dev/snd:/dev/snd" \
--privileged \
vladfi/phillip:falcon
