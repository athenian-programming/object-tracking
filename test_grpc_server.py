import logging
import sys
import thread
import time

from location_server import LocationServer
from position_server import PositionServer


def test_location_server(port):
    server = LocationServer(port)
    try:
        thread.start_new_thread(server.start_location_server, ())
    except BaseException as e:
        logging.error("Unable to start position server [{0}]".format(e))

    for i in range(0, 100):
        server.publish_location(x=i, y=i + 1, width=i + 2, height=i + 3, middle_inc=i + 4)
        time.sleep(1)


def test_position_server(port):
    server = PositionServer(port)
    try:
        thread.start_new_thread(server.start_position_server, ())
    except BaseException as e:
        logging.error("Unable to start position server [{0}]".format(e))

    for i in range(0, 100):
        server.publish_focus_line_position(in_focus=True if i % 2 == 0 else False,
                                           mid_offset=i,
                                           degrees=i + 1,
                                           mid_line_cross=i + 2,
                                           width=i + 3,
                                           middle_inc=i + 4)
        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    thread.start_new_thread(test_location_server, (50052,))
    thread.start_new_thread(test_position_server, (50053,))
    while True:
        time.sleep(60)
