#!/usr/local/bin/python2

import argparse
import datetime
import logging
import sys
import thread
import threading
import time
import urllib
import urllib2

import cv2
import imutils
import numpy as np

import camera
import gen.color_tracker_pb2
import opencv_utils as utils
from location_server import LocationServer


class ObjectTracker:
    def __init__(self, bgr_color, width, percent, minimum, hsv_range, url, location_server, display=False):
        self._url = url
        self._location_server = location_server
        self._percent = percent
        self._minimum = minimum
        bgr_img = np.uint8([[bgr_color]])
        hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        hsv_value = hsv_img[0, 0, 0]
        self._lower = np.array([hsv_value - hsv_range, 100, 100])
        self._upper = np.array([hsv_value + hsv_range, 255, 255])

        self._width = width
        self._display = display
        self._finished = False
        self._cnt = 0
        self._cam = camera.Camera()

        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._currval = None

    def write_values(self, x, y, width, height):

        # Raspi specific
        # lcd.clear()
        # lcd.write('X, Y: {0}, {1}'.format(cX, cY))

        if self._url:
            params = urllib.urlencode({'x': x, 'y': y, 'w': width, 'h': height})
            try:
                urllib2.urlopen(self._url, params).read()
            except BaseException as e:
                logging.warning("Unable to reach HTTP server {0} [{1}]".format(self._url, e))
        elif self._location_server:
            loc = gen.color_tracker_pb2.Location(x=x, y=y, width=width, height=height)
            self._location_server.write_location(loc)
        else:
            print("{0}, {1} {2}x{3}".format(x, y, width, height))

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):
        img_width = None
        img_height = None
        prev_x = -1
        prev_y = -1
        mid_x = -1
        mid_y = -1
        inc_x = -1
        inc_y = -1
        middle_pct = (self._percent / 100.0) / 2

        self.write_values(-1, -1, 0, 0)

        while self._cam.is_open() and not self._finished:

            frame = self._cam.read()
            frame = imutils.resize(frame, width=self._width)

            if not img_height:
                img_height, img_width = frame.shape[:2]
                mid_x = img_width / 2
                mid_y = img_height / 2
                inc_x = int(mid_x * middle_pct)
                inc_y = int(mid_y * middle_pct)
                logging.info("Width x height: {0}x{1}".format(img_width, img_height))
                logging.info("Center horizontal/vert: {0}/{1}".format(inc_x * 2, inc_y * 2))

            # Convert from BGR to HSV colorspace
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Threshold the HSV image to get only target colors
            mask = cv2.inRange(hsv_frame, self._lower, self._upper)

            # Bitwise-AND mask and original image
            result = cv2.bitwise_and(frame, frame, mask=mask)

            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            contours = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]

            text = '#{0}'.format(self._cnt)

            img_x = -1
            img_y = -1

            max_contour = utils.find_max_contour(contours)

            if max_contour != -1:
                contour = contours[max_contour]
                moment = cv2.moments(contour)
                area = int(moment["m00"])

                if area >= self._minimum:
                    img_x = int(moment["m10"] / area)
                    img_y = int(moment["m01"] / area)

                    if self._display:
                        (x, y, w, h) = cv2.boundingRect(contour)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), utils.BLUE, 2)
                        cv2.drawContours(frame, [contour], -1, utils.GREEN, 2)
                        cv2.circle(frame, (img_x, img_y), 4, utils.RED, -1)
                        text += ' ({0}, {1})'.format(img_x, img_y)
                        text += ' Area: {0}'.format(area)

            # Write location if it is different from previous value written
            if img_x != prev_x or img_y != prev_y:
                self.write_values(img_x, img_y, img_width, img_height)
                prev_x = img_x
                prev_y = img_y

            # Display images
            if self._display:
                x_color = utils.RED if mid_x - inc_x <= img_x <= mid_x + inc_x else utils.BLUE
                y_color = utils.RED if mid_y - inc_y <= img_y <= mid_y + inc_y else utils.BLUE
                cv2.line(frame, (mid_x - inc_x, 0), (mid_x - inc_x, img_height), x_color, 1)
                cv2.line(frame, (mid_x + inc_x, 0), (mid_x + inc_x, img_height), x_color, 1)
                cv2.line(frame, (0, mid_y - inc_y), (img_width, mid_y - inc_y), y_color, 1)
                cv2.line(frame, (0, mid_y + inc_y), (img_width, mid_y + inc_y), y_color, 1)
                cv2.putText(frame, text, utils.text_loc(), utils.text_font(), utils.text_size(), utils.RED,
                            1)
                cv2.imshow("Image", frame)
                # cv2.imshow("Mask", mask)
                # cv2.imshow("Res", result)

                key = cv2.waitKey(30) & 0xFF

                if key == ord("q"):
                    break
                elif key == ord('p'):
                    self.save_frame(frame)
            else:
                # Nap if display is not on
                time.sleep(.1)

            self._cnt += 1

        self._finished = True

    def close(self):
        self._finished = True
        self._cam.close()

    @staticmethod
    def save_frame(frame):
        file_name = "ct-{0}.png".format(datetime.datetime.now().strftime("%H-%M-%S"))
        cv2.imwrite(file_name, frame)
        logging.info("Wrote image to {0}".format(file_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"[174, 56, 5]\"")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-p", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [15]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-g", "--grpc", default=False, action="store_true", help="Run gRPC server [false]")
    parser.add_argument("-n", "--hostname", default="", type=str, help="Servo controller hostname")
    parser.add_argument("-t", "--test", default=False, action="store_true", help="Test mode [false]")
    parser.add_argument('-v', '--verbose', default=logging.INFO, help="Include debugging info",
                        action="store_const", dest="loglevel", const=logging.DEBUG)
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stdout, level=args['loglevel'],
                        format="%(funcName)s():%(lineno)i: %(message)s %(levelname)s")

    # Note this is a BGR value, not RGB!
    bgr_color = eval(args["bgr"])
    logging.info("BGR color: {0}".format(bgr_color))

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

    use_grpc = args["grpc"] or args["test"]
    hostname = args["hostname"]
    url = None
    location_server = None

    if use_grpc:
        location_server = LocationServer('[::]:50051')
        try:
            thread.start_new_thread(LocationServer.start, (location_server,))
            logging.info("Started gRPC location server")
        except BaseException as e:
            logging.error("Unable to start gRPC location server [{0}]".format(e))
            sys.exit(1)
    elif hostname:
        url = "http://" + hostname + "/set_values" if hostname != "" else ""
        logging.info("Servo controller hostname: {0}".format(hostname))

    if args["test"]:
        for i in range(0, 1000):
            loc = gen.color_tracker_pb2.Location(x=i, y=i + 1, width=i + 2, height=i + 3)
            location_server.write_location(loc)
            time.sleep(1)
        print("Exiting...")
        sys.exit(0)

    # Raspi specific
    # import dothat.backlight as backlight
    # import dothat.lcd as lcd
    # backlight.rgb(200, 0,0)

    tracker = ObjectTracker(bgr_color, width, percent, minimum, hsv_range, url, location_server, display)
    tracker.start()
