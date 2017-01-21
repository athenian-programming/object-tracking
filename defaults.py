import logging
import sys

import cv2

from opencv_utils import is_raspi

TEXT_LOC = (10, 25)

TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX

TEXT_SIZE = .55 if is_raspi() else .75

LOGGING_ARGS = {"stream": sys.stderr,
                "level": logging.INFO,
                "format": "%(asctime)s %(name)-10s %(funcName)-10s():%(lineno)i: %(levelname)-6s %(message)s"}
