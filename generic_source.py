import threading


class GenericDataSource:
    def __init__(self):
        self._curr_loc = (-1, -1, -1, -1)
        self._lock = threading.Lock()
        self._x_ready = threading.Event()
        self._y_ready = threading.Event()

    def set_curr_loc(self, new_loc):
        self._lock.acquire()
        try:
            self._curr_loc = new_loc
            self._x_ready.set()
            self._y_ready.set()
        finally:
            self._lock.release()

    def get_x(self, block):
        if block:
            self._x_ready.wait()  # wait until new value has arrived
        self._lock.acquire()
        try:
            return self._curr_loc[0], self._curr_loc[2]
        finally:
            self._x_ready.clear()  # set ready to wait again
            self._lock.release()

    def get_y(self, block):
        if block:
            self._y_ready.wait()  # wait until new value has arrived
        self._lock.acquire()
        try:
            return self._curr_loc[1], self._curr_loc[3]
        finally:
            self._y_ready.clear()  # set ready to wait again
            self._lock.release()

    def get_nowait_pos(self, name):
        return (self.get_x(False) if name == "x" else self.get_y(False))[0]

    def get_nowait_size(self, name):
        return (self.get_x(False) if name == "x" else self.get_y(False))[1]
