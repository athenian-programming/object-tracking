import logging
import socket
import threading
import time

import grpc

from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import FocusLinePositionServerStub


class PositionClient(object):
    def __init__(self, grpc_hostname):
        self._grpc_hostname = grpc_hostname if ":" in grpc_hostname else grpc_hostname + ":50051"
        self._stopped = False
        self._in_focus = False
        self._mid_offset = -1
        self._degrees = -1
        self._mid_cross = -1
        self._width = -1
        self._middle_inc = -1
        self._lock = threading.Lock()
        self._ready = threading.Event()

    def _set_focus_line_position(self, position):
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
        while True:
            self._ready.wait()
            with self._lock:
                if self._ready.is_set() and not self._stopped:
                    self._ready.clear()
                    return self._in_focus, \
                           self._mid_offset, \
                           self._degrees, \
                           self._mid_cross, \
                           self._width, \
                           self._middle_inc

    def read_positions(self):
        channel = grpc.insecure_channel(self._grpc_hostname)
        stub = FocusLinePositionServerStub(channel)
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
                for pos in stub.getFocusLinePositions(client_info):
                    self._set_focus_line_position((pos.in_focus,
                                                   pos.mid_offset,
                                                   pos.degrees,
                                                   pos.mid_line_cross,
                                                   pos.width,
                                                   pos.middle_inc))
            except BaseException:
                logging.info("Disconnected from gRPC server at {0} [{1}]".format(self._grpc_hostname,
                                                                                 server_info.info))

    def stop(self):
        logging.info("Stopping position client")
        self._stopped = True
        self._ready.set()
