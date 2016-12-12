import time

import cv2

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)


def find_max_contour(contours):
    max_index = -1
    max_val = 0
    if contours is not None:
        for i, c in enumerate(contours):
            moments = cv2.moments(c)
            area = moments["m00"]
            if area > max_val and area > 0:
                max_val = area
                max_index = i
    return max_index


def is_raspi(val):
    return val.lower() in ("raspi", "pi", "raspberry", "raspberrypi", "rp")


class Camera:
    def __init__(self, using_raspi, src=0, use_picamera=False, resolution=(320, 240), framerate=32):
        if using_raspi:
            self.using_raspi = using_raspi
            from imutils.video import VideoStream
            # initialize the video stream and allow the cammera sensor to warmup
            self.vs = VideoStream(src=src, usePiCamera=use_picamera, resolution=resolution, framerate=framerate).start()
            time.sleep(2.0)
        else:
            self.using_raspi = using_raspi
            self.cap = cv2.VideoCapture(0)

    def is_open(self):
        return True if self.using_raspi else self.cap.isOpened()

    def close(self):
        if self.using_raspi:
            self.vs.stop()
        else:
            self.cap.release()

        cv2.destroyAllWindows()

    def read(self):
        return self.vs.read() if self.using_raspi else self.cap.read()[1]

    def is_raspi(self):
        return self.using_raspi

    @staticmethod
    def text_loc():
        return 10, 25

    @staticmethod
    def text_font():
        return cv2.FONT_HERSHEY_SIMPLEX

    def text_size(self):
        return .70 if self.using_raspi else .75
