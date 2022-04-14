import os
import sys
import cv2
import logging
from world import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world = world
        self.world_points = []  # x, y, 4 points
        

    def get_first_cp(self):
        pts = [[2749, 785], [884, 1170], [1718, 1541], [3650, 1069]]
        return pts

    def convert_pts(self, cameras):
        pass

    def write_file(self):
        pass