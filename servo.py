import logging
import time


class Servo:
    def __init__(self, name, board, pin_args, secs_per_180=0.50, pix_per_degree=6.5):
        self._name = name
        self._pin = board.get_pin(pin_args)
        self._secs_per_180 = secs_per_180
        self._ppd = pix_per_degree
        self._stopped = False
        self._jiggle()

    def _jiggle(self):
        # Provoke an update from the color tracker
        self.write_pin(80)
        self.write_pin(90)

    @property
    def name(self):
        return self._name

    def read_pin(self):
        return self._pin.read()

    def write_pin(self, val, pause=-1.0):
        if pause >= 0:
            self._pin.write(val)
            time.sleep(pause)
        else:
            wait = (self._secs_per_180 / 180) * abs((val - self.read_pin()))
            self._pin.write(val)
            time.sleep(wait)

    def start(self,
              forward,
              loc_source,
              this_servo_ready,
              other_servo_ready):

        while not self._stopped:
            try:
                this_servo_ready.wait()
                this_servo_ready.clear()
                # print(self._name + " is doing work")

                # Get latest location
                img_pos, img_total, middle_inc = loc_source()

                # Skip if object is not seen
                if img_pos == -1 or img_total == -1:
                    logging.info("No target seen: {0}".format(self._name))
                    continue

                midpoint = img_total / 2
                curr_pos = self.read_pin()

                if img_pos < midpoint - middle_inc:
                    err = abs((midpoint - middle_inc) - img_pos)
                    adj = max(int(err / self._ppd), 1)
                    new_pos = curr_pos + adj if forward else curr_pos - adj
                    print("{0} above moving to {1} from {2} adj {3}".format(self._name, new_pos, curr_pos, adj))
                elif img_pos > midpoint + middle_inc:
                    err = img_pos - (midpoint + middle_inc)
                    adj = max(int(err / self._ppd), 1)
                    new_pos = curr_pos - adj if forward else curr_pos + adj
                    print("{0} above moving to {1} from {2} adj {3}".format(self._name, new_pos, curr_pos, adj))
                else:
                    # print "{0} in middle".format(self.name)
                    # new_pos = curr_pos
                    continue

                delta = abs(new_pos - curr_pos)

                # If you do not pause long enough, the servo will go bonkers
                # Pause for a time relative to distance servo has to travel
                wait_time = (self._secs_per_180 / 180) * delta

                # if curr_pos != new_pos:
                # logging.info("Pos: [{0} Delta: {1}".format(new_pos, delta))

                # Write servo values
                self.write_pin(new_pos, wait_time)

            finally:
                other_servo_ready.set()

    def stop(self):
        self._stopped = True

