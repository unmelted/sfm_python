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

        self.K = np.zeros((3, 3))
        self.focal = 0
        self.prj_crns = np.empty((4, 2), dtype=np.float64)        

        self.adj_image = None
        self.adj_pts3d = None
        
    def convert_focal2px(self) :
        focalPx = 0
        sensor_size = 17.30
        if self.image_width == 3840 :
            sensor_size /= 1.35

        focalPx = (self.focal / sensor_size) * self.image_width
        return focalPx
    
    def set_extra_info(self, width, height, type):
        self.view.image_width = width
        self.view.image_height = height
        self.image_width = width
        self.image_height = height

        if type == '3D': 
            focalPx = self.convert_focal2px()
            self.K[0][0] = focalPx
            self.K[0][1] = 0
            self.K[0][2] = self.image_width / 2
            self.K[1][1] = focalPx
            self.K[1][2] = self.image_height / 2
            self.K[2][2] = 1
