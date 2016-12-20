#!/usr/bin/env python3

import argparse
from threading import Thread

from position_client import PositionClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    position_client = PositionClient(args["grpc"])

    try:
        Thread(target=position_client.read_positions).start()
    except BaseException as e:
        print("Unable to start position client [{0}]".format(e))

    try:
        while True:
            print("Got location: {0}".format(position_client.get_focus_line_position()))
    except KeyboardInterrupt as e:
        print("Exiting...")
