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

        self.cam_count = 0

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

        filename = os.path.join(self.root_path, 'images', df.pts_file_name)

        # if list_from == 'colmap_db': ## shoud block those after using init pari of colmap
        self.answer = import_answer(filename, 0) 
        # else :
        #     self.answer = import_answer(filename, 2)


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
        self.cam_count = len(self.cameras)

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
            result = self.colmap.recon_command(self.cam_count)
            if result < 0 :
                l.get().w.error("Recon command error : {}".format(result))
                return result 

            result = self.colmap.cvt_colmap_model(self.ext)
            if result < 0 :
                return result

            self.colmap.modify_pair_table()
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

    def get_camera_byView(self, viewname) :
        cam = None
        for i, cam in enumerate(self.cameras):
            cam_view = get_viewname(self.cameras[i].view.name, self.ext)
            if cam_view == viewname :
                return 0, cam
            
        return -150, None
        
        
    def generate_points(self, job_id, base_pts=None) :

        if df.answer_from == 'input' and base_pts == None :
            df.answer_from = 'pts' #for analysis mode
        
        if df.answer_from == 'pts' and self.answer == None:
            return -303
            
        err, pts_3d, viewname1, viewname2 = self.make_seed_answer(job_id, pair_type=df.init_pair_mode, answer_from=df.answer_from, base_pts=base_pts)

        if err < 0 :
            return err

        for i in range(len(self.cameras)):
            viewname = get_viewname(self.cameras[i].view.name, self.ext)            
            if viewname == viewname1 or viewname == viewname2 :
                continue
            else :
                self.adjust.reproject_3D(pts_3d, self.cameras[i])

        return 0

    def make_seed_answer(self, job_id, pair_type='zero', answer_from='pts', base_pts= None) :
        viewname1 = None
        viewname2 = None
        c0 = None
        c1 = None
        err = 0
        _3d = None

        if pair_type == 'zero' :
            viewname1 = get_viewname(self.cameras[0].view.name, self.ext)
            viewname2 = get_viewname(self.cameras[1].view.name, self.ext)
            c0 = self.cameras[0]
            c1 = self.cameras[1]
        elif pair_type == 'pair' :
            result, image_name1, image_name2 = get_pair(job_id)
            
            viewname1 = get_viewname(image_name1, self.ext)
            viewname2 = get_viewname(image_name2, self.ext)
            err, c0 = self.get_camera_byView(viewname1)
            if err < 0 :
                return err, None, None, None

            err, c1 = self.get_camera_byView(viewname2)
            if err < 0 :
                return err, None, None, None

        l.get().w.debug("Pair name {} {}".format(viewname1, viewname2))

        if answer_from == 'pts' :
            pts1 = self.answer[viewname1]
            pts2 = self.answer[viewname2]
        elif answer_from == 'input' :
            base1 = [[base_pts[0],base_pts[1]], [base_pts[2], base_pts[3]], [base_pts[4], base_pts[5]] ,[base_pts[6], base_pts[7]]]
            base2 = [[base_pts[8],base_pts[9]], [base_pts[10], base_pts[11]], [base_pts[12], base_pts[13]] ,[base_pts[14], base_pts[15]]]
            pts1 = np.array(base1)
            pts2 = np.array(base2)

        c0.pts = pts1
        c1.pts = pts2
        _3d = self.adjust.make_3D(c0, c1)

        return err, _3d, viewname1, viewname2

    def calculate_real_error(self) :

        max = 0
        min = 10000
        ave = 0
        t_error = 0

        if len(self.answer) < 3 :
            return -501

        for i in range(len(self.cameras)) :
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

        return 0

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