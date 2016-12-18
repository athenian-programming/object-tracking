import logging
import sys
import thread
import time

from  grpc_source import LocationSource
from  grpc_source import PositionSource


def test_location_source(port):
    source = LocationSource(port)
    try:
        thread.start_new_thread(source.start_telemetry_server, ())
    except BaseException as e:
        logging.error("Unable to start position server [{0}]".format(e))

    print("Waiting for location values")
    for i in range(0, 1000):
        x_vals = source.get_x()
        y_vals = source.get_y()
        print("Received positions {0} {1}".format(i, x_vals, y_vals))


def test_position_source(port):
    source = PositionSource(port)
    try:
        thread.start_new_thread(source.start_telemetry_server, ())
    except BaseException as e:
        logging.error("Unable to start position server [{0}]".format(e))

    print("Waiting for position values")
    for i in range(0, 1000):
        vals = source.get_focus_line_position()
        print("Received locaiton {0} {1}".format(i, vals))


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    # thread.start_new_thread(test_location_source, (50052,))
    thread.start_new_thread(test_position_source, (50051,))
    while True:
        time.sleep(60)
