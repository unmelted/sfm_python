import os
import sys
import pickle
import cv2
import numpy as np
import glob
import logging


class View(object):
    """Represents an image used in the reconstruction"""

    def __init__(self, image_path, root_path, bMask, feature_path, feature_type='sift'):
        self.name = image_path[image_path.rfind('/') + 1:-8]  # image name without extension
        self.image = cv2.imread(image_path)  # numpy array of the image
        self.keypoints = []  # list of keypoints obtained from feature extraction
        self.descriptors = []  # list of descriptors obtained from feature extraction
        self.feature_type = feature_type  # feature extraction method
        self.root_path = root_path  # root directory containing the image folder
        self.image_width = self.image.shape[1]
        self.image_height = self.image.shape[0]
        self.bMask = bMask
        self.initial_pt1 = [[708, 183], [120, 1614], [2766, 1485], [2091, 144]] # ncaa 
        self.initial_pt2 = [[798, 218], [97, 1617], [2715, 1510], [2163, 179]] # ncaa         
        self.keypoints_mask = []
        self.descriptors_mask = []

        if not feature_path:
            self.extract_features()
        else:
            self.read_features()

    def extract_features(self):
        """Extracts features from the image"""

        if self.feature_type == 'sift':
            detector = cv2.xfeatures2d.SIFT_create()
        elif self.feature_type == 'surf':
            detector = cv2.xfeatures2d.SURF_create()
        elif self.feature_type == 'orb':
            detector = cv2.ORB_create(nfeatures=1500)
        else:
            logging.error("Admitted feature types are SIFT, SURF or ORB")
            sys.exit(0)

        if(self.bMask > 0) :
            mask = self.make_mask_image(self.bMask)
            self.keypoints, self.descriptors = detector.detectAndCompute(self.image, None)
            self.keypoints_mask, self.descriptors_mask = detector.detectAndCompute(self.image, mask)
            print("name : {} Extract features no mask {} mask {} ".format(self.name, len(self.keypoints), len(self.keypoints_mask)))
        else :
            self.keypoints, self.descriptors = detector.detectAndCompute(self.image, None)
            print("Key points count : ", self.name, len(self.keypoints))

        self.write_features()

    def make_mask_image(self, bmask) :
        mask = np.full((self.image_height, self.image_width, 1), 0, np.uint8)
        if(bmask == 1):
            pts = np.array([self.initial_pt1])
        elif (bmask == 2):
            pts = np.array([self.initial_pt2])

        # cv2.polylines(mask, pts, True, (255), 3)
        # cv2.imwrite("test_mask1.png", mask)
        cv2.fillPoly(mask, pts, 255)
        filename = "test_mask_" + str(bmask) + ".png"
        cv2.imwrite(filename, mask)

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

