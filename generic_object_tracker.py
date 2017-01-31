import argparse
import sys

import camera
import cv2
import opencv_utils as utils
from common_cli_args import *
from common_utils import is_raspi
from contour_finder import ContourFinder
from location_server import LocationServer

# I tried to include this in the constructor and make it depedent on self.__leds, but it does not work
if is_raspi():
    from blinkt import set_pixel, show


class GenericObjectTracker(object):
    def __init__(self,
                 bgr_color,
                 width,
                 percent,
                 minimum,
                 hsv_range,
                 grpc_port=50051,
                 display=False,
                 flip=False,
                 usb_camera=False,
                 leds=False):
        self.__width = width
        self.__percent = percent
        self.__orig_width = width
        self.__orig_percent = percent
        self.__minimum = minimum
        self.__display = display
        self.__flip = flip
        self.__leds = leds
        self.__stopped = False
        self.__cnt = 0

        self._prev_x, self._prev_y = -1, -1

        self.__contour_finder = ContourFinder(bgr_color, hsv_range)
        self.__location_server = LocationServer(grpc_port)
        self.__cam = camera.Camera(use_picamera=not usb_camera)

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if 200 <= width <= 4000:
            self.__width = width
            self._prev_x, self._prev_y = -1, -1

    @property
    def percent(self):
        return self.__percent

    @percent.setter
    def percent(self, percent):
        if 2 <= percent <= 98:
            self.__percent = percent
            self._prev_x, self._prev_y = -1, -1

    @property
    def minimum(self):
        return self.__minimum

    @property
    def display(self):
        return self.__display

    @property
    def flip(self):
        return self.__flip

    @property
    def stopped(self):
        return self.__stopped

    @property
    def contour_finder(self):
        return self.__contour_finder

    @property
    def location_server(self):
        return self.__location_server

    @property
    def cam(self):
        return self.__cam

    @property
    def cnt(self):
        return self.__cnt

    @cnt.setter
    def cnt(self, val):
        self.__cnt = val

    def stop(self):
        self.__stopped = True
        self.__location_server.stop()

    def clear_leds(self):
        self.set_left_leds([0, 0, 0])
        self.set_right_leds([0, 0, 0])

    def set_left_leds(self, color):
        if self.__leds:
            for i in range(0, 4):
                set_pixel(i, color[2], color[1], color[0], brightness=0.05)
            show()

    def set_right_leds(self, color):
        if self.__leds:
            for i in range(4, 8):
                set_pixel(i, color[2], color[1], color[0], brightness=0.05)
            show()

    def start(self):
        try:
            self.location_server.start()
        except BaseException as e:
            logging.error("Unable to start location server [{0}]".format(e))
            sys.exit(1)

        self.location_server.write_location(-1, -1, 0, 0, 0)

    def process_keystroke(self, image):
        key = cv2.waitKey(1) & 0xFF

        if key == 255:
            pass
        elif key == ord("w"):
            self.width = self.width - 10
        elif key == ord("W"):
            self.width = self.width + 10
        elif key == ord("-") or key == ord("_") or key == 0:
            self.percent = self.percent - 1
        elif key == ord("+") or key == ord("=") or key == 1:
            self.percent = self.percent + 1
        elif key == ord("r"):
            self.width = self.__orig_width
            self.percent = self.__orig_percent
        elif key == ord("s"):
            utils.save_image(image)
        elif key == ord("q"):
            self.stop()

    @staticmethod
    def cli_args():
        parser = argparse.ArgumentParser()
        bgr(parser)
        usb(parser)
        flip(parser)
        width(parser)
        percent(parser)
        min(parser)
        range(parser)
        port(parser)
        leds(parser)
        display(parser)
        verbose(parser)
        return vars(parser.parse_args())
