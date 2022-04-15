import os
import sys
import numpy as np
import cv2
import logging
from world import *
from util import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world = world
        self.normal = [[50, 50, 0], [50, 50, -50]]
        print("Adjust init .. ", world.world_points)
    
    def get_initial_cp(self):
        if self.calib_type == '3D' : 
            pts = [[2749, 785], [884, 1170], [1718, 1541], [3650, 1069]] # ncaa 
        else :
            pts = [[2749, 785], [884, 1170]] # 2D는 2point?

        return pts

    def convert_pts(self, target):
        for normal in self.normal:
            reproject = target.K.dot(target.R.dot(normal) + target.t)
            reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
            print(" normal .. " , normal)
            print("reproject .. ",  reproject)
            target.normal.append(reproject)

        for pt in self.world.world_points:
            reproject = target.K.dot(target.R.dot(pt) + target.t)
            reproject = cv2.convertPointsFromHomogeneous(reproject.T)[:, 0, :].T
            print("4point .. " , pt)
            print("reproject .. " ,reproject)
            target.pts.append(reproject)
    
    def conver_center(self, target) :
        pass


    def write_file(self):
        pass