import os
import sys
import numpy as np
import cv2
import logging
import json
from world import *
from util import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world = world
        scale = 100
        self.normal = np.array([[50/scale, 50/scale, 0], [50/scale, 50/scale, 50/scale]])
    
    def get_initial_cp(self):
        if self.calib_type == '3D' : 
            pts = [[708, 183], [120, 1614], [2766, 1485], [2091, 144]] # ncaa 
        else :
            pts = [[2749, 785], [884, 1170]] # 2D는 2point?

        return pts

    def convert_pts(self, target):
        for normal in self.normal:        
            normal = normal.reshape((3,1))    
            # K_inv = np.linalg.inv(target.K)
            # normal = K_inv.dot(normal)            
            reproject = target.K.dot(target.R.dot(normal) + target.t)
            reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T           
            print("normal .. " , normal)
            print("reproject .. ",  reproject)
            target.normal.append(reproject)

        for pt in self.world.world_points:
            pt = pt.reshape((3,1))
            # K_inv = np.linalg.inv(target.K)
            # pt = K_inv.dot(pt) 
            reproject = target.K.dot(target.R.dot(pt) + target.t)
            reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
            # print("4point .. " , pt)
            # print("reproject .. " ,reproject)
            target.pts.append(reproject)
    
    def conver_center(self, target) :
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
            