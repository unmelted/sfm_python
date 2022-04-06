from cam_group import *
import numpy as np
import logging
import argparse


def run(args):

    logging.basicConfig(level=logging.INFO)

    preset1 = Group()
    preset1.create_group(args.root_dir, 'jpg')
    preset1.run_sfm()


def set_args(parser):

    parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
                        help='root directory containing the images/ folder')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    set_args(parser)
    args = parser.parse_args()
    run(args)
