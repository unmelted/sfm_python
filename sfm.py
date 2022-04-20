import os
from util import *
import open3d as o3d

class SFM:
    """Represents the main reconstruction loop"""

    def __init__(self, views, pairs):

        self.views = views  # list of views
        self.matches = pairs  # dictionary of matches
        self.names = []  # image names
        self.done = []  # list of views that have been reconstructed
        self.points_3D = np.zeros((0, 3))  # reconstructed 3D points
        self.point_counter = 0  # keeps track of the reconstructed points
        self.point_map = {}  # a dictionary of the 2D points that contributed to a given 3D point
        self.errors = []  # list of mean reprojection errors taken at the end of every new view being added

        for view in self.views:
            self.names.append(view.name)

        if not os.path.exists(self.views[0].root_path + '/points'):
            os.makedirs(self.views[0].root_path + '/points')

        # store results in a root_path/points
        self.results_path = os.path.join(self.views[0].root_path, 'points')

    def get_index_of_view(self, view):
        """Extracts the position of a view in the list of views"""

        return self.names.index(view.name)

    def remove_mapped_points(self, match_object, image_idx):
        """Removes points that have already been reconstructed in the completed views"""

        inliers1 = []
        inliers2 = []

        for i in range(len(match_object.inliers1)):
            if (image_idx, match_object.inliers1[i]) not in self.point_map:
                inliers1.append(match_object.inliers1[i])
                inliers2.append(match_object.inliers2[i])

        match_object.inliers1 = inliers1
        match_object.inliers2 = inliers2

    def compute_pose(self, pair, is_baseline=False):
        """Computes the pose of the new view"""

        # procedure for baseline pose estimation
        if is_baseline:
            print("view -- 1 : 2 ", pair.camera1.view.name, pair.camera2.view.name)
            pair.camera1.R = np.eye(3, 3)  # identity rotation since the first view is said to be at the origin            
            match_object = self.matches[(pair.camera1.view.name, pair.camera2.view.name)]
            pair.camera2.R, pair.camera2.t = self.get_pose(pair)
            print("baseline -- R : ", pair.camera2.R)
            print("baseline -- T : ", pair.camera2.t)

            rpe1, rpe2 = self.triangulate_with(pair)
            self.errors.append(np.mean(rpe1))
            self.errors.append(np.mean(rpe2))

            self.done.append(pair.camera1.view)
            self.done.append(pair.camera2.view)

        # procedure for estimating the pose of all other views
        else:

            pair.camera2.R, pair.camera2.t, pair.camera2.Rvec = self.compute_pose_pnp(pair.camera2.view, pair.camera2.K)
            print("view -- R ", pair.camera2.R)
            print("view -- T ", pair.camera2.t)
            print("view -- Rvec ", pair.camera2.Rvec)
            errors = []
            print("-- view2 : ", pair.camera2.view.name)
            
            # reconstruct unreconstructed points from all of the previous views
            for i, old_view in enumerate(self.done):
                print(" -- oldview name : camera2 name  -- ", old_view.name, pair.camera2.view.name)
                if(old_view.name, pair.camera2.view.name) in self.matches : 
                    match_object = self.matches[(old_view.name, pair.camera2.view.name)]
                    _, pair.inliers1, pair.inliers2 = remove_outliers_using_F(old_view, pair.camera2.view, pair.indices1, pair.indices2)
                    self.remove_mapped_points(match_object, i)
                    _, rpe = self.triangulate_with(pair, old_view, pair.camera2.view)
                    errors += rpe

            self.done.append(pair.camera2.view)
            self.errors.append(np.mean(errors))

    def get_pose(self, pair):
        """Computes and returns the rotation and translation components for the second view"""

        F , pair.inliers1, pair.inliers2 = remove_outliers_using_F(pair.camera1.view, pair.camera2.view, pair.indices1, pair.indices2)
        pair.camera2.F = F
        K = pair.camera2.K
        E = K.T @ F @ K  # compute the essential matrix from the fundamental matrix
        # logging.info("Computed essential matrix")
        # logging.info("Choosing correct pose out of 4 solutions")

        # print("get_pose.. F: ", F)
        # print("get_pose.. normal E: ", E)        
        # print('Computed essential matrix:', (-E / E[0][1]))

        return self.check_pose(pair, E)

    def check_pose(self, pair, E):
        """Retrieves the rotation and translation components from the essential matrix by decomposing it and verifying the validity of the 4 possible solutions"""
        K = pair.camera2.K
        R1, R2, t1, t2 = get_camera_from_E(E)  # decompose E

        if not check_determinant(R1):
            R1, R2, t1, t2 = get_camera_from_E(-E)  # change sign of E if R1 fails the determinant test


        # solution 1
        reprojection_error, points_3D = self.triangulate(pair, K, R1, t1)
        # check if reprojection is not faulty and if the points are correctly triangulated in the front of the camera
        if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R1, t1))):

            # solution 2
            reprojection_error, points_3D = self.triangulate(pair, K, R1, t2)
            if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R1, t2))):

                # solution 3
                reprojection_error, points_3D = self.triangulate(pair, K, R2, t1)
                if reprojection_error > 100.0 or not check_triangulation(points_3D, np.hstack((R2, t1))):

                    # solution 4
                    return R2, t2

                else:
                    return R2, t1

            else:
                return R1, t2

        else:
            return R1, t1

    def triangulate_with(self, pair, view1=None, view2=None):
        """Triangulates 3D points from two views whose poses have been recovered. Also updates the point_map dictionary"""

        K_inv = np.linalg.inv(pair.camera2.K)
        P1 = np.hstack((pair.camera1.R, pair.camera1.t))
        P2 = np.hstack((pair.camera2.R, pair.camera2.t))
        pixel_points1 = None
        pixle_points2 = None

        if(view1 == None or view2 == None) :
            pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=pair.camera1.view.keypoints,
                                                                    keypoints2=pair.camera2.view.keypoints,
                                                                    index_list1=pair.inliers1,
                                                                    index_list2=pair.inliers2)
        else : 
            match_object = self.matches[(view1.name, view2.name)]
            pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=pair.camera1.view.keypoints,
                                                                    keypoints2=pair.camera2.view.keypoints,
                                                                    index_list1=match_object.inliers1,
                                                                    index_list2=match_object.inliers2)


        pixel_points1 = cv2.convertPointsToHomogeneous(pixel_points1)[:, 0, :]
        pixel_points2 = cv2.convertPointsToHomogeneous(pixel_points2)[:, 0, :]
        reprojection_error1 = []
        reprojection_error2 = []
        
        # print("K_inv : ", K_inv)

        for i in range(len(pixel_points1)):

            u1 = pixel_points1[i, :]
            u2 = pixel_points2[i, :]

            u1_normalized = K_inv.dot(u1)
            u2_normalized = K_inv.dot(u2)

            point_3D = get_3D_point(u1_normalized, P1, u2_normalized, P2)
            #print("pix {} {} - u {} {} 3D {} ".format(pixel_points1[i, :], pixel_points2[i, :], u1_normalized, u2_normalized, point_3D.T))

            self.points_3D = np.concatenate((self.points_3D, point_3D.T), axis=0)

            error1 = calculate_reprojection_error(point_3D, u1[0:2], pair.camera1.K, pair.camera1.R, pair.camera1.t)
            reprojection_error1.append(error1)
            error2 = calculate_reprojection_error(point_3D, u2[0:2], pair.camera2.K, pair.camera2.R, pair.camera2.t)
            reprojection_error2.append(error2)

            # updates point_map with the key (index of view, index of point in the view) and value point_counter
            # multiple keys can have the same value because a 3D point is reconstructed using 2 points
            self.point_map[(self.get_index_of_view(pair.camera1.view), pair.inliers1[i])] = self.point_counter
            self.point_map[(self.get_index_of_view(pair.camera2.view), pair.inliers2[i])] = self.point_counter
            self.point_counter += 1

        return reprojection_error1, reprojection_error2

    def compute_pose_pnp(self, view, K):
        """Computes pose of new view using perspective n-point"""
        Rvec = np.zeros((3,1), dtype=float)
        if view.feature_type in ['sift', 'surf']:
            matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        else:
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # collects all the descriptors of the reconstructed views
        old_descriptors = []
        for old_view in self.done:
            old_descriptors.append(old_view.descriptors)
            print(" old view name : ", old_view.name)            

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
        # print("PNP .. point 3D", np.shape(points_3D))
        # print(points_3D)
        _, Rvec, t, _ = cv2.solvePnPRansac(points_3D[:, np.newaxis], points_2D[:, np.newaxis], K, None,
                                        confidence=0.99, reprojectionError=8.0, flags=cv2.SOLVEPNP_DLS)

        R, _ = cv2.Rodrigues(Rvec)
        return R, t, Rvec

    def plot_points(self):
        """Saves the reconstructed 3D points to ply files using Open3D"""

        number = len(self.done)
        filename = os.path.join(self.results_path, str(number) + '_images.ply')
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self.points_3D)
        o3d.io.write_point_cloud(filename, pcd)

    def triangulate(self, pair, K, R, t):
        """Triangulate points between the baseline views and calculates the mean reprojection error of the triangulation"""
        K_inv = np.linalg.inv(K)
        P1 = np.hstack((pair.camera1.R, pair.camera1.t))
        P2 = np.hstack((R, t))

        # only reconstructs the inlier points filtered using the fundamental matrix
        pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=pair.camera1.view.keypoints,
                                                                  keypoints2=pair.camera2.view.keypoints,
                                                                  index_list1=pair.inliers1,
                                                                  index_list2=pair.inliers2)

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
