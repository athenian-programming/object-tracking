#!/usr/bin/env python3

import argparse
import logging

from common_constants import LOGGING_ARGS
from grpc_support import TimeoutException
from position_client import PositionClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(**LOGGING_ARGS)

    positions = PositionClient(args["grpc"])
    positions.start()

    try:
        while True:
            try:
                print("Got position: {0}".format(positions.get_position(timeout=0.5)))
            except TimeoutException:
                print("No change in value")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        positions.stop()
