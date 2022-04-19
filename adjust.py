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
        zc = np.array([[0, 0, 1]]).T
        cam_pos = R_inv.dot(target.t)
        zw = R_inv.dot(zc)
        print("Camera pose z -- ", zw)
        pan = math.atan2 (zw[1], zw[0]) - math.pi / 2
        xc = np.array([1, 0, 0]).T
        xw = R_inv.dot(xc)
        xpan = [math.cos(pan), math.sin(pan), 0]
        roll = math.acos(xw[0]*xpan[0] + xw[1] * xpan[1] + xw[2]*xpan[2])
        if xw[2] < 0 : roll = -roll

        print(roll, roll * 180/math.pi)
    
    def get_camera_relative(self, ref, target) :
        print("get_camera_relative.. ref / target ") 
        print(ref.R, target.R)
        newR = np.dot(target.R, ref.R.T)
        print("get_camera_releative.. ", newR)

        temp = np.dot(newR, ref.t)
        newT = target.t - temp
        print("new T " , newT)
        K_inv = np.linalg.inv(target.K)
        pts = K_inv.dot(np.array([[1162, 0, -1579]]).T)
        self.convert_pts_relative(target, newR, newT, pts)

    def convert_pts_relative(self, target, newR, newT, pts) : 
        reproject = target.K.dot(newR.dot(pts) + newT)
        #reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
        print("convert_pts_releative.. ", reproject)
        K_inv = np.linalg.inv(target.K)      
        print(".. " , K_inv.dot(reproject).T)          

        return reproject

    def convert_pts(self, target):
        for normal in self.normal:        
            normal2 = self.cart2hom(normal)
            print("normal .. " , normal2)            
            reproject = np.dot(target.P, normal2)
            reproject /= reproject[2]
            print("reproject .. 1  ",  reproject)
            normal = normal.reshape((3,1))
            reproject2 = target.K.dot(target.R.dot(normal) + target.t)
            reproject2 = cv2.convertPointsFromHomogeneous(reproject2.T)[:, 0, :].T
            print("reporject.. 2 ", reproject2)
            target.normal.append(reproject)

        for pt in self.world.world_points:
            pt = pt.reshape((3,1))
            # K_inv = np.linalg.inv(target.K)
            # pt = K_inv.dot(pt) 
            reproject = (target.R.T.dot(pt) + target.t)
            eproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
            # print("4point .. " , pt)
            # print("reproject .. " ,reproject)
            target.pts.append(reproject)
    
    def convert_pts2(self, target):
        pts = np.array([[1168.0, 1576.0, 0.0]])
        pts = pts.reshape((3,1))         
        K_inv = np.linalg.inv(target.K)
        pts = K_inv.dot(pts)  
        distcoeff = np.array([[0., 0., 0., 0.]])
        print("convert_pts2 .. start ")
        print(target.Rvec)

        projectvector, _ = cv2.projectPoints(pts, target.Rvec, target.t, target.K, distcoeff)
        print("convert_pts2 .. " , projectvector)
        print("convert_pts2 .. " , target.K.dot(projectvector))

    def convert_pts3(self, target) :
        pts = np.array([[1470.0, 0.0, -630.0]])
        pts = pts.reshape((3, 1))
        K_inv = np.linalg.inv(target.K)
        #pts = K_inv.dot(pts)
        pts = np.vstack([pts, 1])
        reproject = np.dot(target.P, pts)        
        print("convert_pt3.. " , K_inv.dot(reproject).T)


    def convert_center(self, target) :
        pass


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
            