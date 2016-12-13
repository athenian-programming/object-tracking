#!/usr/local/bin/python2

import cv2
import imutils
import numpy as np

import camera
import opencv_utils as utils

roi_size = 24
roi_inc = 6
move_inc = 4
x_adj = 0
y_adj = 0
mag_width = 400

cam = camera.Camera()

cnt = 0
while cam.is_open():
    frame = cam.read()
    frame = imutils.resize(frame, width=600)
    frame_h, frame_w = frame.shape[:2]

    roi_y = (frame_h / 2) - (roi_size / 2) + y_adj
    roi_x = (frame_w / 2) - (roi_size / 2) + x_adj
    roi = frame[roi_y:roi_y + roi_size, roi_x:roi_x + roi_size]

    roi_h, roi_w = roi.shape[:2]
    roi_canvas = np.zeros((roi_h, roi_w, 3), dtype="uint8")
    roi_canvas[0:roi_h, 0:roi_w] = roi

    avg_color_per_row = np.average(roi_canvas, axis=0)
    avg_color = np.average(avg_color_per_row, axis=0)
    avg_color = np.uint8(avg_color)

    mag_img = imutils.resize(roi_canvas, width=mag_width)
    mag_h, mag_w = mag_img.shape[:2]
    color_img = np.zeros((mag_h, mag_w, 3), dtype="uint8")
    color_img[:, :] = avg_color

    # Draw a rectangle around the sample area
    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_size, roi_y + roi_size), utils.GREEN, 1)

    xy_text = 'Frame: {0} '.format(cnt) \
              + 'ROI: {0}x{1} '.format(str(roi_size), str(roi_size)) \
              + 'X,Y: ({0}, {1})'.format(roi_x, roi_y)
    cv2.putText(frame, xy_text, utils.text_loc(), utils.text_font(), utils.text_size(), utils.RED, 1)

    bgr_text = "BGR value: [{0}, {1}, {2}]".format(avg_color[0], avg_color[1], avg_color[2])
    cv2.putText(color_img, bgr_text, utils.text_loc(), utils.text_font(), utils.text_size(), utils.RED, 1)

    # Display images
    # cv2.imshow('ROI', roi_canvas)
    # cv2.imshow('Magnified ROI', mag_img)
    cv2.imshow('Average BGR Value', color_img)
    cv2.imshow('Image', frame)

    key = cv2.waitKey(30) & 0xFF

    if key == ord('c') or key == ord(' '):
        print(bgr_text)
    elif roi_y >= move_inc and (key == 0 or key == ord('k')):  # Up
        y_adj -= move_inc
    elif roi_y <= frame_h - roi_size - move_inc and (key == 1 or key == ord('j')):  # Down
        y_adj += move_inc
    elif roi_x >= move_inc and (key == 2 or key == ord('h')):  # Left
        x_adj -= move_inc
    elif roi_x <= frame_w - roi_size - move_inc - move_inc and (key == 3 or key == ord('l')):  # Right
        x_adj += move_inc
    elif roi_size >= roi_inc * 2 and (key == ord('-') or key == ord('_')):
        roi_size -= roi_inc
        x_adj = 0
        y_adj = 0
    elif roi_size <= roi_inc * 49 and (key == ord('+') or key == ord('=')):
        roi_size += roi_inc
        x_adj = 0
        y_adj = 0
    elif key == ord('q'):
        break

    cnt += 1

cam.close()
