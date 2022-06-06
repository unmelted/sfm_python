import os
import time
from datetime import datetime
import logging
from multiprocessing.dummy import Queue
from cam_group import *
import definition as df
from db_manager import DbManager
from image_proc import *

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
        print("command init : ", DbManager.getInstance())

    def Receiver(self, t) :
        self.index = 110

        while True :
            if(self.index % 100000 == 0) :
                self.index = 0
            time.sleep(0.2)
            print("..")
            if(self.cmd_que.empty() is False) :
                task, obj = self.cmd_que.get()
                print("que.. get  ", task, obj)                
                self.processor(task, obj)


    def send_query(self, query, obj) :
        result = 0
        DbManager.getInstance().insert('command', job_id=obj, task=query.name,  mode=query.value)
        if query == df.TaskCategory.AUTOCALIB_STATUS :
            if obj == None :
                return -21

            result = DbManager.getInstance().getJobStatus(obj)

        elif query == df.TaskCategory.VISUALIZE :
            if obj == None :
                return -21

            result = visualize_mode(obj)

        return result

    def add_task(self, task, obj) :
        self.cmd_que.put((task, obj))
        self.index += 1
        return self.index

    def processor(self, task, obj) :
        if task == df.TaskCategory.AUTOCALIB :
            print("auto calib task add !")
            print("process  : ", DbManager.getInstance())            
            DbManager.getInstance().insert('command', job_id=self.index, task=task.name, input_path=obj[0], mode=obj[1])
            ac = autocalib(obj[0], obj[1], self.index)
            ac.run()

def visualize_mode(job_id) :
    root_path = DbManager.getInstance().getRootPath(job_id)
    colmap = Colmap(root_path)
    colmap.visualize_colmap_model()
    return 0


class autocalib(object) :

    def __init__ (self, input_dir, mode, job_id) :
        self.input_dir = input_dir
        self.root_dir = None
        self.run_mode = 'colmap'
        self.mode = mode
        self.job_id = job_id
        logging.basicConfig(level=logging.INFO)        

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
                return -104

        else :
            if not os.path.exists(self.input_dir):
                return -105
            video_files = 0
            video_files = sorted(glob.glob(os.path.join(self.input_dir,'*.mp4')))
            if len(video_files) < 3 :
                return -102

            now = datetime.now()
            root = 'Cal' + datetime.strftime(now, '%Y%m%d_%H%M_') + str(self.job_id)
            if not os.path.exists(os.path.join(os.getcwd(), root)) :
                os.makedirs(os.path.join(os.getcwd(), root))
            self.root_dir = os.path.join(os.getcwd(), root)
            print("check validity : " , self.root_dir)
            DbManager.getInstance().update('command', root_path=self.root_dir, job_id=self.job_id)

            if not os.path.exists(os.path.join(self.root_dir, 'images')) :
                os.makedirs(os.path.join(self.root_dir, 'images'))
            result = make_snapshot(self.input_dir, os.path.join(self.root_dir, 'images'))

        DbManager.getInstance().update('command', status=10, job_id=self.job_id)
        return result

    def run(self) :
        time_s = time.time()                
        preset1 = Group()        

        result = self.checkDataValidity()

        if result != 0 :
            return result

        if self.run_mode == 'colmap' :
            ret = preset1.create_group_colmap(self.root_dir, self.mode)
        else:
            ret = preset1.create_group(self.root_dir)

        DbManager.getInstance().update('command', status=50, job_id=self.job_id)
        if( ret < 0 ):
            return -101

        if self.mode == df.CommandMode.FULL or self.mode == 'full':
            preset1.read_cameras()
            preset1.generate_points()    
            preset1.export()
            DbManager.getInstance().update('command', status=100, job_id=self.job_id)            

        if self.mode == df.CommandMode.PTS_ERROR_ANALYSIS or self.mode == 'analysis':
            preset1.calculate_real_error()

        if self.mode  == df.CommandMode.VISUALIZE or self.mode == 'visualize':
            preset1.visualize()

        time_e = time.time() - time_s
        print("Spending time total (sec) :", time_e)
        
        return 0
