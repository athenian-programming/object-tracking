import logging
import socket
import time
from threading import Event

import grpc

from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import ObjectLocationServerStub
from grpc_support import GenericClient
from grpc_support import TimeoutException


class LocationClient(GenericClient):
    def __init__(self, hostname):
        super(LocationClient, self).__init__(hostname)
        self._x_ready = Event()
        self._y_ready = Event()
        self._id = -1
        self._x = -1
        self._y = -1
        self._width = -1
        self._height = -1
        self._middle_inc = -1

    # Blocking
    def get_x(self, timeout=None):
        while not self._stopped:
            if not self._x_ready.wait():
                raise TimeoutException
            with self._lock:
                if self._x_ready.is_set() and not self._stopped:
                    self._x_ready.clear()
                    return self._x, self._width, self._middle_inc, self._id

    # Blocking
    def get_y(self, timeout=None):
        while not self._stopped:
            if not self._y_ready.wait():
                raise TimeoutException
            with self._lock:
                if self._y_ready.is_set() and not self._stopped:
                    self._y_ready.clear()
                    return self._y, self._height, self._middle_inc, self._id

    # Blocking
    def get_xy(self):
        return self.get_x(), self.get_y()

    # Non-blocking
    def get_loc(self, name):
        return self._x if name == "x" else self._y

    # Non-blocking
    def get_size(self, name):
        return self._width if name == "x" else self._height

    def read_locations(self, pause_secs=2.0):
        channel = grpc.insecure_channel(self._hostname)
        stub = ObjectLocationServerStub(channel)
        while not self._stopped:
            logging.info("Connecting to gRPC server at {0}...".format(self._hostname))
            try:
                client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
                server_info = stub.registerClient(client_info)
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)
                continue

            logging.info("Connected to gRPC server at {0} [{1}]".format(self._hostname, server_info.info))

            try:
                for loc in stub.getObjectLocations(client_info):
                    with self._lock:
                        self._id = loc.id
                        self._x = loc.x
                        self._y = loc.y
                        self._width = loc.width
                        self._height = loc.height
                        self._middle_inc = loc.middle_inc
                    self._x_ready.set()
                    self._y_ready.set()
            except BaseException as e:
                logging.info("Disconnected from gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)

    def stop(self):
        logging.info("Stopping location client")
        self._stopped = True
        self._x_ready.set()
        self._y_ready.set()
