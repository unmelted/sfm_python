import os
import time
import logging
from multiprocessing.dummy import Queue
from cam_group import *
import definition as df

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
        self.db = DbManager()

    def Receiver(self, t) :
        self.index = 0

        while True :
            if(self.index % 100000 == 0) :
                self.index = 0
            time.sleep(0.2)
            if(self.cmd_que.empty() is False) :
                task, obj = self.cmd_que.get()
                print("que.. get  ", task, obj)                
                self.processor(task, obj)
                self.index += 1

    def send_query(self, query, obj) :
        result = None
        if query == df.TaskCategory.AUTOCALIB_STATUS :
            result = DbManager.getInstance().getJobStatus(obj[0])
        
        return result

    def add_task(self, task, obj) :
        self.cmd_que.put((task, obj))

    def processor(self, task, obj) :
        if task == df.TaskCategory.AUTOCALIB :
            print("auto calib task add !")
            ac = autocalib(obj[0], obj[1])
            ac.run()
            # subprocess.call('python bb.py', creationflags=subprocess.CREATE_NEW_CONSOLE)


class autocalib(object) :

    def __init__ (self, root_dir, mode) :
        self.root_dir = root_dir
        self.run_mode = 'colmap'
        self.mode = mode
        logging.basicConfig(level=logging.INFO)        

    def run(self) :
        time_s = time.time()                
        preset1 = Group()        

        if self.run_mode == 'colmap' :
            ret = preset1.create_group_colmap(self.root_dir, self.mode)
        else:
            ret = preset1.create_group(self.root_dir)

        if( ret < 0 ):
            return -11

        if self.mode > df.CommandMode.HALF:
            preset1.read_cameras()
            preset1.generate_points()    
            preset1.export()

        if df.CommandMode.PTS_ERROR_ANALYSIS in self.mode :
            preset1.calculate_real_error()

        if df.CommandMode.VISUALIZE in self.mode:
            preset1.visualize()

        time_e = time.time() - time_s
        print("Spending time total (sec) :", time_e)
        
        return 0
