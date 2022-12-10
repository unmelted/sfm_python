import os
import sys
import numpy as np
import cv2

from mathutil import *
from spline import *

class World(object):

    def __init__(self) :
        self.world_type = None
        self.stadium = './ground/Soccer_Half.png'
        self.event = None
        self.world_points = None
        self.world_npoints = None
        self.wcenter = []
        self.new_center = []

        self.spline = Interpolate()
        self.root_path = None

    def set_world(self, world_pts) :
        print("world setworld is calll --- ", world_pts)
        p = np.array([[world_pts[0], world_pts[1], 0], [world_pts[2], world_pts[3], 0], [
                world_pts[4], world_pts[5], 0], [world_pts[6], world_pts[7], 0]])
        pn = get_normalized_point(p)
        self.world_points = np.array(p)
        self.world_npoints = np.array(pn)

    def get_world(self) :
        return self.world_npoints

    def calculate_center_inworld(self, cameras, root_path) :
        self.root_path = root_path
        ground = cv2.imread(self.stadium)
        center = [1920, 1080, 1] #4k standard
        # centern = get_normalized_point(center)

        np_center = np.array(center)
        np_world = self.world_points

        print("draw_center_inworld.." , np_center, np_world)

        for i in range(len(cameras)):
            print("-- in loop ", i, cameras[i].pts_3d)
            h, _ = cv2.findHomography(cameras[i].pts_3d, np_world)
            w_center = np.dot(h , np_center)
            w_cenx = w_center[0] / w_center[2]
            w_ceny = w_center[1] / w_center[2]
            print(cameras[i].view.name, w_cenx, w_ceny)         
            self.wcenter.append([w_cenx, w_ceny])   
            cv2.circle(ground, (int(w_cenx), int(w_ceny)), 2, (255, 0, 0), -1)

        filename = root_path + '/dbg_ground.png'
        print(self.wcenter)
        cv2.imwrite(filename, ground)

        self.spline.store_posisition(self.wcenter)


    def interpolate_center_inworld(self, cameras) :

        filename = self.root_path + '/dbg_ground.png'        
        self.spline.make_trajectory()
        self.spline.show_trajectory(filename, self.root_path)

        np_world = self.world_points
        
        for i in range(len(cameras)) :

            np_fitcenter = np.array([self.spline.x_fit[i], self.spline.y_fit[i], 1])

            h, _ = cv2.findHomography(np_world, cameras[i].pts_3d)
            new_center = np.dot(h, np_fitcenter)
            new_cenx = new_center[0] / new_center[2]
            new_ceny = new_center[1] / new_center[2]
            print("-- new cen ", new_cenx, new_ceny)
            self.new_center.append([new_cenx, new_ceny])


        return self.new_center

