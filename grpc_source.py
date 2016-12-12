import logging
import time

import grpc

import gen.color_tracker_pb2
from  generic_source import GenericDataSource


class GrpcDataSource(GenericDataSource):
    def __init__(self, hostname):
        GenericDataSource.__init__(self)
        self._hostname = hostname

    def start(self):
        cnt = 1
        while True:
            try:
                channel = grpc.insecure_channel(self._hostname)
                stub = gen.color_tracker_pb2.ObjectTrackerStub(channel)
                locations = stub.ReportLocation(gen.color_tracker_pb2.ClientInfo(info='Session {0}'.format(cnt)))
                cnt += 1
                for location in locations:
                    self.set_curr_loc((location.x, location.y, location.width, location.height))
            except BaseException as e:
                logging.error("Failed to connect to gRPC server at {0} - [{1}]".format(self._hostname, e))
                time.sleep(1)
