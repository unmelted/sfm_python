from cam_group import *
import numpy as np
import logging
import argparse
import visualize

def run(args):

    logging.basicConfig(level=logging.INFO)

    preset1 = Group()
    ret = preset1.create_group(args.root_dir, 'png')
    if( ret < 0 ):
        logging.error("terminated. ")
        return 0

    if args.mode == 'sfm' : 
        preset1.run_sfm()
        preset1.generate_points()    
        preset1.calculate_real_error()
        preset1.visualize()    

    elif args.mode == 'vis' :
        preset1.read_cameras()
        preset1.visualize() 

    elif args.mode == 'eval':
        preset1.read_cameras()
        preset1.generate_points()            
        preset1.calculate_real_error()
        preset1.export()

    elif args.mode == 'test' :
        preset1.calculate_real_error()


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
