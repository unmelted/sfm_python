import os
from re import I
import sys
import glob
import numpy as np
import logging
from sfm import *

from camera import *
from pair import *
from view import *
from visualize import *
from adjust import *
from world import *


class Group(object):

    def __init__ (self):
        print("Group Init")
        self.cameras = []
        self.views = []
        self.pairs = None
        self.matches = {}        
        self.K = None
        self.sfm = None
        self.world = World()
        self.adjust = None

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
            tcam = Camera(image_name, root_path, self.K, feature_path=feature_path)
            self.cameras.append(tcam)
            self.views.append(tcam.view)

        self.pairs = Pair.create_pair(self.cameras)
        self.sfm = SFM(self.views, self.pairs)

    def run_sfm(self) :
        baseline = True
        for pair in self.pairs :
            pair_obj = self.pairs[pair]
            print("pair_obj ------ " , pair)
            j  = 0
            if baseline == True:
                self.sfm.compute_pose(pair_obj, baseline)
                baseline = False
                logging.info("Mean reprojection error for 1 image is %f", self.sfm.errors[0])
                logging.info("Mean reprojection error for 2 images is %f", self.sfm.errors[1])
                j = 2

            else :
                self.sfm.compute_pose(pair_obj, baseline)
                logging.info("Mean reprojection error for images is %f ", self.sfm.errors[j])
                j += 1

            self.sfm.plot_points()

    def generate_refpoints(self) :
        self.adjust = Adjust(self.world.get_world())
        is_first = True

        for i in enumerate(self.cameras):
            if (is_first == True): 
                self.cameras[i].pts = self.adjust.get_first_cp()
                self.adjust.convert_pts(self.cameras[i])
            # else : 
            #     self.adjust.convert_pts(self.cameras[i-1], self.cameras[i])

    def visualize_group(self) :
        print("visualize camera in group")
