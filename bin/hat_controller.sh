#! /bin/bash

export PYTHONPATH=${PYTHONPATH}:../common-robotics
./hat_controller.py --grpc pleiku
