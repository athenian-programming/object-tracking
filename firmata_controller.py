#!/usr/bin/env python2

import argparse
import logging
import sys
from logging import error
from logging import info
from threading import Thread

import calibrate_servo
from common_constants import LOGGING_ARGS
from common_utils import is_windows
from firmata_servo import FirmataServo
from location_client import LocationClient
from pyfirmata import Arduino

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial", default="ttyACM0", type=str,
                        help="Arduino serial port [ttyACM0] (OSX is cu.usbmodemXXXX)")
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-a", "--alternate", default=False, action="store_true", help="Alternate servo actions [false]")
    parser.add_argument("-x", "--xservo", default=5, type=int, help="X servo PWM pin [5]")
    parser.add_argument("-y", "--yservo", default=6, type=int, help="Y servo PWM pin [6]")
    parser.add_argument("-c", "--calib", default=False, action="store_true", help="Calibration mode [false]")
    parser.add_argument("-v", "--verbose", default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())
    alternate = args["alternate"]
    calib = args["calib"]
    xservo = args["xservo"]
    yservo = args["yservo"]

    logging.basicConfig(**LOGGING_ARGS)

    # Setup firmata client
    port = ("" if is_windows() else "/dev/") + args["serial"]
    try:
        board = Arduino(port)
        info("Connected to Arduino at: {0}".format(port))
    except OSError as e:
        error("Failed to connect to Arduino at {0} - [{1}]".format(port, e))
        sys.exit(0)

    locations = LocationClient(args["grpc"]).start()

    # Create servos
    servo_x = FirmataServo("Pan", alternate and not calib, board, "d:{0}:s".format(xservo), 1.0, 8)
    servo_y = FirmataServo("Tilt", alternate and not calib, board, "d:{0}:s".format(yservo), 1.0, 8)

    calib_t = None
    if calib:
        calib_t = Thread(target=calibrate_servo.calibrate, args=(locations, servo_x, servo_y))
        calib_t.start()
    else:
        # Set servo X to go first
        servo_x.ready_event.set()

    servo_x.start(True, lambda: locations.get_x(), servo_y.ready_event if not calib else None)
    servo_y.start(False, lambda: locations.get_y(), servo_x.ready_event if not calib else None)

    try:
        if calib_t is not None:
            calib_t.join()
        else:
            servo_x.join()
            servo_y.join()
    except KeyboardInterrupt:
        pass
    finally:
        servo_x.stop()
        servo_y.stop()
        board.exit()
        locations.stop()

    info("Exiting...")
