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

    def Receiver(self, t) :
        self.index = 0
        print("start? ")
        while True :
            if(self.index % 10000000 == 0) :
                self.index = 0
            time.sleep(0.5)
            print("..")            
            if(self.cmd_que.empty() is False) :
                print("que.. ! ")
                task, obj = self.cmd_que.get()
                print("que.. get  ", task, obj)                
                self.processor(task, obj)
                self.index += 1

    def add_task(self, task, obj) :
        print("call ? ")
        self.cmd_que.put((task, obj))
        print(task, obj)
        print(self.cmd_que.empty())        

    def processor(self, task, obj) :
        if task == df.TaskCategory.AUTOCALIB :
            print("auto calib task add !")

class autocalib(object) :

    def __init__ (self, root_dir, mode) :
        self.root_dir = root_dir
        self.run_mdoe = 'colmap'
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
            logging.error("terminated. ")
            return

        if self.mode == 'full' or self.mode == 'visualize' :
            preset1.read_cameras()        
            preset1.generate_points()    
            # preset1.calculate_real_error()
            preset1.export()
            preset1.visualize()
        
        time_e = time.time() - time_s
        print("Spending time total (sec) :", time_e)
        
        return 0
