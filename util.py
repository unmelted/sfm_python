import numpy as np
import cv2
import logging

def read_matrix(path, astype=np.float64):
    """ Reads a file containing a matrix where each line represents a point
        and each point is tab or space separated. * are replaced with -1.
    :param path: path to the file
    :parama astype: type to cast the numbers. Default: np.float64
    :returns: array of array of numbers
    """
    with open(path, 'r') as f:
        arr = []
        for line in f:
            arr.append([(token if token != '*' else -1)
                        for token in line.strip().split()])
        return np.asarray(arr).astype(astype)


def cart2hom(arr):
    """ Convert catesian to homogenous points by appending a row of 1s
    :param arr: array of shape (num_dimension x num_points)
    :returns: array of shape ((num_dimension+1) x num_points) 
    """
    if arr.ndim == 1:
        return np.hstack([arr, 1])
    return np.asarray(np.vstack([arr, np.ones(arr.shape[1])]))


def hom2cart(arr):
    """ Convert homogenous to catesian by dividing each row by the last row
    :param arr: array of shape (num_dimension x num_points)
    :returns: array of shape ((num_dimension-1) x num_points) iff d > 1 
    """
    # arr has shape: dimensions x num_points
    num_rows = len(arr)
    if num_rows == 1 or arr.ndim == 1:
        return arr

    return np.asarray(arr[:num_rows - 1] / arr[num_rows - 1])

def rotation_3d_from_angles(x_angle, y_angle=0, z_angle=0):
    """ Creates a 3D rotation matrix given angles in degrees.
        Positive angles rotates anti-clockwise.
    :params x_angle, y_angle, z_angle: x, y, z angles between 0 to 360
    :returns: 3x3 rotation matrix """
    ax = np.deg2rad(x_angle)
    ay = np.deg2rad(y_angle)
    az = np.deg2rad(z_angle)

    # Rotation matrix around x-axis
    rx = np.array([
        [1, 0, 0],
        [0, np.cos(ax), -np.sin(ax)],
        [0, np.sin(ax), np.cos(ax)]
    ])
    # Rotation matrix around y-axis
    ry = np.array([
        [np.cos(ay), 0, np.sin(ay)],
        [0, 1, 0],
        [-np.sin(ay), 0, np.cos(ay)]
    ])
    # Rotation matrix around z-axis
    rz = np.array([
        [np.cos(az), -np.sin(az), 0],
        [np.sin(az), np.cos(az), 0],
        [0, 0, 1]
    ])

    return np.dot(np.dot(rx, ry), rz)



def get_keypoints_from_indices(keypoints1, index_list1, keypoints2, index_list2):
    """Filters a list of keypoints based on the indices given"""

    points1 = np.array([kp.pt for kp in keypoints1])[index_list1]
    points2 = np.array([kp.pt for kp in keypoints2])[index_list2]
    return points1, points2


def skew(x):
    """ Create a skew symmetric matrix *A* from a 3d vector *x*.
        Property: np.cross(A, v) == np.dot(x, v)
    :param x: 3d vector
    :returns: 3 x 3 skew symmetric matrix from *x*
    """
    return np.array([
        [0, -x[2], x[1]],
        [x[2], 0, -x[0]],
        [-x[1], x[0], 0]
    ])
    
def get_3D_point(u1, P1, u2, P2):
    """Solves for 3D point using homogeneous 2D points and the respective camera matrices"""

    A = np.array([[u1[0] * P1[2, 0] - P1[0, 0], u1[0] * P1[2, 1] - P1[0, 1], u1[0] * P1[2, 2] - P1[0, 2]],
                  [u1[1] * P1[2, 0] - P1[1, 0], u1[1] * P1[2, 1] - P1[1, 1], u1[1] * P1[2, 2] - P1[1, 2]],
                  [u2[0] * P2[2, 0] - P2[0, 0], u2[0] * P2[2, 1] - P2[0, 1], u2[0] * P2[2, 2] - P2[0, 2]],
                  [u2[1] * P2[2, 0] - P2[1, 0], u2[1] * P2[2, 1] - P2[1, 1], u2[1] * P2[2, 2] - P2[1, 2]]])

    B = np.array([-(u1[0] * P1[2, 3] - P1[0, 3]),
                  -(u1[1] * P1[2, 3] - P1[1, 3]),
                  -(u2[0] * P2[2, 3] - P2[0, 3]),
                  -(u2[1] * P2[2, 3] - P2[1, 3])])

    X = cv2.solve(A, B, flags=cv2.DECOMP_SVD)

    return X[1]

    C = np.vstack([
        np.dot(skew(u1), P1),
        np.dot(skew(u2), P2)
    ])
    U, S, V = np.linalg.svd(C)
    P = np.ravel(V[-1, :4])
    P = P / P[3]
    P1 = P[:-1]
    return P1.reshape((3, 1))


def compute_fundamental_remove_outliers(view1, view2, indices1, indices2):
    """Removes outlier keypoints using the fundamental matrix"""

    pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=view1.keypoints,
                                                              keypoints2=view2.keypoints,
                                                              index_list1=indices1,
                                                              index_list2=indices2)
    F, mask = cv2.findFundamentalMat(pixel_points1, pixel_points2, method=cv2.FM_RANSAC,
                                     ransacReprojThreshold=0.9, confidence=0.99)
    # print("FindFundamental : ", F)
    mask = mask.astype(bool).flatten()
    inliers1 = np.array(indices1)[mask]
    inliers2 = np.array(indices2)[mask]
    return F, inliers1, inliers2


def calculate_reprojection_error2(point_3D, point_2D, K, R, t):
    """Calculates the reprojection error for a 3D point by projecting it back into the image plane"""
    #print("error input point : ", point_3D, point_2D)    
    reprojected_point = K.dot(R.dot(point_3D) + t)
    reprojected_point = cv2.convertPointsFromHomogeneous(reprojected_point.T)[:, 0, :].T
    #print("error output reproject : ", reprojected_point)    
    # print(point_2D.reshape((2, 1)))
    error = np.linalg.norm(point_2D.reshape((2, 1)) - reprojected_point)
    err_x = point_2D[0] - reprojected_point[0]
    err_y = point_2D[1] - reprojected_point[1]
    print("calculate_reprojecitopn_err : ", err_x, err_y)
    print("  ", point_2D.T)
    return error

def calculate_reprojection_error(point_3D, point_2D, K, R, t):
    """Calculates the reprojection error for a 3D point by projecting it back into the image plane"""
    #print("error input point : ", point_3D, point_2D)    
    reprojected_point = K.dot(R.dot(point_3D) + t)
    reprojected_point = cv2.convertPointsFromHomogeneous(reprojected_point.T)[:, 0, :].T
    #print("error output reproject : ", reprojected_point)    
    # print(point_2D.reshape((2, 1)))
    error = np.linalg.norm(point_2D.reshape((2, 1)) - reprojected_point)
    return error


def get_camera_from_E(E):
    """Calculates rotation and translation component from essential matrix"""

    W = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    W_t = W.T
    u, w, vt = np.linalg.svd(E)

    R1 = u @ W @ vt
    R2 = u @ W_t @ vt
    t1 = u[:, -1].reshape((3, 1))
    t2 = - t1
    return R1, R2, t1, t2


def check_determinant(R):
    """Validates using the determinant of the rotation matrix"""

    if np.linalg.det(R) + 1.0 < 1e-9:
        return False
    else:
        return True


def check_triangulation(points, P):
    """Checks whether reconstructed points lie in front of the camera"""

    P = np.vstack((P, np.array([0, 0, 0, 1])))
    reprojected_points = cv2.perspectiveTransform(src=points[np.newaxis], m=P)
    z = reprojected_points[0, :, -1]
    if (np.sum(z > 0)/z.shape[0]) < 0.75:
        return False
    else:
        return True
