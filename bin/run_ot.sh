#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common_robotics_python
./object_tracker.py --bgr "[174, 56, 5]" --display
