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


def get_pair(job_id):
    l.get().w.info("GetPair start : {} ".format(job_id))
    result, image_name1, image_name2 = Db.getPair(job_id)
    if result < 0:
        return finish_querys(job_id, result, 2)
    else:
        return 0, image_name1, image_name2


def get_targetpath(job_id):
    l.get().w.info("Get target path start : {} ".format(job_id))
    result, target_path = Db.getTargetPath(job_id)
    if result < 0:
        return finish_query(job_id, result)
    else:
        return 0, target_path


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
