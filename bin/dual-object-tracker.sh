#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./dual_object_tracker.py --bgr "174, 56, 5" --display --leds --usb
