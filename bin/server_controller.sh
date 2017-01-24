#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./servo_controller.py --grpc pleiku -s ttyACM0
