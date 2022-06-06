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
from db_manager import *
from colmap_proc import *

class Group(object):

    def __init__ (self):
        self.cameras = []
        self.views = []
        self.pairs = None
        self.matches = {}        
        self.K = None
        self.x_lambda = np.zeros((2), dtype=np.float64)
        self.y_lambda = np.zeros((2), dtype=np.float64)
        self.sfm = None
        self.world = World()
        self.adjust = None
        self.limit = 0

        self.root_path = None
        self.answer = {}
        self.db = None
        self.colmap = None
        self.ext = None

    def create_group_colmap(self, root_path, mode) :
        self.root_path = root_path        
        self.world.get_world()
        self.adjust = Adjust(self.world)
        self.colmap = Colmap(self.root_path)

        self.ext = check_image_format(self.root_path)
        image_names = sorted(glob.glob(os.path.join(self.root_path, 'images', '*.' + self.ext)))
        if len(image_names) < 1 : 
            logging.error("can't read images . ")
            return -1

        index = 0

        for image_name in image_names:
            tcam = Camera(image_name, self.root_path, self.K, feature_path='colmap')
            self.cameras.append(tcam)
            self.views.append(tcam.view)
            if self.limit != 0 and index == self.limit :
                break 

            index += 1            

        if mode == 'visualize' :
            return 0

        result = self.colmap.recon_command(False)
        if result < 0 :
            print("recon command error : ", result)
            return result 

        result = self.colmap.cvt_colmap_model(self.ext)

        return result

    def create_group(self, root_path):
        """Loops through the images and creates an array of views"""
        self.world.get_world()
        self.adjust = Adjust(self.world)

        feature_path = False
        self.root_path = root_path
        if os.path.exists(os.path.join(root_path, 'features')):
            feature_path = True

        print(root_path)
        self.ext = check_image_format(self.root_path)        
        image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + self.ext)))
        if len(image_names) < 1 : 
            logging.error("can't read images . ")
            return -1

        print(image_names)
        self.K = np.loadtxt(os.path.join(root_path, 'images', 'K.txt'))
        index = 0

        for image_name in image_names:
            tcam = Camera(image_name, root_path, self.K, 0, feature_path=feature_path)
            self.cameras.append(tcam)
            self.views.append(tcam.view)
            if self.limit != 0 and index == self.limit :
                break 

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

    def read_cameras(self, mode='colmap'):
        if mode == 'colmap' :
            if self.colmap == None :
                print("there is no colmap data")                
                return -10
           
            result = self.colmap.read_colmap_cameras(self.cameras)

        else :             
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
                # homo_points = pair_obj.find_homography_from_points()
                # homo_pose = pair_obj.find_homography_from_disp()
                baseline = False
                logging.info("Mean reprojection error for 1 image is %f", self.sfm.errors[0])
                logging.info("Mean reprojection error for 2 images is %f", self.sfm.errors[1])
                j = 2

            else :
                self.sfm.compute_pose(pair_obj, baseline)
                logging.info("Mean reprojection error for images is %f ", self.sfm.errors[j])
                j += 1

            self.sfm.save_3d_points()

            if self.limit != 0 and j-1 == self.limit :
                break

        self.write_cameras()

    def check_pair(self) :
        for i, pair in enumerate(self.pairs):
            pair_obj = self.pairs[pair]
            print("Pair name ", pair_obj.image_name1, pair_obj.image_name2)
            pair_obj.check_points_3d()
            break

    def generate_points(self, mode='colmap') :
        filename = os.path.join(self.root_path, 'images', 'UserPointData.pts')
        #not calculate_real_error mode 
        self.answer = import_answer(filename, 2)

        if mode == 'colmap' :
            for i, cam in enumerate(self.cameras):
                if i == 0 or i == 1 :
                    viewname = self.cameras[i].view.name[:-4]
                    if self.ext == 'tiff':
                        viewname = self.cameras[i].view.name[:-8]
                    
                    pts = self.answer[viewname]
                    print(" generate_points name {} \n {} ".format(self.cameras[i].view.name, pts))
                    cam.pts = pts
                
                if i > 1 : 
                    self.adjust.reproject_3D(self.cameras[i - 1], self.cameras[i])
                    # if i == 2 : 
                    #     self.adjust.find_homography(self.answer[self.cameras[i].view.name], self.cameras[i])
                self.adjust.backprojection(self.cameras[i])

                if i > 0 :
                    if i == 1 : 
                        self.adjust.make_3D(self.cameras[i - 1], self.cameras[i])
                    else :
                        self.cameras[i].pts_3D = self.cameras[i - 1].pts_3D
                    # 
                    # self.adjust.reproject_3D_only(self.cameras[i -1], self.cameras[i])                
                    # self.adjust.check_normal(self.cameras[i])
                    # self.adjust.backprojection(self.cameras[i - 1], self.cameras[i])

        else : 
            for i, cam in enumerate(self.cameras):
                if i == 0 or i == 1 :
                    viewname = self.cameras[i].view.name[:-7]
                    if self.ext == 'tiff':
                        viewname = self.cameras[i].view.name[:-8]

                    pts = self.answer[viewname]
                    print(" generate_points name {} \n {} ".format(self.cameras[i].view.name, pts))
                    cam.pts = pts
                
                if i > 1 : 
                    self.adjust.reproject_3D(self.cameras[i - 1], self.cameras[i])
                    # if i == 2 : 
                    #     self.adjust.find_homography(self.answer[self.cameras[i].view.name], self.cameras[i])
                self.adjust.backprojection(self.cameras[i])

                if i > 0 :
                    # if i == 1 : 
                    self.adjust.make_3D(self.cameras[i - 1], self.cameras[i])
                    # else :
                    #     self.cameras[i].pts_3D = self.cameras[i - 1].pts_3D
                    # # 
                    # self.adjust.reproject_3D_only(self.cameras[i -1], self.cameras[i])                
                    # self.adjust.check_normal(self.cameras[i])
                    # self.adjust.backprojection(self.cameras[i - 1], self.cameras[i])

                if self.limit != 0 and i == self.limit :
                    break                


    def calculate_real_error(self) :

        max = 0
        min = 10000
        ave = 0
        t_error = 0

        for i in range(len(self.cameras)) :
            if i < 2 : 
                continue
            s_error = 0
            viewname = self.cameras[i].view.name[:-4]
            if self.ext == 'tiff':
                viewname = self.cameras[i].view.name[:-8]

            print("name : ", self.cameras[i].view.name, viewname)            
            gt = self.answer[viewname]

            for j in range(self.cameras[i].pts.shape[0]) :
                # pt_3d = self.cameras[i].pts_3D[j, :]
                pt_2d = self.cameras[i].pts[j, :]
                gt_pt = gt[j, :]
                terr = np.linalg.norm(pt_2d - gt_pt)
                # print("3d {} pts {} : answer {} : err {} ".format(pt_3d, pt_2d, gt_pt, terr))
                print("pts {} : answer {} : err {} ".format(pt_2d, gt_pt, terr))
                if terr > max : 
                    max = terr

                if terr < min : 
                    min = terr

                s_error += terr
                t_error += terr

            print('scene err : ', s_error)
            if self.limit != 0 and i == self.limit :
                break

        ave = t_error / len(self.cameras)
        print("total real error : {} ave {} max {} min {} ".format(t_error, ave, max, min))

    def visualize(self, mode='colmap') :
        if mode == 'colmap' :
            self.colmap.visualize_colmap_model()
        else :         
            plot_scene(self.cameras, self.sfm, mode)


    def export(self) :
        export_points(self, 'dm')
        save_point_image(self)        