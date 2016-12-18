#!/usr/bin/env python2

import argparse
import logging
import sys
import thread
import time

from pyfirmata import Arduino

from  grpc_source import LocationSource
from servo import Servo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serial", default="ttyACM0", type=str,
                        help="Arduino serial port [ttyACM0] (OSX is cu.usbmodemXXXX)")
    parser.add_argument("-p", "--port", default=50051, type=int, help="gRPC port [50051]")
    parser.add_argument("-x", "--xservo", default=5, type=int, help="X servo PWM pin [5]")
    parser.add_argument("-y", "--yservo", default=6, type=int, help="Y servo PWM pin [6]")
    parser.add_argument("-c", "--calib", default=False, action="store_true", help="Calibration mode [false]")
    parser.add_argument('-v', '--verbose', default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=args['loglevel'],
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    location_source = LocationSource(args["port"])

    try:
        thread.start_new_thread(location_source.start_telemetry_server(), ())
    except BaseException as e:
        logging.error("Unable to start location server [{0}]".format(e))

    # Setup firmata client
    port = "/dev/" + args["serial"]
    try:
        board = Arduino(port)
        logging.info("Connected to Arduino at: {0}".format(port))
    except OSError as e:
        logging.error("Failed to connect to Arduino at {0} - [{1}]".format(port, e))
        sys.exit(0)

    # Create servos
    servo_x = Servo(board, "X servo", "d:{0}:s".format(args["xservo"]), lambda: location_source.get_x(), True)
    servo_y = Servo(board, "Y Servo", "d:{0}:s".format(args["yservo"]), lambda: location_source.get_y(), False)

    if args["calib"]:
        Servo.calibrate(location_source, servo_x, servo_y)
        print("Exiting...")
        board.exit()
    else:
        try:
            thread.start_new_thread(servo_x.start, ())
        except BaseException as e:
            logging.error("Unable to start servo controller for {0} [{1}]".format(servo_x.name(), e))

        try:
            thread.start_new_thread(servo_y.start, ())
        except BaseException as e:
            logging.error("Unable to start servo controller for {0} [{1}]".format(servo_y.name(), e))

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt as e:
            print("Exiting...")
