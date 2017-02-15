from threading import Thread

import cli_args  as cli
from cli_args import LOG_LEVEL, GRPC_HOST
from cli_args import setup_cli_args
from flask import Flask
from location_client import LocationClient
from utils import setup_logging
from utils import sleep

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.verbose)

    # Setup logging
    setup_logging(level=args[LOG_LEVEL])

    http = Flask(__name__)


    @http.route("/count")
    def val_count():
        global count
        return "Read {0} values".format(count)


    def read_values():
        global count
        while True:
            print("Got location: {0}".format(locations.get_xy()))
            count += 1


    # Start client
    locations = LocationClient(args[GRPC_HOST]).start()

    # Run read_values in a thread
    count = 0
    Thread(target=read_values).start()

    # Run HTTP server in a thread
    Thread(target=http.run, kwargs={"port": 8080}).start()

    sleep()
