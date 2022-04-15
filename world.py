import os
import sys
import numpy as np

class World(object):

    def __init__(self) :
        self.world_type = None
        self.stadium = None
        self.event = None
        self.world_points = None

    def get_world(self) :
        '''insert world data by connecting db or storage / points insert'''

        self.stadium = "Football"
        self.event = "football"
        self.world_points = np.array([[226, 755, 0],
                                    [572, 755, 0],
                                    [572, 608, 0],
                                    [226, 608, 0]])

        print(" Get World .. " , self.world_points)

