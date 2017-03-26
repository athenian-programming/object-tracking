#!/usr/bin/env python2

from threading import Thread

import cli_args  as cli
from cli_args import LOG_LEVEL, GRPC_HOST
from cli_args import setup_cli_args
from location_client import LocationClient
from utils import is_python3
from utils import setup_logging

if is_python3():
    import tkinter as tk
else:
    import Tkinter as tk


class LocationSketch(object):
    def __init__(self, canvas):
        self.__canvas = canvas
        self.__drawLines = True
        self.__drawPoints = True
        self.__stopped = False

    def toggle_lines(self):
        self.__drawLines = not self.__drawLines

    def toggle_points(self):
        self.__drawPoints = not self.__drawPoints

    def clear_canvas(self):
        self.__canvas.delete("all")

    def plot_vals(self, locations, w, h):
        prev_x, prev_y = None, None
        curr_w = w
        while not self.__stopped:
            x_val, y_val = locations.get_xy()

            if x_val[0] == -1 or y_val[0] == -1:
                prev_x, prev_y = None, None
                continue

            # Check if width of image has changed
            if x_val[1] != curr_w:
                self.__canvas.delete("all")
                self.__canvas.config(width=x_val[1], height=y_val[1])
                curr_w = x_val[1]
                prev_x, prev_y = None, None
                continue

            x = x_val[1] - abs(x_val[1] - x_val[0])
            y = y_val[0]

            if self.__drawPoints:
                self.__canvas.create_oval(x - 1, y - 1, x + 1, y + 1)

            if self.__drawLines and prev_x is not None:
                self.__canvas.create_line(prev_x, prev_y, x, y, fill="red")

            prev_x, prev_y = x, y

    def stop(self):
        self.__stopped = True

if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.grpc_host, cli.verbose)

    setup_logging(level=args[LOG_LEVEL])

    with LocationClient(args[GRPC_HOST]) as client:
        init_w, init_h = 800, 450

        root = tk.Tk()

        canvas = tk.Canvas(root, bg="white", width=init_w, height=init_h)
        canvas.pack()

        sketch = LocationSketch(canvas)

        b = tk.Button(root, text="Clear", command=sketch.clear_canvas)
        b.pack(side=tk.LEFT)

        lb_var = tk.IntVar()
        lb_var.set(1)
        lb = tk.Checkbutton(root, text="Lines", variable=lb_var, command=sketch.toggle_lines)
        lb.pack(side=tk.LEFT)

        pb_var = tk.IntVar()
        pb_var.set(1)
        pb = tk.Checkbutton(root, text="Points", variable=pb_var, command=sketch.toggle_points)
        pb.pack(side=tk.LEFT)

        Thread(target=sketch.plot_vals, args=(client, init_w, init_h)).start()

        root.mainloop()
