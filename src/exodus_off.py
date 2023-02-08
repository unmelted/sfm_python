import os
import time
from camera_group import *
import numpy as np
import logging
import argparse
import visualize
from extn_util import * 
from logger import Logger as l

def run(args):

    time_s = time.time()        
    logging.basicConfig(level=logging.INFO)

    preset1 = Group()

    run_mode = 'colmap'
    ret = preset1.create_group(args.root_dir, run_mode, list_from='image_folder')

    if( ret < 0 ):
        l.get().w.error("terminated. ")
        return 0

    '''
    if args.mode == 'sfm' : 
        preset1.run_sfm('off')
        preset1.generate_points(args.mode)    
        preset1.calculate_real_error()
        preset1.export()
        preset1.visualize()

    elif args.mode == 'vis' :
        preset1.read_cameras(args.mode)
        # import_camera_pose(preset1)        
        preset1.visualize(args.mode)

    elif args.mode == 'eval':
        preset1.read_cameras(args.mode)
        # import_camera_pose(preset1)
        preset1.generate_points(args.mode)            
        preset1.calculate_real_error()
        preset1.export()
        preset1.visualize(args.mode)

    elif args.mode == 'test' :
        preset1.calculate_real_error()
    '''
    if args.mode == 'full' or args.mode == 'visualize' :
        preset1.run_sfm('off')        
        # preset1.read_cameras()
        preset1.generate_points()    
        # preset1.calculate_real_error()
        preset1.export()
        preset1.visualize('off')

    time_e = time.time() - time_s
    l.get().w.info("Exodus Offline Spending time total (sec) : {} ".format(time_e))

def set_args(parser):

    parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
                        help='root directory containing the images/ folder')
    parser.add_argument('--mode', action='store', type=str, dest='mode', default='sfm',
                    help='select mode sfm , visualize')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    set_args(parser)
    args = parser.parse_args()
    run(args)
