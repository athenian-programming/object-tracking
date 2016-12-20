#!/usr/bin/env python2

import argparse
import logging
import sys
import time
from threading import Lock
from threading import Thread

import cv2
import imutils

import camera
import opencv_utils as utils
from contour_finder import ContourFinder
from location_server import LocationServer
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import is_raspi


class ObjectTracker:
    def __init__(self, bgr_color, width, percent, minimum, hsv_range, grpc_port, display=False):
        self._width = width
        self._orig_percent = percent
        self._orig_width = width
        self._percent = percent
        self._minimum = minimum
        self._display = display
        self._stopped = False

        self._prev_x = -1
        self._prev_y = -1
        self._cnt = 0
        self._lock = Lock()
        self._currval = None

        self._contour_finder = ContourFinder(bgr_color, hsv_range)
        self._location_server = LocationServer(grpc_port)
        self._cam = camera.Camera()

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

        try:
            Thread(target=self._location_server.start_location_server).start()
            time.sleep(1)
        except BaseException as e:
            logging.error("Unable to start telemetry server [{0}]".format(e))
            sys.exit(1)

        self._location_server.write_location(-1, -1, 0, 0, 0)

        while self._cam.is_open() and not self._stopped:

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

            text = "#{0} ({1}, {2})".format(self._cnt, img_width, img_height)
            text += " {0}%".format(self._percent)

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
                    text += " ({0}, {1})".format(img_x, img_y)
                    text += " {0}".format(area)

            x_in_middle = mid_x - middle_inc <= img_x <= mid_x + middle_inc
            y_in_middle = mid_y - middle_inc <= img_y <= mid_y + middle_inc
            x_missing = img_x == -1
            y_missing = img_y == -1

            _set_left_leds(RED if x_missing else (GREEN if x_in_middle else BLUE))
            _set_right_leds(RED if y_missing else (GREEN if y_in_middle else BLUE))

            # Write location if it is different from previous value written
            if img_x != self._prev_x or img_y != self._prev_y:
                self._location_server.write_location(img_x, img_y, img_width, img_height, middle_inc)
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

                if key == ord("w"):
                    self._set_width(self._width - 10)
                elif key == ord("W"):
                    self._set_width(self._width + 10)
                elif key == ord("-") or key == ord("_"):
                    self._set_percent(self._percent - 1)
                elif key == ord("+") or key == ord("="):
                    self._set_percent(self._percent + 1)
                elif key == ord("r"):
                    self._set_width(self._orig_width)
                    self._set_percent(self._orig_percent)
                elif key == ord("p"):
                    utils.save_image(image)
                elif key == ord("q"):
                    self.stop()
            else:
                # Nap if display is not on
                time.sleep(.1)

            self._cnt += 1

        if is_raspi():
            clear()
        self._cam.close()

    def stop(self):
        self._stopped = True
        self._location_server.stop()


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
    parser.add_argument("-p", "--port", default=50051, type=int, help="gRPC port [50051]")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-v", "--verbose", default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=args["loglevel"],
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    # Raspi specific
    # import dothat.backlight as backlight
    # import dothat.lcd as lcd
    # backlight.rgb(200, 0,0)

    if is_raspi():
        from blinkt import set_pixel, show, clear

    tracker = ObjectTracker(eval(args["bgr"]),
                            int(args["width"]),
                            int(args["percent"]),
                            int(args["min"]),
                            int(args["range"]),
                            args["port"],
                            args["display"])

    try:
        tracker.start()
    except KeyboardInterrupt as e:
        tracker.stop()
        pass

    logging.info("Exiting...")
