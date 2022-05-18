import enum
import os
from cv2 import CV_32FC3
import numpy as np
import matplotlib.pyplot as plt
import cv2
import logging
import pickle
from adjust import *
from mathutil import *

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

        self.H = None
        self.indices1_mask = []  # indices of the matched keypoints in the first view
        self.indices2_mask = []  # indices of the matched keypoints in the second view
        self.distances_mask = []  # distance between the matched keypoints in the first view

        if camera1.view.feature_type in ['sift', 'surf']:
            self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        else:
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        if not match_path:
            self.get_matches(self.camera1.view, self.camera2.view)
        else :
            self.read_matches()
        

    def draw_matches(self):
        if not os.path.exists(os.path.join(self.camera1.view.root_path, 'draw')):
            os.makedirs(os.path.join(self.camera1.view.root_path, 'draw'))

        filename = os.path.join(self.camera1.view.root_path +'/draw' , self.image_name1 + '_' + self.image_name2 + '_match.png')
        drw_match = np.concatenate((self.camera1.view.image, self.camera2.view.image), axis=1)
        print("draw_matches.. name : ", self.image_name1, len(self.inliers1))

        for i in range(0, len(self.inliers1)) :
            x1 = self.camera1.view.keypoints[self.indices1[i]].pt[0]
            x2 = self.camera2.view.keypoints[self.indices2[i]].pt[0]
            y1 = self.camera1.view.keypoints[self.indices1[i]].pt[1]
            y2 = self.camera2.view.keypoints[self.indices2[i]].pt[1]            
            cv2.line(drw_match, (int(x1), int(y1)), (int(x2 + 3840), int(y2)), (255, 100, 200), 2)

        cv2.imwrite(filename, drw_match)


    def check_points_3d(self):
        print("check_points_3d ", len(self.points_3D), self.points_3D.shape)
        #sorted_3d = sorted(self.points_3D, key=lambda x: x[2])
        unique = np.unique(self.points_3D, axis=0)
        print("unique .. ", len(unique))
        for i in range(len(unique)) :
            print(("{0:0.5f} {1:0.5f} {2:0.5f} {3:0.2f} {4:0.2f} {5:0.2f} {6:0.2f}").format(unique[i][0], unique[i][1], unique[i][2], unique[i][3], unique[i][4], unique[i][5], unique[i][6]))

        index = np.lexsort((unique[:, 0], unique[:, 2]))
        unique = unique[index]
        unique[:, 2] = np.round(unique[:, 2], 2)
        
        # hist_z =  np.histogram(unique[:, 2], bins=abins)
        # print(hist_z)
        # maxz = np.max(hist_z[0])
        # print("check__ ", maxz)        
        # l = list(hist_z[0])
        # maxz_index = l.index(maxz)
        # print("check___  ", maxz_index)
        # maxz_val = hist_z[1][maxz_index]
        # print("check____  ", maxz_val)

        zunique, counts = np.unique(unique[:, 2], return_counts=True)
        max_index = np.argmax(counts)
        zvalue = zunique[max_index]
        print("hist __ " , max_index, zunique[max_index], unique[max_index, :])

        find = np.where(unique == zvalue)
        print(find)

        cam1_pt = []
        cam2_pt = []

        for i in range(len(find[0])) :
            print(unique[find[0][i]])
            # print( ([unique[find[0][i]][3] , unique[find[0][i]][4]]) )
            # print( ([unique[find[0][i]][5] , unique[find[0][i]][6]]) )
            cam1_pt.append([unique[find[0][i]][3] , unique[find[0][i]][4]])
            cam2_pt.append([unique[find[0][i]][5] , unique[find[0][i]][6]])

        # print(cam1_pt)
        # print(cam2_pt)
        cam1_np = np.array(cam1_pt)
        cam2_np = np.array(cam2_pt)

        M , mask = cv2.findHomography(cam1_np, cam2_np, cv2.RANSAC, 1)
        print(M)

        ori = np.float32([ [2214.09, 75.21], [2701.92, 70.73], [2481.49, 145.95] ]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(ori, M)
        print(dst)

        # abins=np.arange(min(unique[:, 2]), max(unique[:, 2])+0.01, step=0.1)            
        # plt.hist(unique[:, 2], bins=abins)
        # plt.show()

    def get_matches(self, view1, view2):
        """Extracts feature matches between two views"""
        self.match = self.matcher.match(view1.descriptors, view2.descriptors)
        self.match = sorted(self.match, key=lambda x: x.distance)

        refine = True
        if refine == True :
            del_x = np.empty( (0), dtype=np.float64)
            del_y = np.empty( (0), dtype=np.float64)

            for i in range(0, len(self.match)) :
                x2 = self.camera2.view.keypoints[self.match[i].trainIdx].pt[0]
                y2 = self.camera2.view.keypoints[self.match[i].trainIdx].pt[1]                
                x1 = self.camera1.view.keypoints[self.match[i].queryIdx].pt[0]
                y1 = self.camera1.view.keypoints[self.match[i].queryIdx].pt[1]

                del_x = np.append(del_x, np.array(x2 - x1).reshape((1)), axis = 0)
                del_y = np.append(del_y, np.array(y2 - y1).reshape((1)), axis = 0)

            d_atan = np.arctan2(del_x, del_y)
            d_ma, d_threshold  = calculate_mahalanobis(d_atan)

            if d_threshold == 0 :
                pass
            else : 
                print("refine ouliers .. before ", len(self.match))
                cnt = 0
                new_mat = []
                for i in range(0, len(self.match)) :
                    if( d_ma[i] < d_threshold ) :
                        new_mat.append(self.match[i])
                    else :
                        cnt += 1

                self.match = new_mat
                print("refine ouliers .. after ", cnt, len(self.match))                

        # store match components in their respective lists
        for i in range(len(self.match)):
            self.indices2.append(self.match[i].trainIdx)            
            self.indices1.append(self.match[i].queryIdx)
            self.distances.append(self.match[i].distance)


        # if(view1.bMask > 0 and view2.bMask > 0) :
        #     print("get matches .. with mask !! ")
        #     self.match_mask = self.matcher.match(view1.descriptors_mask, view2.descriptors_mask)
        #     self.match_mask = sorted(self.match_mask, key=lambda x: x.distance)

        #     # store match components in their respective lists
        #     for i in range(len(self.match_mask)):
        #         self.indices2_mask.append(self.match_mask[i].trainIdx)            
        #         self.indices1_mask.append(self.match_mask[i].queryIdx)
        #         self.distances_mask.append(self.match_mask[i].distance)


        #logging.info("Computed matches between view %s and view %s", self.image_name1, self.image_name2)
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

        if(self.camera1.view.bMask > 0 and self.camera2.view.bMask > 0) :
            temp_array = []
            for i in range(len(self.indices1_mask)):
                temp = (self.distances_mask[i], self.indices1_mask[i], self.indices2_mask[i])
                temp_array.append(temp)

            matches_file2 = open(os.path.join(self.root_path, 'matches', self.image_name1 + '_' + self.image_name2 + '_mask.pkl'), 'wb')
            pickle.dump(temp_array, matches_file2)
            matches_file2.close()


    def read_matches(self):
        """Reads matches from file"""

        try:
            self.match = pickle.load(
                open(
                    os.path.join(self.root_path, 'matches', self.image_name1 + '_' + self.image_name2 + '.pkl'),
                    "rb"
                )
            )
            #logging.info("Read matches from file for view pair %s %s", self.image_name1, self.image_name2)

            for point in self.match:
                self.distances.append(point[0])
                self.indices1.append(point[1])
                self.indices2.append(point[2])

        except FileNotFoundError:
            logging.error("Pkl file not found for match %s_%s. Computing from scratch", self.image_name1, self.image_name2)
            self.get_matches(self.view1, self.view2)

        if(self.camera1.view.bMask == 0 or self.camera2.view.bMask == 0) :
            return

        try:
            self.match_mask = pickle.load(open(os.path.join(self.root_path, 'matches', self.image_name1 + '_' + self.image_name2 + '_mask.pkl'),"rb"))
            #logging.info("Read matches from file for view pair %s %s", self.image_name1, self.image_name2)

            for point in self.match_mask:
                self.distances_mask.append(point[0])
                self.indices1_mask.append(point[1])
                self.indices2_mask.append(point[2])

        except FileNotFoundError:
            logging.error("Pkl mask file not found for match %s_%s. Computing from scratch", self.image_name1, self.image_name2)


    def find_homography_from_points(self):
        print("find homography start.. ")
        method = cv2.RANSAC
        ransacReprojThreshold = 3

        srcpts = np.float32(self.indices1_mask).reshape(-1, 1, 2)
        dstpts = np.float32(self.indices2_mask).reshape(-1, 1, 2)
        print(srcpts.shape, dstpts.shape)       
        H, mask = cv2.findHomography(dstpts, srcpts, method, ransacReprojThreshold)
        print(H)
        # Af = cv2.estimateAffine2D(dstpts, srcpts, method)
        # print("Affine .. ")
        # print(Af)

        pt1 = [[708, 183], [120, 1614], [2766, 1485], [2091, 144]] # ncaa 
        pt2 = [[798, 218], [97, 1617], [2715, 1510], [2163, 179]] # ncaa
        np_pt1 = np.array(pt1)
        np_pt2 = np.array(pt2)
        print("validate homography.. ")
        H2, mask = cv2.findHomography(np_pt2, np_pt1)
        print(H2)

        dst = np.full((self.camera2.view.image_height, self.camera2.view.image_width, 3), 255, np.uint8)
        dst = cv2.warpPerspective(self.camera2.view.image, H, (self.camera2.view.image_width, self.camera2.view.image_height))
        dst2 = np.full((self.camera2.view.image_height, self.camera2.view.image_width, 3), 255, np.uint8)
        dst2 = cv2.warpPerspective(self.camera2.view.image, H2, (self.camera2.view.image_width, self.camera2.view.image_height))      

        cv2.imwrite("warp_test1.png", dst)
        cv2.imwrite("warp_test2.png", dst2)

        return H, mask

    def compute_camera_relative(self, ref, target) :
        newR = np.dot(target.R, ref.R.T)
        temp = -1* np.dot(ref.R.T, ref.t)
        newT = np.dot(target.R, temp) + target.t
        return newR, newT

    def find_homography_from_disp(self):
        print("find_homography_from_disp .. ")
        K_inv = np.linalg.inv(self.camera2.K)        
        rR, rT = self.compute_camera_relative(self.camera1, self.camera2)
        normal = np.array([0, 0, 1], dtype=float)
        normal1 = np.dot(self.camera1.R, normal)
        origin = np.array([0, 0, 0], dtype=float)
        origin1 = np.dot(self.camera1.R, origin) + self.camera1.t
        d_inv1 = 1.0/ normal1.dot(origin1)
        temp = []
        if(np. all(origin1 == 0)) :
            temp = np.array([0, 0, 0])            
        else :
            temp = np.dot(d_inv1, rT)            

        # print("check .. 4", temp.shape, temp)
        # print("check .. 5", normal1)
        euc_H = rR + np.dot(temp , normal1)
        H = np.dot(np.dot(self.camera2.K, euc_H), K_inv)
        euc_H = euc_H / euc_H[2][2]
        H = H/ H[2][2]
        #print(euc_H)        
        print(H)

        dst = np.full((self.camera1.view.image_height, self.camera1.view.image_width, 3), 255, np.uint8)
        dst = cv2.warpPerspective(self.camera1.view.image, H, (self.camera1.view.image_width, self.camera1.view.image_height))
        cv2.imwrite("warp_dist_test1.png", dst)

        return H

    def create_pair(cameras):
        """Computes matches between every possible pair of views and stores in a dictionary"""

        match_path = False
        if os.path.exists(os.path.join(cameras[0].view.root_path, 'matches')):
            match_path = True

        pairs = {}

        for j in range(1, len(cameras)):
            key = (cameras[j-1].view.name, cameras[j].view.name)
            pairs[key] = Pair(cameras[j-1], cameras[j], match_path)

        return pairs