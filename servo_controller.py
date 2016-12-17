#!/usr/bin/env python2

import argparse
import logging
import sys
import thread
import time

from pyfirmata import Arduino

from  grpc_source import GrpcSource
from servo import Servo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", default=False, action="store_true", help="Test mode [false]")
    parser.add_argument("-c", "--calib", default=False, action="store_true", help="Calibration mode [false]")
    parser.add_argument("-p", "--port", default="ttyACM0", type=str,
                        help="Arduino serial port [ttyACM0] (OSX is cu.usbmodemXXXX)")
    parser.add_argument("-x", "--xservo", default=5, type=int, help="X servo PWM pin [5]")
    parser.add_argument("-y", "--yservo", default=6, type=int, help="Y servo PWM pin [6]")
    parser.add_argument('-v', '--verbose', default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=args['loglevel'],
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    loc_source = GrpcSource(50051)

    try:
        thread.start_new_thread(loc_source.start_grpc_source(), ())
    except BaseException as e:
        logging.error("Unable to start source server [{0}]".format(e))

    if args["test"]:
        for i in range(0, 1000):
            x_vals = loc_source.get_x()
            y_vals = loc_source.get_y()
            print("Received {0}: {1}, {2} {3}x{4} {5}".format(i, x_vals[0], y_vals[0], x_vals[1], y_vals[1], x_vals[2]))
        print("Exiting...")
        sys.exit(0)

    # Setup firmata client
    port = "/dev/" + args["port"]
    try:
        board = Arduino(port)
        logging.info("Connected to arduino at: {0}".format(port))
    except OSError as e:
        logging.error("Failed to connect to arduino at {0} - [{1}]".format(port, e))
        sys.exit(0)

    # Create servos
    servo_x = Servo(board, "X servo", "d:{0}:s".format(args["xservo"]), lambda: loc_source.get_x(), True)
    servo_y = Servo(board, "Y Servo", "d:{0}:s".format(args["yservo"]), lambda: loc_source.get_y(), False)

    if args["calib"]:
        Servo.calibrate(loc_source, servo_x, servo_y)
        print("Exiting...")
        board.exit()
    else:
        try:
            thread.start_new_thread(servo_x.start, ())
        except BaseException as e:
            logging.error("Unable to start controller for {0} [{1}]".format(servo_x.name(), e))

        try:
            thread.start_new_thread(servo_y.start, ())
        except BaseException as e:
            logging.error("Unable to start controller for {0} [{1}]".format(servo_y.name(), e))

        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt as e:
            print("Exiting...")
