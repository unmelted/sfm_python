import os
import sys
import pickle
import cv2
import numpy as np
import glob
import logging


class View(object):
    """Represents an image used in the reconstruction"""

    def __init__(self, image_path, root_path, feature_path, feature_type='sift'):
        self.name = image_path[image_path.rfind('/') + 1:-8]  # image name without extension
        self.image = cv2.imread(image_path)  # numpy array of the image
        self.keypoints = []  # list of keypoints obtained from feature extraction
        self.descriptors = np.zeros((0, 128), dtype=np.float32)  # list of descriptors obtained from feature extraction
        self.feature_type = feature_type  # feature extraction method
        self.root_path = root_path  # root directory containing the image folder
        self.image_width = self.image.shape[1]
        self.image_height = self.image.shape[0]
        self.bMask = None
        self.keypoints_mask = []
        self.descriptors_mask = []

        self.extraction_mode = 'half'

        if(self.extraction_mode == 'None') :
            self.proc_width = self.image_width
            self.proc_height = self.image_height
        else :
            self.proc_width = int(self.image_width / 2)
            self.proc_height = int(self.image_height / 2)


        if not feature_path:
            self.extract_features()
        elif feature_path == 'colmap' :
            pass
        else:
            self.read_features()

    def extract_features(self):
        """Extracts features from the image"""

        if self.feature_type == 'sift':
            if self.extraction_mode == 'None':
                detector = cv2.SIFT.create(1600)
            elif  self.extraction_mode == 'half':
                detector = cv2.SIFT.create(2000)
            elif self.extraction_mode == 'quad':
                detector = cv2.SIFT.create(2000)
                
        elif self.feature_type == 'akaze':
            detector = cv2.AKAZE_create()

        elif self.feature_type == 'surf':
            detector = cv2.SURF.create()
        elif self.feature_type == 'orb':
            detector = cv2.ORB_create(nfeatures=1500)
        else:
            logging.error("Admitted feature types are SIFT, SURF or ORB")
            sys.exit(0)


        if self.extraction_mode == 'half' : 
            half_image = cv2.resize(self.image, (self.proc_width, self.proc_height))
            half_image = cv2.cvtColor(half_image, cv2.COLOR_BGR2GRAY)
            # image_norm = cv2.normalize(half_image, None, 0, 255, cv2.NORM_MINMAX)
            # testname = 'proc_' + self.name + '.png'            
            # cv2.imwrite(testname, image_norm)
            # half_image = cv2.GaussianBlur(half_image, (3, 3), 0)

            t_keypoints, self.descriptors = detector.detectAndCompute(half_image, None)

            for point in t_keypoints:
                keypoint = cv2.KeyPoint(x=point.pt[0]*2, y=point.pt[1]*2, size=point.size, angle=point.angle, response=point.response, octave=point.octave, class_id=point.class_id)
                self.keypoints.append(keypoint)

        elif self.extraction_mode == 'quad':
            half_image = cv2.resize(self.image, (self.proc_width, self.proc_height))
            # half_image = cv2.GaussianBlur(half_image, (3, 3), 0)

            t_keypoints = []            
            t_descriptors = []
            for i in range(0, 4) :
                mask = self.make_mask(self.proc_height, self.proc_width, i+1)
                keypoints, descriptors = detector.detectAndCompute(half_image, mask)
                t_keypoints.append(keypoints)
                t_descriptors.append(descriptors)
                print("quad keypoints : ", i , len(keypoints))

            for i in range(0, 4) :
                for point in t_keypoints[i]:
                    pt = cv2.KeyPoint(x=point.pt[0]*2, y=point.pt[1]*2, size=point.size, angle=point.angle, response=point.response, octave=point.octave, class_id=point.class_id)
                    self.keypoints.append(pt)

                for desc in t_descriptors[i]:                     
                    self.descriptors = np.append(self.descriptors, desc)
                self.descriptors = self.descriptors.reshape(int(len(self.descriptors)/128), 128)

        else : 
                self.keypoints, self.descriptors = detector.detectAndCompute(self.image, None)

        # outkey = cv2.drawKeypoints(self.image, self.keypoints,  2, (255, 255, 0))
        # testname = 'key_' + self.name + '.png'            
        # cv2.imwrite(testname, outkey)

        print("Key points count : ", self.name, len(self.keypoints))
        self.write_features()

    def make_mask(self, rows, cols, position) :
        '''
        1 | 2 
        ------
        3 | 4
        '''

        quad1 = [[0, 0], [cols/2, 0], [cols/2, rows/2], [0, rows/2]] 
        quad2 = [[cols/2, 0], [cols, 0], [cols, rows/2], [cols/2, rows/2]] 
        quad3 = [[0, rows/2], [cols/2, rows/2], [cols/2, rows], [0, rows]] 
        quad4 = [[cols/2, rows/2], [cols, rows/2], [cols, rows], [cols/2, rows]]        
        mask = np.full((rows, cols, 1), 0, np.uint8)
        pts = None
        if(position == 1):
            pts = np.array([quad1], dtype=np.int64)
        elif (position == 2):
            pts = np.array([quad2], dtype=np.int64)
        elif (position == 3):
            pts = np.array([quad3], dtype=np.int64)
        elif (position == 4):
            pts = np.array([quad4], dtype=np.int64)

        # cv2.polylines(mask, pts, True, (255), 3)
        # cv2.imwrite("test_mask1.png", mas20
        cv2.fillPoly(mask, pts, 255)
        testname = 'test_mask_' + str(position) + '.png'
        cv2.imwrite(testname, mask)

        return mask

    def read_features(self):
        """Reads features stored in files. Feature files have filenames corresponding to image names without extensions"""

        # logic to compute features for images that don't have pkl files
        try:
            features = pickle.load(open(os.path.join(self.root_path, 'features', self.name + '.pkl'), "rb"))
            # logging.info("Read features from file for image %s", self.name)

            keypoints = []
            descriptors = []

            for point in features:
                keypoint = cv2.KeyPoint(x=point[0][0], y=point[0][1], size=point[1], angle=point[2],
                                        response=point[3], octave=point[4], class_id=point[5])
                descriptor = point[6]
                keypoints.append(keypoint)
                descriptors.append(descriptor)

            self.keypoints = keypoints
            self.descriptors = np.array(descriptors)  # convert descriptors into n x 128 numpy array

        except FileNotFoundError:
            logging.error("Pkl file not found for image %s. Computing from scratch", self.name)
            self.extract_features()

        if self.bMask == 0 :
            return 

        try:
            features = pickle.load(open(os.path.join(self.root_path, 'features', self.name + '_mask.pkl'), "rb"))

            keypoints = []
            descriptors = []

            for point in features:
                keypoint = cv2.KeyPoint(x=point[0][0], y=point[0][1], size=point[1], angle=point[2],
                                        response=point[3], octave=point[4], class_id=point[5])
                descriptor = point[6]
                keypoints.append(keypoint)
                descriptors.append(descriptor)

            print(".... read feature _mask pkl file ...")
            self.keypoints_mask = keypoints
            self.descriptors_mask = np.array(descriptors)  # convert descriptors into n x 128 numpy array

        except FileNotFoundError:
            logging.error("Pkl with mask file not found for image %s. Computing from scratch", self.name)


    def write_features(self):
        """Stores computed features to pkl files. The files are written inside a features directory inside the root directory"""

        if not os.path.exists(os.path.join(self.root_path, 'features')):
            os.makedirs(os.path.join(self.root_path, 'features'))

        temp_array = []
        for idx, point in enumerate(self.keypoints):
            temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id,
                    self.descriptors[idx])
            temp_array.append(temp)

        features_file = open(os.path.join(self.root_path, 'features', self.name + '.pkl'), 'wb')
        pickle.dump(temp_array, features_file)
        features_file.close()

        mask_array = []
        if self.bMask > 0 :
            for idx, point in enumerate(self.keypoints_mask):
                temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id,
                        self.descriptors_mask[idx])
                mask_array.append(temp)

            features_file2 = open(os.path.join(self.root_path, 'features', self.name + '_mask.pkl'), 'wb')
            pickle.dump(mask_array, features_file2)
            features_file2.close()

