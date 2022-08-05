import os
import glob
import sys
import cv2
import shutil
from logger import Logger as l
from definition import DEFINITION as df

def prepare_job(from_path, root_path, type) :
    if not os.path.exists(os.path.join(from_path, df.pts_file_name)):
        return -106

    to_path = os.path.join(root_path, 'images')
    pts = os.path.join(from_path, df.pts_file_name)
    shutil.copy(pts, to_path)
    copy_answer_pts(from_path, to_path)
    setup_proj_ini(root_path)

    if type == 'video_folder' :
        return prepare_video_job(from_path, to_path)
    elif type == 'image_folder' or type == 'pts_file':
        return prepare_image_job(from_path, to_path)


def prepare_video_job(from_path, to_path) :
    
    video_files = sorted(glob.glob(os.path.join(from_path,'*.mp4')))
    pick_frame = 1
    if len(video_files) < 5 :
        return -102

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

def prepare_image_job(from_path, to_path) :

    image_files = sorted(glob.glob(os.path.join(from_path,'*')))

    if len(image_files) < 5 :
        return -102

    for image in image_files : 
        from_file = os.path.join(from_path, image)
        shutil.copy(from_file, to_path)

    del image_files
    return 0


def copy_answer_pts(from_path, to_path) :
    ans_pts = os.path.join(from_path, 'answer.pts')    
    if os.path.exists(ans_pts) :
        shutil.copy(ans_pts, to_path)

def setup_proj_ini(root_path) :
    from_path = os.path.join(os.getcwd(), 'config')
    fi = os.path.join(from_path, df.feature_ini)
    shutil.copy(fi, root_path)
    fi = os.path.join(from_path, df.matcher_ini)    
    shutil.copy(fi, root_path)
    fi = os.path.join(from_path, df.mapper_ini)        
    shutil.copy(fi, root_path)

    imgpath = os.path.join(root_path, 'images')
    coldb_path = os.path.join(root_path, df.colmap_db_name)
    outpath = os.path.join(root_path, 'sparse')

    feature = os.path.join(root_path, df.feature_ini)
    matcher = os.path.join(root_path, df.matcher_ini)    
    mapper = os.path.join(root_path, df.mapper_ini)

    ini_file = open(feature, 'r')
    contents1 = ini_file.readlines()
    contents1.insert(0, 'image_path=' + imgpath + '\n')
    contents1.insert(1, 'database_path=' + coldb_path + '\n')
    ini_file = open(feature, 'w')
    contents1 = "".join(contents1)
    ini_file.write(contents1)
    ini_file.close()

    ini_file = open(matcher, 'r')
    contents2 = ini_file.readlines()
    contents2.insert(0, 'database_path=' + coldb_path + '\n')
    ini_file = open(matcher, 'w')
    contents2 = "".join(contents2)
    ini_file.write(contents2)
    ini_file.close()

    ini_file = open(mapper, 'r')
    contents3 = ini_file.readlines()    
    contents3.insert(0, 'image_path=' + imgpath + '\n')
    contents3.insert(1, 'database_path=' + coldb_path + '\n')
    contents3.insert(1, 'output_path=' + outpath + '\n')    
    ini_file = open(mapper, 'w')
    contents3 = "".join(contents3)
    ini_file.write(contents3)
    ini_file.close()

    