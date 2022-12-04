import os
import time
from datetime import datetime
from camera_group import *
import definition as df
from logger import Logger as l
from intrn_util import *
from prepare_proc import *
from db_manager import DbManager


class Autocalib(object):

    def __init__(self, input_dir, job_id, group, config1, config2, ip):
        self.input_dir = input_dir
        self.root_dir = None
        self.run_mode = df.DEFINITION.run_mode
        self.list_from = df.DEFINITION.cam_list
        self.mode = 0  # mode
        self.job_id = job_id
        self.ip = ip
        self.group = group
        self.config1 = config1
        self.config2 = config2

    def run(self):
        print("--------------AUTOCALIB3------")
        print(os.getpid())
        print("------------------------------")

        DbManager.insert_newcommand(self.job_id, 0, self.ip, df.TaskCategory.AUTOCALIB.name,
                                    self.input_dir, df.DEFINITION.run_mode, self.config1, self.config2)
        time_s = time.time()
        preset1 = Group(self.job_id)
        result = self.checkDataValidity()

        if result != 0:
            return finish(self.job_id, result)
        status_update(self.job_id, 10)

        l.get().w.error("list from type : {} ".format(self.list_from))
        ret = preset1.create_group(
            self.root_dir, self.run_mode, self.list_from, self.group)

        if (ret < 0):
            return finish(self.job_id, ret)
        status_update(self.job_id, 30)
        time_e1 = time.time()
        l.get().w.critical("Spending time of create group (sec) : {}".format(time_e1 - time_s))

        ret = preset1.run_sfm()
        if (ret < 0):
            return finish(self.job_id, ret)
        status_update(self.job_id, 90)

        ret = self.init_pair_update(preset1.colmap)
        if (ret < 0):
            return finish(self.job_id, ret)
        status_update(self.job_id, 100)

        time_eg = time.time() - time_e1
        l.get().w.critical("Spending time of post matching (sec) : {}".format(time_eg))
        time_e2 = time.time() - time_s
        l.get().w.critical("Spending time total (sec) : {}".format(time_e2))

        return 0

    def init_pair_update(self, cm):
        err, img_id1, img_id2 = get_initpair(self.root_dir)
        if err < 0:
            return err

        err, image1 = cm.getImagNamebyId(img_id1)
        if err < 0:
            return err
        err, image2 = cm.getImagNamebyId(img_id2)
        if err < 0:
            return err

        l.get().w.info("JOB_ID: {} update initial pair {} {}".format(self.job_id, image1, image2))
        DbManager.update_command_pair(image1, image2, self.job_id)

        return 0

    def checkDataValidity(self):
        if self.mode == df.TaskCategory.VISUALIZE or  \
                self.mode == 'visualize' or \
                self.mode == df.TaskCategory.ANALYSIS or \
                self.mode == 'analysis':

            self.root_dir = self.input_dir

            if not os.path.exists(self.root_dir) or \
               not os.path.exists(os.path.join(self.root_dir, 'cameras.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'images.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'point3D.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'sparse')):
                return finish(self.job_id, -104)

        else:
            if not os.path.exists(self.input_dir):
                return -105

            result = 0
            now = datetime.now()
            root = 'Cal' + \
                datetime.strftime(now, '%Y%m%d_%H%M_') + str(self.job_id)
            if not os.path.exists(os.path.join(os.getcwd(), root)):
                os.makedirs(os.path.join(os.getcwd(), root))
            self.root_dir = os.path.join(os.getcwd(), root)
            if not os.path.exists(os.path.join(self.root_dir, 'images')):
                os.makedirs(os.path.join(self.root_dir, 'images'))

            result = prepare_job(self.input_dir, self.root_dir, self.list_from)
            if result < 0:
                return result

            if self.list_from == 'video_folder':
                self.list_from = 'image_folder'

            l.get().w.info("Check validity root path: {} ".format(self.root_dir))
            DbManager.update_command_path(self.root_dir, self.job_id)

            return result
