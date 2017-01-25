import logging
import time
from threading import Thread

from common_constants import LOGGING_ARGS
from common_utils import sleep
from location_server import LocationServer


def test_location_server(port):
    server = LocationServer(port).start()

    for i in range(0, 100):
        server.write_location(x=i, y=i + 1, width=i + 2, height=i + 3, middle_inc=i + 4)
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(**LOGGING_ARGS)
    Thread(target=test_location_server, args=(50052,)).start()
    sleep()
