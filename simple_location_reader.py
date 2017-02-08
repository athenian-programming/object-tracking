#!/usr/bin/env python3

import logging

import cli_args  as cli
from cli_args import setup_cli_args
from location_client import LocationClient
from utils import setup_logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.verbose)

    # Setup logging
    setup_logging(args["loglevel"])

    locations = LocationClient(args["grpc_host"]).start()

    try:
        while True:
            print("Got location: {0}".format(locations.get_xy()))
    except KeyboardInterrupt:
        pass
    finally:
        locations.stop()

    logger.info("Exiting...")
