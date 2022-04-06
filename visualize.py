from curses import KEY_A1
import numpy as np
import matplotlib.pyplot as plt
import pytransform3d.camera as pc
import pytransform3d.transformations as pt
from cam_group import *



def plot_cameragroup(group):
    for view in group.views :
        print(group.K)
        pass
    