import os
import json
import cv2
import math


def test_atan():
    x = [10, 7.0, 0, -7, -10, -7, 0,  7]
    y = [0,  7.0, 10, 7,  0,  -7, -7, -7]
    deg = [0, 45, 90, 135, 180, 225, 270, 315]

    for i in range(len(x)):
        print("------------------------ ", deg[i])
        degree3d = cv2.fastAtan2(x[i], -y[i])
        if -y[i] > 0:
            degree3d = 360 - degree3d
        else:
            degree3d = 180 - degree3d

        if degree3d >= -180:
            degree3d += -90
        else:
            degree3d += 270

        degree2d = math.atan2(y[i], x[i]) * -180/math.pi

        margin3d = -1 * (degree3d + 90)
        margin2d = -1 * (degree3d + 90)

        print("-- old --- ")
        print("3d angle : ", degree3d)
        print("2d angle : ", degree2d)
        print("3d amrgin: ", margin3d)
        print("2d amrgin: ", margin2d)

        ndegree3d = cv2.fastAtan2(x[i], y[i])
        if y[i] < 0:
            ndegree3d = 90 - ndegree3d
        else:
            ndegree3d = 270 - ndegree3d

        ndegree2d = cv2.fastAtan2(y[i], x[i]) * -1 + 90

        print("-- new --- ")
        print("3d angle : ", ndegree3d)
        print("2d angle : ", ndegree2d)
        print("3d amrgin: ", ndegree3d)
        print("2d amrgin: ", ndegree2d)


test_atan()
