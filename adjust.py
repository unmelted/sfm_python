import os
import sys
import numpy as np
import math
import cv2
import logging
import json
from world import *
from mathutil import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world = world
        scale = 100
        self.normal = np.array([[1920, 1080, 0], [1920, 1080, -500]])
    
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
        return P

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


    def check_normal(self, c1) :
        K_inv = np.linalg.inv(c1.K)
        cv_pts = self.normal[0, :]
        #cv_pts = K_inv.dot(cv_pts)
        cv_pts = np.hstack([cv_pts, 1])
        cv_pts = cv_pts.reshape((4,1))
        reproject = c1.project(cv_pts)
        print("normal 1 ")
        print(reproject)
    
        cv_pts = self.normal[1, :]
        cv_pts = np.hstack([cv_pts, 1])
        cv_pts = cv_pts.reshape((4,1))
        reproject = c1.project(cv_pts)
        print("normal 2 ")
        print(reproject)    

    def make_3D_byCam(self, c0, c1) :
        print(" make_3D .... ", c0.view.name, c1.view.name)

        cam0 = cv2.convertPointsToHomogeneous(c0.pts)[:, 0, :]
        cam1 = cv2.convertPointsToHomogeneous(c1.pts)[:, 0, :]

        for i in range(c0.pts.shape[0]) :
            K0_inv = np.linalg.inv(c0.K)            
            K1_inv = np.linalg.inv(c1.K)
            u1_normalized = K0_inv.dot(cam0[i, :])
            u2_normalized = K1_inv.dot(cam1[i, :])

            point_3D = get_3D_point(u1_normalized, c0.EX, u2_normalized, c1.EX)

            error1 = calculate_reprojection_error(point_3D, cam0[i, 0:2], c0.K, c0.R, c0.t)
            error2 = calculate_reprojection_error(point_3D, cam1[i, 0:2], c1.K, c1.R, c1.t)
            # print("error " , error1, error2)
            c1.pts_3D = np.append(c1.pts_3D, np.array(point_3D).T, axis=0)        

        print(c1.pts_3D)

    def make_3D(self, c0, c1) :
        print(" make_3D .... ", c0.view.name, c1.view.name)
        pts_3d = []
        cam0 = cv2.convertPointsToHomogeneous(c0.pts)[:, 0, :]
        cam1 = cv2.convertPointsToHomogeneous(c1.pts)[:, 0, :]

        for i in range(c0.pts.shape[0]) :
            K0_inv = np.linalg.inv(c0.K)            
            K1_inv = np.linalg.inv(c1.K)
            u1_normalized = K0_inv.dot(cam0[i, :])
            u2_normalized = K1_inv.dot(cam1[i, :])

            _3d = get_3D_point(u1_normalized, c0.EX, u2_normalized, c1.EX)
            pts_3d.append(np.array(_3d).T)        

        c0.pts_3D = pts_3d
        c1.pts_3D = pts_3d        
        print(pts_3d)
        return pts_3d

    def reproject_3D_byCam(self, c0, c1) :
        print("reproject_3D .. : ", c1.view.name)

        for i in range(c0.pts.shape[0]) :
            cv_pts = c0.pts_3D[i, :]
            cv_pts = np.hstack([cv_pts, 1])
            cv_pts = cv_pts.reshape((4,1))
            reproject = c1.project(cv_pts)
            c1.pts = np.append(c1.pts, np.array(reproject).T, axis=0)        

        print(c1.pts)            

    def reproject_3D(self, pts_3d, c1) :
        print("reproject_3D .. : ", c1.view.name)

        for i in range(len(pts_3d)) :
            cv_pts = np.array(pts_3d[i]).T
            cv_pts = np.vstack([cv_pts, 1])
            reproject = c1.project(cv_pts)
            c1.pts = np.append(c1.pts, np.array(reproject).T, axis=0)        

        print(c1.pts)            

    def reproject_3D_extra(self, pts_3d, c1) :
        print("reproject_3D extra .. : ", c1.view.name)

        for i in range(len(pts_3d)) :
            cv_pts = np.array(pts_3d[i]).T
            cv_pts = np.vstack([cv_pts, 1])
            reproject = c1.project(cv_pts)
            c1.pts_extra = np.append(c1.pts_extra, np.array(reproject).T, axis=0)        

        print(c1.pts)            


    def reproject(self, c0, c1) :
        print("reproject .. : ", c1.view.name)

        for i in range(c0.pts.shape[0]) :
            cv_pts = c0.pts_back[i, :]
            cv_pts = np.hstack([cv_pts, 1])
            cv_pts = cv_pts.reshape((4,1))
            reproject = c1.project(cv_pts)
            c1.pts = np.append(c1.pts, np.array(reproject).T, axis=0)        

        print(c1.pts)            

    def backprojection(self, c):
        cam = cv2.convertPointsToHomogeneous(c.pts)[:, 0, :]
        K_inv = np.linalg.inv(c.K)
        R0_inv = np.linalg.inv(c.R)

        print(" Back projection .. : ", c.view.name)

        for i in range(c.pts.shape[0]) :        
            u1_normalized = K_inv.dot(cam[i, :])
            u1_normalized = u1_normalized.T - c.t.reshape((1,3))
            c_wrld = np.dot(R0_inv, u1_normalized.reshape((3,1)))
            c.pts_back = np.append(c.pts_back, np.array(c_wrld).T, axis=0)

            print(c_wrld.reshape((1,3)))

    def find_homography(self, answer, c0) :
       H, mask = cv2.findHomography(c0.pts, answer, 1)
       return H


    def backprojection_extra(self, c) :
        extra_3d = np.empty((0, 3))
        cam = cv2.convertPointsToHomogeneous(c.pts_extra)[:, 0, :]
        K_inv = np.linalg.inv(c.K)
        R0_inv = np.linalg.inv(c.R)

        for i in range(c.pts_extra.shape[0]) :
            u1_normalized = K_inv.dot(cam[i, :])
            u1_normalized = u1_normalized.T - c.t.reshape((1,3))
            extra_3d = np.append(extra_3d, np.arra().T, axis=0)

        return extra_3d

