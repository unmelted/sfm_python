import os
import sys

class World(object):

    def __init__(self) :
        self.world_type = None
        self.event = None
        self.world_points = []

    def get_world(self) :
        '''insert world data by connecting db or storage / points insert'''
        self.stadium = "Football"
        self.event = "football"
        pt1 = [220, 691]
        self.world_points.append(pt1)        
        pt2 = [427, 694]
        self.world_points.append(pt2)
        pt3 = [427, 574]
        self.world_points.append(pt3)        
        pt4 = [217, 578]
        self.world_points.append(pt4)

