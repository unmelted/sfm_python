import os
from re import I
import sys
import glob
import numpy as np
import logging

from camera import *
from match import *
from view import *
from sfm import *
from visualize import *



class Group(object):

    def __init__ (self):
        print("Group Init")
        self.cameras= []
        self.views = []
        self.matches = None
        self.sfm = None
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
      
        for image_name in image_names:
            self.cameras.append(Camera(image_name, root_path, feature_path=feature_path))
#            self.views.append(View(image_name, root_path, feature_path=feature_path))

        self.matches = create_matches(self.views)
        self.K = np.loadtxt(os.path.join(root_path, 'images', 'K.txt'))
        self.sfm = SFM(self.views, self.matches, self.K)

    def run_sfm(self) :
        self.sfm.reconstruct()

    def visualize_group(self) :

        pass