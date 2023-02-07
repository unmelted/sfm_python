import os
import glob
import cv2
import json
import argparse
import math
from camera import *


def prepare_video_job(from_path, to_path):

    if not os.path.exists(to_path):
        os.makedirs(to_path)

    video_files = sorted(glob.glob(os.path.join(from_path, '*.mp4')))

    pick_frame = 1
    if len(video_files) < 5:
        return -102

    for video in video_files:
        filename = video[video.rfind('/') + 1:]
        print(filename)
        filename = filename[0:filename.rfind('_')] + '.jpg'

        cam = cv2.VideoCapture(video)
        cam.set(cv2.CAP_PROP_POS_FRAMES, pick_frame)
        ret, frame = cam.read()
        if not ret:
            return -103

        target = os.path.join(to_path, filename)
        print("create : ", target)
        cv2.imwrite(target, frame)
        cam.release()

    return 0


def get_adjust_info(from_path, cam_idx):

    filename = os.path.join(from_path, "UserPointData.adj")

    with open(filename, "r") as json_file:
        from_data = json.load(json_file)

    info = {}

    for j in range(len(from_data["adjust_list"])):
        if from_data["adjust_list"][j]["dsc_id"] == cam_idx:
            info = from_data["adjust_list"][j]["adjust"]
            # print(info)
            return info


def get_rotate_point(center_x, center_y, point_x, point_y, radian):
    print("rotate point input .. ", center_x,
          center_y, point_x, point_y, radian)
    delx = point_x - center_x
    dely = point_y - center_y

    cos_ = math.cos(radian)
    sin_ = math.sin(radian)

    ret_x = delx * cos_ - dely * sin_
    ret_y = delx * sin_ + dely * cos_

    ret_x = ret_x + center_x
    ret_y = ret_y + center_y

    print(ret_x, ret_y)
    return ret_x, ret_y


def get_scale_point(center_x, center_y, point_x, point_y, scale):
    print("scale point input .. ", center_x,
          center_y, point_x, point_y, scale)
    delx = point_x - center_x
    dely = point_y - center_y

    ret_x = delx * (1/scale)
    ret_y = dely * (1/scale)

    ret_x = ret_x + center_x
    ret_y = ret_y + center_y

    return ret_x, ret_y


def cal_inv_calib(info):
    crns = list(range(8))
    print("received.. ", info)
    crns[0] = int(info["RectMargin"]["Left"])
    crns[1] = int(info["RectMargin"]["Top"])
    crns[2] = int(info["RectMargin"]["Left"]) + \
        int(info["RectMargin"]["Width"])
    crns[3] = int(info["RectMargin"]["Top"])
    crns[4] = int(info["RectMargin"]["Left"]) + \
        int(info["RectMargin"]["Width"])
    crns[5] = int(info["RectMargin"]["Top"]) + \
        int(info["RectMargin"]["Height"])
    crns[6] = int(info["RectMargin"]["Left"])
    crns[7] = int(info["RectMargin"]["Top"]) + \
        int(info["RectMargin"]["Height"])

    print(crns)

    for i in range(len(crns)):
        if i % 2 == 0:
            crns[i] = crns[i] - int(info["AdjustX"])
        else:
            crns[i] = crns[i] - int(info["AdjustY"])

        if i % 2 == 1:
            s_x, s_y = get_scale_point(
                info["RotateX"], info["RotateY"], crns[i-1], crns[i], info["Scale"])
            print("scale,, ", s_x, s_y)

            t_x, t_y = get_rotate_point(
                info["RotateX"], info["RotateY"], s_x, s_y, -info["Angle"])

            crns[i-1] = int(t_x)
            crns[i] = int(t_y)

            if isflip == True:
                crns[i-1] = 3840 - int(t_x)
                crns[i] = 1920 - int(t_y)

            if crns[i-1] < 0 or crns[i-1] > 3840:
                print("WARN X------------------------ ")
            elif crns[i] < 0 or crns[i] > 1920:
                print("WARN y------------------------ ")

    print("--- adjust apply")
    print(crns)

    return crns


def show_original_image(img, crns):
    # img = cv2.imread("./inv_test/30075.png")
    cv2.circle(img, (crns[0], crns[1]), 10, (255, 0, 255), -1)
    cv2.circle(img, (crns[2], crns[3]), 10, (255, 0, 255), -1)
    cv2.circle(img, (crns[4], crns[5]), 10, (255, 0, 255), -1)
    cv2.circle(img, (crns[6], crns[7]), 10, (255, 0, 255), -1)
    cv2.imshow("TEST", img)
    cv2.waitKey()


# parser = argparse.ArgumentParser()
# parser.add_argument('--cam_idx', type=str)
# args = parser.parse_args()
# print("input cam_idx : ", args.cam_idx)

from_path = './Cal3D_Preset0_230107_085658'
to_path = './Cal3D_Preset0_230107_085658/image'
#prepare_video_job(from_path, to_path)

files = sorted(glob.glob(os.path.join(to_path, '*.jpg')))
isflip = True
cameras = []

for file in files:
    print("start : ", file)
    target = file.split('/')[-1][:-4]
    print(target)
    info = get_adjust_info(to_path, target)
    if info == None:
        continue
    img = cv2.imread(file)
    show_original_image(img, cal_inv_calib(info))
