#!/usr/bin/env python

import logging

from cli_args import LOG_LEVEL
from constants import DISPLAY, BGR_COLOR, WIDTH, MIDDLE_PERCENT, MASK_X, MASK_Y, USB_PORT
from constants import FLIP_X, DRAW_CONTOUR, DRAW_BOX, VERTICAL_LINES, HORIZONTAL_LINES
from constants import FLIP_Y, HTTP_DELAY_SECS, HTTP_FILE, HTTP_VERBOSE
from constants import MINIMUM_PIXELS, GRPC_PORT, LEDS, HSV_RANGE, CAMERA_NAME, USB_CAMERA, HTTP_HOST
from object_tracker import ObjectTracker
from opencv_utils import contour_slope_degrees
from single_object_filter import SingleObjectFilter
from utils import setup_logging

logger = logging.getLogger(__name__)


def test_for_rope(_filter):
    # Bail if no contour is available
    if _filter.contour is None:
        _filter.reset_data()
        return

    slope, degrees = contour_slope_degrees(_filter.contour)

    # logger.info("Slope: {0}".format(slope))
    # logger.info("Degrees: {0}".format(degrees))

    if abs(degrees) < 80 or (slope is not None and abs(slope) < 20):
        _filter.reset_data()


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
                            mask_x=args[MASK_X],
                            mask_y=args[MASK_Y],
                            usb_camera=args[USB_CAMERA],
                            usb_port=args[USB_PORT],
                            camera_name=args[CAMERA_NAME],
                            http_host=args[HTTP_HOST],
                            http_file=args[HTTP_FILE],
                            http_delay_secs=args[HTTP_DELAY_SECS],
                            http_verbose=args[HTTP_VERBOSE])

    obj_filter = SingleObjectFilter(tracker,
                                    bgr_color=args[BGR_COLOR],
                                    hsv_range=args[HSV_RANGE],
                                    minimum_pixels=args[MINIMUM_PIXELS],
                                    grpc_port=args[GRPC_PORT],
                                    leds=args[LEDS],
                                    display_text=True,
                                    draw_contour=args[DRAW_CONTOUR],
                                    draw_box=args[DRAW_BOX],
                                    vertical_lines=args[VERTICAL_LINES],
                                    horizontal_lines=args[HORIZONTAL_LINES],
                                    predicate=test_for_rope)
    try:
        tracker.start(obj_filter)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    logger.info("Exiting...")
