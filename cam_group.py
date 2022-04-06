import os
from re import I
import sys
import glob
import numpy as np
import logging
import camera
from view import *

class Group(object):

    def __init__ (self):
        print("Group Init")

    def create_group(root_path, image_format='jpg'):
        """Loops through the images and creates an array of views"""

        feature_path = False

        # if features directory exists, the feature files are read from there
        logging.info("Created features directory")
        if os.path.exists(os.path.join(root_path, 'features')):
            feature_path = True

        image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + image_format)))

        logging.info("Computing features")
        print(image_names)
        views = []
       
        for image_name in image_names:
            print(image_name, root_path)
            views.append(View(image_name, root_path, feature_path=feature_path))

        return views
