import argparse
import logging
import socket
import sys
import thread
import threading
import time
import urllib
import urllib2

import cv2
import grpc
import imutils
import numpy as np

import camera
import gen.location_server_pb2
import opencv_utils as utils
from opencv_utils import BLUE
from opencv_utils import GREEN
from opencv_utils import RED


class ObjectTracker:
    def __init__(self, bgr_color, width, percent, minimum, hsv_range, url, grpc_hostname, display=False):
        self._url = url
        self._percent = percent
        self._minimum = minimum
        bgr_img = np.uint8([[bgr_color]])
        hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        hsv_value = hsv_img[0, 0, 0]
        self._lower = np.array([hsv_value - hsv_range, 100, 100])
        self._upper = np.array([hsv_value + hsv_range, 255, 255])

        self._width = width
        self._display = display
        self._prev_x = -1
        self._prev_y = -1
        self._cnt = 0

        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._currval = None

        self._use_grpc = False
        if grpc_hostname:
            self._use_grpc = True
            try:
                thread.start_new_thread(self._connect_to_grpc, (grpc_hostname,))
            except BaseException as e:
                logging.error("Unable to start gRPC client at {0} [{1}]".format(http_hostname, e))

        self._cam = camera.Camera()

    def _write_location(self, val):
        with self._lock:
            self._currloc = val
            self._data_ready.set()

    def _read_location(self):
        self._data_ready.wait()
        with self._lock:
            self._data_ready.clear()
            return self._currloc

    def _generate_locations(self):
        while True:
            yield self._read_location()

    def _connect_to_grpc(self, hostname):
        while True:
            try:
                channel = grpc.insecure_channel(hostname)
                stub = gen.location_server_pb2.LocationServerStub(channel)
                client_info = gen.location_server_pb2.ClientInfo(
                    info='Client running on {0}'.format(socket.gethostname()))
                server_info = stub.RegisterClient(client_info)
                logging.info("Connected to {0}: {1}".format(hostname, server_info.info))
                stub.ReportLocation(self._generate_locations())
                logging.info("Disconnected from {0}: {1}".format(hostname, server_info.info))
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} - [{1}]".format(hostname, e))
                time.sleep(1)

    def _write_location_values(self, x, y, width, height, percent):
        # Raspi specific
        # lcd.clear()
        # lcd.write('X, Y: {0}, {1}'.format(cX, cY))
        if self._url:
            try:
                params = urllib.urlencode({'x': x, 'y': y, 'w': width, 'h': height, 'p': percent})
                urllib2.urlopen(self._url, params).read()
            except BaseException as e:
                logging.warning("Unable to reach HTTP server {0} [{1}]".format(self._url, e))
        elif self._use_grpc:
            loc = gen.location_server_pb2.Location(x=x, y=y, width=width, height=height, percent=percent)
            self._write_location(loc)
        else:
            # Print to console
            print("{0}, {1} {2}x{3} {4}%".format(x, y, width, height, percent))

    def _set_percent(self, percent):
        if 2 <= self._percent <= 98:
            self._percent = percent
            self._prev_x = -1
            self._prev_y = -1

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):

        self._write_location_values(-1, -1, 0, 0, 0)

        while self._cam.is_open():

            frame = self._cam.read()
            frame = imutils.resize(frame, width=self._width)

            middle_pct = (self._percent / 100.0) / 2
            img_height, img_width = frame.shape[:2]
            mid_x = img_width / 2
            mid_y = img_height / 2
            inc_x = int(mid_x * middle_pct)
            inc_y = int(mid_y * middle_pct)

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
                        cv2.rectangle(frame, (x, y), (x + w, y + h), BLUE, 2)
                        cv2.drawContours(frame, [contour], -1, GREEN, 2)
                        cv2.circle(frame, (img_x, img_y), 4, RED, -1)
                        text += ' ({0}, {1})'.format(img_x, img_y)
                        text += ' Area: {0}'.format(area)
                        text += ' {0}%'.format(self._percent)

            if img_x == -1 and img_y == -1:
                set_leds(0, 0, 50)
            else:
                set_leds(50, 0, 0)

            # Write location if it is different from previous value written
            if img_x != self._prev_x or img_y != self._prev_y:
                self._write_location_values(img_x, img_y, img_width, img_height, self._percent)
                self._prev_x = img_x
                self._prev_y = img_y

            # Display images
            if self._display:
                x_color = RED if mid_x - inc_x <= img_x <= mid_x + inc_x else GREEN if img_x == -1 else BLUE
                y_color = RED if mid_y - inc_y <= img_y <= mid_y + inc_y else GREEN if img_x == -1 else BLUE
                cv2.line(frame, (mid_x - inc_x, 0), (mid_x - inc_x, img_height), x_color, 1)
                cv2.line(frame, (mid_x + inc_x, 0), (mid_x + inc_x, img_height), x_color, 1)
                cv2.line(frame, (0, mid_y - inc_y), (img_width, mid_y - inc_y), y_color, 1)
                cv2.line(frame, (0, mid_y + inc_y), (img_width, mid_y + inc_y), y_color, 1)
                cv2.putText(frame, text, utils.text_loc(), utils.text_font(), utils.text_size(), RED,
                            1)
                cv2.imshow("Image", frame)
                # cv2.imshow("Mask", mask)
                # cv2.imshow("Res", result)

                key = cv2.waitKey(30) & 0xFF

                if key == ord('-') or key == ord('_'):
                    self._set_percent(self._percent - 1)
                elif key == ord('+') or key == ord('='):
                    self._set_percent(self._percent + 1)
                elif key == ord('s'):
                    print("Width x height: {0}x{1}".format(img_width, img_height))
                    print("Middle horizontal/vert pixels: {0}/{1} {2}%".format(inc_x * 2, inc_y * 2, self._percent))
                elif key == ord('p'):
                    utils.save_frame(frame)
                elif key == ord("q"):
                    break
            else:
                # Nap if display is not on
                time.sleep(.1)

            self._cnt += 1

        self._cam.close()
        print("Exiting...")

    def _test(self):
        for i in range(0, 1000):
            self._write_location_values(i, i + 1, i + 2, i + 3)
            time.sleep(1)
        print("Exiting...")
        sys.exit(0)


def set_leds(r, g, b):
    if utils.is_raspi():
        for i in range(0, 8):
            set_pixel(i, r, g, b)
        show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bgr", type=str, required=True, help="BGR target value, e.g., -b \"[174, 56, 5]\"")
    parser.add_argument("-w", "--width", default=400, type=int, help="Image width [400]")
    parser.add_argument("-e", "--percent", default=15, type=int, help="Middle percent [15]")
    parser.add_argument("-m", "--min", default=100, type=int, help="Minimum pixel area [100]")
    parser.add_argument("-r", "--range", default=20, type=int, help="HSV range")
    parser.add_argument("-d", "--display", default=False, action="store_true", help="Display image [false]")
    parser.add_argument("-g", "--grpc", default="", help="Servo controller gRPC server hostname")
    parser.add_argument("-o", "--http", default="", type=str,
                        help="Servo controller HTTP hostname, e.g., --http localhost")
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

    grpc_hostname = args["grpc"]
    http_hostname = args["http"]

    url = None

    if grpc_hostname:
        grpc_hostname += ":50051"
        logging.info("Servo controller gRPC hostname: {0}".format(grpc_hostname))
    elif http_hostname:
        url = "http://" + http_hostname + ":8080/set_values"
        logging.info("Servo controller HTTP URL: {0}".format(http_hostname))

    # Raspi specific
    # import dothat.backlight as backlight
    # import dothat.lcd as lcd
    # backlight.rgb(200, 0,0)

    if utils.is_raspi():
        from blinkt import set_pixel, show

    tracker = ObjectTracker(bgr_color, width, percent, minimum, hsv_range, url, grpc_hostname, display)

    if args["test"]:
        try:
            thread.start_new_thread(tracker._test, ())
        except BaseException as e:
            logging.error("Unable to run test thread [{0}]".format(e))
            sys.exit(1)

    try:
        tracker.start()
    except KeyboardInterrupt as e:
        print("Exiting...")
