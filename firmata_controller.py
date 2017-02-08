#!/usr/bin/env python2

import argparse
import logging
import sys
from threading import Thread

import calibrate_servo
import cli_args as cli
from firmata_servo import FirmataServo
from location_client import LocationClient
from pyfirmata import Arduino
from utils import is_windows
from utils import setup_logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial", default="ttyACM0", type=str,
                        help="Arduino serial port [ttyACM0] (OSX is cu.usbmodemXXXX)")
    cli.grpc_host(parser)
    parser.add_argument("-x", "--xservo", default=5, type=int, help="X servo PWM pin [5]")
    parser.add_argument("-y", "--yservo", default=6, type=int, help="Y servo PWM pin [6]")
    cli.alternate(parser)
    cli.calib(parser)
    cli.verbose(parser)
    args = vars(parser.parse_args())

    alternate = args["alternate"]
    calib = args["calib"]
    xservo = args["xservo"]
    yservo = args["yservo"]

    setup_logging(args["loglevel"])

    # Setup firmata client
    port = ("" if is_windows() else "/dev/") + args["serial"]
    try:
        board = Arduino(port)
        logger.info("Connected to Arduino at: {0}".format(port))
    except OSError as e:
        logger.error("Failed to connect to Arduino at {0} - [{1}]".format(port, e))
        sys.exit(0)

    locations = LocationClient(args["grpc_host"]).start()

    # Create servos
    servo_x = FirmataServo("Pan", alternate, board, "d:{0}:s".format(xservo), 1.0, 8)
    servo_y = FirmataServo("Tilt", alternate, board, "d:{0}:s".format(yservo), 1.0, 8)

    try:
        if calib:
            try:
                calib_t = Thread(target=calibrate_servo.calibrate, args=(locations, servo_x, servo_y))
                calib_t.start()
                calib_t.join()
            except KeyboardInterrupt:
                pass
        else:
            if alternate:
                # Set servo X to go first
                servo_x.ready_event.set()
            try:
                servo_x.start(True, lambda: locations.get_x(), servo_y.ready_event if not calib else None)
                servo_y.start(False, lambda: locations.get_y(), servo_x.ready_event if not calib else None)
                servo_x.join()
                servo_y.join()
            except KeyboardInterrupt:
                pass
            finally:
                servo_x.stop()
                servo_y.stop()
    finally:
        board.exit()
        locations.stop()

    logger.info("Exiting...")
