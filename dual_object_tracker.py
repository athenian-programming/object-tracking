#!/usr/bin/env python2

import argparse
import logging
from logging import info

import cv2
import imutils
import opencv_defaults as defs
from common_constants import LOGGING_ARGS
from common_utils import is_raspi
from generic_object_tracker import GenericObjectTracker
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import YELLOW


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
                 leds=False):
        super(DualObjectTracker, self).__init__(bgr_color,
                                                width,
                                                percent,
                                                minimum,
                                                hsv_range,
                                                grpc_port=grpc_port,
                                                display=display,
                                                flip=flip,
                                                usb_camera=usb_camera,
                                                leds=leds)
        self.__cnt = 0


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

                text = "#{0} ({1}, {2})".format(self.__cnt, img_width, img_height)
                text += " {0}%".format(self.percent)

                # Find the 2 largest contours
                contours = self.contour_finder.get_max_contours(image, self.minimum, count=2)

                # Check for > 2 in case one of the targets is divided.
                # The calculation will be off, but something will be better than nothing
                if contours is not None and len(contours) >= 2:
                    max1 = contours[0]
                    moment1 = cv2.moments(max1)
                    area1 = int(moment1["m00"])
                    img_x1 = int(moment1["m10"] / area1)
                    img_y1 = int(moment1["m01"] / area1)

                    max2 = contours[1]
                    moment2 = cv2.moments(max2)
                    area2 = int(moment2["m00"])
                    img_x2 = int(moment2["m10"] / area2)
                    img_y2 = int(moment2["m01"] / area2)

                    avg_x = (abs(img_x1 - img_x2) / 2) + min(img_x1, img_x2)
                    avg_y = (abs(img_y1 - img_y2) / 2) + min(img_y1, img_y2)

                    if self.display:
                        x1, y1, w1, h1 = cv2.boundingRect(max1)
                        cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), BLUE, 2)
                        cv2.drawContours(image, [max1], -1, GREEN, 2)
                        cv2.circle(image, (img_x1, img_y1), 4, RED, -1)
                        # text += " Obj1: ({0}, {1})".format(img_x1, img_y1)
                        # text += " {0}".format(area1)

                        x2, y2, w2, h2 = cv2.boundingRect(max2)
                        cv2.rectangle(image, (x2, y2), (x2 + w2, y2 + h2), BLUE, 2)
                        cv2.drawContours(image, [max2], -1, GREEN, 2)
                        cv2.circle(image, (img_x2, img_y2), 4, RED, -1)
                        # text += " Obj2: ({0}, {1})".format(img_x2, img_y2)
                        # text += " {0}".format(area2)

                        # Draw midpoint
                        cv2.circle(image, (avg_x, avg_y), 4, YELLOW, -1)
                        text += " Avg: ({0}, {1})".format(avg_x, avg_y)

                x_in_middle = mid_x - middle_inc <= avg_x <= mid_x + middle_inc
                y_in_middle = mid_y - middle_inc <= avg_y <= mid_y + middle_inc
                x_missing = avg_x == -1
                y_missing = avg_y == -1

                # Set Blinkt leds
                self.set_left_leds(RED if x_missing else (GREEN if x_in_middle else BLUE))
                self.set_right_leds(RED if y_missing else (GREEN if y_in_middle else BLUE))

                # Write location if it is different from previous value written
                if avg_x != self._prev_x or avg_y != self._prev_y:
                    self.location_server.write_location(avg_x, avg_y, img_width, img_height, middle_inc)
                    self._prev_x, self._prev_y = avg_x, avg_y

                # Display images
                if self.display:
                    x_color = GREEN if x_in_middle else RED if x_missing else BLUE
                    y_color = GREEN if y_in_middle else RED if y_missing else BLUE

                    # Draw the alignment lines
                    cv2.line(image, (mid_x - middle_inc, 0), (mid_x - middle_inc, img_height), x_color, 1)
                    cv2.line(image, (mid_x + middle_inc, 0), (mid_x + middle_inc, img_height), x_color, 1)
                    cv2.line(image, (0, mid_y - middle_inc), (img_width, mid_y - middle_inc), y_color, 1)
                    cv2.line(image, (0, mid_y + middle_inc), (img_width, mid_y + middle_inc), y_color, 1)

                    cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

                    cv2.imshow("Image", image)

                    self.process_keystroke(image)
                else:
                    # Nap if display is not on
                    # time.sleep(.01)
                    pass

                self.__cnt += 1
            except BaseException as e:
                logging.error("Unexpected error in main loop [{0}]".format(e))

        self.clear_leds()
        self.cam.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"174, 56, 5\"")
    parser.add_argument("-u", "--usb", default=False, action="store_true", help="Use USB Raspi camera [false]")
    parser.add_argument("-f", "--flip", default=False, action="store_true", help="Flip image [false]")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-e", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [100]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-p", "--port", default=50051, type=int, help="gRPC port [50051]")
    parser.add_argument("-l", "--leds", default=False, action="store_true", help="Enable Blinkt led feedback [false]")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-v", "--verbose", default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(**LOGGING_ARGS)

    tracker = DualObjectTracker(bgr_color=eval(args["bgr"] if "[" in args["bgr"] else "[{0}]".format(args["bgr"])),
                                width=args["width"],
                                percent=args["percent"],
                                minimum=args["min"],
                                hsv_range=args["range"],
                                grpc_port=args["port"],
                                display=args["display"],
                                flip=args["flip"],
                                usb_camera=args["usb"],
                                leds=args["leds"] and is_raspi())

    try:
        tracker.start()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()

    info("Exiting...")
