#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./firmata_controller.py --grpc pleiku -s ttyACM0
