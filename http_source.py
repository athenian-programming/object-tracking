import logging

from flask import Flask
from flask import request

from  generic_source import GenericSource


class HttpSource(GenericSource):
    def __init__(self, port=8080):
        GenericSource.__init__(self)
        self._port = port
        self._flask = Flask(__name__)
        self._flask.logger.disabled = True

        @self._flask.route("/set_values", methods=['POST'])
        def set_values():
            try:
                self.set_curr_loc((int(request.form['x']),
                                   int(request.form['y']),
                                   int(request.form['w']),
                                   int(request.form['h'])))
            except BaseException as e:
                logging.error("Unable to read POST data {0} [{1}]".format(request.form, e))
            return "OK"

    def start(self):
        self._flask.run(port=self._port, host="0.0.0.0")
