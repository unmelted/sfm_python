import os
import sys
import numpy as np
import math
import cv2
import logging
import json
from world import *
from util import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world = world
        scale = 1
        self.normal = np.array([[50/scale, 50/scale, 0], [50/scale, 50/scale, -50/scale]])
    
    def get_initial_cp(self):
        if self.calib_type == '3D' : 
            pts = [[708, 183], [120, 1614], [2766, 1485], [2091, 144]] # ncaa 
        else :
            pts = [[2749, 785], [884, 1170]] # 2D는 2point?

        return pts

    def cart2hom(self, arr):
        """ Convert catesian to homogenous points by appending a row of 1s
        :param arr: array of shape (num_dimension x num_points)
        :returns: array of shape ((num_dimension+1) x num_points) 
        """
        if arr.ndim == 1:
            return np.hstack([arr, 1])
        return np.asarray(np.vstack([arr, np.ones(arr.shape[1])]))


    def get_camera_pos(self, target):
        R_inv = np.linalg.inv(target.R)
        zc = np.array([[0, 1, 0]]).T
        cam_pos = R_inv.dot(target.t)
        zw = R_inv.dot(zc)
        print("Camera pose z -- ", zw)
        pan = math.atan2 (zw[2], zw[0]) - math.pi / 2
        xc = np.array([1, 0, 0]).T
        xw = R_inv.dot(xc)
        xpan = [math.cos(pan), math.sin(pan), 0]
        roll = math.acos(xw[0]*xpan[0] + xw[1] * xpan[1] + xw[2]*xpan[2])
        if xw[2] < 0 : roll = -roll

        print(roll, roll * 180/math.pi)
    
    def get_camera_relative(self, ref, target) :
        newR = np.dot(target.R.T, ref.R)
        print("camera_releative.. ", newR)

        temp = -1* np.dot(newR, ref.t)
        newT = temp + target.t
        K_inv = np.linalg.inv(target.K)
        print("new T " , newT)
        # pts = K_inv.dot(np.array([[1162, 0, -1579]]).T)
        # self.convert_pts_relative(target, newR, newT, pts)

        temp = np.hstack([newR, newT])
        P = np.dot(target.K, temp) 

        ppts = ref.pts.reshape((3, 1))        
        ppts = np.vstack([ppts, 1])
        reproject = np.dot(P, ppts)
        target.pts =  K_inv.dot(reproject).T    
        # target.pts[0][1] = 0            
        print("camera_relative.. " , target.pts)

    #cam1 -> cam2 relative
    def get_camera_relative2(self, ref, target) :
        newR = np.dot(ref.R.T, target.R)
        print("camera_releative.. ", newR)

        temp = -1* np.dot(newR, ref.t)
        newT = temp + target.t
        K_inv = np.linalg.inv(target.K)
        print("new T " , newT)

        temp = np.hstack([newR, newT])
        P = np.dot(target.K, temp) 

        ppts = ref.pts.reshape((3, 1))        
        ppts = np.vstack([ppts, 1])
        reproject = np.dot(P, ppts)
        target.pts =  K_inv.dot(reproject).T    
        # target.pts[0][1] = 0            
        print("camera_relative.. " , target.pts)


    def convert_pts(self, ppts, target):
        ppts2 = ppts.reshape((3,1))
        ppts2 = self.cart2hom(ppts2)
        print("convert_pts .. " , ppts2) 

        reproject = np.dot(target.P, ppts2)
        reproject /= reproject[2]
        print("reproject .. 1  ",  reproject)
        ppts = ppts.reshape((3,1))
        reproject2 = target.K.dot(target.R.dot(ppts) + target.t)
        reproject2 = cv2.convertPointsFromHomogeneous(reproject2.T)[:, 0, :].T
        print("reporject.. 2 ", reproject2)

        # for pt in self.world.world_points:
        #     pt = pt.reshape((3,1))
        #     # K_inv = np.linalg.inv(target.K)
        #     # pt = K_inv.dot(pt) 
        #     reproject = (target.R.T.dot(pt) + target.t)
        #     eproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
        #     # print("4point .. " , pt)
        #     # print("reproject .. " ,reproject)
        #     target.pts.append(reproject)
    
    def convert_pts2(self, ppts, target):
        print("convert_pts2 .. ", target.view.name, ppts)
        pts = np.zeros((3), dtype=np.float)
        pts[0] = ppts[0][0]
        pts[1] = ppts[0][1]
        pts[2] = ppts[0][2]
        pts = np.array([pts])
        ppts = pts.reshape((3,1))         
        K_inv = np.linalg.inv(target.K)
        #ppts = np.vstack([ppts, 1])        
        ppts = K_inv.dot(ppts)
        distcoeff = np.array([[0., 0., 0., 0.]])
        projectvector, _ = cv2.projectPoints(ppts, target.Rvec, target.t, target.K, distcoeff)
        ppts = K_inv.dot(np.vstack([projectvector[0][0].reshape((2,1)), 1]))
        print("convert_pts2 .. " ,  ppts)

    def convert_pts3(self, ppts, target) :
        print("convert_pt3  ", target.view.name, ppts)
        ppts = ppts.reshape((3, 1))    
        ppts = np.vstack([ppts, 1])            
        K_inv = np.linalg.inv(target.K)
        reproject = np.dot(target.P, ppts)
        target.pts =  K_inv.dot(reproject).T
        # target.pts =  reproject
        print("convert_pt3 1.. " , target.pts)
        self.convert_pts2(target.pts, target)
        # temp = target.pts.reshape((3, 1))        
        # temp = K_inv.dot(temp)
        # distcoeff = np.array([[0., 0., 0., 0.]])
        # projectvector, _ = cv2.projectPoints(temp, target.Rvec, target.t, target.K, distcoeff)
        # temp = np.vstack([projectvector[0][0].reshape((2,1)), 1])
        # print("convert_pt3 2.. " , (temp))

    def convert_pts4(self, ppts, target) :
        pts = np.zeros((2), dtype=float)
        pts[0] = ppts[0][0]
        pts[1] = ppts[0][2]
        print(pts)
        pts = np.array([pts])
        K_inv = np.linalg.inv(target.K)
        #ppts = np.vstack([ppts, 1])

        reprojected_points = cv2.perspectiveTransform(src=pts, m=target.P)
        print("convert_pts4 .. ", reprojected_points)
        z = reprojected_points[0, :, -1]        
        print("convert_pts4 .. ", z)

    def convert_pts5(self, ppts, target):
        print("convert_pt5..  ", target.view.name, ppts)
        K_inv = np.linalg.inv(target.K)                 
        ppts = ppts.reshape((3, 1))        
        ppts = K_inv.dot(ppts)        
        ppts = np.vstack([ppts, 1])
        R_inv = np.linalg.inv(target.R)                 
        temp = np.dot(R_inv, target.t)
        print("convert_pt5.. campos : ", temp)
        temp = np.dot(target.K, temp)
        # back_proj = np.dot(temp, ppts)
        # back_proj = np.vstack([back_proj, 1])        
        # print("convert_pt5 .. ", back_proj)
        # move_pt = np.dot(target.P, back_proj)        
        # print("convert_pt5.. " , move_pt, np.dot(K_inv, move_pt))


    def make_3D(self, c0, c1) :
        print("check_pts .. ", c0.view.name, c1.view.name)

        cam0 = cv2.convertPointsToHomogeneous(c0.pts)[:, 0, :]
        cam1 = cv2.convertPointsToHomogeneous(c1.pts)[:, 0, :]

        for i in range(c0.pts.shape[0]) :
            K_inv = np.linalg.inv(c1.K)                         
            u1_normalized = K_inv.dot(cam0[i, :])
            u2_normalized = K_inv.dot(cam1[i, :])

            point_3D = get_3D_point(u1_normalized, c0.EX, u2_normalized, c1.EX)

            error1 = calculate_reprojection_error(point_3D, cam0[i, 0:2], c0.K, c0.R, c0.t)
            error2 = calculate_reprojection_error(point_3D, cam1[i, 0:2], c1.K, c1.R, c1.t)
            print("make 3D error  .. ", point_3D, error1, error2)
            c1.pts_3D = np.append(c1.pts_3D, np.array(point_3D).T, axis=0)        


    def reproject_3D(self, c0, c1) :
        print("reproject_3D ..", c1.view.name)
        print("pts_3D : ", c0.pts_3D)

        cam0 = cv2.convertPointsToHomogeneous(c0.pts_3D)[:, 0, :]

        for i in range(c0.pts.shape[0]) :
            cv_pts = c0.pts_3D[i, :]
            cv_pts = np.hstack([cv_pts, 1])
            cv_pts = cv_pts.reshape((4,1))
            reproject = c1.project(cv_pts)
            c1.pts = np.append(c1.pts, np.array(reproject).T, axis=0)        

        print(c1.pts)            
        
            # moved = c1.K.dot(c1.R.dot(c0.pts_3D) + c1.t)
            # moved =  cv2.convertPointsFromHomogeneous(moved.T)[:, 0, :].T
            # c1.pts = np.vstack([moved, 1])
            # c1.pts = c1.pts.reshape((3, 1))
            # #print("moved .. ", moved.shape, c0.pts.shape, c1.pts.shape)
            # print("reproject fianl : ", moved, c1.pts)
            # temp = np.vstack([c0.pts_3D, 1])
            # temp = temp.reshape((4, 1))
            # print("compare function .. :  ", c1.project(temp))
