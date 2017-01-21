import logging
import time
from threading import Thread

from defaults import LOGGING_ARGS
from location_server import LocationServer
from position_server import PositionServer


def test_location_server(port):
    server = LocationServer(port)

    Thread(target=server.start_location_server).start()

    for i in range(0, 100):
        server.write_location(x=i, y=i + 1, width=i + 2, height=i + 3, middle_inc=i + 4)
        time.sleep(1)


def test_position_server(port):
    server = PositionServer(port)
    try:
        Thread(target=server.start_position_server).start()
    except BaseException as e:
        logging.error("Unable to start position server [{0}]".format(e))

    for i in range(0, 100):
        server.write_position(in_focus=True if i % 2 == 0 else False,
                              mid_offset=i,
                              degrees=i + 1,
                              mid_line_cross=i + 2,
                              width=i + 3,
                              middle_inc=i + 4)
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(**LOGGING_ARGS)

    Thread(target=test_location_server, args=(50052,)).start()
    Thread(target=test_position_server, args=(50053,)).start()
    while True:
        time.sleep(60)
