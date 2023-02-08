import os
import glob
import numpy as np
import math
from mathutil import *
import cv2


def get_affine_matrix(image_width, image_height, degree, rotate_x, rotate_y, scale, adjust_x, adjust_y, start_x, start_y, flip, width, height):
    # print(adjust_x, adjust_y, rotate_x, rotate_y,
    #       start_x, start_y, width, height)
    radian = degree * math.pi / 180

    mat0 = get_flip_matrix(image_width, image_height, flip, flip)
    # print(mat0)
    mat1 = get_rotation_matrix_with_center(
        radian, rotate_x, rotate_y)
    mat2 = get_scale_matrix_center(scale, scale, rotate_x, rotate_y)
    mat3 = get_translation_matrix(adjust_x, adjust_y)
    mat4 = get_margin_matrix(image_width, image_height,
                             start_x, start_y, width, height)
    mat5 = get_scale_matrix(0.5, 0.5)
    out = np.linalg.multi_dot([mat5, mat4, mat3, mat2, mat1])
    # print(out)
    # print(np.array_str(out, precision=4, suppress_small=True))

    return out


def adjust_image(image, matrix, target_width, target_height):
    dst_img = cv2.warpAffine(
        image, matrix[:2, :3], (target_width, target_height))

    return dst_img


def check_points(pts, m):
    x = 0
    y = 0
    print(np.array_str(m, precision=4, suppress_small=True))

    for i in range(len(pts)):
        x = pts[i][0]
        y = pts[i][1]
        print(x, y)
        ret = cv2.transform(np.array([[[x, y]]]), m)
        print(ret)
        # print("input : ", x, y)
        # print("output : ", xx, yy)


def check_blackline(frame, degree, width, height):
    hori_black = 0
    verti_black = 0
    check_warn = False

    for i in range(width):
        if (dst_img.item(0, i, 0) == 0 and dst_img.item(0, i, 1) == 0 and dst_img.item(0, i, 2) == 0):
            hori_black += 1

    for i in range(height):
        if (dst_img.item(i, 0, 0) == 0 and dst_img.item(i, 0, 1) == 0 and dst_img.item(i, 0, 2) == 0):
            verti_black += 1

    print("degree : ", hori_black, verti_black)
    # if hori_black > width * 0.8 or verti_black > height * 0.8:
    # if hori_black > width * 0.8 and verti_black > height * 0.8:
    # print("WARN BLACK LINE ")
    out_file = "affine_" + str(degree) + ".jpg"
    cv2.imwrite(out_file, frame)
    # check_warn = True

    return check_warn


# cam = cv2.VideoCapture(filename)
# ret, frame = cam.read()
# cv2.imwrite("capture.jpg", frame)
# cam.release()
filename = "test.tiff"
frame = cv2.imread(filename)
pts = [[0, 0], [1920, 0], [1080, 0], [1920, 1080]]

for deg in range(-360, -170):
    mat = get_affine_matrix(3840, 2160, deg, 1920, 1080, 1,
                            0, 0, 0, 0, True, 3840, 2160)
    dst_img = adjust_image(frame, mat, 1920, 1080)
    result = check_blackline(dst_img, deg, 1920, 1080)
    # if result == True:
    #     check_points(pts, mat)

for deg in range(170, 360):
    mat = get_affine_matrix(3840, 2160, deg, 1920, 1080, 1,
                            0, 0, 0, 0, True, 3840, 2160)
    dst_img = adjust_image(frame, mat, 1920, 1080)
    result = check_blackline(dst_img, deg, 1920, 1080)
    # if result == True:
    #     check_points(pts, mat)

mm = [[-0.51,   -0.,  1920.],
      [0.,    -0.5, 1080.],
      [0.,     0.,     1.]]
mat = np.array(mm)
print("---- check ")
ddst_img = adjust_image(frame, mat, 1920, 1080)
cv2.imwrite("affine_0.51.jpg", ddst_img)
result = check_blackline(ddst_img, 1234, 1920, 1080)
