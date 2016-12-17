import logging
import threading
import time

import grpc
from concurrent import futures

from gen.location_server_pb2 import Empty
from gen.location_server_pb2 import LocationServerServicer
from gen.location_server_pb2 import LocationServerStub
from gen.location_server_pb2 import ServerInfo
from gen.location_server_pb2 import add_LocationServerServicer_to_server


class LocationServer(LocationServerServicer):
    def __init__(self, hostname, grpc_source):
        self._hostname = hostname
        self._grpc_source = grpc_source
        self._invoke_cnt = 0
        self._lock = threading.Lock()

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
                logging.error("Unable to read gRPC data [{0}]".format(e))
        logging.info("Disconnected [{0}]".format(context.peer()))
        return Empty()

    def ReportFocusLinePositions(self, requests, context):
        for pos in requests:
            try:
                self._grpc_source.set_focus_line_position((pos.in_focus,
                                                           pos.mid_offset,
                                                           pos.degrees,
                                                           pos.width,
                                                           pos.middle_inc))
            except BaseException as e:
                logging.error("Unable to read gRPC data [{0}]".format(e))
        logging.info("Disconnected [{0}]".format(context.peer()))
        return Empty()

    def hostname(self):
        return self._hostname

    @staticmethod
    def get_grpc_stub(hostname):
        channel = grpc.insecure_channel(hostname)
        grpc_stub = LocationServerStub(channel)
        return grpc_stub

    @staticmethod
    def start_location_server(server):
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_LocationServerServicer_to_server(server, grpc_server)
        grpc_server.add_insecure_port(server.hostname())
        grpc_server.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            grpc_server.stop(0)
