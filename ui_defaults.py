import cv2

from opencv_utils import is_raspi


def text_loc():
    return 10, 25


def text_font():
    return cv2.FONT_HERSHEY_SIMPLEX


def text_size():
    return .55 if is_raspi() else .75
