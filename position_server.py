import logging
import threading
import time

import grpc
from concurrent import futures

import opencv_utils as utils
from gen.grpc_server_pb2 import FocusLinePosition
from gen.grpc_server_pb2 import FocusLinePositionServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_FocusLinePositionServerServicer_to_server

if utils.is_python3():
    from queue import Queue
else:
    from Queue import Queue

class PositionServer(FocusLinePositionServerServicer):
    def __init__(self, port):
        self._hostname = "[::]:" + str(port)
        self._invoke_cnt = 0
        self._lock = threading.Lock()
        self._queue = Queue()

    def RegisterClient(self, request, context):
        logging.info("Connected to client {0} [{1}]".format(context.peer(), request.info))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def GetFocusLinePositions(self, request, context):
        try:
            client_info = request.info
            while True:
                yield self._queue.get()
        finally:
            logging.info("Disconnected GetFocusLinePositions stream for client {0}".format(context.peer()))

    def write_focus_line_position(self, in_focus, mid_offset, degrees, mid_line_cross, width, middle_inc):
        pos = FocusLinePosition(in_focus=in_focus,
                                mid_offset=mid_offset,
                                degrees=degrees,
                                mid_line_cross=mid_line_cross,
                                width=width,
                                middle_inc=middle_inc)
        self._queue.put(pos)

    def start_position_server(self):
        logging.info("Starting gRPC position server listening on {0}".format(self._hostname))
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_FocusLinePositionServerServicer_to_server(self, grpc_server)
        grpc_server.add_insecure_port(self._hostname)
        grpc_server.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            grpc_server.stop(0)
