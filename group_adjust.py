import os
import subprocess
import numpy as np
import math
from logger import Logger as l
from mathutil import *
from intrn_util import *
from extn_util import *
from definition import DEFINITION as defn


class GroupAdjust(object):

    def __init__(self, cameras):
        self.cameras = cameras

    def set_group_margin(self, left, top, right, bottom, width, height):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height

    def calculate_radian(self):
        for i in range(len(self.cameras)):
            dist = 0
            diffx = self.cameras[i].pts_extra[1][0] - \
                self.cameras[i].pts_extra[0][0]
            diffy = self.cameras[i].pts_extra[1][1] - \
                self.cameras[i].pts_extra[0][1]

            if diffx == 0:
                dist = diffy
            else :
                if diffy < 0 :
                    diffy *= -1
                    diffx *= -1

                dist = math.sqrt(diffx * diffx + diffy * diffy)

            self.cameras[i].rod_length = dist
            if diffx == 0:
                degree = 90
            else:
                degree = cv2.fastAtan2(diffy, diffx) * -1 + 90
            if degree < 0:
                degree = degree + 360

            self.cameras[i].radian = degree * math.pi / 180
            l.get().w.debug("camera {} diffx {} diffy {} degree {} radian {} ".format(
                self.cameras[i].view.name, diffx, diffy, degree, self.cameras[i].radian))

    def calculate_scaleshift(self):
        sumx = 0
        sumy = 0
        avex = 0
        avey = 0
        dsccnt = 0
        targx = 0
        targy = 0

        startx = self.cameras[0].pts_extra[1][0]
        startx = self.cameras[0].pts_extra[1][1]
        start_len = self.cameras[0].rod_length
        target_len = self.cameras[len(self.cameras) - 1].rod_length

        for i in range(len(self.cameras)):
            sumx += self.cameras[i].pts_extra[1][0]
            sumy += self.cameras[i].pts_extra[1][1]
            dsccnt += 1

        avex = sumx / dsccnt
        avey = sumy / dsccnt
        targx = avex
        targy = avey
        interval = (target_len - start_len) / (dsccnt - 1)

        for i in range(len(self.cameras)):
            dist_len = start_len + (interval * i)
            self.cameras[i].scale = dist_len / self.cameras[i].rod_length
            self.cameras[i].adjust_x = targx - self.cameras[i].pts_extra[1][0]
            self.cameras[i].adjust_y = targy - self.cameras[i].pts_extra[1][1]
            self.cameras[i].rotate_x = self.cameras[i].pts_extra[1][0]
            self.cameras[i].rotate_y = self.cameras[i].pts_extra[1][1]
            l.get().w.debug("camera {} scale {} adjustx {} ajdusty {} ".format(
                self.cameras[i].view.name, self.cameras[i].scale, self.cameras[i].adjust_x, self.cameras[i].adjust_y))

    def calculate_margin(self):
        left = []
        right = []
        top = []
        bottom = []
        left.append(0)
        right.append(self.cameras[0].view.image_width)
        top.append(0)
        bottom.append(self.cameras[0].view.image_height)

        for i in range(len(self.cameras)):
            scale = self.cameras[i].scale
            center_x = self.cameras[i].rotate_x
            center_y = self.cameras[i].rotate_y
            w = self.cameras[i].view.image_width
            h = self.cameras[i].view.image_height

            e1_x = center_x * (1 - scale)
            e1_y = center_y * (1 - scale)
            e2_x = e1_x + (scale * w)
            e2_y = e1_y
            e3_x = e2_x
            e3_y = e1_y + (scale * h)
            e4_x = e1_x
            e4_y = e3_y

            e1r_x, e1r_y = get_rotate_point(
                center_x, center_y, e1_x, e1_y, self.cameras[i].radian)
            e2r_x, e2r_y = get_rotate_point(
                center_x, center_y, e2_x, e2_y, self.cameras[i].radian)
            e3r_x, e3r_y = get_rotate_point(
                center_x, center_y, e3_x, e3_y, self.cameras[i].radian)
            e4r_x, e4r_y = get_rotate_point(
                center_x, center_y, e4_x, e4_y, self.cameras[i].radian)

            margin_left = max((e1r_x + self.cameras[i].adjust_x), 0)
            margin_top = max((e1r_y + self.cameras[i].adjust_y), 0)

            margin_right = min((e2r_x + self.cameras[i].adjust_x), w)
            margin_top = max((e2r_y + self.cameras[i].adjust_y), 0)

            margin_right = min(
                (e3r_x + self.cameras[i].adjust_x), margin_right)
            margin_bottom = min((e3r_y + self.cameras[i].adjust_y), h)

            margin_left = max((e4r_x + self.cameras[i].adjust_x), margin_left)
            margin_bottom = min(
                (e4r_y + self.cameras[i].adjust_y), margin_bottom)

            if margin_left > margin_top * w / h:
                margin_top = margin_left * h / w
            else:
                margin_left = margin_top * w / h

            if margin_right < margin_bottom * w / h:
                margin_bottom = margin_right * h / w
            else:
                margin_right = margin_bottom * w / h

            if margin_left > margin_right:
                t = margin_left
                margin_left = margin_right
                margin_right = t

            if margin_top > margin_bottom:
                t = margin_top
                margin_top = margin_bottom
                margin_bottom = t

            # print(margin_left, margin_right, margin_top, margin_bottom)
            left.append(margin_left)
            right.append(margin_right)
            top.append(margin_top)
            bottom.append(margin_bottom)

        left.sort(reverse=True)
        right.sort()
        top.sort(reverse=True)
        bottom.sort()
        margin_width = right[0] - left[0]
        margin_height = bottom[0] - top[0]
        l.get().w.debug('calculated margin l {} r {} t {} b {} width {} height {}'.format(
            left[0], right[0], top[0], bottom[0], margin_width, margin_height))

        self.set_group_margin(
            left[0], right[0], top[0], bottom[0], margin_width, margin_height)
        return left[0], right[0], top[0], bottom[0], margin_width, margin_height

    def get_affine_matrix(self, cam):
        mat1 = get_rotation_matrix_with_center(
            cam.radian, cam.rotate_x, cam.rotate_y)
        mat2 = get_scale_matrix_center(
            cam.scale, cam.scale, cam.rotate_x, cam.rotate_y)
        mat3 = get_translation_matrix(cam.adjust_x, cam.adjust_y)
        mat4 = get_margin_matrix(cam.view.image_width, cam.view.image_height,
                                 self.left, self.right, self.width, self.height)
        mat5 = get_scale_matrix(0.5, 0.5)
        out = np.linalg.multi_dot([mat5, mat3, mat2, mat1])
        return out

    def adjust_image(self, output_path, ext, job_id):
        w = int(self.cameras[0].view.image_width/2)
        h = int(self.cameras[0].view.image_height/2)
        analysis_path = os.path.join(defn.output_adj_image_dir, str(job_id))
        os.makedirs(analysis_path)

        for i in range(len(self.cameras)):
            file_name = os.path.join(output_path, get_viewname(
                self.cameras[i].view.name, ext) + '_adj.jpg')
            mat = self.get_affine_matrix(self.cameras[i])
            # l.get().w.debug("view name adjust : {} matrix {} ".format(self.cameras[i].view.name, mat))

            for j in range(self.cameras[i].pts_3d.shape[0]):
                pt_int = self.cameras[i].pts_3d.astype(np.int32)
                pt_3d = self.cameras[i].pts_3d[j, :]
                cv2.circle(self.cameras[i].view.image, (int(
                    pt_3d[0]), int(pt_3d[1])), 5, (0, 255, 0), -1)

                if j > 0:
                    cv2.line(self.cameras[i].view.image,
                             pt_int[j-1], pt_int[j], (255, 0, 0), 3)
                if j == (self.cameras[i].pts_3d.shape[0] - 1):
                    cv2.line(self.cameras[i].view.image,
                             pt_int[j], pt_int[0], (255, 255, 0), 3)
                    cv2.circle(self.cameras[i].view.image, (int(
                        pt_3d[0]), int(pt_3d[1])), 10, (0, 0, 255), -1)

            for j in range(self.cameras[i].pts_2d.shape[0]):
                pt_int = self.cameras[i].pts_2d.astype(np.int32)
                pt_2d = self.cameras[i].pts_2d[j, :]
                cv2.circle(self.cameras[i].view.image, (int(
                    pt_2d[0]), int(pt_2d[1])), 5, (0, 255, 0), -1)

                if j > 0:
                    cv2.line(self.cameras[i].view.image,
                             pt_int[j-1], pt_int[j], (255, 0, 0), 3)
                if j == (self.cameras[i].pts_2d.shape[0] - 1):
                    cv2.line(self.cameras[i].view.image,
                             pt_int[j], pt_int[0], (255, 255, 0), 3)

            if (self.cameras[i].pts_extra.shape[0]) > 1:
                pt_ex = self.cameras[i].pts_extra
                cv2.circle(self.cameras[i].view.image, (int(
                    pt_ex[0][0]), int(pt_ex[0][1])), 5, (0, 255, 0), -1)
                cv2.circle(self.cameras[i].view.image, (int(
                    pt_ex[1][0]), int(pt_ex[1][1])), 5, (0, 255, 0), -1)
                #cv2.circle(self.cameras[i].view.image, (int(pt_ex[2][0]), int(pt_ex[2][1])), 5, (0, 255, 0), -1)
                cv2.line(self.cameras[i].view.image, (int(pt_ex[0][0]), int(pt_ex[0][1])), (int(pt_ex[1][0]), int(pt_ex[1][1])),
                         (255, 0, 0), 3)
                print("extra point ! :",  int(pt_ex[0][0]), int(
                    pt_ex[0][1]), int(pt_ex[1][0]), int(pt_ex[1][1]))

            dst_img = cv2.warpAffine(
                self.cameras[i].view.image, mat[:2, :3], (w, h))
            cv2.imwrite(file_name, dst_img)
            shutil.copy(file_name, analysis_path)

        cli = "convert -delay 25 -resize 960x540 -loop 0 " + \
            output_path + "/*.jpg " + output_path + "/animated.gif"
        print(cli)
        process = subprocess.Popen(
            cli, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
