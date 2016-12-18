from __future__ import print_function

import logging
import socket
import sys
import thread
import time

import grpc

from  gen.telemetry_server_pb2 import ClientInfo
from  gen.telemetry_server_pb2 import FocusLinePosition
from  gen.telemetry_server_pb2 import ObjectLocation
from  gen.telemetry_server_pb2 import TelemetryServerStub


def write_locations(hostname):
    channel = grpc.insecure_channel(hostname)
    grpc_stub = TelemetryServerStub(channel)
    client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
    server_info = grpc_stub.RegisterClient(client_info)
    logging.info("Connected to: {0}".format(server_info.info))
    response = grpc_stub.ReportObjectLocations(_gen_locations())
    print("Disconnected from gRPC server at {0}".format(hostname))


def write_positionss(hostname):
    channel = grpc.insecure_channel(hostname)
    grpc_stub = TelemetryServerStub(channel)
    client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
    server_info = grpc_stub.RegisterClient(client_info)
    logging.info("Connected to: {0}".format(server_info.info))
    response = grpc_stub.ReportFocusLinePositions(_gen_positions())
    print("Disconnected from gRPC server at {0}".format(hostname))


def _gen_locations():
    for i in range(0, 100):
        loc = ObjectLocation(x=i, y=i + 1, width=i + 2, height=i + 3, middle_inc=i + 4)
        yield loc
        time.sleep(1)


def _gen_positions():
    for i in range(0, 100):
        loc = FocusLinePosition(in_focus=True if i % 2 == 0 else False,
                                mid_offset=i,
                                degrees=i + 1,
                                mid_line_cross=i + 2,
                                width=i + 3,
                                middle_inc=i + 4)
        yield loc
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    thread.start_new_thread(write_locations, ('localhost:50052',))
    thread.start_new_thread(write_positionss, ('localhost:50053',))
    while True:
        time.sleep(60)
