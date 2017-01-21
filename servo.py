import logging
import time

from threading import Event
from threading import Thread


class Servo(object):
    def __init__(self, name, board, pin_args, secs_per_180=0.50, pix_per_degree=6.5):
        self.__name = name
        self.__pin = board.get_pin(pin_args)
        self.__secs_per_180 = secs_per_180
        self.__ppd = pix_per_degree
        self.__stopped = False
        self.__ready_event = Event()
        self.__thread = None
        self.jiggle()

    def jiggle(self):
        # Provoke an update from the color tracker
        self.write_pin(80)
        self.write_pin(90)

    @property
    def name(self):
        return self.__name

    @property
    def readyEvent(self):
        return self.__ready_event

    def read_pin(self):
        return self.__pin.read()

    def write_pin(self, val, pause=-1.0):
        if pause >= 0:
            self.__pin.write(val)
            time.sleep(pause)
        else:
            wait = (self.__secs_per_180 / 180) * abs((val - self.read_pin()))
            self.__pin.write(val)
            time.sleep(wait)

    def run_servo(self, forward, loc_source, other_ready_event):

        while not self.__stopped:
            try:
                self.__ready_event.wait()
                self.__ready_event.clear()

                # print(self.__name + " is evaluating location")

                # Get latest location
                img_pos, img_total, middle_inc = loc_source()

                # Skip if object is not seen
                if img_pos == -1 or img_total == -1:
                    logging.info("No target seen: {0}".format(self.__name))
                    continue

                midpoint = img_total / 2
                curr_pos = self.read_pin()

                if img_pos < midpoint - middle_inc:
                    # err = abs((midpoint - middle_inc) - img_pos)
                    err = abs(midpoint - img_pos)
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos + adj if forward else curr_pos - adj
                    print(
                        "{0} off by {1} pixels going from {2} to {3} adj {4}".format(self.__name, err, new_pos,
                                                                                     curr_pos,
                                                                                     adj))
                elif img_pos > midpoint + middle_inc:
                    # err = img_pos - (midpoint + middle_inc)
                    err = img_pos - midpoint
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos - adj if forward else curr_pos + adj
                    print(
                        "{0} off by {1} pixels going from {2} to {3} adj {4}".format(self.__name, err, new_pos,
                                                                                     curr_pos,
                                                                                     adj))
                else:
                    # print "{0} in middle".format(self.name)
                    # new_pos = curr_pos
                    continue

                delta = abs(new_pos - curr_pos)

                # If you do not pause long enough, the servo will go bonkers
                # Pause for a time relative to distance servo has to travel
                wait_time = (self.__secs_per_180 / 180) * delta

                # if curr_pos != new_pos:
                # logging.info("Pos: [{0} Delta: {1}".format(new_pos, delta))

                # Write servo values
                self.write_pin(new_pos, wait_time)

            finally:
                if other_ready_event is not None:
                    other_ready_event.set()

            time.sleep(.25)

    def start(self, forward, loc_source, other_ready_event):
        self.__thread = Thread(target=self.run_servo, args=(forward, loc_source, other_ready_event))
        self.__thread.start()

    def join(self):
        self.__thread.join()

    def stop(self):
        logging.info("Stopping servo {0}".format(self.name()))
        self.__stopped = True
