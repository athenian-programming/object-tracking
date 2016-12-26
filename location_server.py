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
        self._lock = Lock()
        self._currval = None
        self._id = 0
        self._client_dict = {}

    def registerClient(self, request, context):
        logging.info("Connected to client {0} [{1}]".format(context.peer(), request.info))
        with self._lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def getObjectLocations(self, request, context):
        client_info = request.info
        client_name = context.peer()
        try:
            ready = Event()
            with self._lock:
                self._client_dict[client_name] = ready

            while not self._stopped:
                ready.wait()
                with self._lock:
                    if ready.is_set() and not self._stopped:
                        ready.clear()
                        val = self._currval
                        if val is not None:
                            print("Client context: {0} id: {1} Clients: {2}".format(client_name,
                                                                                    val.id,
                                                                                    len(self._client_dict)))
                            yield val
                    else:
                        logging.info("Skipped sending data to {0}".format(client_name))
        finally:
            logging.info("Discontinued getObjectLocations() stream for client {0}".format(client_name))
            with self._lock:
                if self._client_dict.pop(client_name, None) is None:
                    logging.error("Error cleaning up client {0}".format(client_name))

    def _set_currval(self, val):
        with self._lock:
            self._currval = val
            for key in self._client_dict:
                self._client_dict[key].set()

    def write_location(self, x, y, width, height, middle_inc):
        if not self._stopped:
            self._set_currval(ObjectLocation(x=x, y=y,
                                             width=width,
                                             height=height,
                                             middle_inc=middle_inc,
                                             ts=time.time(),
                                             id=self._id))
            self._id += 1

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
        self._set_currval(None)
        self._grpc_server.stop(None)
