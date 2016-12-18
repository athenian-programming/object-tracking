import logging
import threading
import time

import grpc
from concurrent import futures

from gen.telemetry_server_pb2 import Empty
from gen.telemetry_server_pb2 import ServerInfo
from gen.telemetry_server_pb2 import TelemetryServerServicer
from gen.telemetry_server_pb2 import add_TelemetryServerServicer_to_server


class TelemetryServer(TelemetryServerServicer):
    def __init__(self, hostname, grpc_source):
        self._hostname = hostname
        self._grpc_source = grpc_source
        self._invoke_cnt = 0
        self._lock = threading.Lock()
        self._grpc_server = None

    def RegisterClient(self, request, context):
        print("Connected {0} [{1}]".format(request.info, context.peer()))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info='Server invoke count {0}'.format(self._invoke_cnt))

    def ReportObjectLocations(self, requests, context):
        for loc in requests:
            try:
                self._grpc_source.set_location((loc.x, loc.y, loc.width, loc.height, loc.middle_inc))
            except BaseException as e:
                logging.error("Unable to read gRPC location data [{0}]".format(e))
        logging.info("Disconnected [{0}]".format(context.peer()))
        return Empty()

    def ReportFocusLinePositions(self, requests, context):
        for pos in requests:
            try:
                self._grpc_source.set_focus_line_position((pos.in_focus,
                                                           pos.mid_offset,
                                                           pos.degrees,
                                                           pos.mid_line_cross,
                                                           pos.width,
                                                           pos.middle_inc))
            except BaseException as e:
                logging.error("Unable to read gRPC position data [{0}]".format(e))
        logging.info("Disconnected [{0}]".format(context.peer()))
        return Empty()

    def start_server(self):
        logging.info("Starting gRPC telemetry server listening on {0}".format(self._hostname))
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_TelemetryServerServicer_to_server(self, grpc_server)
        grpc_server.add_insecure_port(self._hostname)
        grpc_server.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            grpc_server.stop(0)

