#!/usr/bin/env python2

import argparse
import logging
import sys
from threading import Thread

from pyfirmata import Arduino

from location_client import LocationClient
from servo import Servo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial", default="ttyACM0", type=str,
                        help="Arduino serial port [ttyACM0] (OSX is cu.usbmodemXXXX)")
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    parser.add_argument("-x", "--xservo", default=5, type=int, help="X servo PWM pin [5]")
    parser.add_argument("-y", "--yservo", default=6, type=int, help="Y servo PWM pin [6]")
    parser.add_argument("-c", "--calib", default=False, action="store_true", help="Calibration mode [false]")
    parser.add_argument("-v", "--verbose", default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=args["loglevel"],
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    # Setup firmata client
    port = "/dev/" + args["serial"]
    try:
        board = Arduino(port)
        logging.info("Connected to Arduino at: {0}".format(port))
    except OSError as e:
        logging.error("Failed to connect to Arduino at {0} - [{1}]".format(port, e))
        sys.exit(0)

    location_client = LocationClient(args["grpc"])

    # Create servos
    servo_x = Servo(board, "X servo", "d:{0}:s".format(args["xservo"]), lambda: location_client.get_x(), True)
    servo_y = Servo(board, "Y Servo", "d:{0}:s".format(args["yservo"]), lambda: location_client.get_y(), False)

    if args["calib"]:
        Servo.calibrate(location_client, servo_x, servo_y)
        logging.info("Exiting...")
        board.exit()
        sys.exit(0)

    try:
        Thread(target=location_client.read_locations).start()
    except BaseException as e:
        logging.error("Unable to start location client [{0}]".format(e))

    servo_x_t = Thread(target=servo_x.start)
    try:
        servo_x_t.start()
    except BaseException as e:
        logging.error("Unable to start servo controller for {0} [{1}]".format(servo_x.name(), e))

    servo_y_t = Thread(target=servo_y.start)
    try:
        servo_y_t.start()
    except BaseException as e:
        logging.error("Unable to start servo controller for {0} [{1}]".format(servo_y.name(), e))

    try:
        servo_x_t.join()
        servo_y_t.join()
    except KeyboardInterrupt as e:
        board.exit()
        location_client.stop()
        logging.info("Exiting...")
