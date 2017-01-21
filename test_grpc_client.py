from __future__ import print_function

import logging
import socket
import time
from threading import Thread

import grpc

from common_constants import LOGGING_ARGS
from gen.grpc_server_pb2 import ClientInfo
from gen.grpc_server_pb2 import FocusLinePositionServerStub
from gen.grpc_server_pb2 import ObjectLocationServerStub


def read_locations(hostname):
    channel = grpc.insecure_channel(hostname)
    stub = ObjectLocationServerStub(channel)
    client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
    server_info = stub.registerClient(client_info)

    for loc in stub.getObjectLocations(client_info):
        print("Received location {0}".format(loc))
    print("Disconnected from gRPC server at {0}".format(hostname))


def read_positions(hostname):
    channel = grpc.insecure_channel(hostname)
    stub = FocusLinePositionServerStub(channel)
    client_info = ClientInfo(info="{0} client".format(socket.gethostname()))
    server_info = stub.registerClient(client_info)

    for pos in stub.getFocusLinePositions(client_info):
        print("Received position {0}".format(pos))

    print("Disconnected from gRPC server at {0}".format(hostname))


if __name__ == "__main__":
    logging.basicConfig(**LOGGING_ARGS)

    Thread(target=read_locations, args=("localhost:50052",)).start()
    Thread(target=read_positions, args=("localhost:50053",)).start()
    while True:
        time.sleep(60)
