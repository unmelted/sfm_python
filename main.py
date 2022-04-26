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

    preset1.run_sfm()
    preset1.generate_points()    
    preset1.calculate_real_error()
    preset1.visualize()    

def set_args(parser):

    parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
                        help='root directory containing the images/ folder')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    set_args(parser)
    args = parser.parse_args()
    run(args)
