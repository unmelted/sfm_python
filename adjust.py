import os
import sys
import cv2
import logging
from world import *

class Adjust(object):

    def __init__(self, world):
        self.calib_type = None  # 2d, 3d
        self.world_type = None  # stadium
        self.event = None       # event (sports category)
        self.world_points = []  # x, y, 4 points
        

    def convert_pts(self, cameras):
        pass

    def write_file(self):
        pass