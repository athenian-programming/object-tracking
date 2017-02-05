#!/usr/bin/env python2

import logging

import camera
import common_cli_args  as cli
import cv2
import imutils
import numpy as np
import opencv_defaults as defs
from common_cli_args import setup_cli_args
from common_constants import LOGGING_ARGS
from opencv_utils import GREEN
from opencv_utils import RED


class ColorPicker(object):
    def __init__(self, width, flip=False, usb_camera=False):
        self.__width = width
        self.__flip = flip
        self.__usb_camera = usb_camera
        self.__roi_size = 24
        self.__roi_inc = 6
        self.__move_inc = 4
        self.__x_adj = 0
        self.__y_adj = 0
        self.__orig_width = self.__width
        self.__orig_roi_size = self.__roi_size
        self.__mag_width = 300
        self.__cam = camera.Camera(use_picamera=not usb_camera)

    # Do not run this in a background thread. cv2.waitKey has to run in main thread
    def start(self):
        cnt = 0
        while self.__cam.is_open():
            image = self.__cam.read()
            image = imutils.resize(image, width=self.__width)

            if self.__flip:
                image = cv2.flip(image, 0)

            frame_h, frame_w = image.shape[:2]

            roi_x = (frame_w / 2) - (self.__roi_size / 2) + self.__x_adj
            roi_y = (frame_h / 2) - (self.__roi_size / 2) + self.__y_adj
            roi = image[roi_y:roi_y + self.__roi_size, roi_x:roi_x + self.__roi_size]

            roi_h, roi_w = roi.shape[:2]
            roi_canvas = np.zeros((roi_h, roi_w, 3), dtype="uint8")
            roi_canvas[0:roi_h, 0:roi_w] = roi

            avg_color_per_row = np.average(roi_canvas, axis=0)
            avg_color = np.average(avg_color_per_row, axis=0)
            avg_color = np.uint8(avg_color)

            mag_img = imutils.resize(roi_canvas, width=self.__mag_width)
            mag_h, mag_w = mag_img.shape[:2]
            color_img = np.zeros((mag_h, mag_w, 3), dtype="uint8")
            color_img[:, :] = avg_color

            # Draw a rectangle around the sample area
            cv2.rectangle(image, (roi_x, roi_y), (roi_x + self.__roi_size, roi_y + self.__roi_size), GREEN, 1)

            xy_text = "Frame: {0} ".format(cnt) \
                      + "ROI: {0}x{1} ".format(str(self.__roi_size), str(self.__roi_size)) \
                      + "X,Y: ({0}, {1})".format(roi_x, roi_y)
            cv2.putText(image, xy_text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

            bgr_text = "BGR value: [{0}, {1}, {2}]".format(avg_color[0], avg_color[1], avg_color[2])
            cv2.putText(color_img, bgr_text, defs.TEXT_LOC, defs.TEXT_FONT, defs.TEXT_SIZE, RED, 1)

            # Display images
            # cv2.imshow("ROI", roi_canvas)
            # cv2.imshow("Magnified ROI", mag_img)
            cv2.imshow("Average BGR Value", color_img)
            cv2.imshow("Image", image)

            cnt += 1

            key = cv2.waitKey(30) & 0xFF

            if key == 255:
                pass
            elif key == ord("c") or key == ord(" "):
                print(bgr_text)
            elif roi_y >= self.__move_inc and (key == 0 or key == ord("k")):  # Up
                self.__y_adj -= self.__move_inc
            elif roi_y <= frame_h - self.__roi_size - self.__move_inc and (key == 1 or key == ord("j")):  # Down
                self.__y_adj += self.__move_inc
            elif roi_x >= self.__move_inc and (key == 2 or key == ord("h")):  # Left
                self.__x_adj -= self.__move_inc
            elif roi_x <= frame_w - self.__roi_size - self.__move_inc - self.__move_inc \
                    and (key == 3 or key == ord("l")):  # Right
                self.__x_adj += self.__move_inc
            elif self.__roi_size >= self.__roi_inc * 2 and (key == ord("-") or key == ord("_")):
                self.__roi_size -= self.__roi_inc
                self.__x_adj, self.__y_adj = 0, 0
            elif self.__roi_size <= self.__roi_inc * 49 and (key == ord("+") or key == ord("=")):
                self.__roi_size += self.__roi_inc
                self.__x_adj, self.__y_adj = 0, 0
            elif key == ord("r"):
                self.__width = self.__orig_width
                self.__roi_size = self.__orig_roi_size
            elif key == ord("w"):
                self.__width -= 10
            elif key == ord("W"):
                self.__width += 10
            elif key == ord("q"):
                self.__cam.close()
                break


if __name__ == "__main__":
    # Parse CLI args
    args = setup_cli_args(cli.width, cli.usb, cli.flip_x, cli.flip_y)

    # Setup logging
    logging.basicConfig(**LOGGING_ARGS)

    try:
        ColorPicker(args["width"], flip=args["flip"], usb_camera=args["usb"]).start()
    except KeyboardInterrupt as e:
        pass

    print("Exiting...")
