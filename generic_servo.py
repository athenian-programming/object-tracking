import time
from logging import info
from threading import Event
from threading import Thread


class Servo(object):
    def __init__(self, name, alternate, secs_per_180=0.50, pix_per_degree=6.5):
        self.__name = name
        self.__alternate = alternate
        self.__secs_per_180 = secs_per_180
        self.__ppd = pix_per_degree
        self.__stopped = False
        self.__ready_event = Event()
        self.__thread = None

    @property
    def name(self):
        return self.__name

    @property
    def ready_event(self):
        return self.__ready_event

    def get_currpos(self):
        pass

    def set_angle(self, val, pause=None):
        pass

    def run_servo(self, forward, loc_source, other_ready_event):
        while not self.__stopped:
            try:
                if self.__alternate:
                    self.__ready_event.wait()
                    self.__ready_event.clear()

                # Get latest location
                img_pos, img_total, middle_inc, id = loc_source()

                # Skip if object is not seen
                if img_pos == -1 or img_total == -1:
                    info("No target seen: {0}".format(self.__name))
                    continue

                midpoint = img_total / 2

                curr_pos = self.get_currpos()

                if img_pos < midpoint - middle_inc:
                    err = abs(midpoint - img_pos)
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos + adj if forward else curr_pos - adj
                    # print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                    #      .format(self.__name, err, curr_pos, new_pos, adj))
                elif img_pos > midpoint + middle_inc:
                    err = img_pos - midpoint
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos - adj if forward else curr_pos + adj
                    # print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                    #      .format(self.__name, err, curr_pos, new_pos, adj))
                else:
                    continue

                delta = abs(new_pos - curr_pos)

                # If you do not pause long enough, the servo will go bonkers
                # Pause for a time relative to distance servo has to travel
                wait_time = (self.__secs_per_180 / 180) * delta

                # Write servo value
                self.set_angle(new_pos, pause=wait_time)

            finally:
                if self.__alternate and other_ready_event is not None:
                    other_ready_event.set()

            time.sleep(.10)

    def start(self, forward, loc_source, other_ready_event):
        self.__thread = Thread(target=self.run_servo, args=(forward, loc_source, other_ready_event))
        self.__thread.start()

    def join(self):
        self.__thread.join()

    def stop(self):
        info("Stopping servo {0}".format(self.name))
        self.__stopped = True
