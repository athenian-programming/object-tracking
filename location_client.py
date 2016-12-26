import logging
import socket
import time
from threading import Event
from threading import Lock

import grpc

from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import ObjectLocationServerStub


class LocationClient(object):
    def __init__(self, grpc_hostname):
        self._grpc_hostname = grpc_hostname if ":" in grpc_hostname else grpc_hostname + ":50051"
        self._stopped = False
        self._x = -1
        self._y = -1
        self._width = -1
        self._height = -1
        self._middle_inc = -1
        self._x_lock = Lock()
        self._y_lock = Lock()
        self._x_ready = Event()
        self._y_ready = Event()

    def _set_location(self, location):
        with self._x_lock:
            self._x = location[0]
            self._width = location[2]
            self._middle_inc = location[4]
            self._id = location[5]
            self._x_ready.set()

        with self._y_lock:
            self._y = location[1]
            self._height = location[3]
            self._middle_inc = location[4]
            self._id = location[5]
            self._y_ready.set()

    # Blocking
    def get_x(self):
        while not self._stopped:
            self._x_ready.wait()
            with self._x_lock:
                if self._x_ready.is_set() and not self._stopped:
                    self._x_ready.clear()
                    return self._x, self._width, self._middle_inc, self._ts, self._id

    # Blocking
    def get_y(self):
        while not self._stopped:
            self._y_ready.wait()
            with self._y_lock:
                if self._y_ready.is_set() and not self._stopped:
                    self._y_ready.clear()
                    return self._y, self._height, self._middle_inc, self._ts, self._id

    # Blocking
    def get_xy(self):
        return (self.get_x(), self.get_y())

    # Non-blocking
    def get_loc(self, name):
        return self._x if name == "x" else self._y

    # Non-blocking
    def get_size(self, name):
        return self._width if name == "x" else self._height

    def read_locations(self):
        channel = grpc.insecure_channel(self._grpc_hostname)
        stub = ObjectLocationServerStub(channel)
        while not self._stopped:
            logging.info("Connecting to gRPC server at {0}...".format(self._grpc_hostname))
            try:
                client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
                server_info = stub.registerClient(client_info)
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} [{1}]".format(self._grpc_hostname, e))
                time.sleep(2)
                continue

            logging.info("Connected to gRPC server at {0} [{1}]".format(self._grpc_hostname, server_info.info))

            try:
                for loc in stub.getObjectLocations(client_info):
                    self._set_location((loc.x,
                                        loc.y,
                                        loc.width,
                                        loc.height,
                                        loc.middle_inc,
                                        loc.ts,
                                        loc.id))
            except BaseException:
                logging.info("Disconnected from gRPC server at {0} [{1}]".format(self._grpc_hostname, server_info.info))
                time.sleep(2)

    def stop(self):
        logging.info("Stopping location client")
        self._stopped = True
        self._x_ready.set()
        self._y_ready.set()
