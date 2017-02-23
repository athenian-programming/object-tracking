import argparse
import logging

import cli_args as cli
from cli_args import GRPC_PORT_DEFAULT
from cli_args import LOG_LEVEL
from constants import DRAW_CONTOUR, DRAW_BOX, VERTICAL_LINES, HORIZONTAL_LINES, HTTP_STARTUP_SLEEP_SECS, MASK_X, MASK_Y, \
    USB_PORT
from constants import HSV_RANGE, MIDDLE_PERCENT, FLIP_X, FLIP_Y
from constants import HTTP_DELAY_SECS, HTTP_FILE, HTTP_VERBOSE
from constants import MINIMUM_PIXELS, CAMERA_NAME, HTTP_HOST, USB_CAMERA, DISPLAY, WIDTH
from dual_object_filter import DualObjectFilter
from object_tracker import ObjectTracker
from single_object_filter import SingleObjectFilter
from utils import setup_logging

DUAL_BGR = "dual_bgr"
SINGLE_BGR = "single_bgr"
DUAL_PORT = "dual_port"
SINGLE_PORT = "single_port"

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    p = argparse.ArgumentParser()
    cli.usb(p),
    cli.width(p),
    cli.middle_percent(p),
    cli.minimum_pixels(p),
    cli.hsv_range(p),
    cli.leds(p),
    cli.flip_x(p),
    cli.flip_y(p),
    cli.mask_x(p),
    cli.mask_y(p),
    cli.vertical_lines(p),
    cli.horizontal_lines(p),
    cli.camera_name_optional(p),
    cli.display(p),
    cli.draw_contour(p),
    cli.draw_box(p),
    cli.http_host(p),
    cli.http_delay_secs(p),
    cli.http_startup_sleep_secs(p),
    cli.http_file(p),
    cli.http_verbose(p),
    p.add_argument("--dualbgr", dest=DUAL_BGR, required=True, help="Dual color BGR value")
    p.add_argument("--singlebgr", dest=SINGLE_BGR, required=True, help="Single color BGR value")
    p.add_argument("--dualport", dest=DUAL_PORT, default=GRPC_PORT_DEFAULT, type=int,
                   help="Dual gRPC port [{0}]".format(GRPC_PORT_DEFAULT))
    p.add_argument("--singleport", dest=SINGLE_PORT, default=GRPC_PORT_DEFAULT + 1, type=int,
                   help="Dual gRPC port [{0}]".format(GRPC_PORT_DEFAULT + 1))
    cli.verbose(p)
    args = vars(p.parse_args())

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
                            http_startup_sleep_secs=args[HTTP_STARTUP_SLEEP_SECS],
                            http_verbose=args[HTTP_VERBOSE])

    dual_filter = DualObjectFilter(tracker,
                                   bgr_color=args[DUAL_BGR],
                                   hsv_range=args[HSV_RANGE],
                                   minimum_pixels=args[MINIMUM_PIXELS],
                                   grpc_port=args[DUAL_PORT],
                                   leds=False,
                                   display_text=False,
                                   draw_contour=args[DRAW_CONTOUR],
                                   draw_box=args[DRAW_BOX],
                                   vertical_lines=args[VERTICAL_LINES],
                                   horizontal_lines=args[HORIZONTAL_LINES])

    single_filter = SingleObjectFilter(tracker,
                                       bgr_color=args[SINGLE_BGR],
                                       hsv_range=args[HSV_RANGE],
                                       minimum_pixels=args[MINIMUM_PIXELS],
                                       grpc_port=args[SINGLE_PORT],
                                       leds=False,
                                       display_text=True,
                                       draw_contour=args[DRAW_CONTOUR],
                                       draw_box=args[DRAW_BOX],
                                       vertical_lines=False,
                                       horizontal_lines=False)

    try:
        tracker.start(single_filter, dual_filter)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    logger.info("Exiting...")
