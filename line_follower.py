#!/usr/bin/env python2

import argparse
import logging
import math
import socket
import sys
import thread
import threading
import time

import cv2
import grpc
import imutils
import numpy as np

import camera
import opencv_utils as utils
from contour_finder import ContourFinder
from  gen.telemetry_server_pb2 import ClientInfo
from  gen.telemetry_server_pb2 import FocusLinePosition
from gen.telemetry_server_pb2 import TelemetryServerStub
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED
from opencv_utils import YELLOW
from opencv_utils import is_raspi


class ObjectTracker:
    def __init__(self, bgr_color, focus_line_pct, width, percent, minimum, hsv_range, http_url, grpc_hostname,
                 display=False):
        self._focus_line_pct = focus_line_pct
        self._width = width
        self._orig_percent = percent
        self._orig_width = width
        self._percent = percent
        self._minimum = minimum
        self._display = display
        self._http_url = http_url

        self._prev_focus_img_x = None
        self._prev_degrees = None
        self._cnt = 0
        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._currval = None

        self._contour_finder = ContourFinder(bgr_color, hsv_range)

        self._use_grpc = False
        if grpc_hostname:
            self._use_grpc = True
            thread.start_new_thread(self._report_focus_line_positions, (grpc_hostname,))

        self._cam = camera.Camera()

    def _generate_focus_line_positions(self):
        while True:
            self._data_ready.wait()
            with self._lock:
                self._data_ready.clear()
                yield self._current_position

    def _report_focus_line_positions(self, hostname):
        channel = grpc.insecure_channel(hostname)
        grpc_stub = TelemetryServerStub(channel)
        while True:
            try:
                client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
                server_info = grpc_stub.RegisterClient(client_info)
                logging.info("Connected to {0} at {1}".format(server_info.info, hostname))
                grpc_stub.ReportFocusLinePositions(self._generate_focus_line_positions())
                logging.info("Disconnected from {0} at {1}".format(server_info.info, hostname))
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} - [{1}]".format(hostname, e))
                time.sleep(1)

    def _write_focus_line_position(self, in_focus, mid_offset, degrees, mid_line_cross, width, middle_inc):
        if self._use_grpc:
            with self._lock:
                self._current_position = FocusLinePosition(in_focus=in_focus,
                                                           mid_offset=mid_offset,
                                                           degrees=degrees,
                                                           mid_line_cross=mid_line_cross,
                                                           width=width,
                                                           middle_inc=middle_inc)
                self._data_ready.set()
        else:
            # Print to console
            print("Offset: {0} Angle: {1} Mid line cross: {2} Width: {3} Mid margin: {4}".format(mid_offset,
                                                                                                 degrees,
                                                                                                 mid_line_cross,
                                                                                                 width,
                                                                                                 middle_inc))

    def _set_focus_line_pct(self, focus_line_pct):
        if 1 <= focus_line_pct <= 99:
            self._focus_line_pct = focus_line_pct

    def _set_width(self, width):
        if 200 <= width <= 2000:
            self._width = width
            self._prev_focus_img_x = None
            self._prev_degrees = None

    def _set_percent(self, percent):
        if 2 <= percent <= 98:
            self._percent = percent
            self._prev_focus_img_x = None
            self._prev_degrees = None

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):

        self._write_focus_line_position(False, -1, -1, -1, -1, -1)

        while self._cam.is_open():

            image = self._cam.read()
            image = imutils.resize(image, width=self._width)

            img_height, img_width = image.shape[:2]

            middle_pct = (self._percent / 100.0) / 2
            mid_x = img_width / 2
            mid_y = img_height / 2
            mid_inc = int(mid_x * middle_pct)
            focus_line_intersect = None
            focus_img_x = None
            mid_line_intersect = None
            degrees = None
            mid_line_cross = None

            focus_line_y = int(img_height - (img_height * (self._focus_line_pct / 100.0)))

            focus_mask = np.zeros(image.shape[:2], dtype="uint8")
            cv2.rectangle(focus_mask, (0, focus_line_y - 5), (img_width, focus_line_y + 5), 255, -1)
            focus_image = cv2.bitwise_and(image, image, mask=focus_mask)

            focus_contour = self._contour_finder.get_max_contour(focus_image, 100)
            if focus_contour is not None:
                focus_moment = cv2.moments(focus_contour)
                focus_area = int(focus_moment["m00"])
                focus_img_x = int(focus_moment["m10"] / focus_area)
                # focus_img_y = int(focus_moment["m01"] / focus_area)

            text = '#{0} ({1}, {2})'.format(self._cnt, img_width, img_height)
            text += ' {0}%'.format(self._percent)

            contour = self._contour_finder.get_max_contour(image, self._minimum)
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

                # if self._display:
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
                if slope == None:
                    # Vertical
                    y_intercept = None
                    if self._display:
                        cv2.line(image, (img_x, 0), (img_x, img_height), BLUE, 2)
                else:
                    # Non vertical
                    y_intercept = int(img_y - (slope * img_x))
                    other_y = int((img_width * slope) + y_intercept)
                    if self._display:
                        cv2.line(image, (0, y_intercept), (img_width, other_y), BLUE, 2)

                if focus_img_x is not None:
                    text += ' Pos: {0}'.format(focus_img_x - mid_x)

                text += ' Angle: {0}'.format(degrees)

                # Calculate point where line intersects focus line
                if slope != 0:
                    focus_line_intersect = int(
                        (focus_line_y - y_intercept) / slope) if y_intercept is not None else img_x

                # Calculate point where line intersects x midpoint
                if slope == None:
                    # Vertical line
                    if focus_line_intersect == mid_x:
                        mid_line_intersect = mid_y
                else:
                    # Non-vertical line
                    mid_line_intersect = int((slope * mid_x) + y_intercept)

                if mid_line_intersect is not None:
                    mid_line_cross = focus_line_y - mid_line_intersect
                    mid_line_cross = mid_line_cross if mid_line_cross > 0 else -1
                    if mid_line_cross != -1:
                        text += ' Mid cross: {0}'.format(mid_line_cross)

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
                # text += ' {0} degrees'.format(degrees)

            focus_in_middle = mid_x - mid_inc <= focus_img_x <= mid_x + mid_inc if focus_img_x is not None else False
            focus_x_missing = focus_img_x is None

            # Write position if it is different from previous value written
            if focus_img_x != self._prev_focus_img_x or degrees != self._prev_degrees:
                self._write_focus_line_position(focus_img_x is not None,
                                                focus_img_x - mid_x if focus_img_x is not None else 0,
                                                degrees,
                                                mid_line_cross if mid_line_cross is not None else -1,
                                                img_width,
                                                mid_inc)
                self._prev_focus_img_x = focus_img_x
                self._prev_degrees = degrees

            if focus_x_missing:
                _set_left_leds(RED)
                _set_right_leds(RED)
            else:
                _set_left_leds(GREEN if focus_in_middle else BLUE)
                _set_right_leds(GREEN if focus_in_middle else BLUE)

            if self._display:
                # Draw focus line
                cv2.line(image, (0, focus_line_y), (img_width, focus_line_y), GREEN, 2)

                # Draw point where intersects focus line
                if focus_line_intersect is not None:
                    cv2.circle(image, (focus_line_intersect, focus_line_y), 6, RED, -1)

                # Draw center of focus image
                if focus_img_x is not None:
                    cv2.circle(image, (focus_img_x, focus_line_y + 10), 6, YELLOW, -1)

                # Draw point of midline insection
                if mid_line_intersect is not None and mid_line_intersect <= focus_line_y:
                    cv2.circle(image, (mid_x, mid_line_intersect), 6, RED, -1)

                x_color = GREEN if focus_in_middle else RED if focus_x_missing else BLUE
                cv2.line(image, (mid_x - mid_inc, 0), (mid_x - mid_inc, img_height), x_color, 1)
                cv2.line(image, (mid_x + mid_inc, 0), (mid_x + mid_inc, img_height), x_color, 1)
                cv2.putText(image, text, utils.text_loc(), utils.text_font(), utils.text_size(), RED, 1)

                cv2.imshow("Image", image)
                # cv2.imshow("Focus", focus_image)

                key = cv2.waitKey(30) & 0xFF

                if key == ord('w'):
                    self._set_width(self._width - 10)
                elif key == ord('W'):
                    self._set_width(self._width + 10)
                elif key == ord('-') or key == ord('_'):
                    self._set_percent(self._percent - 1)
                elif key == ord('+') or key == ord('='):
                    self._set_percent(self._percent + 1)
                elif key == ord('j'):
                    self._set_focus_line_pct(self._focus_line_pct - 1)
                elif key == ord('k'):
                    self._set_focus_line_pct(self._focus_line_pct + 1)
                elif key == ord('r'):
                    self._set_width(self._orig_width)
                    self._set_percent(self._orig_percent)
                elif key == ord('p'):
                    utils.save_image(image)
                elif key == ord("q"):
                    break
            else:
                # Nap if display is not on
                time.sleep(.1)

            self._cnt += 1

        if is_raspi():
            clear()
        self._cam.close()


def distance(point1, point2):
    xsqr = (point2[0] - point1[0]) ** 2
    ysqr = (point2[1] - point1[1]) ** 2
    return int(math.sqrt(xsqr + ysqr))


def _set_left_leds(color):
    if is_raspi():
        for i in range(0, 4):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


def _set_right_leds(color):
    if is_raspi():
        for i in range(4, 8):
            set_pixel(i, color[2], color[1], color[0], brightness=0.05)
        show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"[174, 56, 5]\"")
    parser.add_argument("-f", "--focus", default=10, type=int, help="Focus line %  [10]")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-e", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [100]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-g", "--grpc", default="", help="Servo controller gRPC server hostname")
    parser.add_argument('-v', '--verbose', default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stdout, level=args['loglevel'],
                        format="%(funcName)s():%(lineno)i: %(message)s %(levelname)s")

    # Note this is a BGR value, not RGB!
    bgr_color = eval(args["bgr"])
    logging.info("BGR color: {0}".format(bgr_color))

    # Horizontal focus line
    focus_line_pct = args["focus"]
    logging.info("Focus line %: {0}".format(focus_line_pct))

    # Define range of colors in HSV
    hsv_range = int(args["range"])
    logging.info("HSV range: {0}".format(hsv_range))

    width = int(args["width"])
    logging.info("Image width: {0}".format(width))

    percent = int(args["percent"])
    logging.info("Middle percent: {0}".format(percent))

    minimum = int(args["min"])
    logging.info("Minimum tager pixel area: {0}".format(minimum))

    display = args["display"]
    logging.info("Display images: {0}".format(display))

    grpc_hostname = args["grpc"]

    url = None

    if grpc_hostname:
        if (":" not in grpc_hostname):
            grpc_hostname += ":50051"
        logging.info("Servo controller gRPC hostname: {0}".format(grpc_hostname))

    if is_raspi():
        from blinkt import set_pixel, show, clear

    try:
        tracker = ObjectTracker(bgr_color,
                                focus_line_pct,
                                width, percent,
                                minimum,
                                hsv_range,
                                url,
                                grpc_hostname,
                                display)
        tracker.start()
    except KeyboardInterrupt as e:
        pass

    print("Exiting...")
