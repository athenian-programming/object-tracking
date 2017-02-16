import argparse
import logging

import cli_args as cli
from cli_args import GRPC_PORT_DEFAULT
from cli_args import LOG_LEVEL
from constants import MINIMUM_PIXELS, CAMERA_NAME, HTTP_HOST, USB_CAMERA, DISPLAY, WIDTH, HSV_RANGE, MIDDLE_PERCENT, \
    FLIP_X, FLIP_Y
from dual_object_filter import DualObjectFilter
from object_tracker import ObjectTracker
from single_object_filter import SingleObjectFilter
from utils import setup_logging

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
    cli.camera_name_optional(p),
    cli.display(p),
    cli.http_host(p),
    cli.http_delay_secs(p),
    cli.http_file(p),
    cli.verbose_http(p),
    p.add_argument("--dualbgr", dest="dual_bgr", required=True, help="Dual color BGR value")
    p.add_argument("--singlebgr", dest="single_bgr", required=True, help="Single color BGR value")
    p.add_argument("--dualport", dest="dual_port", default=GRPC_PORT_DEFAULT, type=int,
                   help="Dual gRPC port [{0}]".format(GRPC_PORT_DEFAULT))
    p.add_argument("--singleport", dest="single_port", default=GRPC_PORT_DEFAULT + 1, type=int,
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
                            usb_camera=args[USB_CAMERA],
                            camera_name=args[CAMERA_NAME],
                            http_host=args[HTTP_HOST],
                            http_delay_secs=args["http_delay_secs"],
                            http_file=args["http_file"],
                            http_verbose=args["http_verbose"])

    dual_filter = DualObjectFilter(tracker,
                                   bgr_color=args["dual_bgr"],
                                   hsv_range=args[HSV_RANGE],
                                   minimum_pixels=args[MINIMUM_PIXELS],
                                   grpc_port=args["dual_port"],
                                   leds=False,
                                   display_text=False,
                                   vertical_lines=True,
                                   horizontal_lines=False)

    single_filter = SingleObjectFilter(tracker,
                                       bgr_color=args["single_bgr"],
                                       hsv_range=args[HSV_RANGE],
                                       minimum_pixels=args[MINIMUM_PIXELS],
                                       grpc_port=args["single_port"],
                                       leds=False,
                                       display_text=True,
                                       draw_contour=True,
                                       draw_box=True,
                                       vertical_lines=False,
                                       horizontal_lines=False)

    try:
        tracker.start(single_filter, dual_filter)
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    logger.info("Exiting...")
