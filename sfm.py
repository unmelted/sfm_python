import os
import open3d as o3d
import logging
from util import *
from pair import *


class SFM:
    """Represents the main reconstruction loop"""

    #def __init__(self, view1, view2, indices1, indices2, K1, K2):
    def __init__(self, pairobj):    
        self.pair = pairobj

        self.done = None 
        self.points_3D = np.zeros((0, 3))  # reconstructed 3D points
        self.point_counter = 0  # keeps track of the reconstructed points
        self.point_map = {}  # a dictionary of the 2D points that contributed to a given 3D point
        self.errors = None  #  mean reprojection errors taken at the end of every new view being added

        if not os.path.exists(self.pair.camera1.view.root_path + '/points'):
            os.makedirs(self.pair.camera1.view.root_path + '/points')

        # store results in a root_path/points
        self.results_path = os.path.join(self.pair.camera1.view.root_path, 'points')

    def remove_mapped_points(self):
        """Removes points that have already been reconstructed in the completed views"""

        inliers1 = []
        inliers2 = []

        for i in range(len(self.pair.inliers1)):
            if (self.pair.match.inliers1[i]) not in self.point_map:            
                inliers1.append(self.pair.inliers1[i])
                inliers2.append(self.pair.inliers2[i])

        self.pair.inliers1.clear()
        self.pair.inliers2.clear()        
        self.pair.inliers1 = inliers1
        self.pair.inliers2 = inliers2

    def compute_pose(self, is_baseline=False):
        """Computes the pose of the new view"""

        # procedure for baseline pose estimation
        if is_baseline and self.pair.camera2.view:
            print("Base line true .. Compute pose ")
            self.pair.camera2.R, self.pair.camera2.t = self.get_pose()
            print("baseline -- R : ", self.pair.camera2.R)
            print("baseline -- T : ", self.pair.camera2.t)

            rpe1, rpe2 = self.triangulate_with()
            self.errors = (np.mean(rpe1))
            self.errors = (np.mean(rpe2))

            self.done = True

        # procedure for estimating the pose of all other views
        else:
            print("Base line false .. Compute pose PNP ")
            self.pair.camera2.view.R, self.pair.camera2.view.t = self.compute_pose_PNP(self.pair.camera1.view)
            print("view -- R ", self.pair.camera2.view.R)
            print("view -- T ", self.pair.camera2.view.t)

            # reconstruct unreconstructed points from all of the previous views
            _ = remove_outliers_using_F(self.pair.camera1.view, self.pair.camera2.view, self.pair.match)
            self.remove_mapped_points()
            _, rpe = self.triangulate_with()
            errors += rpe

            self.done = True
            self.errors = np.mean(errors)

    def triangulate_with(self):
        """Triangulates 3D points from two views whose poses have been recovered. Also updates the point_map dictionary"""

        K_inv = np.linalg.inv(self.pair.camera2.K)
        P1 = np.hstack((self.pair.camera1.R, self.pair.camera1.t))
        P2 = np.hstack((self.pair.camera2.R, self.pair.camera2.t))

        pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=self.pair.camera1.view.keypoints,
                                                                  keypoints2=self.pair.camera2.view.keypoints,
                                                                  index_list1=self.pair.inliers1,
                                                                  index_list2=self.pair.inliers2)
        pixel_points1 = cv2.convertPointsToHomogeneous(pixel_points1)[:, 0, :]
        pixel_points2 = cv2.convertPointsToHomogeneous(pixel_points2)[:, 0, :]
        reprojection_error1 = []
        reprojection_error2 = []

        for i in range(len(pixel_points1)):

            u1 = pixel_points1[i, :]
            u2 = pixel_points2[i, :]

            u1_normalized = K_inv.dot(u1)
            u2_normalized = K_inv.dot(u2)

            point_3D = get_3D_point(u1_normalized, P1, u2_normalized, P2)
            self.points_3D = np.concatenate((self.points_3D, point_3D.T), axis=0)

            error1 = calculate_reprojection_error(point_3D, u1[0:2], self.pair.camera1.K, self.pair.camera1.R, self.pair.camera1.t)
            reprojection_error1.append(error1)
            error2 = calculate_reprojection_error(point_3D, u2[0:2], self.pair.camera2.K, self.pair.camera2.R, self.pair.camera2.t)
            reprojection_error2.append(error2)

            # updates point_map with the key (index of view, index of point in the view) and value point_counter
            # multiple keys can have the same value because a 3D point is reconstructed using 2 points
            self.point_map[self.pair.inliers1[i]] = self.point_counter
            self.point_map[self.pair.inliers2[i]] = self.point_counter
            self.point_counter += 1

        return reprojection_error1, reprojection_error2

    def compute_pose_PNP(self, view):
        """Computes pose of new view using perspective n-point"""

        if view.feature_type in ['sift', 'surf']:
            matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # collects all the descriptors of the reconstructed views
        old_descriptors = []
        for old_view in self.done:
            old_descriptors.append(old_view.descriptors)

        # match old descriptors against the descriptors in the new view
        matcher.add(old_descriptors)
        matcher.train()
        matches = matcher.match(queryDescriptors=view.descriptors)
        points_3D, points_2D = np.zeros((0, 3)), np.zeros((0, 2))

        # build corresponding array of 2D points and 3D points
        for match in matches:
            old_image_idx, new_image_kp_idx, old_image_kp_idx = match.imgIdx, match.queryIdx, match.trainIdx

            if (old_image_idx, old_image_kp_idx) in self.point_map:

                # obtain the 2D point from match
                point_2D = np.array(view.keypoints[new_image_kp_idx].pt).T.reshape((1, 2))
                points_2D = np.concatenate((points_2D, point_2D), axis=0)

                # obtain the 3D point from the point_map
                point_3D = self.points_3D[self.point_map[(old_image_idx, old_image_kp_idx)], :].T.reshape((1, 3))
                points_3D = np.concatenate((points_3D, point_3D), axis=0)

        # compute new pose using solvePnPRansac
        _, R, t, _ = cv2.solvePnPRansac(points_3D[:, np.newaxis], points_2D[:, np.newaxis], self.K, None,
                                        confidence=0.99, reprojectionError=8.0, flags=cv2.SOLVEPNP_DLS)
        R, _ = cv2.Rodrigues(R)
        return R, t

    def get_pose(self):
        """Computes and returns the rotation and translation components for the second view"""

        F , self.pair.inliers1, self.pair.inliers2 = remove_outliers_using_F(self.pair.camera1.view, self.pair.camera2.view, self.pair.indices1, self.pair.indices2)

        K = self.pair.camera2.K
        E = K.T @ F @ K  # compute the essential matrix from the fundamental matrix
        logging.info("Computed essential matrix")
        logging.info("Choosing correct pose out of 4 solutions")

        print("get_pose.. F: ", F)
        print("get_pose.. normal E: ", E)        
        print('Computed essential matrix:', (-E / E[0][1]))

        return self.check_pose(E)

    def check_pose(self, E):
        """Retrieves the rotation and translation components from the essential matrix by decomposing it and verifying the validity of the 4 possible solutions"""
        K = self.pair.camera2.K
        R1, R2, t1, t2 = get_camera_from_E(E)  # decompose E

        if not check_determinant(R1):
            R1, R2, t1, t2 = get_camera_from_E(-E)  # change sign of E if R1 fails the determinant test


        # solution 1
        reprojection_error, points_3D = self.triangulate(K, R1, t1)
        # check if reprojection is not faulty and if the points are correctly triangulated in the front of the camera
        if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R1, t1))):

            # solution 2
            reprojection_error, points_3D = self.triangulate(K, R1, t2)
            if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R1, t2))):

                # solution 3
                reprojection_error, points_3D = self.triangulate(K, R2, t1)
                if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R2, t1))):

                    # solution 4
                    return R2, t2

                else:
                    return R2, t1

            else:
                return R1, t2

        else:
            return R1, t1

    def triangulate(self, K, R, t):
        """Triangulate points between the baseline views and calculates the mean reprojection error of the triangulation"""
        K_inv = np.linalg.inv(K)
        P1 = np.hstack((self.pair.camera1.R, self.pair.camera1.t))
        P2 = np.hstack((R, t))

        # only reconstructs the inlier points filtered using the fundamental matrix
        pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=self.pair.camera1.view.keypoints,
                                                                  keypoints2=self.pair.camera2.view.keypoints,
                                                                  index_list1=self.pair.inliers1,
                                                                  index_list2=self.pair.inliers2)

        # convert 2D pixel points to homogeneous coordinates
        pixel_points1 = cv2.convertPointsToHomogeneous(pixel_points1)[:, 0, :]
        pixel_points2 = cv2.convertPointsToHomogeneous(pixel_points2)[:, 0, :]

        reprojection_error = []

        points_3D = np.zeros((0, 3))  # stores the triangulated points

        for i in range(len(pixel_points1)):
            u1 = pixel_points1[i, :]
            u2 = pixel_points2[i, :]

            # convert homogeneous 2D points to normalized device coordinates
            u1_normalized = K_inv.dot(u1)
            u2_normalized = K_inv.dot(u2)

            # calculate 3D point
            point_3D = get_3D_point(u1_normalized, P1, u2_normalized, P2)

            # calculate reprojection error
            error = calculate_reprojection_error(point_3D, u2[0:2], K, R, t)
            reprojection_error.append(error)

            # append point
            points_3D = np.concatenate((points_3D, point_3D.T), axis=0)

        return np.mean(reprojection_error), points_3D


    def plot_points(self):
        """Saves the reconstructed 3D points to ply files using Open3D"""

        number = len(self.done)
        filename = os.path.join(self.results_path, str(number) + '_images.ply')
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self.points_3D)
        o3d.io.write_point_cloud(filename, pcd)
