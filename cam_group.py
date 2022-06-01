import os
from re import I
import sys
import subprocess
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

    def create_group_colmap(self, root_path, image_format='png') :
        self.root_path = root_path        
        self.world.get_world()
        self.adjust = Adjust(self.world)
        self.db = DbManager(self.root_path)

        print(root_path)
        image_names = sorted(glob.glob(os.path.join(self.root_path, 'images', '*.' + image_format)))
        if len(image_names) < 1 : 
            logging.error("can't read images . ")
            return -1

        print(image_names)
        index = 0

        for image_name in image_names:
            tcam = Camera(image_name, self.root_path, self.K, feature_path='colmap')
            self.cameras.append(tcam)
            self.views.append(tcam.view)
            if self.limit != 0 and index == self.limit :
                break 

            index += 1            

        print("recall_colmap")
        colmap_cmd = import_colmap_cmd_json()
        result = subprocess.run([colmap_cmd["auto_recon_cmd"], colmap_cmd["auto_recon_param1"], self.root_path, colmap_cmd["auto_recon_param2"], os.path.join(self.root_path, 'images')], capture_output=True)
        print(result)

        return 0


    def create_group(self, root_path, image_format='png'):
        """Loops through the images and creates an array of views"""
        self.world.get_world()
        self.adjust = Adjust(self.world)

        feature_path = False
        self.root_path = root_path
        if os.path.exists(os.path.join(root_path, 'features')):
            feature_path = True

        print(root_path)
        image_names = sorted(glob.glob(os.path.join(root_path, 'images', '*.' + image_format)))
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

    def read_cameras(self, mode):
        if mode == 'coalmap' :
            print("read cameras from colmap..")
            return 0
            
            cam_db = self.db.read_cameras()
            for i, cam in enumerate(self.cameras):
                cam.P = cam_db[i]
                cam.EX = cam_db[i]
                cam.K = cam_db[i]
                cam.R = cam_db[i]
                cam.t = cam_db[i]
                cam.F = cam_db[i]
                cam.Rvec = cam_db[i]

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

    def calculate_lambda(self, c0, c1) :
        print("calculate_scale..")

        gt = self.answer[c1.view.name]        
        ''' self reproject
        input_pt1 = c1.pts_3D[0, :]
        input_pt1 = np.hstack([input_pt1, 1]).reshape((4,1))
        result_pt1 = c1.project(input_pt1, 0, 0)
        input_pt2 = c1.pts_3D[2, :]
        input_pt2 = np.hstack([input_pt2, 1]).reshape((4,1))
        result_pt2 = c1.project(input_pt2, 0, 0)
        '''

        # x : X 
        a = np.array([ [c0.pts_3D[0, 2], c1.pts[0, 0]], 
                    [c0.pts_3D[2, 2], c1.pts[2, 0]]
                    ], dtype=np.float64)
        b = np.array([gt[0, 0], gt[2, 0]], dtype=np.float64)
        print("solve.. x --- ")        
        # print(a)
        # print(b)

        self.x_lambda = np.linalg.solve(a, b)
        print(self.x_lambda)
        
        a = np.array([ [c0.pts_3D[0, 2], c1.pts[0, 1]], 
                    [c0.pts_3D[2, 2], c1.pts[2, 1]  ]], dtype=np.float64)
        b = np.array([gt[0, 1], gt[2, 1]], dtype=np.float64)
        print("solve.. y --- ")
        # print(a)
        # print(b)

        self.y_lambda = np.linalg.solve(a, b)
        print(self.y_lambda)


        ''' x : z : X 
        a = np.array([ [c0.pts_3D[0, 0], c0.pts_3D[0, 2], c1.pts[0, 0]], 
                    [c0.pts_3D[2, 0], c0.pts_3D[2, 2], c1.pts[2, 0]], 
                    [c0.pts_3D[3, 0], c0.pts_3D[3, 2], c1.pts[3, 0]] ], dtype=np.float64)
        b = np.array([gt[0, 0], gt[2, 0], gt[3, 0]], dtype=np.float64)
        print("solve.. x --- ")        
        # print(a)
        # print(b)

        self.x_lambda = np.linalg.solve(a, b)
        print(self.x_lambda)
        
        a = np.array([ [c0.pts_3D[0, 1], c0.pts_3D[0, 2], c1.pts[0, 1]], 
                    [c0.pts_3D[2, 1], c0.pts_3D[2, 2], c1.pts[2, 1]],
                    [c0.pts_3D[3, 1], c0.pts_3D[3, 2], c1.pts[3, 1]] ], dtype=np.float64)
        b = np.array([gt[0, 1], gt[2, 1], gt[3, 1]], dtype=np.float64)
        print("solve.. y --- ")
        # print(a)
        # print(b)

        self.y_lambda = np.linalg.solve(a, b)
        print(self.y_lambda)
        '''


    def generate_points(self) :
        first_index = 0
        #self.check_pair()

        filename = os.path.join(self.root_path, 'images', 'answer.pts')
        self.answer = import_answer(filename, self.limit)

        for i, cam in enumerate(self.cameras):
            # if i == 5 :
            #     self.cameras[i].K = self.cameras[i].K - 20
            #     self.cameras[i].calculate_p()

            if i == 0 or i == 1 :
                pts = self.answer[self.cameras[i].view.name]
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
                    # self.cameras[i].pts_3D = self.cameras[i - 1].pts_3D
                # 
                # self.adjust.reproject_3D_only(self.cameras[i -1], self.cameras[i])                
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
        # plot_pointmap(self.sfm)    


    def export(self) :
        export_points(self)
        save_point_image(self)        