from cam_group import *
import numpy as np
import logging
import argparse
import visualize
from extn_util import * 

def run(args):

    logging.basicConfig(level=logging.INFO)

    preset1 = Group()

    if args.mode == 'colmap' :
        ret = preset1.create_group_colmap(args.root_dir, 'png')        
    else:
        ret = preset1.create_group(args.root_dir, 'tiff')

    if( ret < 0 ):
        logging.error("terminated. ")
        return 0

    if args.mode == 'sfm' : 
        preset1.run_sfm()
        preset1.generate_points()    
        preset1.calculate_real_error()
        preset1.export()
        preset1.visualize()    

    elif args.mode == 'vis' :
        preset1.read_cameras(args.mode)
        # import_camera_pose(preset1)        
        preset1.visualize() 

    elif args.mode == 'eval':
        preset1.read_cameras(args.mode)
        # import_camera_pose(preset1)
        preset1.generate_points()            
        preset1.calculate_real_error()
        preset1.export()
        preset1.visualize() 

    elif args.mode == 'test' :
        preset1.calculate_real_error()

    elif args.mode == 'colmap' :
        preset1.read_cameras(args.mode)        
    #     preset1.generate_points()    
    #     preset1.calculate_real_error()
    #     preset1.export()
    #     preset1.visualize()    
    
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
