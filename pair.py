import enum
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
import logging
import pickle


class Pair:
    """Represents a feature matches between two views"""

    def __init__(self, camera1, camera2, match_path):

        self.indices1 = []  # indices of the matched keypoints in the first view
        self.indices2 = []  # indices of the matched keypoints in the second view
        self.distances = []  # distance between the matched keypoints in the first view
        self.image_name1 = camera1.view.name  # name of the first view
        self.image_name2 = camera2.view.name  # name of the second view
        self.root_path = camera1.view.root_path  # root directory containing the image folder
        self.inliers1 = None  # list to store the indices of the keypoints from the first view not removed using the fundamental matrix
        self.inliers2 = None  # list to store the indices of the keypoints from the second view not removed using the fundamental matrix
        self.camera1 = camera1
        self.camera2 = camera2
        self.match = None
        self.points_3D = np.array([0, 0, 0, 0, 0, 0, 0])

        if camera1.view.feature_type in ['sift', 'surf']:
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        else:
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        if not match_path:
            self.get_matches(self.camera1.view, self.camera2.view)
        else :
            self.read_matches()
        
    def check_points_3d(self):
        print("check_points_3d ", len(self.points_3D), self.points_3D.shape)
        #sorted_3d = sorted(self.points_3D, key=lambda x: x[2])
        unique = np.unique(self.points_3D, axis=0)
        print("unique .. ", len(unique))
        index = np.lexsort((unique[:, 0], unique[:, 2]))
        unique = unique[index]
        unique[:, 2] = np.round(unique[:, 2], 2)
        abins=np.arange(min(unique[:, 2]), max(unique[:, 2])+0.01, step=0.1)
        hist_z =  np.histogram(unique[:, 2], bins=abins)
        print(hist_z)
        maxz = np.max(hist_z[0])
        print("check__ ", maxz)        
        l = list(hist_z[0])
        maxz_index = l.index(maxz)
        print("check___  ", maxz_index)
        maxz_val = hist_z[1][maxz_index]
        print("check____  ", maxz_val)

        # for i in range(len(self.points_3D)) :
        #     print(sorted_3d[i][0], sorted_3d[i][1], sorted_3d[i][2], sorted_3d[i][3], sorted_3d[i][4], sorted_3d[i][5], sorted_3d[i][6])
        for i in range(len(unique)) :
            print(unique[i][0], unique[i][1], unique[i][2], unique[i][3], unique[i][4], unique[i][5], unique[i][6])
        plt.hist(unique[:, 2], bins=abins)
        plt.show()

    def get_matches(self, view1, view2):
        """Extracts feature matches between two views"""

        self.match = self.matcher.match(view1.descriptors, view2.descriptors)
        self.match = sorted(self.match, key=lambda x: x.distance)

        # store match components in their respective lists
        for i in range(len(self.match)):
            self.indices2.append(self.match[i].trainIdx)            
            self.indices1.append(self.match[i].queryIdx)
            self.distances.append(self.match[i].distance)


        logging.info("Computed matches between view %s and view %s", self.image_name1, self.image_name2)
        self.write_matches()

    def write_matches(self):
        """Writes a match to a pkl file in the root_path/matches directory"""

        if not os.path.exists(os.path.join(self.root_path, 'matches')):
            os.makedirs(os.path.join(self.root_path, 'matches'))

        temp_array = []
        for i in range(len(self.indices1)):
            temp = (self.distances[i], self.indices1[i], self.indices2[i])
            temp_array.append(temp)

        matches_file = open(os.path.join(self.root_path, 'matches', self.image_name1 + '_' + self.image_name2 + '.pkl'), 'wb')
        pickle.dump(temp_array, matches_file)
        matches_file.close()

    def read_matches(self):
        """Reads matches from file"""

        try:
            self.match = pickle.load(
                open(
                    os.path.join(self.root_path, 'matches', self.image_name1 + '_' + self.image_name2 + '.pkl'),
                    "rb"
                )
            )
            logging.info("Read matches from file for view pair %s %s", self.image_name1, self.image_name2)

            for point in self.match:
                self.distances.append(point[0])
                self.indices1.append(point[1])
                self.indices2.append(point[2])

        except FileNotFoundError:
            logging.error("Pkl file not found for match %s_%s. Computing from scratch", self.image_name1, self.image_name2)
            self.get_matches(self.view1, self.view2)


    def create_pair(cameras):
        """Computes matches between every possible pair of views and stores in a dictionary"""

        match_path = False
        print(cameras)

        if os.path.exists(os.path.join(cameras[0].view.root_path, 'matches')):
            match_path = True

        pairs = {}

        for j in range(1, len(cameras)):
            key = (cameras[j-1].view.name, cameras[j].view.name)
            pairs[key] = Pair(cameras[j-1], cameras[j], match_path)

        return pairs
