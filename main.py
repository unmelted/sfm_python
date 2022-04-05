from view import *
from match import *
from sfm import *
import numpy as np
import logging
import argparse


def run(args):

    logging.basicConfig(level=logging.INFO)
    views = create_views(args.root_dir, args.image_format)
    matches = create_matches(views)
    K = np.loadtxt(os.path.join(args.root_dir, 'images', 'K.txt'))
    sfm = SFM(views, matches, K)
    sfm.reconstruct()


def set_args(parser):

    parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
                        help='root directory containing the images/ folder')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    set_args(parser)
    args = parser.parse_args()
    run(args)
