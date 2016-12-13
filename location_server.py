import logging
import threading
import time

import grpc
from concurrent import futures

import gen.location_server_pb2


class LocationServer(gen.location_server_pb2.LocationServerServicer):
    def __init__(self, hostname, grpc_source):
        self._hostname = hostname
        self._grpc_source = grpc_source
        self._invoke_cnt = 0
        self._lock = threading.Lock()

    def RegisterClient(self, request, context):
        print("Connected {0} [{1}]".format(request.info, context.peer()))
        with self._lock:
            self._invoke_cnt += 1
        return gen.location_server_pb2.ServerInfo(info='Server invoke count {0}'.format(self._invoke_cnt))

    def ReportLocation(self, requests, context):
        for location in requests:
            try:
                self._grpc_source.set_curr_loc((location.x, location.y, location.width, location.height))
            except BaseException as e:
                logging.error("Unable to read gRPC data [{0}]".format(e))
        logging.info("Disconnected [{0}]".format(context.peer()))
        return gen.location_server_pb2.Empty()

    def hostname(self):
        return self._hostname

    @staticmethod
    def start_server(server):
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        gen.location_server_pb2.add_LocationServerServicer_to_server(server, grpc_server)
        grpc_server.add_insecure_port(server.hostname())
        grpc_server.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            grpc_server.stop(0)

