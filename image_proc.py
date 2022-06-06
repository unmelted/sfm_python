import os
import glob
import sys
import cv2
import shutil

def make_snapshot(from_path, to_path) :

    if not os.path.exists(os.path.join(from_path, 'UserPointData.pts')):
        return -106
    pts = os.path.join(from_path, 'UserPointData.pts')
    shutil.copy(pts, to_path)

    video_files = sorted(glob.glob(os.path.join(from_path,'*.mp4')))
    pick_frame = 5

    for video in video_files : 
        print(video)
        filename = video[video.rfind('/') + 1:]
        print(filename)        
        filename = filename[0:filename.rfind('_')] + '.png'
        print(filename)

        cam = cv2.VideoCapture(video)
        cam.set(cv2.CAP_PROP_POS_FRAMES, pick_frame)
        ret, frame = cam.read()
        if not ret :
            return -103

        target = os.path.join(to_path, filename)
        print("snapshot save : ", target)
        cv2.imwrite(target, frame)
        cam.release()

    return 0