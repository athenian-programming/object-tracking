import logging
import time

class Servo:
    def __init__(self, board, name, pin_args, loc_source, forward):
        self._name = name
        self._pin = board.get_pin(pin_args)
        self._loc_source = loc_source
        self._forward = forward
        self._jiggle()

    def _jiggle(self):
        # Provoke an update from the color tracker
        self.write_pin(85, .5)
        self.write_pin(90, 1)

    @property
    def name(self):
        return self._name

    def read_pin(self):
        return self._pin.read()

    def write_pin(self, val, pause=0.0):
        self._pin.write(val)
        if pause > 0:
            time.sleep(pause)

    def start(self):
        curr_pos = self.read_pin()
        pix_per_deg = 6.5

        while True:
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
                adj = max(int(err / pix_per_deg), 1)
                new_pos = curr_pos + adj if self._forward else curr_pos - adj
                # print("{0} above moving to {1} from {2}".format(self._name, new_pos, curr_pos))
            elif img_pos > midpoint + middle_inc:
                err = img_pos - (midpoint + middle_inc)
                adj = max(int(err / pix_per_deg), 1)
                new_pos = curr_pos - adj if self._forward else curr_pos + adj
                # print("{0} above moving to {1} from {2}".format(self._name, new_pos, curr_pos))
            else:
                # print "{0} in middle".format(self.name)
                # new_pos = curr_pos
                continue

            delta = abs(new_pos - curr_pos)

            # If you do not pause long enough, the servo will go bonkers
            # Pause for a time relative to distance servo has to travel
            # wait_time = .2 #delta * (3.50 / 180)
            wait_time = .2 if delta > 2 else .075

            # if curr_pos != new_pos:
            # logging.info("Pos: [{0} Delta: {1}".format(new_pos, delta))

            # Write servo values
            self.write_pin(new_pos, wait_time)

            curr_pos = new_pos

    @staticmethod
    def calibrate(location_client, servo_x, servo_y):
        def center_servos(pause=0.0):
            servo_x.write_pin(90, pause)
            servo_y.write_pin(90, pause)

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
                servo.write_pin(90, .5)
            elif val == "C":
                center_servos(.5)
            elif val.lower() == "x":
                name = "x"
                servo = servo_x
            elif val.lower() == "y":
                name = "y"
                servo = servo_y
            elif val.lower() == "s":
                center_servos(1)
                servo.write_pin(0, 2)

                start_pos = -1
                end_pos = -1
                for i in range(0, 180, 1):
                    servo.write_pin(i, .1)
                    if location_client.get_loc(name) != -1:
                        start_pos = i
                        break

                if start_pos == -1:
                    print("No target found")
                    continue

                for i in range(start_pos, 180, 1):
                    servo.write_pin(i, .1)
                    if location_client.get_loc(name) == -1:
                        break
                    end_pos = i

                total_pixels = location_client.get_size(name)
                total_pos = end_pos - start_pos
                pix_deg = round(total_pixels / float(total_pos), 2)
                servo.write_pin(90)
                print("{0} degrees to cover {1} pixels [{2} pixels/degree]".format(total_pos, total_pixels, pix_deg))
            elif len(val) == 0:
                pass
            elif val == "-" or val == "_":
                servo.write_pin(servo.read_pin() - 1, .5)
            elif val == "+" or val == "=":
                servo.write_pin(servo.read_pin() + 1, .5)
            elif val.isdigit():
                servo.write_pin(int(val), .5)
            elif val.lower() == "q":
                return
            else:
                print("Invalid input")
