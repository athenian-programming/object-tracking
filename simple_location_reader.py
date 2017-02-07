#!/usr/bin/env python3

import logging

import common_cli_args  as cli
from common_cli_args import setup_cli_args
from common_constants import LOGGING_ARGS
from location_client import LocationClient

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc)

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    locations = LocationClient(args["grpc"]).start()

    try:
        while True:
            print("Got location: {0}".format(locations.get_xy()))
    except KeyboardInterrupt:
        pass
    finally:
        locations.stop()

    logging.info("Exiting...")
