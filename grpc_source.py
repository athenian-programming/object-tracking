import logging
import sys
import thread
import threading

from telemetry_server import TelemetryServer


class GrpcSource(object):
    def __init__(self, port):
        self._telemetry_server = TelemetryServer('[::]:' + str(port), self)

    def start_telemetry_server(self):
        try:
            thread.start_new_thread(self._telemetry_server.start_server, ())
        except BaseException as e:
            logging.error("Unable to start telemetry server [{0}]".format(e))
            sys.exit(1)


class LocationSource(GrpcSource):
    def __init__(self, port):
        super(LocationSource, self).__init__(port)
        self._x = -1
        self._y = -1
        self._width = -1
        self._height = -1
        self._middle_inc = -1
        self._x_lock = threading.Lock()
        self._y_lock = threading.Lock()
        self._x_ready = threading.Event()
        self._y_ready = threading.Event()

    def set_location(self, location):
        with self._x_lock:
            self._x = location[0]
            self._width = location[2]
            self._middle_inc = location[4]
            self._x_ready.set()

        with self._y_lock:
            self._y = location[1]
            self._height = location[3]
            self._middle_inc = location[4]
            self._y_ready.set()

    # Blocking
    def get_x(self):
        self._x_ready.wait()
        with self._x_lock:
            self._x_ready.clear()
            return self._x, self._width, self._middle_inc

    # Blocking
    def get_y(self):
        self._y_ready.wait()
        with self._y_lock:
            self._y_ready.clear()
            return self._y, self._height, self._middle_inc

    # Non-blocking
    def get_pos(self, name):
        return self._x if name == "x" else self._y

    # Non-blocking
    def get_size(self, name):
        return self._width if name == "x" else self._height


class PositionSource(GrpcSource):
    def __init__(self, port):
        super(PositionSource, self).__init__(port)
        self._in_focus = False
        self._mid_offset = -1
        self._degrees = -1
        self._mid_cross = -1
        self._width = -1
        self._middle_inc = -1
        self._lock = threading.Lock()
        self._ready = threading.Event()

    def set_focus_line_position(self, position):
        with self._lock:
            self._in_focus = position[0]
            self._mid_offset = position[1]
            self._degrees = position[2]
            self._mid_cross = position[3]
            self._width = position[4]
            self._middle_inc = position[5]
            self._ready.set()

    # Blocking
    def get_focus_line_position(self):
        self._ready.wait()
        with self._lock:
            self._ready.clear()
            return self._in_focus, self._mid_offset, self._degrees, self._mid_cross, self._width, self._middle_inc
