import os
import glob
import time
from logger import Logger as l
import definition as df
from db_manager import DbManager as Db


def status_update(job_id, status):
    l.get().w.info("Status update. JOB_ID: {} Status: {} ".format(job_id, status))
    Db.status_update(job_id, status)
    if status == 100:
        finish(job_id, 100)


def status_update_quiet(job_id, status):
    l.get().w.info("Quiet tatus update. JOB_ID: {} Status: {} ".format(job_id, status))
    Db.status_update(job_id, status)


def finish_querys(job_id, result, count):
    if count == 0:
        return finish_query(job_id, result)
    elif count == 1:
        return finish_query(job_id, result), None
    elif count == 2:
        return finish_query(job_id, result), None, None
    elif count == 3:
        return finish_query(job_id, result), None, None, None


def finish_query(job_id, result):
    msg = df.get_err_msg(result)
    l.get().w.warning("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    return result


def finish(job_id, result):
    msg = df.get_err_msg(result)
    l.get().w.warning("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    Db.status_update_withresult(100, msg, result, job_id)

    return result


def check_image_format(path):
    flist = glob.glob(os.path.join(path, 'images', '*'))
    for i in flist:
        print(i)
        ext = i[i.rfind('.')+1:]
        if ext == 'png':
            return 'png'
        elif ext == 'tiff':
            return 'tiff'
        elif ext == 'jpeg':
            return 'jpeg'
        elif ext == 'jpg':
            return 'jpg'
        return 'png'


def get_viewname(name, ext):
    viewname = None

    if name.rfind('_') == -1:
        viewname = name[:-1 * (len(ext) + 1)]
    else:
        viewname = name[:name.rfind('_')]

    return viewname


def get_pairname(job_id, pair_type):
    l.get().w.info("GetPair start : {} by {}".format(job_id, pair_type))
    image_names = []
    if pair_type == 'colmap':
        result, image_name1, image_name2 = Db.getPair(job_id)
        if result < 0:
            return finish_querys(job_id, result, 2)
        else:
            return 0, image_name1, image_name2

    elif pair_type == 'isometric':
        _, root_path = Db.getRootPath(job_id)
        ext = check_image_format(root_path)
        image_names = sorted(
            glob.glob(os.path.join(root_path, 'images', '*.'+ ext)))
        cam_count = len(image_names)

        unit1 = float(cam_count) / 4.0
        unit2 = float(cam_count) * 3.0 / 4.0
        print("get_pairname 3", cam_count, unit1, unit2, int(unit1), int(unit2))
        image_name1 = image_names[int(unit1)]
        image1 = image_name1[image_name1.rfind('/') +1:]
        image_name2 = image_names[int(unit2)]
        image2 = image_name2[image_name2.rfind('/') +1:]
        print("get_pairname 4", image_name1, image_name2, image1, image2)
        
        return 0, image1, image2

    return -1, 0, 0


def get_result(job_id):
    contents = None
    l.get().w.info("GetPts start : {} ".format(job_id))
    result, contents = Db.getPts(job_id)
    return result, contents


def get_targetpath(job_id):
    l.get().w.info("Get target path start : {} ".format(job_id))
    result, target_path = Db.getTargetPath(job_id)
    if result < 0:
        return finish_query(job_id, result)
    else:
        return 0, target_path
