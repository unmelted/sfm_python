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
        self.cameras = []
        self.views = []
        self.pairs = None
        self.matches = {}        
        self.K = None
        self.sfm = None
        self.world = World()
        self.adjust = None
        self.limit = 4

    def create_group(self, root_path, image_format='jpg'):
        """Loops through the images and creates an array of views"""

        feature_path = False

        # if features directory exists, the feature files are read from there
        logging.info("Created features directory")
        if os.path.exists(os.path.join(root_path, 'features')):
            feature_path = True

        print(root_path)
        image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + image_format)))
        if len(image_names) < 1 : 
            logging.error("can't read images . ")
            return -1

        logging.info("Computing features")
        print(image_names)
        self.K = np.loadtxt(os.path.join(root_path, 'images', 'K.txt'))

        for image_name in image_names:
            tcam = Camera(image_name, root_path, self.K, feature_path=feature_path)
            self.cameras.append(tcam)
            self.views.append(tcam.view)

        self.pairs = Pair.create_pair(self.cameras)
        self.sfm = SFM(self.views, self.pairs)

        return 0

    def run_sfm(self) :
        baseline = True
        j  = 0          

        for pair in self.pairs :
            pair_obj = self.pairs[pair]
            print("pair_obj ------ " , pair)

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

            if self.limit != 0 and j == self.limit :
                break

    def generate_points(self) :
        self.world.get_world()
        self.adjust = Adjust(self.world)
        first_index = 0
        #self.cameras[first_index].pts = self.adjust.get_initial_cp()
        j  = 0   
        
        for i, cam in enumerate(self.cameras):
            cam.calculate_p()
            #self.adjust.get_camera_pos(cam)
            print("-- index ", i, j)

            if j == 0 :
                cam.pts = np.array([[1208.0, 0, -1550.0]])
            elif j > 0 :
                self.adjust.convert_pts3(self.cameras[j -1].pts, cam)
                self.adjust.get_camera_relative(self.cameras[j -1], cam)
            
            j += 1

            if self.limit != 0 and j == self.limit :
                break

    def visualize(self) :
        print("visualize camera in  group")        
        plot_cameras(self.cameras, self.limit)
        #plot_pointmap(self.sfm)
