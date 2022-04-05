import numpy as np


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