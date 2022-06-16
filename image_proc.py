import os
import glob
import sys
import cv2
import shutil
from logger import Logger as l
from definition import DEFINITION as df

def make_snapshot(from_path, to_path) :
    
    if not os.path.exists(os.path.join(from_path, df.pts_file_name)):
        return -106
    pts = os.path.join(from_path, df.pts_file_name)
    shutil.copy(pts, to_path)
    copy_answer_pts(from_path, to_path)
    
    video_files = sorted(glob.glob(os.path.join(from_path,'*.mp4')))
    pick_frame = 5

    for video in video_files : 
        l.get().w.debug(video)
        filename = video[video.rfind('/') + 1:]
        print(filename)        
        filename = filename[0:filename.rfind('_')] + '.png'
        l.get().w.debug(filename)

        cam = cv2.VideoCapture(video)
        cam.set(cv2.CAP_PROP_POS_FRAMES, pick_frame)
        ret, frame = cam.read()
        if not ret :
            return -103

        target = os.path.join(to_path, filename)
        l.get().w.debug("snapshot save : {}".format(target))
        cv2.imwrite(target, frame)
        cam.release()

    return 0

def make_image_copy(from_path, to_path) :

    if not os.path.exists(os.path.join(from_path, df.pts_file_name)):
        return -106

    pts = os.path.join(from_path, df.pts_file_name)
    shutil.copy(pts, to_path)
    copy_answer_pts(from_path, to_path)

    image_files = sorted(glob.glob(os.path.join(from_path,'*')))

    for image in image_files : 
        from_file = os.path.join(from_path, image)
        shutil.copy(from_file, to_path)

    return 0

def copy_answer_pts(from_path, to_path) :
    ans_pts = os.path.join(from_path, 'answer.pts')    
    if os.path.exists(ans_pts)) :
        shutil.copy(ans_pts, to_path)
