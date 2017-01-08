import cv2
import numpy as np


def find_max_contour(contours, minimum):
    max_index = -1
    max_val = 0
    if contours:
        for i, c in enumerate(contours):
            moments = cv2.moments(c)
            area = moments["m00"]
            if area >= minimum and 0 <= max_val < area:
                max_val = area
                max_index = i
    return contours[max_index] if max_index != -1 else None


class ContourFinder(object):
    def __init__(self, bgr_color, hsv_range):
        bgr_img = np.uint8([[bgr_color]])
        hsv_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        hsv_value = hsv_img[0, 0, 0]
        self.__lower = np.array([hsv_value - hsv_range, 100, 100])
        self.__upper = np.array([hsv_value + hsv_range, 255, 255])

    def get_max_contour(self, image, minimum):
        # Convert from BGR to HSV colorspace
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Threshold the HSV image to get only target colors
        in_range_mask = cv2.inRange(hsv_image, self.__lower, self.__upper)

        # Bitwise-AND mask and original image
        in_range_result = cv2.bitwise_and(image, image, mask=in_range_mask)

        # Convert to grayscale
        grayscale = cv2.cvtColor(in_range_result, cv2.COLOR_BGR2GRAY)

        # Get all contours
        contours = cv2.findContours(grayscale, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[1]

        # cv2.imshow("HSV", hsv_image)
        # cv2.imshow("Mask", in_range_mask)
        # cv2.imshow("Res", in_range_result)
        # cv2.imshow("Grayscale", grayscale)

        # Return max contour
        return find_max_contour(contours, minimum)
