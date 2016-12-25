import logging
import time
from threading import Event
from threading import Lock

import grpc
from concurrent import futures

from gen.grpc_server_pb2 import ObjectLocation
from gen.grpc_server_pb2 import ObjectLocationServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_ObjectLocationServerServicer_to_server


class LocationServer(ObjectLocationServerServicer):
    def __init__(self, port):
        self._hostname = "[::]:" + str(port)
        self._grpc_server = None
        self._stopped = False
        self._invoke_cnt = 0
        self._cnt_lock = Lock()
        self._lock = Lock()
        self._ready = Event()
        self._currval = None

    def registerClient(self, request, context):
        logging.info("Connected to client {0} [{1}]".format(context.peer(), request.info))
        with self._cnt_lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def getObjectLocations(self, request, context):
        try:
            client_info = request.info
            while not self._stopped:
                self._ready.wait()
                with self._lock:
                    if self._ready.is_set and not self._stopped:
                        self._ready.clear()
                        val = self._currval
                        if val is not None:
                            yield val
        finally:
            logging.info("Discontinued getObjectLocations() stream for client {0}".format(context.peer()))

    def write_location(self, x, y, width, height, middle_inc):
        with self._lock:
            if not self._stopped:
                self._currval = ObjectLocation(x=x, y=y, width=width, height=height, middle_inc=middle_inc)
                self._ready.set()

    def start_location_server(self):
        logging.info("Starting gRPC location server listening on {0}".format(self._hostname))
        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ObjectLocationServerServicer_to_server(self, self._grpc_server)
        self._grpc_server.add_insecure_port(self._hostname)
        self._grpc_server.start()
        try:
            while not self._stopped:
                time.sleep(2)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logging.info("Stopping location server")
        self._stopped = True
        with self._lock:
            self._currval = None
            self._ready.set()
        self._grpc_server.stop(None)
