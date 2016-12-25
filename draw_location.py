#!/usr/bin/env python2

import Tkinter
import argparse
import logging
import sys
from threading import Lock
from threading import Thread

from location_client import LocationClient


class LocationSketch(object):
    def __init__(self, canvas):
        self._canvas = canvas
        self._lock = Lock()
        self._drawLines = True
        self._drawPoints = True

    def toggle_drawLines(self):
        with self._lock:
            self._drawLines = not self._drawLines

    def toggle_drawPoints(self):
        with self._lock:
            self._drawPoints = not self._drawPoints

    def clearCanvas(self):
        self._canvas.delete("all")

    def plotVals(self, w, h):
        prev_x = None
        prev_y = None
        curr_w = w
        while True:
            x_val, y_val = location_client.get_xy()
            x = abs(x_val[1] - x_val[0])
            y = y_val[0]

            if x == -1 or y == -1:
                prev_x = None
                prev_y = None
                continue

            if x_val[1] != curr_w:
                self._canvas.delete("all")
                prev_x = None
                prev_y = None
                self._canvas.config(width=x_val[1], height=y_val[1])
                curr_w = x_val[1]
                continue

            if self._drawPoints:
                self._canvas.create_oval(x - 1, y - 1, x + 1, y + 1)

            if self._drawLines and prev_x is not None:
                self._canvas.create_line(prev_x, prev_y, x, y, fill="red")

            prev_x = x
            prev_y = y


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--grpc", required=True, help="gRPC location server hostname")
    args = vars(parser.parse_args())

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s")

    location_client = LocationClient(args["grpc"])

    Thread(target=location_client.read_locations).start()

    init_w = 800
    init_h = 450

    top = Tkinter.Tk()

    canvas = Tkinter.Canvas(top, bg="white", width=init_w, height=init_h)
    canvas.pack()

    sketch = LocationSketch(canvas)

    b = Tkinter.Button(top, text="Clear", command=sketch.clearCanvas)
    b.pack(side=Tkinter.LEFT)

    lb_var = Tkinter.IntVar()
    lb_var.set(1)
    lb = Tkinter.Checkbutton(top, text="Lines", variable=lb_var, command=sketch.toggle_drawLines)
    lb.pack(side=Tkinter.LEFT)

    pb_var = Tkinter.IntVar()
    pb_var.set(1)
    pb = Tkinter.Checkbutton(top, text="Points", variable=pb_var, command=sketch.toggle_drawPoints)
    pb.pack(side=Tkinter.LEFT)

    Thread(target=sketch.plotVals, args=(init_w, init_h)).start()

    top.mainloop()
