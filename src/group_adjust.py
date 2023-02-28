import os
import subprocess
import numpy as np
import math
import cv2
from logger import Logger as l
from mathutil import *
from intrn_util import *
from extn_util import *
from definition import DEFINITION as df
from camera_transform import *


class GroupAdjust(object):

    def __init__(self, cameras, world, root_path, flip, config):
        self.cameras = cameras
        self.world = world
        self.root_path = root_path
        self.flip = flip

        self.x_fit = []
        self.y_fit = []
        self.config = config
        self.left = 0
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

    def set_group_margin(self, left, top, right, bottom, width, height):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height

    def calculate_extra_point_3d(self):

        dist_coeff = np.zeros((4, 1))
        inverse = 0 # 0: unknown // 1: upper->lower  // -1 : lower->upper => should be exchange

        for i, _ in enumerate(self.cameras):
            # print(self.cameras[i].view.name, self.cameras[i].K, self.world)
            result, vector_rotation, vector_translation = cv2.solvePnP(self.world, self.cameras[i].pts_3d, self.cameras[i].K, dist_coeff, cv2.SOLVEPNP_ITERATIVE)

            normal2d, jacobian = cv2.projectPoints(np.array([[50.0, 50.0, 0.0], [
                50.0, 50.0, -50.0]]), vector_rotation, vector_translation, self.cameras[i].K, dist_coeff)
            self.cameras[i].pts_extra = normal2d[:, 0, :]
            if inverse == 0 : 
                if self.cameras[i].pts_extra[0][1] > self.cameras[i].pts_extra[1][1] :
                    inverse = -1
                else :
                    inverse = 1
            if inverse == -1 :
                t_x = self.cameras[i].pts_extra[0][0]
                t_y = self.cameras[i].pts_extra[0][1]
                self.cameras[i].pts_extra[0][0] = self.cameras[i].pts_extra[1][0]
                self.cameras[i].pts_extra[0][1] = self.cameras[i].pts_extra[1][1]
                self.cameras[i].pts_extra[1][0] = t_x
                self.cameras[i].pts_extra[1][1] = t_y

            l.get().w.debug("3d make extra {} : {}".format(self.cameras[i].view.name, self.cameras[i].pts_extra))

    def calculate_rotatecenter(self, cal_type, track_cx=0, track_cy=0):

        if cal_type == '2D' : # simulation mode or cal_type == '3D'
            for i in range(len(self.cameras)):
                self.cameras[i].rotate_x = self.cameras[i].pts_extra[1][0]
                self.cameras[i].rotate_y = self.cameras[i].pts_extra[1][1]

        elif self.config['rotation_center'] == '3d-center':
            for i in range(len(self.cameras)):
                self.cameras[i].rotate_x = self.cameras[i].pts_extra[1][0]
                self.cameras[i].rotate_y = self.cameras[i].pts_extra[1][1]

        elif self.config['rotation_center'] == 'zero-cam':
            center = [self.cameras[0].view.image_width/2, self.cameras[0].view.image_height/2, 1]
            np_center = np.array(center)
            pts_3d0 = self.cameras[0].pts_3d

            for i in range(len(self.cameras)):
                if i == 0:
                    self.cameras[i].rotate_x = center[0] / center[2]
                    self.cameras[i].rotate_y = center[1] / center[2]
                    continue

                h, _ = cv2.findHomography(pts_3d0, self.cameras[i].pts_3d)
                # print("rotatecenter homography ---- \n" , h)
                center = np.dot(h, np_center)
                # print(center)
                if center[2] < 0:
                    print("3rd value is minus ...")
                    center[2] = 1.0

                self.cameras[i].rotate_x = center[0] / center[2]
                self.cameras[i].rotate_y = center[1] / center[2]
                print(self.cameras[i].view.name, self.cameras[i].rotate_x, self.cameras[i].rotate_y)

        elif self.config['rotation_center'] == 'each-center':

            self.world.calculate_center_inworld(self.cameras, self.root_path)
            new_center = self.world.interpolate_center_inworld(self.cameras)

            for i in range(len(self.cameras)):
                self.cameras[i].rotate_x = new_center[i][0]
                self.cameras[i].rotate_y = new_center[i][1]
                print(self.cameras[i].view.name, self.cameras[i].rotate_x, self.cameras[i].rotate_y)

        elif self.config['rotation_center'] == 'tracking-center':
            cam_idx = get_camera_index_byname(self.cameras, self.config['tracking_camidx'])
            pts_3d0 = self.cameras[cam_idx].pts_3d
            center = [track_cx, track_cy, 1]
            np_center = np.array(center)

            for i in range(len(self.cameras)):
                if self.cameras[i].view.name == self.config['tracking_camidx']:
                    self.cameras[i].rotate_x = track_cx
                    self.cameras[i].rotate_y = track_cy
                    continue

                h, _ = cv2.findHomography(pts_3d0, self.cameras[i].pts_3d)
                center = np.dot(h, np_center)
                # print(center)
                if center[2] < 0:
                    print("3rd value is minus ...")
                    center[2] = 1.0

                self.cameras[i].rotate_x = center[0] / center[2]
                self.cameras[i].rotate_y = center[1] / center[2]
                print(self.cameras[i].view.name, self.cameras[i].rotate_x, self.cameras[i].rotate_y)

    def calculate_radian(self):
        for i in range(len(self.cameras)):
            dist = 0
            diffx = self.cameras[i].pts_extra[1][0] - self.cameras[i].pts_extra[0][0]
            diffy = self.cameras[i].pts_extra[1][1] - self.cameras[i].pts_extra[0][1]

            if diffx == 0:
                dist = diffy
            else:
                if diffy < 0:
                    diffy *= -1
                    diffx *= -1

                dist = math.sqrt(diffx * diffx + diffy * diffy)

            self.cameras[i].rod_length = dist
            if diffx == 0:
                degree = 0
            else:
                degree = cv2.fastAtan2(diffy, diffx) * -1 + 90
            if degree < 0:
                degree = degree + 360

            self.cameras[i].degree = degree
            self.cameras[i].radian = degree * math.pi / 180
            l.get().w.debug("camera {} diffx {} diffy {} degree {} radian {} ".format(
                self.cameras[i].name, diffx, diffy, degree, self.cameras[i].radian))

    def calculate_scaleshift(self, calibtype='ave', standard_index=[-1]):
        sumx = 0
        sumy = 0
        avex = 0
        avey = 0
        dsccnt = 0
        targx = 0
        targy = 0
        targs = 0

        start_len = self.cameras[0].rod_length
        target_len = self.cameras[len(self.cameras) - 1].rod_length

        if df.test_applyshift_type == 'ave' or calibtype == 'ave':
            for i in range(len(self.cameras)):
                sumx += self.cameras[i].rotate_x
                sumy += self.cameras[i].rotate_y
                dsccnt += 1

            avex = sumx / dsccnt
            avey = sumy / dsccnt
            targx = avex
            targy = avey
        elif df.test_applyshift_type == 'center' or calibtype == 'center':
            print("------------- shift center ! .")
            center = [self.cameras[0].view.image_width/2, self.cameras[0].view.image_height/2, 1]
            targx = center[0]
            targy = center[1]
            dsccnt = len(self.cameras)

        interval = (target_len - start_len) / (dsccnt - 1)

        # print("scale shift ...", avex, avey, targx, targy)

        for i in range(len(self.cameras)):
            dist_len = start_len + (interval * i)
            self.cameras[i].scale = dist_len / self.cameras[i].rod_length
            self.cameras[i].adjust_x = targx - self.cameras[i].rotate_x
            self.cameras[i].adjust_y = targy - self.cameras[i].rotate_y

            # if df.test_apply_shift == False:
            #     self.cameras[i].adjust_x = 0
            #     self.cameras[i].adjust_y = 0

            l.get().w.debug("camera {} scale {} adjustx {} ajdusty {} ".format(
                self.cameras[i].view.name, self.cameras[i].scale, self.cameras[i].adjust_x, self.cameras[i].adjust_y))

    def get_scale_point(self, center_x, center_y, point_x, point_y, scale):
        print("scale point input .. ", center_x, center_y, point_x, point_y, scale)
        delx = point_x - center_x
        dely = point_y - center_y
        ret_x = delx * (scale)
        ret_y = dely * (scale)
        ret_x = ret_x + center_x
        ret_y = ret_y + center_y
        print("output .. ", ret_x, ret_y)
        return ret_x, ret_y

    def get_adjust_point(self, point_x, point_y, adjust_x, adjust_y):
        ret_x = point_x - adjust_x
        ret_y = point_y - adjust_y
        return ret_x, ret_y

    def calculate_margin(self):
        left = []
        right = []
        top = []
        bottom = []
        w = self.cameras[0].view.image_width
        h = self.cameras[0].view.image_height

        left.append(0)
        right.append(w-1)
        top.append(0)
        bottom.append(h-1)

        for i in range(len(self.cameras)):
            if self.cameras[i].adjust_x == 0 and self.cameras[i].adjust_y == 0 and self.cameras[i].degree == -90.0:  # will be modifed condition
                continue

            edge = np.empty((4, 2), dtype=np.float64)
            edges = np.float32(np.array([[[0, 0], [w, 0], [w, h], [0, h]]]))

            mat = self.get_affine_matrix(self.cameras[i], 'cal_margin', 1.0)
            print(mat)
            dst = cv2.perspectiveTransform(edges, mat)

            # print(" --- Transform --- ", self.cameras[i].name)
            if self.flip == False:
                edge[0] = dst[0][0]
                edge[1] = dst[0][1]
                edge[2] = dst[0][2]
                edge[3] = dst[0][3]
            else:
                edge[2] = dst[0][0]
                edge[3] = dst[0][1]
                edge[0] = dst[0][2]
                edge[1] = dst[0][3]

            print(edge)

            margin_left = 0.0
            margin_top = 0.0
            margin_right = w
            margin_bottom = h

            if edge[0][0] > margin_left:
                margin_left = math.ceil(edge[0][0])
            if edge[0][1] > margin_top:
                margin_top = math.ceil(edge[0][1])
            if edge[1][0] < margin_right:
                margin_right = math.floor(edge[1][0])
            if edge[1][1] > margin_top:
                margin_top = math.ceil(edge[1][1])

            if edge[2][0] < margin_right:
                margin_right = math.floor(edge[2][0])
            if edge[2][1] < margin_bottom:
                margin_bottom = math.floor(edge[2][1])
            if edge[3][0] > margin_left:
                margin_left = math.ceil(edge[3][0])
            if edge[3][1] < margin_bottom:
                margin_bottom = math.floor(edge[3][1])

            l.get().w.debug(" margin :: left {} top {} right {} bottom {}".format(margin_left, margin_top, margin_right, margin_bottom))

            if math.ceil(margin_left) > math.ceil(margin_top * w / h):
                margin_top = math.ceil(margin_left * h / w)
            else:
                margin_left = math.ceil(margin_top * w / h)

            if math.floor(margin_right) < math.floor(margin_bottom * w / h):
                margin_bottom = math.floor(margin_right * h / w)
            else:
                margin_right = math.floor(margin_bottom * w / h)

            if margin_left > margin_right:
                t = margin_left
                margin_left = margin_right
                margin_right = t

            if margin_top > margin_bottom:
                t = margin_top
                margin_top = margin_bottom
                margin_bottom = t

            l.get().w.debug(" margin2: left {} top {} right {} bottom {}".format(margin_left, margin_top, margin_right, margin_bottom))
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
        l.get().w.debug('calculated margin - left {} top {} right {}  bottom {} width {} height {}'.format(left[0], top[0], right[0], bottom[0], margin_width, margin_height))

        self.set_group_margin(left[0], top[0], right[0], bottom[0], margin_width, margin_height)
        return left[0], right[0], top[0], bottom[0], margin_width, margin_height

    def get_affine_matrix(self, cam, margin_proc = False, scale = 1.0):
        # print("get_affine_matrix margin_proc : ", scale, cam.view.image_width, cam.view.image_height)
        mat0 = None
        out = None
        if self.flip == True :
            mat0 = get_flip_matrix(cam.view.image_width, cam.view.image_height, True, True)
        else :
            mat0 = get_flip_matrix(cam.view.image_width, cam.view.image_height, False, False)

        # print("flip : ", mat0)
        mat1 = get_rotation_matrix_with_center(cam.radian, cam.rotate_x/scale, cam.rotate_y/scale)
        # print("rot : ", cam.radian, mat1)
        mat2 = get_scale_matrix_center(cam.scale, cam.scale, cam.rotate_x/scale, cam.rotate_y/scale)
        # print("scale : ", cam.scale, mat2)
        mat3 = get_translation_matrix(cam.adjust_x/scale, cam.adjust_y/scale)
        # print("mtran : ", mat3)
        
        if margin_proc != 'cal_margin' :
            w = 3840
            h = 2160
            if scale == 2.0:
                w = 1920
                h = 1080

            # print("margin matrix ", self.left/scale, self.top/scale, self.width/scale, self.height/scale)
            mat4 = get_margin_matrix(cam.view.image_width, cam.view.image_height, self.left/scale, self.top/scale, self.width/scale, self.height/scale)

            mat5 = get_scale_matrix(w/(self.width/scale), h/(self.height/scale))

        if margin_proc == 'adjust_image':
            out = np.linalg.multi_dot([mat4, mat2, mat1, mat3, mat0])

        elif margin_proc == 'adjust_pts' :
            # mat3 = np.int16(mat3)
            out = np.linalg.multi_dot([mat4, mat2, mat1, mat3]) #must exclude flip matrix           

        elif margin_proc == 'cal_margin':
            out = np.linalg.multi_dot([mat2, mat1, mat3, mat0])

        # print(out[:2, :3])
        return out

    def adjust_images(self, output_path, ext, job_id):
        w = int(self.cameras[0].view.image_width/2)
        h = int(self.cameras[0].view.image_height/2)
        # w = int(self.width)
        # h = int(self.height)

        analysis_path = os.path.join(df.output_adj_image_dir, str(job_id))
        os.makedirs(analysis_path)

        for i in range(len(self.cameras)):
            file_name = os.path.join(output_path, get_viewname(self.cameras[i].view.name, ext) + '_adj.jpg')
            mat = self.get_affine_matrix(self.cameras[i], 'adjust_image')
            # l.get().w.debug("view name adjust : {} matrix {} ".format(self.cameras[i].view.name, mat))

            for j in range(self.cameras[i].pts_3d.shape[0]):
                pt_int = self.cameras[i].pts_3d.astype(np.int32)
                pt_3d = self.cameras[i].pts_3d[j, :]
                cv2.circle(self.cameras[i].view.image, (int(pt_3d[0]), int(pt_3d[1])), 5, (0, 255, 0), -1)

                if j > 0:
                    cv2.line(self.cameras[i].view.image, pt_int[j-1], pt_int[j], (255, 0, 0), 3)
                if j == (self.cameras[i].pts_3d.shape[0] - 1):
                    cv2.line(self.cameras[i].view.image, pt_int[j], pt_int[0], (255, 255, 0), 3)
                    cv2.circle(self.cameras[i].view.image, (int(pt_3d[0]), int(pt_3d[1])), 10, (0, 0, 255), -1)

            for j in range(self.cameras[i].pts_2d.shape[0]):
                pt_int = self.cameras[i].pts_2d.astype(np.int32)
                pt_2d = self.cameras[i].pts_2d[j, :]
                cv2.circle(self.cameras[i].view.image, (int(pt_2d[0]), int(pt_2d[1])), 5, (0, 255, 0), -1)

                if j > 0:
                    cv2.line(self.cameras[i].view.image, pt_int[j-1], pt_int[j], (255, 0, 0), 3)
                if j == (self.cameras[i].pts_2d.shape[0] - 1):
                    cv2.line(self.cameras[i].view.image, pt_int[j], pt_int[0], (255, 255, 0), 3)

            if (self.cameras[i].pts_extra.shape[0]) > 1:
                pt_ex = self.cameras[i].pts_extra
                cv2.circle(self.cameras[i].view.image, (int(pt_ex[0][0]), int(pt_ex[0][1])), 5, (0, 255, 0), -1)
                cv2.circle(self.cameras[i].view.image, (int(pt_ex[1][0]), int(pt_ex[1][1])), 5, (0, 255, 0), -1)
                #cv2.circle(self.cameras[i].view.image, (int(pt_ex[2][0]), int(pt_ex[2][1])), 5, (0, 255, 0), -1)
                # cv2.line(self.cameras[i].view.image, (int(pt_ex[0][0]), int(pt_ex[0][1])), (int(pt_ex[1][0]), int(pt_ex[1][1])),
                #  (255, 0, 0), 3)
                print("extra point ! :",  int(pt_ex[0][0]), int(pt_ex[0][1]), int(pt_ex[1][0]), int(pt_ex[1][1]))

            cv2.circle(self.cameras[i].view.image, (int(self.cameras[i].rotate_x), int(self.cameras[i].rotate_y)), 8, (0, 0, 255), -1)

            dst_img = cv2.warpAffine(self.cameras[i].view.image, mat[:2, :3], (w, h))
            cv2.imwrite(file_name, dst_img)
            shutil.copy(file_name, analysis_path)

        cli = "convert -delay 25 -resize 960x540 -loop 0 " + \
            output_path + "/*.jpg " + output_path + "/animated.gif"
        print(cli)
        process = subprocess.Popen(cli, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    def adjust_image(self, output_path, camera, scale=1.0):
        w = 3840
        h = 2160

        if scale == 2.0:
            w = 1920
            h = 1080
        file_name = os.path.join(output_path, camera.name + '_adj.jpg')
        mat = self.get_affine_matrix(camera, 'adjust_image', scale)
        dst_img = cv2.warpAffine(camera.image, mat[:2, :3], (w, h))

        cv2.imwrite(file_name, dst_img)
        return dst_img

    def adjust_pts(self, output_path ,cameras, scale=1.0) :
        index = 0
        check_detail = True

        for camera in cameras : 
            print("--- cam : ", camera.name, camera.pts_3d)
            file_name = os.path.join(output_path, camera.name + '_adj_pt.jpg')
            mat = self.get_affine_matrix(camera, 'adjust_pts', scale)
            dst_img = camera.adj_image
            pts_3d = np.array([camera.pts_3d]) / scale
            # mv_pts = cv2.perspectiveTransform(pts_3d, mat)
            mv_pts = cv2.transform(pts_3d, mat[:2, :3])
            prev = None
            
            camera.adj_pts3d = mv_pts
            for i, pt in enumerate(mv_pts[0]) :
                if check_detail :
                    print(pt)
                cv2.circle(dst_img, (int(pt[0]), int(pt[1])), 5, (0, 255,255), -1)
                # if i > 0 :
                    # cv2.line(dst_img (int(pt[0]), int(pt[1])), (int(prev[0]), int(prev[1])), (255, 0, 255), 3)
                prev = pt

            # cv2.line(dst_img, (int(mv_pts[0][0][0]), int(mv_pts[0][0][1])), (int(prev[0]), int(prev[1])), (255, 0 , 255), 3)
            # cv2.imwrite(file_name, dst_img)
            # if check_detail :
            #     cv2.imshow("check pts", dst_img)
            #     cv2.waitKey()

    def adjust_pts_any(self, camera, scale, points, many) :
        print("adjust_pts_any .. ", many, points)

        mat = self.get_affine_matrix(camera, 'adjust_pts', scale)
        if many == True :
            n_pts = np.float32(points)
        else : 
            n_pts = np.array([[[points[0], points[1]]]])

        print(n_pts)
        mv_pts = cv2.perspectiveTransform(n_pts, mat)
        print("adjust_pts_any \n", mv_pts)

        return mv_pts
