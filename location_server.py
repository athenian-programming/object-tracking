import logging
import threading
import time

import grpc
from concurrent import futures

from gen.grpc_server_pb2 import ObjectLocation
from gen.grpc_server_pb2 import ObjectLocationServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_ObjectLocationServerServicer_to_server


class LocationServer(ObjectLocationServerServicer):
    def __init__(self, port):
        self._hostname = '[::]:' + str(port)
        self._invoke_cnt = 0
        self._lock = threading.Lock()
        self._data_ready = threading.Event()
        self._current_location = None

    def RegisterClient(self, request, context):
        logging.info("Connected {0} [{1}]".format(request.info, context.peer()))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info='Server invoke count {0}'.format(self._invoke_cnt))

    def GetObjectLocations(self, request, context):
        try:
            client_info = request.info
            while True:
                self._data_ready.wait()
                with self._lock:
                    self._data_ready.clear()
                    yield self._current_location
        finally:
            logging.info("Discontinued GetObjectLocations stream to [{0}]".format(context.peer()))

    def publish_location(self, x, y, width, height, middle_inc):
        with self._lock:
            self._current_location = ObjectLocation(x=x,
                                                    y=y,
                                                    width=width,
                                                    height=height,
                                                    middle_inc=middle_inc)
            self._data_ready.set()

    def start_location_server(self):
        logging.info("Starting gRPC location server listening on {0}".format(self._hostname))
        grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ObjectLocationServerServicer_to_server(self, grpc_server)
        grpc_server.add_insecure_port(self._hostname)
        grpc_server.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            grpc_server.stop(0)
