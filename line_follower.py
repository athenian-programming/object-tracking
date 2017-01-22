#!/usr/bin/env python2

import argparse
import logging
import math
import sys
import time
import traceback
from logging import info
from threading import Lock

import cv2
import imutils
import numpy as np

import camera
import defaults as defs
import opencv_utils as utils
from common_utils import is_raspi
from contour_finder import ContourFinder
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import YELLOW
from position_server import PositionServer

if is_raspi():
    from blinkt import set_pixel, show, clear


class LineFollower(object):
    def __init__(self,
                 bgr_color,
                 focus_line_pct,
                 width,
                 percent,
                 minimum,
                 hsv_range,
                 grpc_port,
                 report_midline,
                 display):
        self.__focus_line_pct = focus_line_pct
        self.__width = width
        self.__orig_percent = percent
        self.__orig_width = width
        self.__percent = percent
        self.__minimum = minimum
        self.__report_midline = report_midline
        self.__display = display
        self.__closed = False

        self.__prev_focus_img_x = -1
        self.__prev_mid_line_cross = -1

        self.__cnt = 0
        self.__lock = Lock()
        self.__currval = None

        self.__contour_finder = ContourFinder(bgr_color, hsv_range)
        self.__position_server = PositionServer(grpc_port)
        self.__cam = camera.Camera()

    def set_focus_line_pct(self, focus_line_pct):
        if 1 <= focus_line_pct <= 99:
            self.__focus_line_pct = focus_line_pct

    def set_width(self, width):
        if 200 <= width <= 2000:
            self.__width = width
            self.__prev_focus_img_x = None
            self.__prev_mid_line_cross = None

    def set_percent(self, percent):
        if 2 <= percent <= 98:
            self.__percent = percent
            self.__prev_focus_img_x = None
            self.__prev_mid_line_cross = None

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):
        try:
            self.__position_server.start()
        except BaseException as e:
            logging.error("Unable to start position server [{0}]".format(e))
            sys.exit(1)

        self.__position_server.write_position(False, -1, -1, -1, -1, -1)

        while self.__cam.is_open() and not self.__closed:
            try:
                image = self.__cam.read()
                image = imutils.resize(image, width=self.__width)

                img_height, img_width = image.shape[:2]

                middle_pct = (self.__percent / 100.0) / 2
                mid_x = img_width / 2
                mid_y = img_height / 2
                mid_inc = int(mid_x * middle_pct)
                focus_line_inter = None
                focus_img_x = None
                mid_line_inter = None
                degrees = None
                mid_line_cross = None

                focus_line_y = int(img_height - (img_height * (self.__focus_line_pct / 100.0)))

                focus_mask = np.zeros(image.shape[:2], dtype="uint8")
                cv2.rectangle(focus_mask, (0, focus_line_y - 5), (img_width, focus_line_y + 5), 255, -1)
                focus_image = cv2.bitwise_and(image, image, mask=focus_mask)

                focus_contour = self.__contour_finder.get_max_contour(focus_image, 100)
                if focus_contour is not None:
                    focus_moment = cv2.moments(focus_contour)
                    focus_area = int(focus_moment["m00"])
                    focus_img_x = int(focus_moment["m10"] / focus_area)
                    # focus_img_y = int(focus_moment["m01"] / focus_area)

                text = "#{0} ({1}, {2})".format(self.__cnt, img_width, img_height)
                text += " {0}%".format(self.__percent)

                contour = self.__contour_finder.get_max_contour(image, self.__minimum)
                if contour is not None:
                    moment = cv2.moments(contour)
                    area = int(moment["m00"])
                    img_x = int(moment["m10"] / area)
                    img_y = int(moment["m01"] / area)

                    # if self._display:
                    # (x, y, w, h) = cv2.boundingRect(contour)
                    # cv2.rectangle(frame, (x, y), (x + w, y + h), BLUE, 2)
                    # cv2.drawContours(frame, [contour], -1, GREEN, 2)
                    # cv2.circle(frame, (img_x, img_y), 4, RED, -1)

                    rect = cv2.minAreaRect(contour)
                    box = cv2.boxPoints(rect)

                    # if self.__display:
                    #    cv2.drawContours(image, [np.int0(box)], 0, RED, 2)

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
                        slope = None
                        degrees = 90
                    else:
                        # Non-vertical line
                        slope = delta_y / delta_x
                        radians = math.atan(slope)
                        degrees = int(math.degrees(radians)) * -1

                    # Draw line for slope
                    if slope is None:
                        # Vertical
                        y_inter = None
                        if self.__display:
                            cv2.line(image, (img_x, 0), (img_x, img_height), BLUE, 2)
                    else:
                        # Non vertical
                        y_inter = int(img_y - (slope * img_x))
                        other_y = int((img_width * slope) + y_inter)
                        if self.__display:
                            cv2.line(image, (0, y_inter), (img_width, other_y), BLUE, 2)

                    if focus_img_x is not None:
                        text += " Pos: {0}".format(focus_img_x - mid_x)

                    text += " Angle: {0}".format(degrees)

                    # Calculate point where line intersects focus line
                    if slope != 0:
                        focus_line_inter = int((focus_line_y - y_inter) / slope) if y_inter is not None else img_x

                    # Calculate point where line intersects x midpoint
                    if slope is None:
                        # Vertical line
                        if focus_line_inter == mid_x:
                            mid_line_inter = mid_y
                    else:
                        # Non-vertical line
                        mid_line_inter = int((slope * mid_x) + y_inter)

                    if mid_line_inter is not None:
                        mid_line_cross = focus_line_y - mid_line_inter
                        mid_line_cross = mid_line_cross if mid_line_cross > 0 else -1
                        if mid_line_cross != -1:
                            text += " Mid cross: {0}".format(mid_line_cross)

                    pass
                    # vx, vy, x, y = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
                    # lefty = int((-x * vy / vx) + y)
                    # righty = int(((img_width - x) * vy / vx) + y)
                    # cv2.line(image, (0, lefty), (img_width - 1, righty), GREEN, 2)
                    # Flip this to reverse polarity
                    # delta_y = float(lefty - righty)
                    # delta_x = float(img_width - 1)
                    # slope = round(delta_y / delta_x, 1)
                    # radians = math.atan(slope)
                    # degrees = round(math.degrees(radians), 1)
                    # text += " {0} degrees".format(degrees)

                focus_in_middle = mid_x - mid_inc <= focus_img_x <= mid_x + mid_inc if focus_img_x is not None else False
                focus_x_missing = focus_img_x is None

                # Write position if it is different from previous value written
                if focus_img_x != self.__prev_focus_img_x or (
                            self.__report_midline and mid_line_cross != self.__prev_mid_line_cross):
                    self.__position_server.write_position(focus_img_x is not None,
                                                          focus_img_x - mid_x if focus_img_x is not None else 0,
                                                          degrees,
                                                          mid_line_cross if mid_line_cross is not None else -1,
                                                          img_width,
                                                          mid_inc)
                    self.__prev_focus_img_x = focus_img_x
                    self.__prev_mid_line_cross = mid_line_cross

                if focus_x_missing:
                    set_left_leds(RED)
                    set_right_leds(RED)
                else:
                    set_left_leds(GREEN if focus_in_middle else BLUE)
                    set_right_leds(GREEN if focus_in_middle else BLUE)

                if self.__display:
                    # Draw focus line
                    cv2.line(image, (0, focus_line_y), (img_width, focus_line_y), GREEN, 2)

                    # Draw point where intersects focus line
                    if focus_line_inter is not None:
                        cv2.circle(image, (focus_line_inter, focus_line_y), 6, RED, -1)

                    # Draw center of focus image
                    if focus_img_x is not None:
                        cv2.circle(image, (focus_img_x, focus_line_y + 10), 6, YELLOW, -1)

                    # Draw point of midline insection
                    if mid_line_inter is not None and mid_line_inter <= focus_line_y:
                        cv2.circle(image, (mid_x, mid_line_inter), 6, RED, -1)

                    x_color = GREEN if focus_in_middle else RED if focus_x_missing else BLUE
                    cv2.line(image, (mid_x - mid_inc, 0), (mid_x - mid_inc, img_height), x_color, 1)
                    cv2.line(image, (mid_x + mid_inc, 0), (mid_x + mid_inc, img_height), x_color, 1)
                    cv2.putText(image, text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

                    cv2.imshow("Image", image)
                    # cv2.imshow("Focus", focus_image)

                    key = cv2.waitKey(30) & 0xFF

                    if key == ord("w"):
                        self.set_width(self.__width - 10)
                    elif key == ord("W"):
                        self.set_width(self.__width + 10)
                    elif key == ord("-") or key == ord("_"):
                        self.set_percent(self.__percent - 1)
                    elif key == ord("+") or key == ord("="):
                        self.set_percent(self.__percent + 1)
                    elif key == ord("j"):
                        self.set_focus_line_pct(self.__focus_line_pct - 1)
                    elif key == ord("k"):
                        self.set_focus_line_pct(self.__focus_line_pct + 1)
                    elif key == ord("r"):
                        self.set_width(self.__orig_width)
                        self.set_percent(self.__orig_percent)
                    elif key == ord("p"):
                        utils.save_image(image)
                    elif key == ord("q"):
                        self.stop()
                else:
                    # Nap if display is not on
                    time.sleep(.1)

                self.__cnt += 1
            except BaseException as e:
                traceback.print_exc()
                logging.error("Unexpected error in main loop [{0}]".format(e))

        if is_raspi():
            clear()
        self.__cam.close()

    def stop(self):
        self.__closed = True
        self.__position_server.stop()


def distance(point1, point2):
    xsqr = (point2[0] - point1[0]) ** 2
    ysqr = (point2[1] - point1[1]) ** 2
    return int(math.sqrt(xsqr + ysqr))


def set_left_leds(color):
    if is_raspi():
        for i in range(0, 4):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


def set_right_leds(color):
    if is_raspi():
        for i in range(4, 8):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=50051, type=int, help="gRPC port [50051]")
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"[174, 56, 5]\"")
    parser.add_argument("-f", "--focus", default=10, type=int, help="Focus line % from bottom [10]")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-e", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [100]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-i", "--midline", default=False, action="store_true",
                        help="Report data when changes in midline [false]")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-v", "--verbose", default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stdout, level=args["loglevel"],
                        format="%(funcName)s():%(lineno)i: %(message)s %(levelname)s")

    line_follower = LineFollower(eval(args["bgr"]),
                                 args["focus"],
                                 int(args["width"]),
                                 int(args["percent"]),
                                 int(args["min"]),
                                 int(args["range"]),
                                 args["port"],
                                 args["midline"],
                                 args["display"])

    try:
        line_follower.start()
    except KeyboardInterrupt:
        info("Exiting...")
    finally:
        line_follower.stop()
