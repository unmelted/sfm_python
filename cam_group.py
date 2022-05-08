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
from extn_util import * 

class Group(object):

    def __init__ (self):
        self.cameras = []
        self.views = []
        self.pairs = None
        self.matches = {}        
        self.K = None
        # self.llambda = np.zeros((3,3), dtype=float)
        self.x_lambda = 0
        self.y_lambda = 0
        self.sfm = None
        self.world = World()
        self.adjust = None
        self.limit = 4

        self.root_path = None
        self.answer = {}

    def create_group(self, root_path, image_format='jpg'):
        """Loops through the images and creates an array of views"""
        self.world.get_world()
        self.adjust = Adjust(self.world)

        feature_path = False
        self.root_path = root_path

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
        index = 0

        for image_name in image_names:
            if(index == 0): 
                tcam = Camera(image_name, root_path, self.K, 1, feature_path=feature_path)
            elif (index == 1) :
                tcam = Camera(image_name, root_path, self.K, 2, feature_path=feature_path)
            else:                 
                tcam = Camera(image_name, root_path, self.K, 0, feature_path=feature_path)
            self.cameras.append(tcam)
            self.views.append(tcam.view)
            index += 1

        self.pairs = Pair.create_pair(self.cameras)
        self.sfm = SFM(self.views, self.pairs)

        return 0

    def write_cameras(self):
        if not os.path.exists(os.path.join(self.root_path, 'cameras')):
            os.makedirs(os.path.join(self.root_path, 'cameras'))

        temp_array = []
        for i, cam in enumerate(self.cameras):
            temp = (cam.P, cam.EX, cam.K, cam.R, cam.t, cam.F, cam.Rvec)
            cam_file = open(os.path.join(self.root_path, 'cameras', cam.view.name + '.pkl'), 'wb')
            pickle.dump(temp, cam_file)
            cam_file.close()

            if self.limit != 0 and i == self.limit :
                break



    def read_cameras(self):
            for i, cam in enumerate(self.cameras):
                try:                
                    tcon = pickle.load(
                        open(
                            os.path.join(self.root_path, 'cameras', cam.view.name + '.pkl'),
                            "rb"
                        )
                    )
                except FileNotFoundError:
                    logging.error("Pkl file not found for camera %s. Computing from scratch", cam.view.name)
                    break

                print("read from camera file : ", cam.view.name)
                print(tcon)
                cam.P = tcon[0]
                cam.EX = tcon[1]
                cam.K = tcon[2]
                cam.R = tcon[3]
                cam.t = tcon[4]
                cam.F = tcon[5]
                cam.Rvec = tcon[6]

                if self.limit != 0 and i == self.limit :
                    break


    
    def run_sfm(self) :
        baseline = True
        j  = 0          

        for pair in self.pairs :
            pair_obj = self.pairs[pair]
            print("pair_obj ------ " , pair)

            if baseline == True:
                self.sfm.compute_pose(pair_obj, baseline)
                homo_points = pair_obj.find_homography_from_points()
                homo_pose = pair_obj.find_homography_from_disp()
                baseline = False
                logging.info("Mean reprojection error for 1 image is %f", self.sfm.errors[0])
                logging.info("Mean reprojection error for 2 images is %f", self.sfm.errors[1])
                j = 2

            else :
                self.sfm.compute_pose(pair_obj, baseline)
                logging.info("Mean reprojection error for images is %f ", self.sfm.errors[j])
                j += 1

            self.sfm.plot_points()

            if self.limit != 0 and j-1 == self.limit :
                break

        self.write_cameras()

    def check_pair(self) :
        for i, pair in enumerate(self.pairs):
            pair_obj = self.pairs[pair]
            print("Pair name ", pair_obj.image_name1, pair_obj.image_name2)
            pair_obj.check_points_3d()
            break

    def calculate_scale(self, c0, c1) :
        print("calculate_scale..")

        x_lambda = 0
        y_lambda = 0
        gt = self.answer[c1.view.name]        

        a = np.array([ [c1.pts_3D[0, 2], c1.pts[0, 0]], [c1.pts_3D[2, 2], c1.pts[2, 0]] ], dtype=np.float64)
        b = np.array([gt[0, 0], gt[2, 0]], dtype=np.float64)
        print(a)
        print(b)

        x = np.linalg.solve(a, b)
        print(x)


        return x_lambda, y_lambda

    def generate_points(self) :
        first_index = 0
        #self.check_pair()

        filename = os.path.join(self.root_path, 'images', 'answer.pts')
        self.answer = import_answer(filename)

        for i, cam in enumerate(self.cameras):

            if i == 0 or i == 1 :
                pts = self.answer[self.cameras[i].view.name]
                print(" generate_points name {} \n {} ".format(self.cameras[i].view.name, pts))
                cam.pts = pts

            if i > 1 : 
                self.adjust.reproject_3D(self.cameras[i - 1], self.cameras[i], self.x_lambda, self.y_lambda)

            if i > 0 :
                self.adjust.make_3D(self.cameras[i - 1], self.cameras[i])
                if i == 1 :
                    self.calculate_scale(self.cameras[i - 1], self.cameras[i])
                # self.adjust.check_normal(self.cameras[i])
                # self.adjust.backprojection(self.cameras[i - 1], self.cameras[i])

            if self.limit != 0 and i == self.limit :
                break                


    def calculate_real_error(self) :

        max = 0
        min = 10000
        t_error = 0

        for i in range(len(self.cameras)) :
            if i < 2 : 
                continue
            s_error = 0
            print("name : ", self.cameras[i].view.name)
            gt = self.answer[self.cameras[i].view.name]

            for j in range(self.cameras[i].pts.shape[0]) :
                pt_3d = self.cameras[i].pts_3D[j, :]
                pt_2d = self.cameras[i].pts[j, :]
                gt_pt = gt[j, :]
                terr = np.linalg.norm(pt_2d - gt_pt)
                print("3d {} pts {} : answer {} : err {} ".format(pt_3d, pt_2d, gt_pt, terr))

                if terr > max : 
                    max = terr

                if terr < min : 
                    min = terr

                s_error += terr
                t_error += terr

            print('scene err : ', s_error)
            if self.limit != 0 and i == self.limit :
                break


        print("total real error : {} max {} min {} ".format(t_error, max, min))


    def visualize(self) :
        print("visualize camera in  group")        
        plot_cameras(self.cameras, self.limit)
        #plot_pointmap(self.sfm)

    def export(self) :
        export_points(self)
        save_point_image(self)        