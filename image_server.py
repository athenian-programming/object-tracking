import logging
import time
import traceback
from threading import Thread

import requests
from flask import Flask
from flask import redirect
from flask import request
from werkzeug.wrappers import Response

http_host_default = "localhost:8080"
http_delay_secs_default = 0.5
http_path_default = "./html"


class ImageServer(object):
    template_name = "image-reader.html"

    def __init__(self, camera_name, http_host, http_delay_secs, http_path, image_src):
        self.__camera_name = camera_name
        self.__http_host = http_host
        self.__http_delay_secs = http_delay_secs
        self.__image_src = image_src

        vals = self.__http_host.split(":")
        self.__host = vals[0]
        self.__port = vals[1] if len(vals) == 2 else 8080
        self.__url = "http://{0}:{1}".format(self.__host, self.__port)

        self.__launched = False
        self.__stopped = False
        self.__ready_to_stop = False
        self.__path = (http_path if http_path.endswith(".html")
                       else "{0}/{1}".format(http_path, self.template_name)).replace("//", "/")
        logging.info("Using html page template {0}".format(self.__path))

    def is_enabled(self):
        return len(self.__http_host) > 0

    def stop(self):
        self.__ready_to_stop = True
        requests.post('{0}/__shutdown__'.format(self.__url))

    def serve_images(self, width, height):
        if self.__launched or not self.is_enabled():
            return

        flask = Flask(__name__)

        @flask.route('/')
        def index():
            return redirect("/image?delay=.5")

        def get_page(delay):
            delay_secs = float(delay) if delay else self.__http_delay_secs
            try:
                with open(self.__path) as f:
                    html = f.read()
                    name = self.__camera_name if self.__camera_name else "UNNAMED"
                    return html.replace("_TITLE_", "Camera: " + name) \
                        .replace("_DELAY_SECS_", str(delay_secs)) \
                        .replace("_NAME_", name) \
                        .replace("_WIDTH_", str(width)) \
                        .replace("_HEIGHT_", str(height))
            except BaseException as e:
                logging.error("Unable to generate html page for {0} [{1}]".format(self.__path, e))
                traceback.print_exc()
                time.sleep(1)

        @flask.route('/image')
        def image_option():
            return get_page(request.args.get("delay"))

        @flask.route("/image" + "/<string:delay>")
        def image_path(delay):
            return get_page(delay)

        @flask.route("/image.jpg")
        def image_jpg():
            b = self.__image_src()
            response = Response(b, mimetype="image/jpeg")
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            return response

        @flask.route("/__shutdown__", methods=['POST'])
        def shutdown():
            if not self.__ready_to_stop:
                return "Not ready to stop"
            shutdown_func = request.environ.get('werkzeug.server.shutdown')
            if shutdown_func is not None:
                self.__stopped = True
                shutdown_func()
            return "Shutting down..."

        def run_http(flask_server, host, port):
            while not self.__stopped:
                try:
                    flask_server.run(host=host, port=port)
                except BaseException as e:
                    logging.error("Restarting HTTP server [{0}]".format(e))
                    traceback.print_exc()
                    time.sleep(1)
                finally:
                    logging.info("HTTP server shutdown")

        # Run HTTP server in a thread
        Thread(target=run_http, kwargs={"flask_server": flask, "host": self.__host, "port": self.__port}).start()
        self.__launched = True
        logging.info("Started HTTP server listening on {0}:{1}".format(self.__host, self.__port))
