import logging
import sys
from threading import Lock, Thread

import camera
import common_cli_args  as cli
import cv2
import opencv_utils as utils
from common_cli_args import setup_cli_args
from common_utils import currentTimeMillis, is_raspi
from contour_finder import ContourFinder
from flask import Flask
from flask import redirect
from flask import request
from location_server import LocationServer
from werkzeug.wrappers import Response

# I tried to include this in the constructor and make it depedent on self.__leds, but it does not work
if is_raspi():
    from blinkt import set_pixel, show


class GenericObjectTracker(object):
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
        self.__width = width
        self.__percent = percent
        self.__orig_width = width
        self.__orig_percent = percent
        self.__minimum = minimum
        self.__display = display
        self.__flip = flip
        self.__leds = leds
        self.__camera_name = camera_name
        self.__serve_images = serve_images
        self.__stopped = False
        self.__cnt = 0
        self.__last_write_millis = 0
        self.__current_image_lock = Lock()
        self.__current_image = None

        self._prev_x, self._prev_y = -1, -1

        self.__contour_finder = ContourFinder(bgr_color, hsv_range)
        self.__location_server = LocationServer(grpc_port)
        self.__cam = camera.Camera(use_picamera=not usb_camera)

        if serve_images:
            NAME = "/image.jpg"
            PAGE = "/image"
            PAUSE = "pause"
            flask = Flask(__name__)

            def get_image_page(pause):
                no_cache = '<meta HTTP-EQUIV="Pragma" content="no-cache">'
                name = self.__camera_name + " - " if self.__camera_name else ""
                title = '<title>{0}{1} second pause</title>'.format(name, pause)
                refresh = '<meta http-equiv="refresh" content="{0}">'.format(pause)
                body = '<body><img src="{0}"></body>'.format(NAME)
                return '<!doctype html><html><head>{0}{1}{2}</head>{3}</html>'.format(title, refresh, no_cache, body)

            @flask.route('/')
            def index():
                return redirect(PAGE + "/0")

            @flask.route(PAGE)
            def image_query():
                return get_image_page(request.args.get(PAUSE))

            @flask.route(PAGE + "/<int:{0}>".format(PAUSE))
            def image_path(pause):
                return get_image_page(pause)

            @flask.route(NAME)
            def image_jpg():
                with self.__current_image_lock:
                    retval, buf = utils.encode_image(self.__current_image)
                    bytes = buf.tobytes()
                return Response(bytes, mimetype="image/jpeg")

            # Run HTTP server in a thread
            Thread(target=flask.run, kwargs={"port": 8080}).start()

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, width):
        if 200 <= width <= 4000:
            self.__width = width
            self._prev_x, self._prev_y = -1, -1

    @property
    def percent(self):
        return self.__percent

    @percent.setter
    def percent(self, percent):
        if 2 <= percent <= 98:
            self.__percent = percent
            self._prev_x, self._prev_y = -1, -1

    @property
    def minimum(self):
        return self.__minimum

    @property
    def display(self):
        return self.__display

    @property
    def flip(self):
        return self.__flip

    @property
    def stopped(self):
        return self.__stopped

    @property
    def contour_finder(self):
        return self.__contour_finder

    @property
    def location_server(self):
        return self.__location_server

    @property
    def cam(self):
        return self.__cam

    @property
    def serve_images(self):
        return self.__serve_images

    @property
    def cnt(self):
        return self.__cnt

    @cnt.setter
    def cnt(self, val):
        self.__cnt = val

    @property
    def last_write_millis(self):
        return self.__last_write_millis

    @last_write_millis.setter
    def last_write_millis(self, val):
        self.__last_write_millis = val

    def stop(self):
        self.__stopped = True
        self.__location_server.stop()

    def clear_leds(self):
        self.set_left_leds([0, 0, 0])
        self.set_right_leds([0, 0, 0])

    def set_left_leds(self, color):
        if self.__leds:
            for i in range(0, 4):
                set_pixel(i, color[2], color[1], color[0], brightness=0.05)
            show()

    def set_right_leds(self, color):
        if self.__leds:
            for i in range(4, 8):
                set_pixel(i, color[2], color[1], color[0], brightness=0.05)
            show()

    def display_image(self, image):
        if self.display:
            cv2.imshow("Image", image)

            key = cv2.waitKey(1) & 0xFF

            if key == 255:
                pass
            elif key == ord("w"):
                self.width -= 10
            elif key == ord("W"):
                self.width += 10
            elif key == ord("-") or key == ord("_") or key == 0:
                self.percent -= 1
            elif key == ord("+") or key == ord("=") or key == 1:
                self.percent += 1
            elif key == ord("r"):
                self.width = self.__orig_width
                self.percent = self.__orig_percent
            elif key == ord("s"):
                utils.write_image(image, log_info=True)
            elif key == ord("q"):
                self.stop()

    def serve_image(self, image):
        if self.serve_images:
            now = currentTimeMillis()
            if now - self.last_write_millis > 100:
                with self.__current_image_lock:
                    self.__current_image = image  # copy.deepcopy(image)
                self.last_write_millis = now

    def start(self):
        try:
            self.location_server.start()
        except BaseException as e:
            logging.error("Unable to start location server [{0}]".format(e))
            sys.exit(1)

        self.location_server.write_location(-1, -1, 0, 0, 0)

    def markup_image(self):
        return self.display or self.serve_images

    @staticmethod
    def cli_args():
        return setup_cli_args(cli.bgr,
                              cli.usb,
                              cli.flip,
                              cli.width,
                              cli.percent,
                              cli.min,
                              cli.range,
                              cli.port,
                              cli.leds,
                              cli.camera_optional,
                              cli.http,
                              cli.display,
                              cli.verbose)
