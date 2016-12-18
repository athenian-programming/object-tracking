import logging
import threading
import time

import grpc
from concurrent import futures

from gen.grpc_server_pb2 import FocusLinePositionServerServicer
from gen.grpc_server_pb2 import ServerInfo, FocusLinePosition
from gen.grpc_server_pb2 import add_FocusLinePositionServerServicer_to_server


class PositionServer(FocusLinePositionServerServicer):
    def __init__(self, port):
        self._hostname = '[::]:' + str(port)
        self._invoke_cnt = 0
        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._current_position = None

    def RegisterClient(self, request, context):
        print("Connected {0} [{1}]".format(request.info, context.peer()))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info='Server invoke count {0}'.format(self._invoke_cnt))

    def GetFocusLinePositions(self, request, context):
        try:
            client_info = request.info
            while True:
                self._data_ready.wait()
                with self._lock:
                    self._data_ready.clear()
                    yield self._current_position
        finally:
            logging.info("Disconnected from [{0}]".format(context.peer()))

    def publish_focus_line_position(self, in_focus, mid_offset, degrees, mid_line_cross, width, middle_inc):
        with self._lock:
            self._current_position = FocusLinePosition(in_focus=in_focus,
                                                       mid_offset=mid_offset,
                                                       degrees=degrees,
                                                       mid_line_cross=mid_line_cross,
                                                       width=width,
                                                       middle_inc=middle_inc)
            self._data_ready.set()
            # else:
            # Print to console
            #    print("Offset: {0} Angle: {1} Mid line cross: {2} Width: {3} Mid margin: {4}".format(mid_offset,
            #                                                                                         degrees,
            #                                                                                         mid_line_cross,
            #                                                                                         width,
            #                                                                                         middle_inc))

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

