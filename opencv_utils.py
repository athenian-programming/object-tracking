import datetime
from logging import info

import cv2

RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
YELLOW = (0, 255, 255)


def save_image(frame):
    file_name = "ct-{0}.png".format(datetime.datetime.now().strftime("%H-%M-%S"))
    cv2.imwrite(file_name, frame)
    info("Wrote image to {0}".format(file_name))
