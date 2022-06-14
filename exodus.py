import os
import time
from datetime import datetime
import logging
from multiprocessing.dummy import Queue
from camera_group import *
import definition as df
from logger import Logger as l
from db_manager import DbManager
from image_proc import *
from intrn_util import *

class Commander(object) :
    instance = None

    @staticmethod
    def getInstance():
        if Commander.instance is None:
            Commander.instance = Commander()
        return Commander.instance

    def __init__(self) :
        self.cmd_que = Queue()        
        self.index = 0
        self.db = DbManager.getInstance()
        self.index = 0
        l.get().w.info("Commander initialized.")

    def Receiver(self, t) :
        while True :
            if(self.index % 100000 == 0) :
                self.index = 0
            time.sleep(0.2)

            if(self.cmd_que.empty() is False) :
                task, obj = self.cmd_que.get()
                self.processor(task, obj)


    def send_query(self, query, obj) :
        result = 0 
        status = 0
        if obj == None :
            return finish(obj, -21)                

        l.get().w.debug('receive query {} {}'.format(query, obj))
        print(df.TaskCategory.ANALYSIS.name)

        if query.upper() == df.TaskCategory.AUTOCALIB_STATUS.name :
            status, result = DbManager.getInstance().getJobStatus(obj)

        elif query.upper() == df.TaskCategory.VISUALIZE :
            status = 100
            result = visualize_mode(obj)

        elif query.upper() == df.TaskCategory.ANALYSIS.name :
            status = 100
            result = analysis_mode(obj)

        return status, result

    def add_task(self, task, obj) :
        self.cmd_que.put((task, obj))
        self.index = DbManager.getInstance().getJobIndex() + 1
        l.get().w.info("Alloc job id ".format(self.index))
       
        return self.index

    def processor(self, task, obj) :
        if task == df.TaskCategory.AUTOCALIB :
            l.get().w.info("Task Proc start : {} ".format(self.index))
            ac = autocalib(obj, self.index)
            ac.run()

def visualize_mode(job_id) :
    l.get().w.info("Visualize start : ".format(job_id))
    root_path = DbManager.getInstance().getRootPath(job_id)
    colmap = Colmap(root_path)
    colmap.visualize_colmap_model()
    return 0

def analysis_mode(job_id) :
    l.get().w.info("analysis  start : ".format(job_id))    
    preset1 = Group()
    root_path = DbManager.getInstance().getRootPath(job_id)
    ret = preset1.create_group(root_path, df.DEFINITION.run_mode, 'colmap_db')
    preset1.read_cameras()
    preset1.generate_points(answer='full')
    preset1.calculate_real_error()
    return 0

class autocalib(object) :

    def __init__ (self, input_dir, job_id) :
        self.input_dir = input_dir
        self.root_dir = None
        self.run_mode = df.DEFINITION.run_mode
        self.list_from = df.DEFINITION.cam_list        
        self.mode = 0 #mode
        self.job_id = job_id

    def run(self) :
        DbManager.getInstance().insert('command', job_id=self.job_id, task=df.TaskCategory.AUTOCALIB.name, input_path=self.input_dir, mode=df.DEFINITION.run_mode, cam_list=df.DEFINITION.cam_list)
        time_s = time.time()                
        preset1 = Group()        
        result = self.checkDataValidity()

        if result != 0 :
            return finish(self.job_id, result)
        status_update(self.job_id, 10)

        l.get().w.error("list from type : {} ".format(self.list_from))        
        ret = preset1.create_group(self.root_dir, self.run_mode, self.list_from)

        if( ret < 0 ):
            return finish(self.job_id, -101)
        status_update(self.job_id, 20)
        time_e1 = time.time()
        l.get().w.critical("Spending time of create group (sec) : {}".format(time_e1 - time_s))

        ret = preset1.run_sfm()
        if( ret < 0 ):
            return finish(self.job_id, -101)
        status_update(self.job_id, 50)

        ret = preset1.read_cameras()
        if( ret < 0 ):
            return finish(self.job_id, ret)

        preset1.generate_points()    
        status_update(self.job_id, 90)            
        preset1.export(self.input_dir, self.job_id)
        status_update(self.job_id, 100)

        time_eg = time.time() - time_e1
        l.get().w.critical("Spending time of post matching (sec) : {}".format(time_eg))
        time_e2 = time.time() - time_s
        l.get().w.critical("Spending time total (sec) : {}".format(time_e2))

        return 0


    def checkDataValidity(self) :
        if self.mode == df.CommandMode.VISUALIZE or  \
            self.mode == 'visualize' or \
            self.mode == df.CommandMode.PTS_ERROR_ANALYSIS or \
            self.mode == 'analysis':
    
            self.root_dir = self.input_dir

            if not os.path.exists(self.root_dir) or \
               not os.path.exists(os.path.join(self.root_dir, 'cameras.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'images.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'point3D.txt')) or \
               not os.path.exists(os.path.join(self.root_dir, 'sparse')):
                return finish(self.job_id, -104)


        else :
            if not os.path.exists(self.input_dir):
                return -105

            result = 0
            now = datetime.now()
            root = 'Cal' + datetime.strftime(now, '%Y%m%d_%H%M_') + str(self.job_id)
            if not os.path.exists(os.path.join(os.getcwd(), root)) :
                os.makedirs(os.path.join(os.getcwd(), root))
            self.root_dir = os.path.join(os.getcwd(), root)
            if not os.path.exists(os.path.join(self.root_dir, 'images')) :
                os.makedirs(os.path.join(self.root_dir, 'images'))

            if self.list_from == 'image_folder':
                result = make_copy(self.input_dir, os.path.join(self.root_dir, 'images'))

            elif self.list_from == 'video_folder' :
                video_files = 0
                video_files = sorted(glob.glob(os.path.join(self.input_dir,'*.mp4')))

                if len(video_files) < 3 :
                    return -102

                result = make_snapshot(self.input_dir, os.path.join(self.root_dir, 'images'))
                self.list_from = 'image_folder'                

            elif self.list_from == 'pts_file' :
                result = make_copy(self.input_dir, os.path.join(self.root_dir, 'images'))

            l.get().w.info("Check validity root path: {} ".format(self.root_dir))
            DbManager.getInstance().update('command', root_path=self.root_dir, job_id=self.job_id)

            return result
