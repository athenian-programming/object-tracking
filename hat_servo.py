import time

from generic_servo import Servo


class HatServo(Servo):
    def __init__(self, name, alternate, hat_func, secs_per_180, pix_per_degree):
        super(HatServo, self).__init__(name, alternate, secs_per_180, pix_per_degree)
        self.__hat_func = hat_func
        self.jiggle()

    def jiggle(self):
        # Provoke an update from the color tracker
        self.set_angle(80, pause=.1)
        self.set_angle(90, pause=.1)

    def set_angle(self, val, pause=None):
        # Pan Tilt Hat servo takes value -90 to 90.  pyFirmata servo takes 0 - 180. So adjust here
        self.__hat_func(val - 90)
        if pause is not None:
            time.sleep(pause)
        self.__currpos = val

