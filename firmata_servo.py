import time
from logging import info

from generic_servo import Servo


class FirmataServo(Servo):
    def __init__(self, name, alternate, board, pin_args, secs_per_180, pix_per_degree):
        super(FirmataServo, self).__init__(name, alternate, secs_per_180, pix_per_degree)
        self.__pin = board.get_pin(pin_args)
        self.jiggle()

    def jiggle(self):
        # Provoke an update from the color tracker
        self.write_pin(80)
        self.write_pin(90)

    def set_angle(self, val, pause=None):
        self.write_pin(val, pause)

    def get_currpos(self):
        return self.read_pin()

    def read_pin(self):
        return self.__pin.read()

    def write_pin(self, val, pause=-None):
        if pause is not None:
            self.__pin.write(val)
            time.sleep(pause)
        else:
            wait = (self.__secs_per_180 / 180) * abs((val - self.get_currpos()))
            self.__pin.write(val)
            time.sleep(wait)

    def run_servo2(self, forward, loc_source, other_ready_event):
        while not self.__stopped:
            try:
                if self.__alternate:
                    self.__ready_event.wait()
                    self.__ready_event.clear()

                # Get latest location
                img_pos, img_total, middle_inc, id_val = loc_source()

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
                    print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                          .format(self.__name, err, new_pos, curr_pos, adj))
                elif img_pos > midpoint + middle_inc:
                    err = img_pos - midpoint
                    adj = max(int(err / self.__ppd), 1)
                    new_pos = curr_pos - adj if forward else curr_pos + adj
                    print("{0} off by {1} pixels going from {2} to {3} adj {4}"
                          .format(self.__name, err, new_pos, curr_pos, adj))
                else:
                    continue

                delta = abs(new_pos - curr_pos)

                # If you do not pause long enough, the servo will go bonkers
                # Pause for a time relative to distance servo has to travel
                wait_time = (self.__secs_per_180 / 180) * delta

                # Write servo value
                self.write_pin(new_pos, wait_time)

            finally:
                if self.__alternate and other_ready_event is not None:
                    other_ready_event.set()

            time.sleep(.10)
