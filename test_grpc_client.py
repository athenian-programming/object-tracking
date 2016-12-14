from __future__ import print_function

import logging
import time

import grpc

import gen.location_server_pb2


def connect(hostname):
    try:
        channel = grpc.insecure_channel(hostname)
        stub = gen.location_server_pb2.LocationServerStub(channel)
        response = stub.ReportLocation(_gen_locations())
        logging.info("Connected to: {0}".format(response.info))
    finally:
        logging.info("Disconnected from gRPC server at {0} - [{1}]".format(hostname, e))


def _gen_locations():
    for i in range(0, 10):
        loc = gen.location_server_pb2.Location(x=i, y=i + 1, width=i + 2, height=i + 3, percent=i + 4)
        yield loc


if __name__ == '__main__':
    while True:
        try:
            connect('localhost:50051')
            time.sleep(1)
            break
        except BaseException as e:
            print("Failed to connect... [{0}]".format(e))
            time.sleep(1)
