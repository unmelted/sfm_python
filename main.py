from cam_group import *
from view import *
from match import *
from sfm import *
import numpy as np
import logging
import argparse


def run(args):

    logging.basicConfig(level=logging.INFO)
    group = Group.create_group(args.root_dir, 'jpg')
    matches = create_matches(group)
    K = np.loadtxt(os.path.join(args.root_dir, 'images', 'K.txt'))
    sfm = SFM(group, matches, K)
    sfm.reconstruct()


def set_args(parser):

    parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
                        help='root directory containing the images/ folder')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    set_args(parser)
    args = parser.parse_args()
    run(args)
