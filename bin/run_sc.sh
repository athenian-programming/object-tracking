#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common_robotics_python
./servo_controller.py --grpc pleiku -s ttyACM0
