import os
import sys
import numpy as np
import mathutil

class Camera(object):
    """ Class for representing pin-hole camera """

    def __init__(self, image_name):
        self.image = None
        self.id = None
        self.index = None
        self.P = None     # camera matrix
        self.EX = None
        self.R = np.zeros((3, 3), dtype=np.float64)     # rotation
        self.t = np.zeros((3, 1), dtype=np.float64)     # translation
        self.F = np.zeros((3, 3), dtype=np.float64)
        self.E = np.zeros((3, 3), dtype=np.float64)
        self.Rvec = np.zeros((3, 1), dtype=np.float64)
        self.c = None  # camera center

        ''' related adjust value '''
        self.pts = np.empty((0, 2), dtype=np.float64)
        self.pts_3d = np.empty((4, 2), dtype=np.float64)
        self.pts_2d = np.empty((2, 2), dtype=np.float64)
        self.pts_back = np.empty((0, 3), dtype=np.float64)
        self.pts_extra = np.empty((2, 2), dtype=np.float64)

        self.center = []  # tracking center
        self.rod_length = 0
        self.radian = 0
        self.degree = 0
        self.scale = 0
        self.adjust_x = 0
        self.adjust_y = 0
        self.rotate_x = 0
        self.rotate_y = 0

        self.adjust_file = None

        class view():
            image_width = 0
            image_height = 0
            name = None

        self.view = view()
        self.view.image_width = 0.0
        self.view.image_height = 0.0
        self.view.name = image_name
        self.name = self.view.name
        self.image_width = 0
        self.image_height = 0