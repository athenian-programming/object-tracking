import copy
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
from utils import setup_logging
from utils import sleep

logger = logging.getLogger(__name__)


class LocationClient(GenericClient):
    def __init__(self, hostname):
        super(LocationClient, self).__init__(hostname, desc="location client")
        self.__x_ready = Event()
        self.__y_ready = Event()
        self.__currval = None

    def _mark_ready(self):
        self.__x_ready.set()
        self.__y_ready.set()

    def _get_values(self, pause_secs=2.0):
        channel = grpc.insecure_channel(self.hostname)
        stub = ObjectLocationServerStub(channel)
        while not self.stopped:
            logger.info("Connecting to gRPC server at {0}...".format(self.hostname))
            try:
                client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
                server_info = stub.registerClient(client_info)
            except BaseException as e:
                logger.error("Failed to connect to gRPC server at {0} [{1}]".format(self.hostname, e))
                time.sleep(pause_secs)
                continue

            logger.info("Connected to gRPC server at {0} [{1}]".format(self.hostname, server_info.info))

            try:
                for val in stub.getObjectLocations(client_info):
                    with self.value_lock:
                        self.__currval = copy.deepcopy(val)
                    self._mark_ready()
            except BaseException as e:
                logger.info("Disconnected from gRPC server at {0} [{1}]".format(self.hostname, e))
                time.sleep(pause_secs)

    # Non-blocking
    def get_loc(self, name):
        return self.__currval.x if name == "x" else self.__currval.y

    # Non-blocking
    def get_size(self, name):
        return self.__currval.width if name == "x" else self.__currval.height

    # Blocking
    def get_x(self, timeout=None):
        while not self.stopped:
            if not self.__x_ready.wait(timeout):
                raise TimeoutException
            with self.value_lock:
                if self.__x_ready.is_set() and not self.stopped:
                    self.__x_ready.clear()
                    return self.__currval.x, self.__currval.width, self.__currval.middle_inc, self.__currval.id

    # Blocking
    def get_y(self, timeout=None):
        while not self.stopped:
            if not self.__y_ready.wait(timeout):
                raise TimeoutException
            with self.value_lock:
                if self.__y_ready.is_set() and not self.stopped:
                    self.__y_ready.clear()
                    return self.__currval.y, self.__currval.height, self.__currval.middle_inc, self.__currval.id

    # Blocking
    def get_xy(self):
        return self.get_x(), self.get_y()


if __name__ == "__main__":
    def _run_client(hostname):
        channel = grpc.insecure_channel(hostname)
        stub = ObjectLocationServerStub(channel)
        client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
        server_info = stub.registerClient(client_info)

        for val in stub.getObjectLocations(client_info):
            print("Received location {0}".format(val))
        print("Disconnected from gRPC server at {0}".format(hostname))


    setup_logging()
    Thread(target=_run_client, args=("localhost:50052",)).start()
    sleep()
