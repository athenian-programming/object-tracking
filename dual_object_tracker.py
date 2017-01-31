#!/usr/bin/env python2

import logging
import time
import traceback
from logging import info

import cv2
import imutils
import opencv_defaults as defs
from common_constants import LOGGING_ARGS
from common_utils import is_raspi
from generic_object_tracker import GenericObjectTracker
from opencv_utils import BLUE, GREEN, RED, YELLOW
from opencv_utils import get_list_arg, get_moment


class DualObjectTracker(GenericObjectTracker):
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
                 leds=False,
                 camera_name="",
                 serve_images=False):
        super(DualObjectTracker, self).__init__(bgr_color,
                                                width,
                                                percent,
                                                minimum,
                                                hsv_range,
                                                grpc_port=grpc_port,
                                                display=display,
                                                flip=flip,
                                                usb_camera=usb_camera,
                                                leds=leds,
                                                camera_name=camera_name,
                                                serve_images=serve_images)

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):
        super(DualObjectTracker, self).start()

        while self.cam.is_open() and not self.stopped:
            try:
                image = self.cam.read()
                image = imutils.resize(image, width=self.width)

                if self.flip:
                    image = cv2.flip(image, 0)

                middle_pct = (self.percent / 100.0) / 2
                img_height, img_width = image.shape[:2]

                mid_x, mid_y = img_width / 2, img_height / 2
                avg_x, avg_y = -1, -1

                # The middle margin calculation is based on % of width for horizontal and vertical boundry
                middle_inc = int(mid_x * middle_pct)

                text = "#{0} ({1}, {2})".format(self.cnt, img_width, img_height)
                text += " {0}%".format(self.percent)

                # Find the 2 largest contours
                contours = self.contour_finder.get_max_contours(image, self.minimum, count=2)

                # Check for > 2 in case one of the targets is divided.
                # The calculation will be off, but something will be better than nothing
                if contours is not None and len(contours) >= 2:
                    countour1, area1, img_x1, img_y1 = get_moment(contours[0])
                    countour2, area2, img_x2, img_y2 = get_moment(contours[1])

                    # Callculate the average location between the two midpoints
                    avg_x = (abs(img_x1 - img_x2) / 2) + min(img_x1, img_x2)
                    avg_y = (abs(img_y1 - img_y2) / 2) + min(img_y1, img_y2)

                    if self.markup_image:
                        x1, y1, w1, h1 = cv2.boundingRect(countour1)
                        cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), BLUE, 2)
                        cv2.drawContours(image, [countour1], -1, GREEN, 2)
                        cv2.circle(image, (img_x1, img_y1), 4, RED, -1)
                        # text += " Obj1: ({0}, {1})".format(img_x1, img_y1)
                        # text += " {0}".format(area1)

                        x2, y2, w2, h2 = cv2.boundingRect(countour2)
                        cv2.rectangle(image, (x2, y2), (x2 + w2, y2 + h2), BLUE, 2)
                        cv2.drawContours(image, [countour2], -1, GREEN, 2)
                        cv2.circle(image, (img_x2, img_y2), 4, RED, -1)
                        # text += " Obj2: ({0}, {1})".format(img_x2, img_y2)
                        # text += " {0}".format(area2)

                        # Draw midpoint
                        cv2.circle(image, (avg_x, avg_y), 4, YELLOW, -1)
                        text += " Avg: ({0}, {1})".format(avg_x, avg_y)

                x_in_middle = mid_x - middle_inc <= avg_x <= mid_x + middle_inc
                y_in_middle = mid_y - middle_inc <= avg_y <= mid_y + middle_inc

                x_color = GREEN if x_in_middle else RED if avg_x == -1 else BLUE
                y_color = GREEN if y_in_middle else RED if avg_y == -1 else BLUE

                # Set Blinkt leds
                self.set_left_leds(x_color)
                self.set_right_leds(y_color)

                # Write location if it is different from previous value written
                if avg_x != self._prev_x or avg_y != self._prev_y:
                    self.location_server.write_location(avg_x, avg_y, img_width, img_height, middle_inc)
                    self._prev_x, self._prev_y = avg_x, avg_y

                # Display images
                if self.markup_image:
                    # Draw the alignment lines
                    cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, img_height), x_color, 1)
                    cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, img_height), x_color, 1)
                    cv2.line(image, (0, mid_y - middle_inc), (img_width, mid_y - middle_inc), y_color, 1)
                    cv2.line(image, (0, mid_y + middle_inc), (img_width, mid_y + middle_inc), y_color, 1)

                    cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

                self.display_image(image)
                self.serve_image(image)

                self.cnt += 1

            except BaseException as e:
                traceback.print_exc()
                logging.error("Unexpected error in main loop [{0}]".format(e))
                time.sleep(1)

        self.clear_leds()
        self.cam.close()


if __name__ == "__main__":
    # Parse CLI args
    args = GenericObjectTracker.cli_args()

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    tracker = DualObjectTracker(get_list_arg(args["bgr"]),
                                args["width"],
                                args["percent"],
                                args["min"],
                                args["range"],
                                grpc_port=args["port"],
                                display=args["display"],
                                flip=args["flip"],
                                usb_camera=args["usb"],
                                leds=args["leds"] and is_raspi(),
                                camera_name=args["camera"],
                                serve_images=args["http"])

    try:
        tracker.start()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    info("Exiting...")
