#!/usr/bin/env python2

import Tkinter
import argparse
import logging
import sys
from threading import Thread

from location_client import LocationClient


def getVals(canvas):
    try:
        prev_x = None
        prev_y = None
        while True:
            x_val, y_val = location_client.get_xy()
            x = abs(x_val[1] - x_val[0])
            y = y_val[0]

            if x == -1 or y == -1:
                prev_x = None
                prev_y = None
                continue

            canvas.create_oval(x - 1, y - 1, x + 1, y + 1)
            if prev_x is not None:
                canvas.create_line(prev_x, prev_y, x, y)
            prev_x = x
            prev_y = y

    except KeyboardInterrupt as e:
        location_client.stop()
        print("Exiting...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    location_client = LocationClient(args["grpc"])

    Thread(target=location_client.read_locations).start()

    top = Tkinter.Tk()

    while True:
        x_val, y_val = location_client.get_xy()
        if x_val[1] > 0:
            break
    canvas = Tkinter.Canvas(top, bg="white", width=x_val[1], height=y_val[1])

    Thread(target=getVals, args=(canvas,)).start()

    canvas.pack()
    top.mainloop()
