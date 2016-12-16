#!/usr/bin/env python2

import argparse
import logging
import socket
import sys
import thread
import threading
import time
import urllib
import urllib2

import cv2
import grpc
import imutils

import camera
import gen.location_server_pb2
import opencv_utils as utils
from contour_finder import ContourFinder
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import is_raspi


class ObjectTracker:
    def __init__(self, bgr_color, width, percent, minimum, hsv_range, http_url, grpc_hostname, display=False):
        self._width = width
        self._orig_percent = percent
        self._orig_width = width
        self._percent = percent
        self._minimum = minimum
        self._display = display
        self._http_url = http_url

        self._prev_x = -1
        self._prev_y = -1
        self._cnt = 0
        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._currval = None

        self._contour_finder = ContourFinder(bgr_color, hsv_range)

        self._use_grpc = False
        if grpc_hostname:
            self._use_grpc = True
            try:
                thread.start_new_thread(self._connect_to_grpc, (grpc_hostname,))
            except BaseException as e:
                logging.error("Unable to start gRPC client at {0} [{1}]".format(http_url, e))

        self._cam = camera.Camera()

    def _write_location(self, val):
        with self._lock:
            self._currloc = val
            self._data_ready.set()

    def _read_location(self):
        self._data_ready.wait()
        with self._lock:
            self._data_ready.clear()
            return self._currloc

    def _generate_locations(self):
        while True:
            yield self._read_location()

    def _connect_to_grpc(self, hostname):
        while True:
            try:
                channel = grpc.insecure_channel(hostname)
                stub = gen.location_server_pb2.LocationServerStub(channel)
                client_info = gen.location_server_pb2.ClientInfo(
                    info='Client running on {0}'.format(socket.gethostname()))
                server_info = stub.RegisterClient(client_info)
                logging.info("Connected to {0}: {1}".format(hostname, server_info.info))
                stub.ReportLocation(self._generate_locations())
                logging.info("Disconnected from {0}: {1}".format(hostname, server_info.info))
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} - [{1}]".format(hostname, e))
                time.sleep(1)

    def _write_location_values(self, x, y, width, height, middle_inc):
        # Raspi specific
        # lcd.clear()
        # lcd.write('X, Y: {0}, {1}'.format(cX, cY))
        if self._http_url:
            try:
                params = urllib.urlencode({'x': x, 'y': y, 'width': width, 'height': height, 'middle_inc': middle_inc})
                urllib2.urlopen(self._http_url, params).read()
            except BaseException as e:
                logging.warning("Unable to reach HTTP server {0} [{1}]".format(self._http_url, e))
        elif self._use_grpc:
            loc = gen.location_server_pb2.Location(x=x, y=y, width=width, height=height, middle_inc=middle_inc)
            self._write_location(loc)
        else:
            # Print to console
            print("{0}, {1} {2}x{3} {4}%".format(x, y, width, height, middle_inc))

    def _set_percent(self, percent):
        if 2 <= percent <= 98:
            self._percent = percent
            self._prev_x = -1
            self._prev_y = -1

    def _set_width(self, width):
        if 200 <= width <= 4000:
            self._width = width
            self._prev_x = -1
            self._prev_y = -1

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):

        self._write_location_values(-1, -1, 0, 0, 0)

        while self._cam.is_open():

            image = self._cam.read()
            image = imutils.resize(image, width=self._width)

            middle_pct = (self._percent / 100.0) / 2
            img_height, img_width = image.shape[:2]

            mid_x = img_width / 2
            mid_y = img_height / 2
            img_x = -1
            img_y = -1
            # The middle margin calculation is based on % of width for horizontal and vertical boundry
            middle_inc = int(mid_x * middle_pct)

            text = '#{0} ({1}, {2})'.format(self._cnt, img_width, img_height)
            text += ' {0}%'.format(self._percent)

            contour = self._contour_finder.get_max_contour(image, self._minimum)
            if contour is not None:
                moment = cv2.moments(contour)
                area = int(moment["m00"])
                img_x = int(moment["m10"] / area)
                img_y = int(moment["m01"] / area)

                if self._display:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(image, (x, y), (x + w, y + h), BLUE, 2)
                    cv2.drawContours(image, [contour], -1, GREEN, 2)
                    cv2.circle(image, (img_x, img_y), 4, RED, -1)
                    text += ' ({0}, {1})'.format(img_x, img_y)
                    text += ' {0}'.format(area)

            x_in_middle = mid_x - middle_inc <= img_x <= mid_x + middle_inc
            y_in_middle = mid_y - middle_inc <= img_y <= mid_y + middle_inc
            x_missing = img_x == -1
            y_missing = img_y == -1

            _set_left_leds(RED if x_missing else (GREEN if x_in_middle else BLUE))
            _set_right_leds(RED if y_missing else (GREEN if y_in_middle else BLUE))

            # Write location if it is different from previous value written
            if img_x != self._prev_x or img_y != self._prev_y:
                self._write_location_values(img_x, img_y, img_width, img_height, middle_inc)
                self._prev_x = img_x
                self._prev_y = img_y

            # Display images
            if self._display:
                x_color = GREEN if x_in_middle else RED if x_missing else BLUE
                y_color = GREEN if y_in_middle else RED if y_missing else BLUE
                cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, img_height), x_color, 1)
                cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, img_height), x_color, 1)
                cv2.line(image, (0, mid_y - middle_inc), (img_width, mid_y - middle_inc), y_color, 1)
                cv2.line(image, (0, mid_y + middle_inc), (img_width, mid_y + middle_inc), y_color, 1)
                cv2.putText(image, text, utils.text_loc(), utils.text_font(), utils.text_size(), RED,
                            1)
                cv2.imshow("Image", image)
                # cv2.imshow("Mask", mask)
                # cv2.imshow("Res", result)

                key = cv2.waitKey(30) & 0xFF

                if key == ord('w'):
                    self._set_width(self._width - 10)
                elif key == ord('W'):
                    self._set_width(self._width + 10)
                elif key == ord('-') or key == ord('_'):
                    self._set_percent(self._percent - 1)
                elif key == ord('+') or key == ord('='):
                    self._set_percent(self._percent + 1)
                elif key == ord('r'):
                    self._set_width(self._orig_width)
                    self._set_percent(self._orig_percent)
                elif key == ord('p'):
                    utils.save_frame(image)
                elif key == ord("q"):
                    break
            else:
                # Nap if display is not on
                time.sleep(.1)

            self._cnt += 1

        if is_raspi():
            clear()
        self._cam.close()

    def _test(self):
        for i in range(0, 1000):
            self._write_location_values(i, i + 1, i + 2, i + 3, i + 4)
            time.sleep(1)
        print("Exiting...")
        sys.exit(0)


def _set_left_leds(color):
    if is_raspi():
        for i in range(0, 4):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


def _set_right_leds(color):
    if is_raspi():
        for i in range(4, 8):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"[174, 56, 5]\"")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-e", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [100]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-g", "--grpc", default="", help="Servo controller gRPC server hostname")
    parser.add_argument("-o", "--http", default="", type=str, help="Servo controller HTTP hostname")
    parser.add_argument("-t", "--test", default=False, action="store_true", help="Test mode [false]")
    parser.add_argument('-v', '--verbose', default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=args['loglevel'],
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    # Note this is a BGR value, not RGB!
    bgr_color = eval(args["bgr"])
    logging.info("BGR color: {0}".format(bgr_color))

    # Define range of colors in HSV
    hsv_range = int(args["range"])
    logging.info("HSV range: {0}".format(hsv_range))

    width = int(args["width"])
    logging.info("Image width: {0}".format(width))

    percent = int(args["percent"])
    logging.info("Middle percent: {0}".format(percent))

    minimum = int(args["min"])
    logging.info("Minimum tager pixel area: {0}".format(minimum))

    display = args["display"]
    logging.info("Display images: {0}".format(display))

    grpc_hostname = args["grpc"]
    http_hostname = args["http"]

    http_url = None
    if grpc_hostname:
        grpc_hostname += ":50051"
        logging.info("Servo controller gRPC hostname: {0}".format(grpc_hostname))
    elif http_hostname:
        http_url = "http://" + http_hostname + ":8080/set_values"
        logging.info("Servo controller HTTP URL: {0}".format(http_hostname))

    # Raspi specific
    # import dothat.backlight as backlight
    # import dothat.lcd as lcd
    # backlight.rgb(200, 0,0)

    if is_raspi():
        from blinkt import set_pixel, show, clear

    tracker = ObjectTracker(bgr_color, width, percent, minimum, hsv_range, http_url, grpc_hostname, display)

    if args["test"]:
        try:
            thread.start_new_thread(tracker._test, ())
        except BaseException as e:
            logging.error("Unable to run test thread [{0}]".format(e))
            sys.exit(1)

    try:
        tracker.start()
    except KeyboardInterrupt as e:
        pass

    print("Exiting...")
