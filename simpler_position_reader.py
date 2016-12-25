#!/usr/bin/env python3

import argparse
import logging
import sys
from threading import Thread

from position_client import PositionClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    client = PositionClient(args["grpc"])

    Thread(target=client.read_positions).start()

    try:
        while True:
            print("Got position: {0}".format(client.get_focus_line_position()))
    except KeyboardInterrupt as e:
        client.stop()
        print("Exiting...")
