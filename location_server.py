import logging
import time

import grpc
from concurrent import futures
from gen.grpc_server_pb2 import ObjectLocation
from gen.grpc_server_pb2 import ObjectLocationServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_ObjectLocationServerServicer_to_server
from grpc_support import GenericServer

logger = logging.getLogger(__name__)


class LocationServer(ObjectLocationServerServicer, GenericServer):
    def __init__(self, port):
        super(LocationServer, self).__init__(port, "location server")
        self._grpc_server = None

    def registerClient(self, request, context):
        logger.info("Connected to {0} client {1} [{2}]".format(self.desc, context.peer(), request.info))
        with self.cnt_lock:
            self._invoke_cnt += 1
        return ServerInfo(info="Server invoke count {0}".format(self._invoke_cnt))

    def getObjectLocations(self, request, context):
        client_info = request.info
        return self.currval_generator(context.peer())

    def _init_values_on_start(self):
        self.write_location(-1, -1, 0, 0, 0)

    def _start_server(self):
        logger.info("Starting gRPC {0} listening on {1}".format(self.desc, self._hostname))
        self._grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ObjectLocationServerServicer_to_server(self, self._grpc_server)
        self._grpc_server.add_insecure_port(self._hostname)
        self._grpc_server.start()
        try:
            while not self.stopped:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def write_location(self, x, y, width, height, middle_inc):
        if not self.stopped:
            self.set_currval(ObjectLocation(id=self._id,
                                            x=x,
                                            y=y,
                                            width=width,
                                            height=height,
                                            middle_inc=middle_inc))
            self._id += 1
