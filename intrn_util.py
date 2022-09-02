import os
import glob
import time
from logger import Logger as l
from db_manager import DbManager
import definition as df


class JobManager(object) :

    instance = None
    @staticmethod
    def getInstance():
        if JobManager.instance is None:
            JobManager.instance = JobManager()
        return JobManager.instance

    def __init__ (self) :
        self.job_id = -1

    def set_current_jobid(self, job_id) :
        print("set current jobid : ", job_id)
        self.job_id = job_id

    def release_current_jobid(self) :
        print("called release_current_jobid() ")
        self.job_id = -1

    def get_current_jobid(self) :
        print("called Jobmanager getcurrent_jobid : ", self.job_id)
        return self.job_id


def get_current_job():
    id = JobManager.getInstance().get_current_jobid()    
    l.get().w.info("Called get_current_job : {} ".format(id))    
    return id

def status_update(job_id, status) :
    l.get().w.info("Status update. JOB_ID: {} Status: {} ".format(job_id, status))
    DbManager.getInstance().update('command', status=status, job_id=job_id)
    if status == 100 :
        finish(job_id, 100)

def status_update_quiet(job_id, status) :
    l.get().w.info("Quiet tatus update. JOB_ID: {} Status: {} ".format(job_id, status))
    DbManager.getInstance().update('command', status=status, job_id=job_id)

def finish_querys(job_id, result, count) :
    if count == 0 :
        return finish_query(job_id, result)        
    elif count == 1 :
        return finish_query(job_id, result), None
    elif count == 2 :
        return finish_query(job_id, result), None, None
    elif count == 3 :
        return finish_query(job_id, result), None, None, None


def finish_query(job_id, result) :
    msg = df.get_err_msg(result)
    l.get().w.warning("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    return result


def finish(job_id, result) :
    msg = df.get_err_msg(result)
    l.get().w.warning("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    DbManager.getInstance().update('command', status=100, result_msg=msg, result_id=result, job_id=job_id)
    return result

def get_pair(job_id) :
    l.get().w.info("GetPair start : {} ".format(job_id))    
    result, image_name1, image_name2 = DbManager.getInstance('external').getPair(job_id)
    if result < 0 :
        return finish_querys(job_id, result, 2)
    else : 
        return 0, image_name1, image_name2
    

def get_targetpath(job_id) :
    l.get().w.info("Get target path start : {} ".format(job_id))    
    result, target_path = DbManager.getInstance().getTargetPath(job_id)
    if result < 0 :
        return finish_query(job_id, result)
    else : 
        return  0, target_path

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
