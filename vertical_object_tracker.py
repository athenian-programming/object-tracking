#!/usr/bin/env python2

import logging
import math

import cv2
from cli_args import LOG_LEVEL
from constants import DISPLAY, BGR_COLOR, WIDTH, MIDDLE_PERCENT, FLIP_X, DRAW_CONTOUR, DRAW_BOX
from constants import FLIP_Y, HTTP_DELAY_SECS, HTTP_FILE, HTTP_VERBOSE
from constants import MINIMUM_PIXELS, GRPC_PORT, LEDS, HSV_RANGE, CAMERA_NAME, USB_CAMERA, HTTP_HOST
from object_tracker import ObjectTracker
from single_object_filter import SingleObjectFilter
from utils import setup_logging, distance

logger = logging.getLogger(__name__)


def test_for_rope(filter):
    # Bail if no contour is available
    if filter.contour is None:
        filter.reset_data()
        return

    rect = cv2.minAreaRect(filter.contour)
    box = cv2.boxPoints(rect)

    point_lr = box[0]
    point_ll = box[1]
    point_ul = box[2]
    point_ur = box[3]

    line1 = distance(point_lr, point_ur)
    line2 = distance(point_ur, point_ul)

    if line1 < line2:
        point_lr = box[1]
        point_ll = box[2]
        point_ul = box[3]
        point_ur = box[0]
        line_width = line1
    else:
        line_width = line2

    delta_y = point_lr[1] - point_ur[1]
    delta_x = point_lr[0] - point_ur[0]

    # Calculate angle of line
    if delta_x == 0:
        # Vertical line
        degrees = 90
        ratio = 100
    else:
        # Non-vertical line
        slope = delta_y / delta_x
        radians = math.atan(slope)
        degrees = int(math.degrees(radians)) * -1
        ratio = abs(delta_y / delta_x)

    # logger.info("Ratio: {0}".format(ratio))
    # logger.info("Degrees: {0}".format(degrees))

    if abs(degrees) < 80 or ratio < 20:
        filter.reset_data()


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
                            http_delay_secs=args[HTTP_DELAY_SECS],
                            http_file=args[HTTP_FILE],
                            http_verbose=args[HTTP_VERBOSE])

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
                                horizontal_lines=False,
                                predicate=test_for_rope)
    try:
        tracker.start(filter)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    logger.info("Exiting...")
