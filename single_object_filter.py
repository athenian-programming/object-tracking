#!/usr/bin/env python2

import logging

import cv2
import opencv_defaults as defs
from cli_args import LOG_LEVEL
from constants import MINIMUM_PIXELS, GRPC_PORT, LEDS, HSV_RANGE, CAMERA_NAME, USB_CAMERA, HTTP_HOST, DISPLAY, \
    BGR_COLOR, \
    WIDTH, MIDDLE_PERCENT, FLIP_X, DRAW_CONTOUR, DRAW_BOX
from generic_filter import GenericFilter
from object_tracker import ObjectTracker
from opencv_utils import BLUE, GREEN, RED
from opencv_utils import get_moment
from utils import setup_logging

logger = logging.getLogger(__name__)


class SingleObjectFilter(GenericFilter):
    def __init__(self, tracker, *args, **kwargs):
        super(SingleObjectFilter, self).__init__(tracker, *args, **kwargs)

    def process_image(self, image):
        img_height, img_width = image.shape[:2]
        mid_x, mid_y = img_width / 2, img_height / 2
        img_x, img_y = -1, -1

        text = "#{0} ({1}, {2})".format(self.tracker.cnt, img_width, img_height)
        text += " {0}%".format(self.tracker.middle_percent)

        # Find the largest contour
        contours = self.contour_finder.get_max_contours(image, count=1)

        if contours is not None and len(contours) == 1:
            contour, area, img_x, img_y = get_moment(contours[0])

            if self.tracker.markup_image:
                x, y, w, h = cv2.boundingRect(contour)
                if self.draw_box:
                    cv2.rectangle(image, (x, y), (x + w, y + h), BLUE, 2)
                if self.draw_contour:
                    cv2.drawContours(image, [contour], -1, GREEN, 2)
                cv2.circle(image, (img_x, img_y), 4, RED, -1)
                text += " ({0}, {1})".format(img_x, img_y)
                text += " {0}".format(area)

        # The middle margin calculation is based on % of width for horizontal and vertical boundary
        middle_pct = (float(self.tracker.middle_percent) / 100.0) / 2
        middle_inc = int(mid_x * middle_pct)
        x_in_middle = mid_x - middle_inc <= img_x <= mid_x + middle_inc
        y_in_middle = mid_y - middle_inc <= img_y <= mid_y + middle_inc
        x_color = GREEN if x_in_middle else RED if img_x == -1 else BLUE
        y_color = GREEN if y_in_middle else RED if img_y == -1 else BLUE

        # Set Blinkt leds
        if self.leds:
            self.set_leds(x_color, y_color)

        # Write location if it is different from previous value written
        if img_x != self.prev_x or img_y != self.prev_y:
            self.location_server.write_location(img_x, img_y, img_width, img_height, middle_inc)
            self.prev_x, self.prev_y = img_x, img_y

        if self.tracker.markup_image:
            # Draw the alignment lines
            if self.vertical_lines:
                cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, img_height), x_color, 1)
                cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, img_height), x_color, 1)
            if self.horizontal_lines:
                cv2.line(image, (0, mid_y - middle_inc), (img_width, mid_y - middle_inc), y_color, 1)
                cv2.line(image, (0, mid_y + middle_inc), (img_width, mid_y + middle_inc), y_color, 1)
            if self.display_text:
                cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)


def FLIPY(args):
    pass


if __name__ == "__main__":
    # Parse CLI args
    args = ObjectTracker.cli_args()

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    tracker = ObjectTracker(width=args[WIDTH],
                            middle_percent=args[MIDDLE_PERCENT],
                            display=args[DISPLAY],
                            flip_x=args[FLIP_X],
                            flip_y=args[FLIPY],
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
