import logging
import socket
import time
from threading import Event

import grpc

from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import FocusLinePositionServerStub
from grpc_support import GenericClient
from grpc_support import TimeoutException


class PositionClient(GenericClient):
    def __init__(self, hostname):
        super(PositionClient, self).__init__(hostname)
        self.__ready = Event()
        self.__id = -1
        self.__in_focus = False
        self.__mid_offset = -1
        self.__degrees = -1
        self.__mid_cross = -1
        self.__width = -1
        self.__middle_inc = -1

    # Blocking
    def get_position(self, timeout=None):
        while not self._stopped:
            if not self.__ready.wait(timeout):
                raise TimeoutException
            with self._lock:
                if self.__ready.is_set() and not self._stopped:
                    self.__ready.clear()
                    return {"id": self.__id,
                            "in_focus": self.__in_focus,
                            "mid_offset": self.__mid_offset,
                            "degrees": self.__degrees,
                            "mid_cross": self.__mid_cross,
                            "width": self.__width,
                            "middle_inc": self.__middle_inc}

    def read_positions(self, pause_secs=2.0):
        channel = grpc.insecure_channel(self._hostname)
        stub = FocusLinePositionServerStub(channel)
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
                for pos in stub.getFocusLinePositions(client_info):
                    with self._lock:
                        self.__id = pos.id
                        self.__in_focus = pos.in_focus
                        self.__mid_offset = pos.mid_offset
                        self.__degrees = pos.degrees
                        self.__mid_cross = pos.mid_line_cross
                        self.__width = pos.width
                        self.__middle_inc = pos.middle_inc
                    self.__ready.set()
            except BaseException as e:
                logging.info("Disconnected from gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)

    def stop(self):
        if not self._stopped:
            logging.info("Stopping position client")
            self._stopped = True
            self.__ready.set()
