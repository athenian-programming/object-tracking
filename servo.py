import logging
import time


class Servo:
    def __init__(self, board, name, pin_args, loc_source, forward, secs_per_180=0.50, pix_per_degree=6.5):
        self._name = name
        self._pin = board.get_pin(pin_args)
        self._loc_source = loc_source
        self._forward = forward
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

    def start(self):

        curr_pos = self.read_pin()

        while not self._stopped:
            # Get latest location
            img_pos, img_total, middle_inc = self._loc_source()


            # Skip if object is not seen
            if img_pos == -1 or img_total == -1:
                curr_pos = self.read_pin()
                logging.info("No target seen: {0}".format(self._name))
                continue

            midpoint = img_total / 2

            if img_pos < midpoint - middle_inc:
                err = abs((midpoint - middle_inc) - img_pos)
                adj = max(int(err / self._ppd), 1)
                new_pos = curr_pos + adj if self._forward else curr_pos - adj
                print("{0} above moving to {1} from {2} adj {3}".format(self._name, new_pos, curr_pos, adj))
            elif img_pos > midpoint + middle_inc:
                err = img_pos - (midpoint + middle_inc)
                adj = max(int(err / self._ppd), 1)
                new_pos = curr_pos - adj if self._forward else curr_pos + adj
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

            curr_pos = new_pos

    def stop(self):
        self._stopped = True

    @staticmethod
    def calibrate(location_client, servo_x, servo_y):
        def center_servos():
            servo_x.write_pin(90)
            servo_y.write_pin(90)

        name = "x"
        servo = servo_x
        while True:
            # This is a hack to get around python3 not having raw_input
            try:
                input = raw_input
            except NameError:
                pass

            try:
                val = input("{0} {1} ({2}, {3})> ".format(name.upper(),
                                                          servo.read_pin(),
                                                          location_client.get_loc("x"),
                                                          location_client.get_loc("y")))
            except KeyboardInterrupt:
                return

            if val == "?":
                print("Valid commands:")
                print("     x      : change to pan servo")
                print("     y      : change to tilt servo")
                print("     s      : run scan on current servo")
                print("     c      : center current servo")
                print("     C      : center both servos")
                print("     +      : increase current servo position 1 degree")
                print("     -      : decrease current servo position 1 degree")
                print("     number : set current servo position number degree")
                print("     ?      : print summary of commands")
                print("     q      : quit")
            elif val == "c":
                servo.write_pin(90)
            elif val == "C":
                center_servos()
            elif val == "x":
                name = "x"
                servo = servo_x
            elif val == "y":
                name = "y"
                servo = servo_y
            elif val == "s":
                pause = 0.01
                center_servos()
                servo.write_pin(0)

                start_pos = -1
                end_pos = -1
                for i in range(0, 180, 1):
                    servo.write_pin(i, pause)
                    if location_client.get_loc(name) != -1:
                        start_pos = i
                        print("Target starts at position {0}".format(start_pos))
                        break

                if start_pos == -1:
                    print("No target found")
                    continue

                for i in range(start_pos, 180, 1):
                    servo.write_pin(i, pause)
                    if location_client.get_loc(name) == -1:
                        break
                    end_pos = i

                print("Target ends at position {0}".format(end_pos))

                total_pixels = location_client.get_size(name)
                total_pos = end_pos - start_pos
                if total_pos > 0:
                    pix_per_deg = round(total_pixels / float(total_pos), 2)
                    servo.write_pin(90)
                    print("{0} degrees to cover {1} pixels [{2} pixels/degree]".format(total_pos,
                                                                                       total_pixels,
                                                                                       pix_per_deg))
                else:
                    print("No target found")

            elif len(val) == 0:
                pass
            elif val == "-" or val == "_":
                servo.write_pin(servo.read_pin() - 1)
            elif val == "+" or val == "=":
                servo.write_pin(servo.read_pin() + 1)
            elif val.isdigit():
                servo.write_pin(int(val))
            elif val == "q":
                break
            else:
                print("Invalid input")
