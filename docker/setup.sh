#!/bin/sh

# sets up udev rule for dolphin wii u adapter
sudo mkdir -p /etc/udev/rules.d/
sudo echo 'SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="0337", MODE="0666"' > /etc/udev/rules.d/51-gcadapter.rules
sudo udevadm control --reload-rules
