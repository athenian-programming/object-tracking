#!/usr/bin/env python2

import argparse
import logging
import sys
from threading import Event
from threading import Thread

from pyfirmata import Arduino

from location_client import LocationClient
from servo import Servo


def calibrate(location_client, servo_x, servo_y):
    def center_servos():
        servo_x.write_pin(90)
        servo_y.write_pin(90)

    name = "x"
    servo = servo_x
    while True:
        # This is a hack to get around python3 not having raw_input
        try:
            input = raw_input
        except NameError:
            pass

        try:
            val = input("{0} {1} ({2}, {3})> ".format(name.upper(),
                                                      servo.read_pin(),
                                                      location_client.get_loc("x"),
                                                      location_client.get_loc("y")))
        except KeyboardInterrupt:
            return

        if val == "?":
            print("Valid commands:")
            print("     x      : change to pan servo")
            print("     y      : change to tilt servo")
            print("     s      : run scan on current servo")
            print("     c      : center current servo")
            print("     C      : center both servos")
            print("     +      : increase current servo position 1 degree")
            print("     -      : decrease current servo position 1 degree")
            print("     number : set current servo position number degree")
            print("     ?      : print summary of commands")
            print("     q      : quit")
        elif val == "c":
            servo.write_pin(90)
        elif val == "C":
            center_servos()
        elif val == "x":
            name = "x"
            servo = servo_x
        elif val == "y":
            name = "y"
            servo = servo_y
        elif val == "s":
            pause = 0.01
            center_servos()
            servo.write_pin(0)

            start_pos = -1
            end_pos = -1
            for i in range(0, 180, 1):
                servo.write_pin(i, pause)
                if location_client.get_loc(name) != -1:
                    start_pos = i
                    print("Target starts at position {0}".format(start_pos))
                    break

            if start_pos == -1:
                print("No target found")
                continue

            for i in range(start_pos, 180, 1):
                servo.write_pin(i, pause)
                if location_client.get_loc(name) == -1:
                    break
                end_pos = i

            print("Target ends at position {0}".format(end_pos))

            total_pixels = location_client.get_size(name)
            total_pos = end_pos - start_pos
            if total_pos > 0:
                pix_per_deg = round(total_pixels / float(total_pos), 2)
                servo.write_pin(90)
                print("{0} degrees to cover {1} pixels [{2} pixels/degree]".format(total_pos,
                                                                                   total_pixels,
                                                                                   pix_per_deg))
            else:
                print("No target found")

        elif len(val) == 0:
            pass
        elif val == "-" or val == "_":
            servo.write_pin(servo.read_pin() - 1)
        elif val == "+" or val == "=":
            servo.write_pin(servo.read_pin() + 1)
        elif val.isdigit():
            servo.write_pin(int(val))
        elif val == "q":
            break
        else:
            print("Invalid input")


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

    servo_x_ready = Event()
    servo_y_ready = Event()

    # Make servo X go first
    servo_x_ready.set()

    # Create servos
    servo_x = Servo("X servo", board, "d:{0}:s".format(args["xservo"]), secs_per_180=.5, pix_per_degree=25)
    servo_y = Servo("Y Servo", board, "d:{0}:s".format(args["yservo"]), secs_per_180=.5, pix_per_degree=25)

    try:
        Thread(target=location_client.read_locations).start()
    except BaseException as e:
        logging.error("Unable to start location client [{0}]".format(e))

    if args["calib"]:
        calibrate(location_client, servo_x, servo_y)
    else:
        servo_x_t = Thread(target=servo_x.start, args=(True,
                                                       lambda: location_client.get_x(),
                                                       servo_x_ready,
                                                       servo_y_ready))
        servo_y_t = Thread(target=servo_y.start, args=(False,
                                                       lambda: location_client.get_y(),
                                                       servo_y_ready,
                                                       servo_x_ready))

        try:
            servo_x_t.start()
        except BaseException as e:
            logging.error("Unable to start servo controller for {0} [{1}]".format(servo_x.name(), e))

        try:
            servo_y_t.start()
        except BaseException as e:
            logging.error("Unable to start servo controller for {0} [{1}]".format(servo_y.name(), e))

        try:
            servo_x_t.join()
            servo_y_t.join()
        except KeyboardInterrupt as e:
            servo_x.stop()
            servo_y.stop()

    board.exit()
    location_client.stop()
    logging.info("Exiting...")
