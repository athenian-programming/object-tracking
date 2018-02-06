#!/usr/bin/env python

import logging

import arc852.cli_args  as cli
from arc852.cli_args import LOG_LEVEL, GRPC_HOST
from arc852.cli_args import setup_cli_args
from arc852.utils import setup_logging

from location_client import LocationClient

logger = logging.getLogger(__name__)


def main():
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.log_level)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    with LocationClient(args[GRPC_HOST]) as client:
        try:
            while True:
                print("Got location: {0}".format(client.get_xy()))
        except KeyboardInterrupt:
            pass

    logger.info("Exiting...")


if __name__ == "__main__":
    main()
