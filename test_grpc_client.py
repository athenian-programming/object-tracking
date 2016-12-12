from __future__ import print_function

import time

import grpc

import gen.color_tracker_pb2


def connect(hostname):
    channel = grpc.insecure_channel(hostname)
    stub = gen.color_tracker_pb2.ColorTrackerStub(channel)
    locations = stub.ReportLocation(gen.color_tracker_pb2.ClientInfo(info='Test info'))
    for location in locations:
        print("Client received: \n" + str(location))


if __name__ == '__main__':
    while True:
        try:
            connect('localhost:50051')
            break
        except BaseException as e:
            print("Failed to connect... [{0}]".format(e))
            time.sleep(1)
