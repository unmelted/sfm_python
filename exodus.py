import os
import time
from datetime import datetime
import logging
from multiprocessing.dummy import Queue
from camera_group import *
import definition as df
from logger import Logger as l
from db_manager import DbManager
from prepare_proc import *
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
        contents = []
        if obj == None :
            return finish(obj, -21)                

        l.get().w.debug('receive query {} {}'.format(query, obj[0]))

        if query == df.TaskCategory.AUTOCALIB_STATUS :
            status, result = DbManager.getInstance().getJobStatus(obj[0])

        elif query == df.TaskCategory.VISUALIZE :
            status = 100
            result = visualize_mode(obj[0])

        elif query == df.TaskCategory.ANALYSIS :
            status = 100
            result = analysis_mode(obj[0])

        elif query == df.TaskCategory.GENERATE_PTS :
            l.get().w.info(" Task Generate start obj : {} {} ".format( obj[0], obj[2]))
            print("data check : ", obj[2])
            result = generate_pts(obj[0], obj[2]['type'], obj[2]['pts'])
            status = 100

        elif query == df.TaskCategory.GET_PAIR :
            result, image1, image2 = get_pair(obj[0])
            status = 100
            if result == 0 :
                contents.append(image1)
                contents.append(image2)

        DbManager.getInstance().insert('request_history', job_id=obj[0], requestor=obj[1], desc=query, result=result)
        return status, result, contents

    def add_task(self, task, obj) :
        self.cmd_que.put((task, obj))
        self.index = DbManager.getInstance().getJobIndex() + 1
        l.get().w.info("Alloc job id {} ".format(self.index))

        return self.index

    def processor(self, task, obj) :
        l.get().w.info("Task Proc start : {} ".format(self.index))        
        if task == df.TaskCategory.AUTOCALIB :
            l.get().w.info("{} Task Autocalib start obj : {} {} ".format(self.index, obj[0], obj[1]))
            ac = autocalib(obj[0], self.index, obj[1])
            ac.run()         

            DbManager.getInstance().insert('request_history', job_id=self.index, requestor=obj[1], desc=task)

def visualize_mode(job_id) :
    l.get().w.info("Visualize start : {} ".format(job_id))
    result, root_path = DbManager.getInstance().getRootPath(job_id)
    if result < 0 :
        l.get().w.error("visualize err: {} ".format(df.get_err_msg(result)))
        return 0

    colmap = Colmap(root_path)
    colmap.visualize_colmap_model()
    return 0


def generate_pts(job_id, type, base_pts) :
    l.get().w.info("Generate pst start : {} ".format(job_id))
    if len(base_pts) < 16 :
        return finish_query(job_id, -301)
    else :
        for val in base_pts :
            if val < 0 :
                return finish_query(job_id, -302)

    preset1 = Group()
    result, root_path = DbManager.getInstance().getRootPath(job_id)
    if result < 0 :
        return finish_query(job_id, result)

    result = preset1.create_group(root_path, df.DEFINITION.run_mode, 'colmap_db')
    if result < 0 :
        return finish_query(job_id, result)

    preset1.read_cameras()
    result = preset1.generate_points(job_id, base_pts=None)
    if result < 0 :
        return finish_query(job_id, result)                

    preset1.export(os.path.join(root_path, 'output'), job_id)
    status_update(job_id, 200)

    return 0

def analysis_mode(job_id) :
    l.get().w.info("analysis  start : {} ".format(job_id))    
    preset1 = Group()
    result, root_path = DbManager.getInstance().getRootPath(job_id)
    if result < 0 :
        l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
        return 0

    result = preset1.create_group(root_path, df.DEFINITION.run_mode, 'colmap_db')
    if result < 0 :
        l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
        return 0

    preset1.read_cameras()
    # result = preset1.generate_points(mode='colmap_zero')
    # if result < 0 :
    #     l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
    #     return 0

    # result = preset1.calculate_real_error()
    # if result < 0 :
    #     l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
    #     return 0

    result = preset1.generate_points()
    if result < 0 :
        l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
        return 0

    result = preset1.calculate_real_error()
    if result < 0 :
        l.get().w.error("analysis err: {} ".format(df.get_err_msg(result)))        
        return 0

    # preset1.colmap.make_sequential_homography(preset1.cameras, preset1.answer, preset1.ext)
    preset1.export(os.path.join(root_path, 'output'), job_id)
    # preset1.save_answer_image()
    return 0

class autocalib(object) :

    def __init__ (self, input_dir, job_id, ip) :
        self.input_dir = input_dir
        self.root_dir = None
        self.run_mode = df.DEFINITION.run_mode
        self.list_from = df.DEFINITION.cam_list        
        self.mode = 0 #mode
        self.job_id = job_id
        self.ip = ip

    def run(self) :
        DbManager.getInstance().insert('command', job_id=self.job_id, requestor=self.ip, task=df.TaskCategory.AUTOCALIB.name, input_path=self.input_dir, mode=df.DEFINITION.run_mode, cam_list=df.DEFINITION.cam_list)
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
        status_update(self.job_id, 30)
        time_e1 = time.time()
        l.get().w.critical("Spending time of create group (sec) : {}".format(time_e1 - time_s))

        ret = preset1.run_sfm()
        if( ret < 0 ):
            return finish(self.job_id, -101)
        status_update(self.job_id, 80)

        ret = self.init_pair_update(preset1.colmap)
        if( ret < 0 ):
            return finish(self.job_id, ret)
        status_update(self.job_id, 100)

        # ret = preset1.read_cameras()
        # if( ret < 0 ):
        #     return finish(self.job_id, ret)

        # preset1.generate_points(mode='colmap_zero')    
        # status_update(self.job_id, 90)            
        # preset1.export(self.input_dir, self.job_id)
        # status_update(self.job_id, 100)

        time_eg = time.time() - time_e1
        l.get().w.critical("Spending time of post matching (sec) : {}".format(time_eg))
        time_e2 = time.time() - time_s
        l.get().w.critical("Spending time total (sec) : {}".format(time_e2))

        return 0


    def init_pair_update(self, cm) :
        err, img_id1, img_id2 = get_initpair(self.root_dir)
        if err < 0 :
            return err

        err, image1 = cm.getImagNamebyId(img_id1)
        if err < 0 :
            return err
        err, image2 = cm.getImagNamebyId(img_id2)
        if err < 0 :
            return err
            
        l.get().w.info("JOB_ID: {} update initial pair {} {}".format(self.job_id, image1, image2))
        DbManager.getInstance().update('command', image_pair1=image1, image_pair2=image2, job_id=self.job_id)
    

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
                result = prepare_image_job(self.input_dir, self.root_dir)

            elif self.list_from == 'video_folder' :
                video_files = 0
                video_files = sorted(glob.glob(os.path.join(self.input_dir,'*.mp4')))

                if len(video_files) < 3 :
                    return -102

                result = prepare_video_job(self.input_dir, self.root_dir)
                self.list_from = 'image_folder'                

            elif self.list_from == 'pts_file' :
                result = prepare_image_job(self.input_dir, self.root_dir)

            l.get().w.info("Check validity root path: {} ".format(self.root_dir))
            DbManager.getInstance().update('command', root_path=self.root_dir, job_id=self.job_id)

            return result
