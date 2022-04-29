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
        self.name = image_path[image_path.rfind('/') + 1:-6]  # image name without extension
        self.image = cv2.imread(image_path)  # numpy array of the image
        self.keypoints = []  # list of keypoints obtained from feature extraction
        self.descriptors = []  # list of descriptors obtained from feature extraction
        self.feature_type = feature_type  # feature extraction method
        self.root_path = root_path  # root directory containing the image folder
        self.image_width = self.image.shape[1]
        self.image_height = self.image.shape[0]

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

        self.keypoints, self.descriptors = detector.detectAndCompute(self.image, None)
        self.write_features()

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
