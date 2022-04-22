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
        newR = np.dot(target.R, ref.R.T)
        print("camera_releative.. ", newR)

        temp = np.dot(newR, ref.t)
        newT = target.t - temp
        print("new T " , np.dot(target.K, newT))
        K_inv = np.linalg.inv(target.K)
        # pts = K_inv.dot(np.array([[1162, 0, -1579]]).T)
        # self.convert_pts_relative(target, newR, newT, pts)

        temp = np.hstack([newR, target.t])
        P = np.dot(target.K, temp) 

        ppts = ref.pts.reshape((3, 1))        
        ppts = np.vstack([ppts, 1])
        reproject = np.dot(P, ppts)
        target.pts =  K_inv.dot(reproject).T    
        # target.pts[0][1] = 0            
        print("camera_relative.. " , target.pts)


    def convert_pts_relative(self, target, newR, newT, pts) : 
        reproject = target.K.dot(newR.dot(pts) + newT)
        #reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
        print("convert_pts_releative.. ", reproject)
        K_inv = np.linalg.inv(target.K)      
        print(".. " , K_inv.dot(reproject).T)          

        return reproject

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
        # ppts[0][1] = -1 * ppts[0][2]
        # ppts[0][2] = 0.0
        print("convert_pts2 .. ", ppts)        
        ppts = ppts.reshape((3,1))         
        K_inv = np.linalg.inv(target.K)

        distcoeff = np.array([[0., 0., 0., 0.]])
        projectvector, _ = cv2.projectPoints(ppts, target.Rvec, target.t, target.K, distcoeff)
        projectvector = projectvector[0][0]
        print("convert_pts2 .. " , projectvector)

        projectvector = np.hstack([projectvector, 0])
        projectvector = projectvector.reshape((3,1))
        print(projectvector)
        print("convert_pts2 .. " , K_inv.dot(projectvector))

    def convert_pts3(self, ppts, target) :
        print("convert_pt3  ", ppts)
        ppts = ppts.reshape((3, 1))        
        K_inv = np.linalg.inv(target.K)
        ppts = np.vstack([ppts, 1])
        reproject = np.dot(target.P, ppts)
        target.pts =  K_inv.dot(reproject).T
        # target.pts[0][1] = 0        

        print("convert_pt3 1.. " , target.pts)

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


    def write_file(self):
        json_data = {
                "RecordName" : None,
                "PreSetNumber" : 0,
                "worlds" : [
                    {
                            
                        "group":None,
                        "stadium":None,
                        "world_coords":None
                    }
                ]
                    ,
                "points" : None
            }
        json_data['worlds'][0]['group'] = "Group1"
        json_data['worlds'][0]['stadium'] = self.world.stadium
            