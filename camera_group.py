import os
from re import I
import sys
import glob
import numpy as np

from logger import Logger as l
from definition import DEFINITION as df
from camera import *
from pair import *
from view import *
from visualize import *
from adjust import *
from world import *
from extn_util import * 
from intrn_util import *
from colmap_proc import *
from sfm import *


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
        self.run_mode = None
        self.answer = {}
        self.db = None
        self.colmap = None
        self.ext = None

    def create_group(self, root_path, run_mode, list_from='pts_file'):
        self.root_path = root_path
        self.run_mode = run_mode

        l.get().w.error("create group run_mode : {} list_from {}".format(self.run_mode, list_from))        
        result = self.prepare_camera_list(list_from)
        if result < 0 :
            return result

        if self.run_mode == 'colmap':
            self.colmap = Colmap(self.root_path)            
        else :
            self.K = np.loadtxt(os.path.join(self.root_path, 'images', 'K.txt'))
            self.pairs = Pair.create_pair(self.cameras)
            self.sfm = SFM(self.views, self.pairs)

        return 0

    def prepare_camera_list(self, list_from, group_id = 'Group1'):
        self.world.get_world()
        self.adjust = Adjust(self.world)
        self.ext = check_image_format(self.root_path)        
        image_names = []

        if list_from == 'image_folder' : 
            l.get().w.error("image folder ext : {} ".format(self.ext))
            image_names = sorted(glob.glob(os.path.join(self.root_path, 'images', '*.' + self.ext)))
            if len(image_names) < 2: 
                return -107

        elif list_from == 'pts_file' :
            from_path = os.path.join(self.root_path, 'images')
            result, image_names = get_info(from_path, group_id, self.ext)
            l.get().w.debug('Create camera list from pts file result : {} count : {}'.format(result, len(image_names)))
            if result < 0 :
                return result

        elif list_from == 'colmap_db' :
            file_names = sorted(glob.glob(os.path.join(self.root_path, 'images', '*.' + self.ext)))            
            t_colmap = Colmap(self.root_path)
            image_names = t_colmap.import_colmap_cameras(file_names)

        index = 0
        for image_name in image_names:
            tcam = Camera(image_name, self.root_path, self.K, self.run_mode)
            self.cameras.append(tcam)
            self.views.append(tcam.view)
            if self.limit != 0 and index == self.limit :
                break 

            index += 1            

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

    def read_cameras(self, mode ='colmap'):
        if mode == 'colmap' :
            if self.colmap == None :
                logging.error("there is no colmap data")                
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
                    logging.error("Pkl file not found for camera %s. Computing from scratch {} ".format(cam.view.name))
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
        return 0
    
    def run_sfm(self) :
        if self.run_mode == 'colmap' :
            result = self.colmap.recon_command(False)
            if result < 0 :
                print("recon command error : ", result)
                return result 

            result = self.colmap.cvt_colmap_model(self.ext)
            return result

        elif self.run_mode == 'off' : 
            baseline = True
            j  = 0          

            for pair in self.pairs :
                pair_obj = self.pairs[pair]

                if baseline == True:
                    self.sfm.compute_pose(pair_obj, baseline)
                    baseline = False
                    l.get().w.debug("Mean reprojection error for 1 image is {}".format(self.sfm.errors[0]))
                    l.get().w.debug("Mean reprojection error for 2 images is {}".format(self.sfm.errors[1]))
                    j = 2

                else :
                    self.sfm.compute_pose(pair_obj, baseline)
                    l.get().w.debug("Mean reprojection error for images is {}".format(self.sfm.errors[j]))
                    j += 1

                self.sfm.save_3d_points()

                if self.limit != 0 and j-1 == self.limit :
                    break

            self.write_cameras()
            return 0

    def check_pair(self) :
        for i, pair in enumerate(self.pairs):
            pair_obj = self.pairs[pair]
            l.get().w.debug("Pair name {} {}".format(pair_obj.image_name1, pair_obj.image_name2))
            pair_obj.check_points_3d()
            break

    def generate_points(self, mode='colmap', answer='seed') :
        filename = os.path.join(self.root_path, 'images', df.pts_file_name)

        if answer == 'seed' :
            self.answer = import_answer(filename, 2)
        else :
            self.answer = import_answer(filename, 0)

        if mode == 'colmap' :
            for i, cam in enumerate(self.cameras):
                if i == 0 or i == 1 :
                    viewname = get_viewname(self.cameras[i].view.name, self.ext)
                    if self.ext == 'tiff':
                        viewname = self.cameras[i].view.name[:-8]
                    
                    pts = self.answer[viewname]
                    l.get().w.debug(" generate_points name {} \n {} ".format(self.cameras[i].view.name, pts))
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
                    viewname = get_viewname(self.cameras[i].view.name, self.ext)

                    pts = self.answer[viewname]
                    l.get().w.debug(" generate_points name {} \n {} ".format(self.cameras[i].view.name, pts))
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
            viewname = get_viewname(self.cameras[i].view.name, self.ext)

            l.get().w.debug("name : {}".format(self.cameras[i].view.name, viewname))
            gt = self.answer[viewname]

            for j in range(self.cameras[i].pts.shape[0]) :
                # pt_3d = self.cameras[i].pts_3D[j, :]
                pt_2d = self.cameras[i].pts[j, :]
                gt_pt = gt[j, :]
                terr = np.linalg.norm(pt_2d - gt_pt)
                # print("3d {} pts {} : answer {} : err {} ".format(pt_3d, pt_2d, gt_pt, terr))
                l.get().w.debug("pts {} : answer {} : err {} ".format(pt_2d, gt_pt, terr))
                if terr > max : 
                    max = terr

                if terr < min : 
                    min = terr

                s_error += terr
                t_error += terr

            l.get().w.info('scene err : {}'.format(s_error))
            if self.limit != 0 and i == self.limit :
                break

        ave = t_error / len(self.cameras)
        l.get().w.info("total real error : {} ave {} max {} min {} ".format(t_error, ave, max, min))

    def visualize(self, mode='colmap') :
        if mode == 'colmap' :
            self.colmap.visualize_colmap_model()
        else :         
            plot_scene(self.cameras, self.sfm, mode)


    def export(self, output_path, job_id) :
        export_points(self, df.export_point_type, output_path, job_id)
        save_point_image(self)

    def save_answer_image(self):
        save_ex_answer_image(self)