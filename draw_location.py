#!/usr/bin/env python2

import argparse
import logging
import sys
from threading import Thread

from location_client import LocationClient
from opencv_utils import is_python3

if is_python3():
    import tkinter as tk
else:
    import Tkinter as tk


class LocationSketch(object):
    def __init__(self, canvas):
        self._canvas = canvas
        self._drawLines = True
        self._drawPoints = True

    def toggle_lines(self):
        self._drawLines = not self._drawLines

    def toggle_points(self):
        self._drawPoints = not self._drawPoints

    def clear_canvas(self):
        self._canvas.delete("all")

    def plot_vals(self, location_client, w, h):
        prev_x = None
        prev_y = None
        curr_w = w
        while True:
            x_val, y_val = location_client.get_xy()

            if x_val[0] == -1 or y_val[0] == -1:
                prev_x = None
                prev_y = None
                continue

            # Check if width of image has changed
            if x_val[1] != curr_w:
                self._canvas.delete("all")
                self._canvas.config(width=x_val[1], height=y_val[1])
                curr_w = x_val[1]
                prev_x = None
                prev_y = None
                continue

            x = abs(x_val[1] - x_val[0])
            y = y_val[0]

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

    top = tk.Tk()

    canvas = tk.Canvas(top, bg="white", width=init_w, height=init_h)
    canvas.pack()

    sketch = LocationSketch(canvas)

    b = tk.Button(top, text="Clear", command=sketch.clear_canvas)
    b.pack(side=tk.LEFT)

    lb_var = tk.IntVar()
    lb_var.set(1)
    lb = tk.Checkbutton(top, text="Lines", variable=lb_var, command=sketch.toggle_lines)
    lb.pack(side=tk.LEFT)

    pb_var = tk.IntVar()
    pb_var.set(1)
    pb = tk.Checkbutton(top, text="Points", variable=pb_var, command=sketch.toggle_points)
    pb.pack(side=tk.LEFT)

    Thread(target=sketch.plot_vals, args=(location_client, init_w, init_h)).start()

    top.mainloop()
