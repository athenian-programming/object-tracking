import logging
import sys

from cli_args import GRPC_PORT_DEFAULT
from contour_finder import ContourFinder
from location_server import LocationServer
from utils import is_raspi

# I tried to include this in the constructor and make it depedent on self.__leds, but it does not work
if is_raspi():
    from blinkt import set_pixel, show

logger = logging.getLogger(__name__)


class GenericFilter(object):
    def __init__(self,
                 tracker,
                 bgr_color,
                 hsv_range,
                 minimum_pixels,
                 grpc_port=GRPC_PORT_DEFAULT,
                 leds=False,
                 display_text=False,
                 vertical_lines=False,
                 horizontal_lines=False):
        self.tracker = tracker
        self.leds = leds
        self.display_text = display_text
        self.vertical_lines = vertical_lines
        self.horizontal_lines = horizontal_lines
        self._prev_x, self._prev_y = -1, -1
        self.contour_finder = ContourFinder(bgr_color, hsv_range, minimum_pixels)
        self.location_server = LocationServer(grpc_port)

    @property
    def prev_x(self):
        return self._prev_x

    @prev_x.setter
    def prev_x(self, val):
        self._prev_x = val

    @property
    def prev_y(self):
        return self._prev_y

    @prev_y.setter
    def prev_y(self, val):
        self._prev_y = val

    def start(self):
        try:
            self.location_server.start()
        except BaseException as e:
            logger.error("Unable to start location server [{0}]".format(e), exc_info=True)
            sys.exit(1)
        if self.leds:
            self.clear_leds()

    def stop(self):
        if self.leds:
            self.clear_leds()
        self.location_server.stop()

    def reset(self):
        self.prev_x, self.prev_y = -1, -1

    def process_image(self, image):
        raise Exception("Should be implemented by sub-class")

    def set_leds(self, left_color, right_color):
        if is_raspi():
            for i in range(0, 4):
                set_pixel(i, left_color[2], left_color[1], left_color[0], brightness=0.05)
            for i in range(4, 8):
                set_pixel(i, right_color[2], right_color[1], right_color[0], brightness=0.05)
            show()

    def clear_leds(self):
        self.set_leds([0, 0, 0], [0, 0, 0])
