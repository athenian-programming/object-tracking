import logging
import sys
import time

import camera
import cli_args  as cli
import cv2
import image_server as img_server
import imutils
import opencv_utils as utils
from cli_args import setup_cli_args
from contour_finder import ContourFinder
from location_server import LocationServer
from utils import is_raspi

# I tried to include this in the constructor and make it depedent on self.__leds, but it does not work
if is_raspi():
    from blinkt import set_pixel, show

logger = logging.getLogger(__name__)


class GenericObjectTracker(object):
    def __init__(self,
                 bgr_color,
                 width,
                 middle_percent,
                 minimum_pixels,
                 hsv_range,
                 grpc_port,
                 display,
                 flip_x,
                 flip_y,
                 usb_camera,
                 leds,
                 camera_name,
                 http_host,
                 http_delay_secs,
                 http_file,
                 http_verbose):
        self.__width = width
        self.__middle_percent = middle_percent
        self.__orig_width = width
        self.__orig_middle_percent = middle_percent
        self.__display = display
        self.__flip_x = flip_x
        self.__flip_y = flip_y
        self.__leds = leds

        self.__last_write_millis = 0
        self._prev_x, self._prev_y = -1, -1

        self.stopped = False
        self.cnt = 0
        self.contour_finder = ContourFinder(bgr_color, hsv_range, minimum_pixels)
        self.location_server = LocationServer(grpc_port)
        self.cam = camera.Camera(use_picamera=not usb_camera)
        self.image_server = img_server.ImageServer(http_file, camera_name, http_host, http_delay_secs, http_verbose)

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if 200 <= width <= 4000:
            self.__width = width
            self._prev_x, self._prev_y = -1, -1

    @property
    def middle_percent(self):
        return self.__middle_percent

    @middle_percent.setter
    def middle_percent(self, val):
        if 2 <= val <= 98:
            self.__middle_percent = val
            self._prev_x, self._prev_y = -1, -1

    @property
    def markup_image(self):
        return self.__display or self.image_server.enabled

    def set_leds(self, left_color, right_color):
        if not is_raspi():
            return
        if self.__leds:
            for i in range(0, 4):
                set_pixel(i, left_color[2], left_color[1], left_color[0], brightness=0.05)
        if self.__leds:
            for i in range(4, 8):
                set_pixel(i, right_color[2], right_color[1], right_color[0], brightness=0.05)
            show()

    def clear_leds(self):
        self.set_leds([0, 0, 0], [0, 0, 0])

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self, *process_funcs):
        try:
            self.location_server.start()
        except BaseException as e:
            logger.error("Unable to start location server [{0}]".format(e), exc_info=True)
            sys.exit(1)

        self.image_server.start()

        while self.cam.is_open() and not self.stopped:
            try:
                image = self.cam.read()
                image = imutils.resize(image, width=self.width)
                image = self.flip(image)

                for process_func in process_funcs:
                    process_func(image)

                self.image_server.image = image
                self.display_image(image)

                self.cnt += 1

            except KeyboardInterrupt as e:
                raise e
            except BaseException as e:
                logger.error("Unexpected error in main loop [{0}]".format(e), exc_info=True)
                time.sleep(1)

        self.clear_leds()
        self.cam.close()

    def stop(self):
        self.stopped = True
        self.location_server.stop()
        self.image_server.stop()

    def display_image(self, image):
        if self.__display:
            cv2.imshow("Image", image)

            key = cv2.waitKey(1) & 0xFF

            if key == 255:
                pass
            elif key == ord("w"):
                self.width -= 10
            elif key == ord("W"):
                self.width += 10
            elif key == ord("-") or key == ord("_") or key == 0:
                self.middle_percent -= 1
            elif key == ord("+") or key == ord("=") or key == 1:
                self.middle_percent += 1
            elif key == ord("r"):
                self.width = self.__orig_width
                self.middle_percent = self.__orig_middle_percent
            elif key == ord("s"):
                utils.write_image(image, log_info=True)
            elif key == ord("q"):
                self.stop()

    def flip(self, image):
        img = image
        if self.__flip_x:
            img = cv2.flip(img, 0)
        if self.__flip_y:
            img = cv2.flip(img, 1)
        return img

    @staticmethod
    def cli_args():
        return setup_cli_args(cli.bgr,
                              cli.usb,
                              cli.width,
                              cli.middle_percent,
                              cli.minimum_pixels,
                              cli.hsv_range,
                              cli.grpc_port,
                              cli.leds,
                              cli.flip_x,
                              cli.flip_y,
                              cli.camera_name_optional,
                              cli.display,
                              cli.http_host,
                              cli.http_delay_secs,
                              cli.http_file,
                              cli.verbose_http,
                              cli.verbose)
