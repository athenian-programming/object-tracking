import logging
import threading
import time

import grpc
from concurrent import futures

import opencv_utils as utils
from gen.grpc_server_pb2 import ObjectLocation
from gen.grpc_server_pb2 import ObjectLocationServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_ObjectLocationServerServicer_to_server

if utils.is_python3():
    from queue import Queue
else:
    from Queue import Queue


class LocationServer(ObjectLocationServerServicer):
    def __init__(self, port):
        self._hostname = "[::]:" + str(port)
        self._grpc_server = None
        self._stopped = False
        self._invoke_cnt = 0
        self._lock = threading.Lock()
        self._queue = Queue()

    def RegisterClient(self, request, context):
        logging.info("Connected to client {0} [{1}]".format(context.peer(), request.info))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def GetObjectLocations(self, request, context):
        try:
            client_info = request.info
            while not self._stopped:
                val = self._queue.get()
                if val is not None:
                    yield val
        finally:
            logging.info("Discontinued GetObjectLocations stream for client {0}".format(context.peer()))

    def write_location(self, x, y, width, height, middle_inc):
        loc = ObjectLocation(x=x,
                             y=y,
                             width=width,
                             height=height,
                             middle_inc=middle_inc)
        self._queue.put(loc)

    def start_location_server(self):
        logging.info("Starting gRPC location server listening on {0}".format(self._hostname))
        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ObjectLocationServerServicer_to_server(self, self._grpc_server)
        self._grpc_server.add_insecure_port(self._hostname)
        self._grpc_server.start()
        try:
            while not self._stopped:
                time.sleep(5)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logging.info("Stopping location server")
        self._stopped = True
        self._queue.put(None)
        self._grpc_server.stop(None)
