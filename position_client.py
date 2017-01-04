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
        self._ready = Event()
        self._id = -1
        self._in_focus = False
        self._mid_offset = -1
        self._degrees = -1
        self._mid_cross = -1
        self._width = -1
        self._middle_inc = -1

    # Blocking
    def get_position(self, timeout=None):
        while not self._stopped:
            if not self._ready.wait(timeout):
                raise TimeoutException
            with self._lock:
                if self._ready.is_set() and not self._stopped:
                    self._ready.clear()
                    return {"id": self._id,
                            "in_focus": self._in_focus,
                            "mid_offset": self._mid_offset,
                            "degrees": self._degrees,
                            "mid_cross": self._mid_cross,
                            "width": self._width,
                            "middle_inc": self._middle_inc}

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
                        self._id = pos.id
                        self._in_focus = pos.in_focus
                        self._mid_offset = pos.mid_offset
                        self._degrees = pos.degrees
                        self._mid_cross = pos.mid_line_cross
                        self._width = pos.width
                        self._middle_inc = pos.middle_inc
                    self._ready.set()
            except BaseException as e:
                logging.info("Disconnected from gRPC server at {0} [{1}]".format(self._hostname, e))
                time.sleep(pause_secs)

    def stop(self):
        logging.info("Stopping position client")
        self._stopped = True
        self._ready.set()
