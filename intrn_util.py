import os
import glob
import time
from logger import Logger as l
from db_manager import DbManager
import definition as df


def status_update(job_id, status) :
    l.get().w.info("Status update. JOB_ID: {} Status: {} ".format(job_id, status))
    DbManager.getInstance().update('command', status=status, job_id=job_id)
    if status == 100 :
        finish(job_id, 100)

def finish(job_id, result) :
    msg = df.get_err_msg(result)
    l.get().w.warning("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    DbManager.getInstance().update('command', status=100, result_msg=msg, result_id=result, job_id=job_id)
    return result


def check_image_format(path) :
    flist = glob.glob(os.path.join(path, 'images', '*'))
    for i in flist :
        print(i)
        ext = i[i.rfind('.')+1 :]
        if ext == 'png' :
            return 'png'
        elif ext == 'tiff' :
            return 'tiff'
        elif ext == 'jpeg' :
            return 'jpeg'
        elif ext == 'jpg' :
            return 'jpg'
    return 'png'

