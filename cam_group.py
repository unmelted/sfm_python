import os
from re import I
import sys
import glob
import numpy as np
import logging

from camera import *
from pair import *
from view import *
from visualize import *


class Group(object):

    def __init__ (self):
        print("Group Init")
        self.cameras = []
        self.views = []
        self.points_3D = np.zeros((0, 3))  # reconstructed 3D points
        self.point_map = {} # key : view name, value : match inliers
        self.pairs = None
        self.K = None

    def create_group(self, root_path, image_format='jpg'):
        """Loops through the images and creates an array of views"""

        feature_path = False

        # if features directory exists, the feature files are read from there
        logging.info("Created features directory")
        if os.path.exists(os.path.join(root_path, 'features')):
            feature_path = True

        print(root_path)
        image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + image_format)))

        logging.info("Computing features")
        print(image_names)
        self.K = np.loadtxt(os.path.join(root_path, 'images', 'K.txt'))

        for image_name in image_names:
            self.cameras.append(Camera(image_name, root_path, self.K, feature_path=feature_path))

        self.pairs = Pair.create_pair(self.cameras)
        print(self.pairs)

    def run_sfm(self) :
        baseline = True
        for pair in self.pairs :
            pair_obj = self.pairs[pair]
            print(" pair  ", pair)
            print("pair_obj " , pair_obj)
            if baseline == True:
                self.point_map, self.points_3D = pair_obj.run_sfm(baseline, self.point_map, self.points_3D)
                baseline = False
            else :
                self.point_map, self.point_3D = pair_obj.run_sfm(baseline, self.point_map, self.points_3D)


    def visualize_group(self) :
        print("visualize camera in group")
