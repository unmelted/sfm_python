import numpy as np
from enum import Enum
import pandas as pd
import math
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

def get_keypoints_from_indices(keypoints1, keypoints2, index_list1, index_list2):
    """Filters a list of keypoints based on the indices given"""

    points1 = np.array([kp.pt for kp in keypoints1])[index_list1]
    points2 = np.array([kp.pt for kp in keypoints2])[index_list2]
    return points1, points2


def compute_fundamental_remove_outliers(view1, view2, indices1, indices2):
    """Removes outlier keypoints using the fundamental matrix"""

    pixel_points1, pixel_points2 = get_keypoints_from_indices(keypoints1=view1.keypoints,
                                                              keypoints2=view2.keypoints,
                                                              index_list1=indices1,
                                                              index_list2=indices2)
    print("compute_fundamental_remove_outliers before mask  : ", len(pixel_points1), len(indices1))

    F, mask = cv2.findFundamentalMat(pixel_points1, pixel_points2, method=cv2.FM_RANSAC,
                                     ransacReprojThreshold=0.9, confidence=0.99)
    # print("FindFundamental : ", F)    
    mask = mask.astype(bool).flatten()
    inliers1 = np.array(indices1)[mask]
    inliers2 = np.array(indices2)[mask]
    print("compute_fundamental_remove_outliers after mask  : ", len(inliers1))

    '''refine match outliers '''
    refine = False
    if refine == True : 
        pixel_points1, pixel_points2, inliers1, inliers2 = refine_outliers(view1, view2, inliers1, inliers2)

        F, mask = cv2.findFundamentalMat(pixel_points1, pixel_points2, method=cv2.FM_RANSAC,
                                        ransacReprojThreshold=0.7, confidence=0.99)
        # print("FindFundamental : ", F)    
        mask = mask.astype(bool).flatten()
        inliers1 = np.array(inliers1)[mask]
        inliers2 = np.array(inliers2)[mask]

        print("compute_fundamental_remove_outliers after refine  : ", len(inliers1))

    # U, S, V = np.linalg.svd(F)
    # S[-1] = 0
    # S = [1, 1, 0] # Force rank 2 and equal eigenvalues
    # E = np.dot(U, np.dot(np.diag(S), V))

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

def calculate_mahalanobis(data):
    d_var = np.var(data)
    d_mean = data.mean()
    mahal = data - d_mean / d_var
    mahal = np.absolute(mahal)
    threshold = 0
    if max(mahal) > 2 :
       threshold = max(mahal) * 0.9

    # print(mahal)
    # print(threshold)

    return mahal, threshold

def refine_outliers(view1, view2, inliers1, inliers2) :
    del_x = np.empty( (0), dtype=np.float64)
    del_y = np.empty( (0), dtype=np.float64)
    # print(len(inliers1), len(inliers2))

    for i in range(0, len(inliers1)) :
        x1 = view1.keypoints[inliers1[i]].pt[0]
        x2 = view2.keypoints[inliers2[i]].pt[0]
        y1 = view1.keypoints[inliers1[i]].pt[1]
        y2 = view2.keypoints[inliers2[i]].pt[1]            

        del_x = np.append(del_x, np.array(x2 - x1).reshape((1)), axis = 0)
        del_y = np.append(del_y, np.array(y2 - y1).reshape((1)), axis = 0)

    d_atan = np.arctan2(del_x, del_y)
    d_ma, d_threshold  = calculate_mahalanobis(d_atan)

    if d_threshold == 0 :
        points1 = np.array([kp.pt for kp in view1.keypoints])[inliers1]
        points2 = np.array([kp.pt for kp in view2.keypoints])[inliers2]
        return points1, points2, inliers1, inliers2    

    print("refine ouliers .. before ")

    cnt = 0
    new_inliers1 = []
    new_inliers2 = []
    for i in range(0, len(inliers1)) :
        if( d_ma[i] < d_threshold ) :
            new_inliers1.append(inliers1[i])
            new_inliers2.append(inliers2[i])
        else :
            cnt += 1

    print("remove ouliers : ", cnt)
    print(len(new_inliers1), len(new_inliers2))
    inliers1 = new_inliers1
    inliers2 = new_inliers2
    points1 = np.array([kp.pt for kp in view1.keypoints])[inliers1]
    points2 = np.array([kp.pt for kp in view2.keypoints])[inliers2]

    return points1, points2, inliers1, inliers2    

def quaternion_rotation_matrix(Q):
    """
    Covert a quaternion into a full three-dimensional rotation matrix.
 
    Input
    :param Q: A 4 element array representing the quaternion (q0,q1,q2,q3) 
 
    Output
    :return: A 3x3 element matrix representing the full 3D rotation matrix. 
             This rotation matrix converts a point in the local reference 
             frame to a point in the global reference frame.
    """
    # Extract the values from Q
    q0 = Q[0]
    q1 = Q[1]
    q2 = Q[2]
    q3 = Q[3]
     
    # First row of the rotation matrix
    r00 = 2 * (q0 * q0 + q1 * q1) - 1
    r01 = 2 * (q1 * q2 - q0 * q3)
    r02 = 2 * (q1 * q3 + q0 * q2)
     
    # Second row of the rotation matrix
    r10 = 2 * (q1 * q2 + q0 * q3)
    r11 = 2 * (q0 * q0 + q2 * q2) - 1
    r12 = 2 * (q2 * q3 - q0 * q1)
     
    # Third row of the rotation matrix
    r20 = 2 * (q1 * q3 - q0 * q2)
    r21 = 2 * (q2 * q3 + q0 * q1)
    r22 = 2 * (q0 * q0 + q3 * q3) - 1
     
    # 3x3 rotation matrix
    rot_matrix = np.array([[r00, r01, r02],
                           [r10, r11, r12],
                           [r20, r21, r22]])
                            
    return rot_matrix

def get_cross_point(x1, y1, x2, y2, x3, y3, x4, y4):
    cx = 0
    cy = 0

    temp1 = (x1*y2 - y1*x2)*(x3 - x4) - (x1 - x2) * ( x3*y4 - y3*x4 )
    temp2 = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    cx = temp1 / temp2
    temp3 = (x1*y2 - y1*x2) * (y3 - y4) - (y1 - y2)*( x3*y4 - y3*x4 )
    temp4 = (x1 - x2)*(y3 - y4) - (y1 - y2)*(x3 -x4)
    cy = temp3 / temp4

    return cx, cy

def get_normalized_point(world) :
    new_world = []
    maxx = 0.0
    maxy = 0.0
    minx = 100000.0
    miny = 100000.0

    for point in world :
        print(point)
        if point[0] > maxx :
            maxx = point[0]
        if point[1] > maxy :
            maxy = point[1]
        if minx > point[0]:
            minx = point[0]
        if miny > point[1] :
            miny = point[1]

    print(minx, maxx, miny, maxy)
    max_range = 100.0
    range = 0.0
    margin_x = 0.0
    margin_y = 0.0

    if (maxx - minx) > (maxy - miny) :
        range = max_range / (maxx - minx)
        margin_y = (max_range - (maxy - miny) * range) / 2.0
    else :
        range = max_range / (maxy - miny)
        margin_x = (max_range - (maxx - minx) * range) / 2.0

    for point in world : 
        newx = (point[0] - minx) * range + margin_x
        newy = (point[1] - miny) * range + margin_y
        newz = 0
        new_world.append([newx, newy, newz])

    print(new_world)
    return new_world

def get_rotate_point(center_x, center_y, point_x, point_y, radian) :
    delx = point_x - center_x
    dely = point_y - center_y

    cos_ = math.cos(radian)
    sin_ = math.sin(radian)

    ret_x = center_x * cos_ - center_y * sin_
    ret_y = center_x * sin_ - center_y * cos_

    ret_x = ret_x + center_x
    ret_y = ret_y + center_y

    return ret_x, ret_y


def get_translation_matrix(dx, dy):
    out = np.eye(3, dtype=np.float64)
    out[0,2] = dx
    out[1,2] = dy
    return out

def get_rotation_matrix(radian) :
    out = np.eye(3, dtype=np.float64)
    out[0,0] = math.cos(radian)
    out[0,1] = -1 * math.sin(radian)
    out[1,0] = math.sin(radian)
    out[1,1] = math.cos(radian)

    return out

def get_rotation_matrix_with_center(radian, cx, cy) :

    mtran = get_translation_matrix(-cx, -cy)
    mrot = get_rotation_matrix(radian)
    mtran2 = get_translation_matrix(cx, cy)
    out = np.linalg.multi_dot([mtran2, mrot, mtran])

    return out 

def get_scale_matrix(scalex, scaley) :
    out = np.eye(3, dtype=np.float64)
    out[0,0] = scalex
    out[1,1] = scaley

    return out 

def get_scale_matrix_center(scalex, scaley, cx, cy) :

    mtran = get_translation_matrix(-cx, -cy)
    msc = get_scale_matrix(scalex, scaley)
    mtran2 = get_translation_matrix(cx, cy)
    out = np.linalg.multi_dot([mtran2, msc, mtran])
    return out


def get_flip_matrix(width, height, flipx, flipy) :
    out = np.eye(3, dtype=np.float64)

    if flipx == True :
        out[0,0] = -1.0
        out[0,2] = width
    
    if flipy == True :
        out[1,1] = -1.0
        out[1,2] = height

    return out

def get_margin_matrix(width, height, margin_x, margin_y, margin_width, margin_height) :
    out = np.eye(3, dtype=np.float64)

    cx = margin_x + margin_width / 2.0
    cy = margin_y + margin_height / 2.0
    scalex = width / margin_width
    scaley = height / margin_height

    mtran = get_translation_matrix(-cx, -cy)
    msc = get_scale_matrix(scalex, scaley)
    mtran2 = get_translation_matrix(width/ 2.0, height/ 2.0)

    out = np.linalg.multi_dot([mtran2, msc, mtran])

    #print("margin matrix ")
    #print(out)
    return out
