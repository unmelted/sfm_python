from curses import KEY_A1
import numpy as np
import matplotlib.pyplot as plt
from pytransform3d.plot_utils import make_3d_axis
from pytransform3d.rotations import active_matrix_from_intrinsic_euler_xyz
from  pytransform3d.camera import make_world_grid, world2image, plot_camera
from pytransform3d.transformations import transform_from, plot_transform
from cam_group import *



def plot_cameras(cameras, limit):
    plt.figure(figsize=(20, 10))
    ax = make_3d_axis(1, 111, 10)
    plot_transform(ax)
    focal_length = 10
    j  = 0   
    sensor_size = np.array([1920, 1080])

    for i, camera in enumerate(cameras):                    
        cam2world = transform_from(camera.R, camera.t.T)
        print("-- plot camera -- ")
        print(camera.R)
        print(camera.t.T)        
        plot_camera(ax, M=camera.K, cam2world=cam2world, sensor_size=sensor_size, virtual_image_distance=1)

        if limit != 0 and i == limit : 
            break

    plt.rcParams['figure.figsize'] = [1, 1]
    plt.show()

def plot_pointmap(sfm) :
    plt.figure()
    plt.suptitle('Point map', fontsize = 16)
    index = 1
    for i in sfm.point_map:
        print(i, sfm.point_map[i])
        plt.subplot(1, len(sfm.point_map), index)
        ax = plt.gca()
        ax.plot(sfm.point_map[i][0], sfm.point_map[i][1], 'r.')
    
    plt.show()

def compute_epipole(F):
    """ Computes the (right) epipole from a
        fundamental matrix F.
        (Use with F.T for left epipole.)
    """
    # return null space of F (Fx=0)
    U, S, V = np.linalg.svd(F)
    e = V[-1]
    return e / e[2]
    
def plot_epipolar_lines(c0, c1, show_epipole=False):
    """ Plot the points and epipolar lines. P1' F P2 = 0 """
    p1 = 0 
    p2 = 0
    plt.figure()
    plt.suptitle('Epipolar lines', fontsize=16)

    plt.subplot(1, 2, 1, aspect='equal')
    # Plot the epipolar lines on img1 with points p2 from the right side
    # L1 = F * p2
    plot_epipolar_line(p1, p2, c1.F, show_epipole)
    plt.subplot(1, 2, 2, aspect='equal')
    # Plot the epipolar lines on img2 with points p1 from the left side
    # L2 = F' * p1
    plot_epipolar_line(p2, p1, c1.F.T, show_epipole)


def plot_epipolar_line(p1, p2, F, show_epipole=False):
    """ Plot the epipole and epipolar line F*x=0
        in an image given the corresponding points.
        F is the fundamental matrix and p2 are the point in the other image.
    """
    lines = np.dot(F, p2)
    pad = np.ptp(p1, 1) * 0.01
    mins = np.min(p1, 1)
    maxes = np.max(p1, 1)

    # epipolar line parameter and values
    xpts = np.linspace(mins[0] - pad[0], maxes[0] + pad[0], 100)
    for line in lines.T:
        ypts = np.asarray([(line[2] + line[0] * p) / (-line[1]) for p in xpts])
        valid_idx = ((ypts >= mins[1] - pad[1]) & (ypts <= maxes[1] + pad[1]))
        plt.plot(xpts[valid_idx], ypts[valid_idx], linewidth=1)
        plt.plot(p1[0], p1[1], 'ro')

    if show_epipole:
        epipole = compute_epipole(F)
        plt.plot(epipole[0] / epipole[2], epipole[1] / epipole[2], 'r*')

