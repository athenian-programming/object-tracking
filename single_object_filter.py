#!/usr/bin/env python2

import logging

import cv2
import opencv_defaults as defs
from cli_args import LOG_LEVEL
from constants import MINIMUM_PIXELS, GRPC_PORT, LEDS, HSV_RANGE, CAMERA_NAME, USB_CAMERA, HTTP_HOST, DISPLAY, \
    BGR_COLOR, \
    WIDTH, MIDDLE_PERCENT, FLIP_X, DRAW_CONTOUR, DRAW_BOX, FLIP_Y
from generic_filter import GenericFilter
from object_tracker import ObjectTracker
from opencv_utils import BLUE, GREEN, RED
from opencv_utils import get_moment
from utils import setup_logging

logger = logging.getLogger(__name__)


class SingleObjectFilter(GenericFilter):
    def __init__(self, tracker, *args, **kwargs):
        super(SingleObjectFilter, self).__init__(tracker, *args, **kwargs)
        self.contour = None
        self.area = None
        self.img_x = -1
        self.img_y = -1

    def process_image(self, image):
        self.height, self.width = image.shape[:2]
        self.img_x, self.img_y = -1, -1
        self.contour = None

        # Find the largest contour
        self.contours = self.contour_finder.get_max_contours(image, count=1)

        if self.contours is not None and len(self.contours) == 1:
            self.contour, self.area, self.img_x, self.img_y = get_moment(self.contours[0])

        # Write location if it is different from previous value written
        if self.img_x != self.prev_x or self.img_y != self.prev_y:
            self.location_server.write_location(self.img_x, self.img_y, self.width, self.height, self.middle_inc())
            self.prev_x, self.prev_y = self.img_x, self.img_y

    def markup_image(self, image):
        mid_x, mid_y = self.width / 2, self.height / 2
        middle_inc = self.middle_inc()

        text = "#{0} ({1}, {2})".format(self.tracker.cnt, self.width, self.height)
        text += " {0}%".format(self.tracker.middle_percent)

        x_in_middle = mid_x - middle_inc <= self.img_x <= mid_x + middle_inc
        y_in_middle = mid_y - middle_inc <= self.img_y <= mid_y + middle_inc
        x_color = GREEN if x_in_middle else RED if self.img_x == -1 else BLUE
        y_color = GREEN if y_in_middle else RED if self.img_y == -1 else BLUE

        if self.tracker.markup_image:
            if self.contours is not None and len(self.contours) == 1:
                x, y, w, h = cv2.boundingRect(self.contour)
                if self.draw_box:
                    cv2.rectangle(image, (x, y), (x + w, y + h), BLUE, 2)
                if self.draw_contour:
                    cv2.drawContours(image, [self.contour], -1, GREEN, 2)
                cv2.circle(image, (self.img_x, self.img_y), 4, RED, -1)
                text += " ({0}, {1})".format(self.img_x, self.img_y)
                text += " {0}".format(self.area)

            # Draw the alignment lines
            if self.vertical_lines:
                cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, self.height), x_color, 1)
                cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, self.height), x_color, 1)
            if self.horizontal_lines:
                cv2.line(image, (0, mid_y - middle_inc), (self.width, mid_y - middle_inc), y_color, 1)
                cv2.line(image, (0, mid_y + middle_inc), (self.width, mid_y + middle_inc), y_color, 1)
            if self.display_text:
                cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

        # Set Blinkt leds
        if self.leds:
            self.set_leds(x_color, y_color)


if __name__ == "__main__":
    # Parse CLI args
    args = ObjectTracker.cli_args()

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    tracker = ObjectTracker(width=args[WIDTH],
                            middle_percent=args[MIDDLE_PERCENT],
                            display=args[DISPLAY],
                            flip_x=args[FLIP_X],
                            flip_y=args[FLIP_Y],
                            usb_camera=args[USB_CAMERA],
                            camera_name=args[CAMERA_NAME],
                            http_host=args[HTTP_HOST],
                            http_delay_secs=args["http_delay_secs"],
                            http_file=args["http_file"],
                            http_verbose=args["http_verbose"])

    filter = SingleObjectFilter(tracker,
                                bgr_color=args[BGR_COLOR],
                                hsv_range=args[HSV_RANGE],
                                minimum_pixels=args[MINIMUM_PIXELS],
                                grpc_port=args[GRPC_PORT],
                                leds=args[LEDS],
                                display_text=True,
                                draw_contour=args[DRAW_CONTOUR],
                                draw_box=args[DRAW_BOX],
                                vertical_lines=True,
                                horizontal_lines=False)
    try:
        tracker.start(filter)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    logger.info("Exiting...")
