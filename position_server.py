import logging
import time
from threading import Lock

import grpc
from concurrent import futures

from gen.grpc_server_pb2 import FocusLinePosition
from gen.grpc_server_pb2 import FocusLinePositionServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_FocusLinePositionServerServicer_to_server
from generic_server import GenericServer


class PositionServer(FocusLinePositionServerServicer, GenericServer):
    def __init__(self, port):
        super(PositionServer, self).__init__(port)
        self._cnt_lock = Lock()

    def registerClient(self, request, context):
        logging.info("Connected to client {0} [{1}]".format(context.peer(), request.info))
        with self._cnt_lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def getFocusLinePositions(self, request, context):
        client_info = request.info
        return self._currval_generator(context.peer())

    def write_position(self, in_focus, mid_offset, degrees, mid_line_cross, width, middle_inc):
        if not self._stopped:
            self._set_currval(FocusLinePosition(id=self._id,
                                                in_focus=in_focus,
                                                mid_offset=mid_offset,
                                                degrees=degrees,
                                                mid_line_cross=mid_line_cross,
                                                width=width,
                                                middle_inc=middle_inc))
            self._id += 1

    def start_position_server(self):
        logging.info("Starting gRPC server listening on {0}".format(self._hostname))
        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_FocusLinePositionServerServicer_to_server(self, self._grpc_server)
        self._grpc_server.add_insecure_port(self._hostname)
        self._grpc_server.start()
        try:
            while not self._stopped:
                time.sleep(2)
        except KeyboardInterrupt:
            self.stop()
