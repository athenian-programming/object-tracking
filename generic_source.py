import threading


class GenericDataSource:
    def __init__(self):
        self._x = -1
        self._y = -1
        self._width = -1
        self._height = -1

        self._x_lock = threading.Lock()
        self._y_lock = threading.Lock()
        self._x_ready = threading.Event()
        self._y_ready = threading.Event()


    def set_curr_loc(self, new_loc):
        with self._x_lock:
            self._x = new_loc[0]
            self._width = new_loc[2]
            self._x_ready.set()

        with self._x_lock:
            self._y = new_loc[1]
            self._height = new_loc[3]
            self._y_ready.set()

    # Blocking
    def get_x(self):
        self._x_ready.wait()
        with self._x_lock:
            self._x_ready.clear()
            return self._x, self._width

    # Blocking
    def get_y(self):
        self._y_ready.wait()
        with self._y_lock:
            self._y_ready.clear()
            return self._y, self._height

    # Non-blocking
    def get_pos(self, name):
        return self._x if name == "x" else self._y

    # Non-blocking
    def get_size(self, name):
        return self._width if name == "x" else self._height
