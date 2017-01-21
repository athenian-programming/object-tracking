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
import defaults as defs
import opencv_utils as utils
from contour_finder import ContourFinder
from defaults import LOGGING_ARGS
from location_server import LocationServer
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import is_raspi

if is_raspi():
    from blinkt import set_pixel, show, clear
    # import dothat.backlight as backlight
    # import dothat.lcd as lcd
    # backlight.rgb(200, 0,0)


class ObjectTracker:
    def __init__(self, bgr_color, width, percent, minimum, hsv_range, grpc_port, display=False):
        self.__width = width
        self.__orig_percent = percent
        self.__orig_width = width
        self.__percent = percent
        self.__minimum = minimum
        self.__display = display
        self.__stopped = False

        self.__prev_x, self.__prev_y = -1, -1
        self.__cnt = 0
        self.__lock = Lock()
        self.__currval = None

        self.__contour_finder = ContourFinder(bgr_color, hsv_range)
        self.__location_server = LocationServer(grpc_port)
        self.__cam = camera.Camera()

    def set_percent(self, percent):
        if 2 <= percent <= 98:
            self.__percent = percent
            self.__prev_x, self.__prev_y = -1, -1

    def set_width(self, width):
        if 200 <= width <= 4000:
            self.__width = width
            self.__prev_x, self.__prev_y = -1, -1

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):

        try:
            Thread(target=self.__location_server.start_location_server).start()
            time.sleep(1)
        except BaseException as e:
            logging.error("Unable to start location server [{0}]".format(e))
            sys.exit(1)

        self.__location_server.write_location(-1, -1, 0, 0, 0)

        while self.__cam.is_open() and not self.__stopped:
            try:
                image = self.__cam.read()
                image = imutils.resize(image, width=self.__width)

                middle_pct = (self.__percent / 100.0) / 2
                img_height, img_width = image.shape[:2]

                mid_x, mid_y = img_width / 2, img_height / 2
                img_x, img_y = -1, -1

                # The middle margin calculation is based on % of width for horizontal and vertical boundry
                middle_inc = int(mid_x * middle_pct)

                text = "#{0} ({1}, {2})".format(self.__cnt, img_width, img_height)
                text += " {0}%".format(self.__percent)

                contour = self.__contour_finder.get_max_contour(image, self.__minimum)
                if contour is not None:
                    moment = cv2.moments(contour)
                    area = int(moment["m00"])
                    img_x = int(moment["m10"] / area)
                    img_y = int(moment["m01"] / area)

                    if self.__display:
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

                set_left_leds(RED if x_missing else (GREEN if x_in_middle else BLUE))
                set_right_leds(RED if y_missing else (GREEN if y_in_middle else BLUE))

                # Write location if it is different from previous value written
                if img_x != self.__prev_x or img_y != self.__prev_y:
                    self.__location_server.write_location(img_x, img_y, img_width, img_height, middle_inc)
                    self.__prev_x, self.__prev_y = img_x, img_y

                # Display images
                if self.__display:
                    x_color = GREEN if x_in_middle else RED if x_missing else BLUE
                    y_color = GREEN if y_in_middle else RED if y_missing else BLUE
                    cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, img_height), x_color, 1)
                    cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, img_height), x_color, 1)
                    cv2.line(image, (0, mid_y - middle_inc), (img_width, mid_y - middle_inc), y_color, 1)
                    cv2.line(image, (0, mid_y + middle_inc), (img_width, mid_y + middle_inc), y_color, 1)
                    cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

                    cv2.imshow("Image", image)

                    key = cv2.waitKey(1) & 0xFF

                    if key == ord("w"):
                        self.set_width(self.__width - 10)
                    elif key == ord("W"):
                        self.set_width(self.__width + 10)
                    elif key == ord("-") or key == ord("_"):
                        self.set_percent(self.__percent - 1)
                    elif key == ord("+") or key == ord("="):
                        self.set_percent(self.__percent + 1)
                    elif key == ord("r"):
                        self.set_width(self.__orig_width)
                        self.set_percent(self.__orig_percent)
                    elif key == ord("p"):
                        utils.save_image(image)
                    elif key == ord("q"):
                        self.stop()
                else:
                    # Nap if display is not on
                    # time.sleep(.01)
                    pass

                self.__cnt += 1
            except BaseException as e:
                logging.error("Unexpected error in main loop [{0}]".format(e))

        if is_raspi():
            clear()
        self.__cam.close()

    def stop(self):
        self.__stopped = True
        self.__location_server.stop()


def set_left_leds(color):
    if is_raspi():
        for i in range(0, 4):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


def set_right_leds(color):
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

    logging.basicConfig(**LOGGING_ARGS)

    tracker = ObjectTracker(eval(args["bgr"]),
                            int(args["width"]),
                            int(args["percent"]),
                            int(args["min"]),
                            int(args["range"]),
                            args["port"],
                            args["display"])

    try:
        tracker.start()
    except KeyboardInterrupt:
        logging.info("Exiting...")
    finally:
        tracker.stop()
