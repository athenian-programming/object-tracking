import threading


class GenericDataSource:
    def __init__(self):
        self._curr_loc = (-1, -1, -1, -1)
        self._lock = threading.Lock()
        self._x_ready = threading.Event()
        self._y_ready = threading.Event()

    def set_curr_loc(self, new_loc):
        with self._lock:
            self._curr_loc = new_loc
            self._x_ready.set()
            self._y_ready.set()

    def get_x(self, block):
        if block:
            self._x_ready.wait()  # wait until new value has arrived
        with self._lock:
            if block:
                self._x_ready.clear()  # set ready to wait again
            return self._curr_loc[0], self._curr_loc[2]

    def get_y(self, block):
        if block:
            self._y_ready.wait()  # wait until new value has arrived
        with self._lock:
            if block:
                self._y_ready.clear()  # set ready to wait again
            return self._curr_loc[1], self._curr_loc[3]

    def get_nowait_pos(self, name):
        return (self.get_x(False) if name == "x" else self.get_y(False))[0]

    def get_nowait_size(self, name):
        return (self.get_x(False) if name == "x" else self.get_y(False))[1]
