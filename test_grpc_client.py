from __future__ import print_function

import logging
import socket
import sys
import thread
import time

import grpc
from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import FocusLinePositionServerStub
from gen.grpc_server_pb2 import ObjectLocationServerStub


def read_locations(hostname):
    channel = grpc.insecure_channel(hostname)
    grpc_stub = ObjectLocationServerStub(channel)
    client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
    server_info = grpc_stub.RegisterClient(client_info)

    for loc in grpc_stub.GetObjectLocations(client_info):
        print("Received location {0}".format(loc))
    print("Disconnected from gRPC server at {0}".format(hostname))


def read_positions(hostname):
    channel = grpc.insecure_channel(hostname)
    grpc_stub = FocusLinePositionServerStub(channel)
    client_info = ClientInfo(info='{0} client'.format(socket.gethostname()))
    server_info = grpc_stub.RegisterClient(client_info)

    for pos in grpc_stub.GetFocusLinePositions(client_info):
        print("Received position {0}".format(pos))

    print("Disconnected from gRPC server at {0}".format(hostname))


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    thread.start_new_thread(read_locations, ('localhost:50052',))
    thread.start_new_thread(read_positions, ('localhost:50053',))
    # thread.start_new_thread(read_locations, ('localhost:50051',))
    while True:
        time.sleep(60)
