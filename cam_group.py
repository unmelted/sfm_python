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
        self.limit = 0

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

    def check_pair(self) :
        for i, pair in enumerate(self.pairs):
            pair_obj = self.pairs[pair]
            print("Pair name ", pair_obj.image_name1, pair_obj.image_name2)
            pair_obj.check_points_3d()
            break

    def generate_points(self) :
        self.world.get_world()
        self.adjust = Adjust(self.world)
        first_index = 0
        #self.cameras[first_index].pts = self.adjust.get_initial_cp()

        #self.check_pair()


        for i, cam in enumerate(self.cameras):
            cam.calculate_p()
            #self.adjust.get_camera_pos(cam)
            if i == 0 :
                cam.pts = np.array([1208.0, 1550.0, 1.0])
            elif i == 1 : 
                cam.pts = np.array([1162.0, 1579.0, 1.0])
                print("check shape : ", cam.pts.shape)
            if i > 1 : 
                self.adjust.reproject_3D(self.cameras[i - 1], self.cameras[i])

            if i > 0 :
                self.adjust.make_3D(self.cameras[i - 1], self.cameras[i])


            if self.limit != 0 and i == self.limit :
                break                

            continue
            if i == 0 :
                cam.pts = np.array([[-1208, -1550, 0]])
                self.adjust.convert_pts3(cam.pts, cam)                
                # self.adjust.convert_pts5(cam.pts, cam)                                
            elif i > 0 :
                self.adjust.convert_pts3(self.cameras[i -1].pts, cam)
                # self.adjust.convert_pts5(cam.pts, cam)                                
                self.adjust.get_camera_relative2(self.cameras[i -1], cam)


    def calculate_real_error(self) :
        answer = np.array([[1208.0, 1550.0], #3085
                         [1162.0, 1579.0], #3086
                         [1150.0, 1538.0], #3087
                         [1115.0, 1527.0], #3088
                         [1080.0, 1520.0], #3089
                         [1052.0, 1488.0], #3090
                         [1039.0, 1446.0], #3091
                         [1001.0, 1427.0], #3092
                         [953.0, 1392.0], #3093
                         [933.0, 1397.0], #3094
                         [901.0, 1373.0], #3095
        ])
        max = 0
        min = 10000
        error = 0
        for i in range(len(self.cameras)) :
            if i < 2 : 
                continue
            tg = self.cameras[i].pts[:-1].reshape((2))
            #print(" .. ", tg, tg.shape)
            print("i {} pts {} - answer {}".format(i, tg, answer[i, :]))
            terr = np.linalg.norm(tg - answer[i, :])
            print("terr : ", terr)
            if terr > max : 
                max = terr

            if terr < min : 
                min = terr

            error += terr

        print("total real error : {} max {} min {} ".format(error, max, min))


    def visualize(self) :
        print("visualize camera in  group")        
        plot_cameras(self.cameras, self.limit)
        #plot_pointmap(self.sfm)
