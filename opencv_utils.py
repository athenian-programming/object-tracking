import datetime
import logging
import platform

import cv2

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)


def find_max_contour(contours):
    max_index = -1
    max_val = 0
    if contours:
        for i, c in enumerate(contours):
            moments = cv2.moments(c)
            area = moments["m00"]
            if area > max_val and area > 0:
                max_val = area
                max_index = i
    return max_index


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
