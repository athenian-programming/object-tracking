from threading import Thread

import arc852.cli_args  as cli
from arc852.cli_args import LOG_LEVEL, GRPC_HOST
from arc852.cli_args import setup_cli_args
from arc852.utils import setup_logging
from arc852.utils import sleep
from flask import Flask

from location_client import LocationClient

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.log_level)

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
            print("Got location: {0}".format(client.get_xy()))
            count += 1


    # Start client
    with LocationClient(args[GRPC_HOST]) as client:

        # Run read_values in a thread
        count = 0
        Thread(target=read_values).start()

        # Run HTTP server in a thread
        Thread(target=http.run, kwargs={"port": 8080}).start()

        sleep()
