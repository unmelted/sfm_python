from curses import KEY_A1
import numpy as np
import matplotlib.pyplot as plt
from pytransform3d.plot_utils import make_3d_axis
from pytransform3d.rotations import active_matrix_from_intrinsic_euler_xyz
from  pytransform3d.camera import make_world_grid, world2image, plot_camera
from pytransform3d.transformations import transform_from, plot_transform
from cam_group import *



def plot_cameras(cameras):
    plt.figure(figsize=(24, 10))
    ax = make_3d_axis(1, 121, unit="m")
    plot_transform(ax)
    focal_length = 10
    j  = 0   
    sensor_size = np.array([1920, 1080])

    for camera in cameras :
        cam2world = transform_from(camera.R, camera.t.T)
        plot_camera(ax, M=camera.K, cam2world=cam2world, sensor_size=sensor_size, virtual_image_distance=1)
        j += 1

        if j == 3 : 
            break

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