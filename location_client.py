import logging
import socket
import threading
import time

import grpc

from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import ObjectLocationServerStub


class LocationClient(object):
    def __init__(self, grpc_hostname):
        self._grpc_hostname = grpc_hostname
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

    def read_locations(self):
        channel = grpc.insecure_channel(self._grpc_hostname)
        grpc_stub = ObjectLocationServerStub(channel)
        while True:
            try:
                client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
                server_info = grpc_stub.RegisterClient(client_info)
                logging.info("Connected to {0} at {1}".format(server_info.info, self._grpc_hostname))
                for loc in grpc_stub.GetObjectLocations(client_info):
                    try:
                        self.set_location((loc.x, loc.y, loc.width, loc.height, loc.middle_inc))
                    except BaseException as e:
                        logging.error("Unable to read gRPC location data [{0}]".format(e))
                logging.info("Disconnected from {0} at {1}".format(server_info.info, self._grpc_hostname))
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0}- [{1}]".format(self._grpc_hostname, e))
                time.sleep(1)
