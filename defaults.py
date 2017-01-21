import cv2

from utils import is_raspi

TEXT_LOC = (10, 25)

TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX

TEXT_SIZE = .55 if is_raspi() else .75
