import logging
import time
import traceback
from threading import Thread

from common_utils import is_raspi
from flask import Flask
from flask import redirect
from flask import request
from werkzeug.wrappers import Response


class HttpServer(object):
    def __init__(self, camera_name, http_host, http_delay_secs, image_src):
        self.__camera_name = camera_name
        self.__http_host = http_host
        self.__http_delay_secs = http_delay_secs
        self.__image_src = image_src
        self.__http_launched = False

    def is_enabled(self):
        return len(self.__http_host) > 0

    def serve_images(self, width, height):
        if self.__http_launched or not self.is_enabled():
            return

        flask = Flask(__name__)

        @flask.route('/')
        def index():
            return redirect("/image?delay=.5")

        def get_page(delay):
            try:
                delay_secs = float(delay) if delay else self.__http_delay_secs
                prefix = "/home/pi/git/object-tracking" if is_raspi() else "."
                with open("{0}/html/image-reader.html".format(prefix)) as file:
                    html = file.read()
                    name = self.__camera_name if self.__camera_name else "UNNAMED"
                    return html.replace("_TITLE_", "Camera: " + name) \
                        .replace("_DELAY_SECS_", str(delay_secs)) \
                        .replace("_NAME_", name) \
                        .replace("_WIDTH_", str(width)) \
                        .replace("_HEIGHT_", str(height))
            except BaseException as e:
                logging.error("Unable to generate html page [{0}]".format(e))
                traceback.print_exc()
                time.sleep(1)

        time.sleep(1)

        @flask.route('/image')
        def image_option():
            return get_page(request.args.get("delay"))

        @flask.route("/image" + "/<string:delay>")
        def image_path(delay):
            return get_page(delay)

        @flask.route("/image.jpg")
        def image_jpg():
            bytes = self.__image_src()
            response = Response(bytes, mimetype="image/jpeg")
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            return response

        def run_http(flask, host, port):
            while True:
                try:
                    flask.run(host=host, port=port)
                except BaseException as e:
                    logging.error("Restarting HTTP server [{0}]".format(e))
                    traceback.print_exc()
                    time.sleep(1)

        # Run HTTP server in a thread
        vals = self.__http_host.split(":")
        host = vals[0]
        port = vals[1] if len(vals) == 2 else 8080
        Thread(target=run_http, kwargs={"flask": flask, "host": host, "port": port}).start()
        self.__http_launched = True
        logging.info("Started HTTP server listening on {0}:{1}".format(host, port))
