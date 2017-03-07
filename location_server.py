import logging
import time
from threading import Thread

import grpc
from concurrent import futures
from gen.grpc_server_pb2 import ObjectLocation
from gen.grpc_server_pb2 import ObjectLocationServerServicer
from gen.grpc_server_pb2 import ServerInfo
from gen.grpc_server_pb2 import add_ObjectLocationServerServicer_to_server
from grpc_support import GenericServer
from utils import setup_logging
from utils import sleep

logger = logging.getLogger(__name__)


class LocationServer(ObjectLocationServerServicer, GenericServer):
    def __init__(self, port=None):
        super(LocationServer, self).__init__(port=port, desc="location server")
        self.grpc_server = None

    def registerClient(self, request, context):
        logger.info("Connected to {0} client {1} [{2}]".format(self.desc, context.peer(), request.info))
        return ServerInfo(info="Server invoke count {0}".format(self.increment_cnt()))

    def getObjectLocations(self, request, context):
        client_info = request.info
        return self.currval_generator(context.peer())

    def _init_values_on_start(self):
        self.write_location(-1, -1, 0, 0, 0)

    def _start_server(self):
        logger.info("Starting gRPC {0} listening on {1}".format(self.desc, self.hostname))
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ObjectLocationServerServicer_to_server(self, self.grpc_server)
        self.grpc_server.add_insecure_port(self.hostname)
        self.grpc_server.start()
        try:
            while not self.stopped:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def write_location(self, x, y, width, height, middle_inc):
        if not self.stopped:
            self.set_currval(ObjectLocation(id=self.id,
                                            x=x,
                                            y=y,
                                            width=width,
                                            height=height,
                                            middle_inc=middle_inc))
            self.id += 1


if __name__ == "__main__":
    def _run_server(port):
        server = LocationServer(port).start()

        for i in range(100):
            server.write_location(x=i, y=i + 1, width=i + 2, height=i + 3, middle_inc=i + 4)
            time.sleep(1)


    setup_logging()
    Thread(target=_run_server, args=(50052,)).start()
    sleep()
