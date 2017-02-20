#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./single_object_tracker.py --bgr "174, 56, 5" --display --flipy --horizontal --vertical
