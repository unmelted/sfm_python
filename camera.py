import numpy as np
import mathutil
from view import *


class Camera(object):
    """ Class for representing pin-hole camera """

    def __init__(self, image_name, root_path, K, run_mode):
        self.id = None
        self.index = None
        self.P = None     # camera matrix
        self.EX = None
        self.R = np.zeros((3,3), dtype=np.float64)     # rotation
        self.t = np.zeros((3,1), dtype=np.float64)     # translation
        self.F = np.zeros((3,3), dtype=np.float64)
        self.E = np.zeros((3,3), dtype=np.float64)        
        self.Rvec = np.zeros((3,1), dtype=np.float64)
        self.c = None  # camera center

        feature_path = None
        if run_mode == 'colmap' :
            self.K = None
            self.focal = None
            feature_path = run_mode
        else :
            self.K = K        # intrinsic matrix
            self.focal = K[0][0]
            if os.path.exists(os.path.join(root_path, 'features')):
                os.makedirs(os.path.join(root_path, 'feature'))
            feature_path = os.path.join(root_path, 'features')

        self.view = View(image_name, root_path, feature_path=feature_path)

        ''' related adjust value '''
        self.pts = np.empty((0 ,2), dtype=np.float64)    # 4points
        self.pts_3D = np.empty((0,3), dtype=np.float64)
        self.pts_back = np.empty((0,3), dtype=np.float64)
        self.pts_repr = np.empty((0,2), dtype=np.float64)

        self.normal = [] # 2 vectocs
        self.center = [] # tracking center
        self.norm = None
        self.angle = None
        self.radian = None

    def calculate_p(self) :
        """ P = K[R|t] camera model. (3 x 4)
         Must either supply P or K, R, t """
        if self.P is None:
            try:
                self.EX =  np.hstack([self.R, self.t])
                self.P = np.dot(self.K, self.EX)
                print('calculate P of camera ', self.view.name)
            except TypeError as e:
                print('Invalid parameters to Camera. Must either supply P or K, R, t')
                raise

    def project(self, X, H = None):
        """ Project 3D homogenous points X (4 * n) and normalize coordinates.
            Return projected 2D points (2 x n coordinates) """

        x = np.dot(self.P, X) 

        # if len(H) > 1:
        #     print("cross .. ", H)
        #     H_inv = np.linalg.inv(H)
        #     x  = np.dot(H, x)

        x[0, :] /= x[2, :]
        x[1, :] /= x[2, :]

        # z : X
        # if np.all(x_lambda == 0) == False and np.all(y_lambda == 0) == False :
        #     x[0, :] = X[2] * x_lambda[0] + x[0, :] * x_lambda[1]
        #     x[1, :] = X[2] * y_lambda[0] + x[1, :] * y_lambda[1]
        #     print("apply lambda : ", x[0, :], x[1, :])

        # x : z : X
        # if np.all(x_lambda == 0) == False and np.all(y_lambda == 0) == False :
        #     x[0, :] = X[2] * x_lambda[0] + x[0, :] * x_lambda[1]
        #     x[1, :] = X[2] * y_lambda[0] + x[1, :] * y_lambda[1]
        #     print("apply lambda : ", x[0, :], x[1, :])
            
        return x[:2, :]

    def qr_to_rq_decomposition(self):
        """ Convert QR to RQ decomposition with numpy.
        Note that this could be done by passing in a square matrix with scipy:
        K, R = scipy.linalg.rq(self.P[:, :3]) """
        Q, R = np.linalg.qr(np.flipud(self.P).T)
        R = np.flipud(R.T)
        return R[:, ::-1], Q.T[::-1, :]

    def factor(self):
        """ Factorize the camera matrix P into K,R,t with P = K[R|t]
          using RQ-factorization """
        if self.K is not None and self.R is not None:
            return self.K, self.R, self.t  # Already been factorized or supplied

        K, R = self.qr_to_rq_decomposition()
        # make diagonal of K positive
        T = np.diag(np.sign(np.diag(K)))
        if np.linalg.det(T) < 0:
            T[1, 1] *= -1

        self.K = np.dot(K, T)
        self.R = np.dot(T, R)  # T is its own inverse
        self.t = np.dot(np.linalg.inv(self.K), self.P[:, 3])

        return self.K, self.R, self.t

    def center(self):
        """  Compute and return the camera center. """
        if self.c is not None:
            return self.c
        elif self.R:
            # compute c by factoring
            self.c = -np.dot(self.R.T, self.t)
        else:
            # P = [M|−MC]
            self.c = np.dot(-np.linalg.inv(self.c[:, :3]), self.c[:, -1])
        return self.c