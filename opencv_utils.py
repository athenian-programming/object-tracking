import platform
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


class Camera:
    def __init__(self, src=0, use_picamera=True, resolution=(320, 240), framerate=32):
        if self.is_raspi():
            from imutils.video import VideoStream
            # initialize the video stream and allow the cammera sensor to warmup
            self._vs = VideoStream(src=src, usePiCamera=use_picamera, resolution=resolution,
                                   framerate=framerate).start()
            time.sleep(2.0)
        else:
            self._cap = cv2.VideoCapture(0)

    def is_open(self):
        return True if self.is_raspi() else self._cap.isOpened()

    def close(self):
        if self.is_raspi():
            self._vs.stop()
        else:
            self._cap.release()

        cv2.destroyAllWindows()

    def read(self):
        return self._vs.read() if self.is_raspi() else self._cap.read()[1]

    def is_raspi(self):
        return platform.system() == "Linux"

    def text_size(self):
        return .70 if self.is_raspi() else .75

    @staticmethod
    def text_loc():
        return 10, 25

    @staticmethod
    def text_font():
        return cv2.FONT_HERSHEY_SIMPLEX
