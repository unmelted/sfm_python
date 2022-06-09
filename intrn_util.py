import os
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
    l.get().w.error("JOB_ID: {} Result: {} Message: {}".format(job_id, result, msg))
    DbManager.getInstance().update('command', status=100, result_msg=msg, result_id=result, job_id=job_id)
    return result