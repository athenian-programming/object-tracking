import logging
import socket
import time
from threading import Event
from threading import Thread

import grpc
from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import ObjectLocationServerStub
from grpc_support import GenericClient
from grpc_support import TimeoutException

logger = logging.getLogger(__name__)

class LocationClient(GenericClient):
    def __init__(self, hostname):
        super(LocationClient, self).__init__(hostname)
        self.__x_ready = Event()
        self.__y_ready = Event()
        self.__id = -1
        self.__x = -1
        self.__y = -1
        self.__width = -1
        self.__height = -1
        self.__middle_inc = -1
        self._stopped = False

    # Blocking
    def get_x(self, timeout=None):
        while not self._stopped:
            if not self.__x_ready.wait(timeout):
                raise TimeoutException
            with self._lock:
                if self.__x_ready.is_set() and not self._stopped:
                    self.__x_ready.clear()
                    return self.__x, self.__width, self.__middle_inc, self.__id

    # Blocking
    def get_y(self, timeout=None):
        while not self._stopped:
            if not self.__y_ready.wait(timeout):
                raise TimeoutException
            with self._lock:
                if self.__y_ready.is_set() and not self._stopped:
                    self.__y_ready.clear()
                    return self.__y, self.__height, self.__middle_inc, self.__id

    # Blocking
    def get_xy(self):
        return self.get_x(), self.get_y()

    # Non-blocking
    def get_loc(self, name):
        return self.__x if name == "x" else self.__y

    # Non-blocking
    def get_size(self, name):
        return self.__width if name == "x" else self.__height

    def read_locations(self, pause_secs=2.0):
        channel = grpc.insecure_channel(self._hostname)
        stub = ObjectLocationServerStub(channel)
        while not self._stopped:
            logger.info("Connecting to gRPC server at {0}...".format(self._hostname))
            try:
                client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
                server_info = stub.registerClient(client_info)
            except BaseException as e:
                logger.error("Failed to connect to gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)
                continue

            logger.info("Connected to gRPC server at {0} [{1}]".format(self._hostname, server_info.info))

            try:
                for loc in stub.getObjectLocations(client_info):
                    with self._lock:
                        self.__id = loc.id
                        self.__x = loc.x
                        self.__y = loc.y
                        self.__width = loc.width
                        self.__height = loc.height
                        self.__middle_inc = loc.middle_inc
                    self.__x_ready.set()
                    self.__y_ready.set()
            except BaseException as e:
                logger.info("Disconnected from gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)

    def start(self):
        Thread(target=self.read_locations).start()
        return self

    def stop(self):
        if not self._stopped:
            logger.info("Stopping location client")
            self._stopped = True
            self.__x_ready.set()
            self.__y_ready.set()
