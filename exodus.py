import os
import time
import numpy as np
import logging

from cam_group import *

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
