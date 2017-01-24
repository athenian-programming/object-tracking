#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./object_tracker.py --bgr "[174, 56, 5]" --display
