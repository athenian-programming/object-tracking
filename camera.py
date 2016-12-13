import time

import cv2

import opencv_utils as utils


class Camera:
    def __init__(self, src=0, use_picamera=True, resolution=(320, 240), framerate=32):
        if utils.is_raspi():
            from imutils.video import VideoStream
            # initialize the video stream and allow the cammera sensor to warmup
            self._vs = VideoStream(src=src, usePiCamera=use_picamera, resolution=resolution,
                                   framerate=framerate).start()
            time.sleep(2.0)
        else:
            self._vp = cv2.VideoCapture(0)

    def is_open(self):
        return True if utils.is_raspi() else self._vp.isOpened()

    def read(self):
        return self._vs.read() if utils.is_raspi() else self._vp.read()[1]

    def close(self):
        if utils.is_raspi():
            self._vs.stop()
        else:
            self._vp.release()

        cv2.destroyAllWindows()
