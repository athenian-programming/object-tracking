import datetime
import logging
import platform

import cv2

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)


def save_frame(frame):
    file_name = "ct-{0}.png".format(datetime.datetime.now().strftime("%H-%M-%S"))
    cv2.imwrite(file_name, frame)
    logging.info("Wrote image to {0}".format(file_name))


def is_raspi():
    return platform.system() == "Linux"


def text_loc():
    return 10, 25


def text_font():
    return cv2.FONT_HERSHEY_SIMPLEX


def text_size():
    return .55 if is_raspi() else .75
