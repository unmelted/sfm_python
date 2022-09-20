import os
import time
from datetime import datetime
import gc
from multiprocessing import Process, Queue
import json
from camera_group import *
import definition as df
from logger import Logger as l
# from db_layer import NewPool
from job_manager import JobManager
from db_manager import DbManager
from intrn_util import *
from auto_calib import Autocalib


class Commander(object):

    cmd_que = Queue()

    @classmethod
    def Receiver(cls, que):
        print("receiver start ", cls.cmd_que, que)
        # if cls.db == None:
        #     cls.db, cls.job = NewProcessBase()
        while True:
            time.sleep(0.2)

            if (que.empty() is False):
                task, job_id, obj = que.get()
                Commander.processor(task, job_id, obj)

    @classmethod
    def getQue(cls):
        print("getque ", cls.cmd_que)
        return cls.cmd_que

    @classmethod
    def send_query(cls, query, obj):
        result = 0
        status = 0
        contents = []
        if obj == None:
            return finish(obj, -21)

        l.get().w.debug('receive query {} {}'.format(query, obj[0]))

        if query == df.TaskCategory.AUTOCALIB_STATUS:
            status, result = DbManager.getJobStatus(obj[0])

        elif query == df.TaskCategory.GET_PAIR:
            result, image1, image2 = get_pair(obj[0])
            status = 100
            if result == 0:
                contents.append(image1)
                contents.append(image2)

        elif query == df.TaskCategory.AUTOCALIB_CANCEL:
            result = JobManager.checkJobStatusForCancel(obj[0])
            print("cancle job result : ", result)
            if result == 0:
                print('can push cancel ')
                JobManager.pushCancelJob(int(obj[0]))
            else:
                l.get().w.info('push cancle is failed result {} '.format(result))
                return status, result, contents

        elif query == df.TaskCategory.GET_PTS:
            result, contents = get_pts(obj[0])
            status = 100

        if query != df.TaskCategory.AUTOCALIB_STATUS:
            if len(obj) > 2:
                DbManager.insert_requesthistory(
                    int(obj[0]), obj[1], query, json.dumps(obj[2]))

            else:
                DbManager.insert_requesthistory(
                    int(obj[0]), obj[1], query, None)

        return status, result, contents

    @classmethod
    def add_task(cls, task, obj):
        print("commander add task is called ", cls.cmd_que)
        if JobManager.checkJobsUnderLimit() == True:
            job_id = DbManager.getJobIndex() + 1
            cls.cmd_que.put((task, job_id, obj))
            l.get().w.info("Alloc job id {} ".format(job_id))
            return job_id
        else:
            return -22

    @classmethod
    def processor(cls, task, job_id, obj):
        result = 0
        status = 0
        contents = []
        l.get().w.info("Task Proc start : {} ".format(job_id))

        if task == df.TaskCategory.AUTOCALIB:
            l.get().w.info("{} Task Autocalib start obj : {} {} ".format(
                job_id, obj[0], obj[1]))
            desc = obj[1]
            DbManager.insert_requesthistory(job_id, obj[2], task, desc)
            p = Process(target=calculate, args=(
                obj[0], job_id, obj[1], obj[2]))
            p.start()
            print("--------------AUTOCALIB1-------------")
            print(os.getpid())
            print("------------------------------")

        elif task == df.TaskCategory.ANALYSIS or task == df.TaskCategory.GENERATE_PTS:
            l.get().w.info(
                " Task Generate start obj : {} {} ".format(obj[0], obj[2]))
            if len(obj[2]['pts_2d']) > 7 and len(obj[2]['pts_3d']) > 15:
                cal_type = '2D3D'
            elif len(obj[2]['pts_2d']) > 7 and len(obj[2]['pts_3d']) < 15:
                cal_type = '2D'
            elif len(obj[2]['pts_2d']) < 7 and len(obj[2]['pts_3d']) > 15:
                cal_type = '3D'
            else:
                result = -304
                status = 0
                return status, result, contents

            desc = obj[2]['pts_2d'] + obj[2]['pts_3d']
            DbManager.insert_requesthistory(job_id, obj[1], task, None)

            if task == df.TaskCategory.ANALYSIS:
                p = Process(target=analysis, args=(job_id, obj[0], cal_type, obj[2]['pts_2d'],
                                                   obj[2]['pts_3d'], obj[2]['world']))
                p.start()

            elif task == df.TaskCategory.GENERATE_PTS:
                p = Process(target=generate, args=(job_id, obj[0], obj[1], cal_type, obj[2]['pts_2d'],
                                                   obj[2]['pts_3d']))
                p.start()


def calculate(input_dir, job_id, group, ip):
    print("calculated mode started pid : ", os.getpid())
    JobManager.insertNewJob(job_id, os.getpid())
    print("--------------AUTOCALIB2-------------")
    print(os.getpid())
    print("------------------------------")

    ac = Autocalib(input_dir, job_id, group, ip)
    ac.run()
    del ac
    ac = None
    JobManager.updateJob(job_id, 'complete')


def generate(myjob_id, job_id, ip, cal_type, pts_2d, pts_3d):
    print("generate mode started pid : ", os.getpid())
    JobManager.insertNewJob(myjob_id, os.getpid())
    DbManager.insert_newcommand(myjob_id, job_id, ip, df.TaskCategory.GENERATE_PTS.name,
                                'None', df.DEFINITION.run_mode, df.DEFINITION.cam_list)
    result = generate_pts(myjob_id, job_id, cal_type, pts_2d, pts_3d)
    JobManager.updateJob(myjob_id, 'complete')


def analysis(myjob_id, job_id, cal_type, pts_2d, pts_3d, world_pts):
    print("analysis mode started pid : ", os.getpid())
    JobManager.insertNewJob(myjob_id, os.getpid())
    analysis_mode(job_id, cal_type, pts_2d, pts_3d, world_pts)
    JobManager.updateJob(myjob_id, 'complete')


def prepare_generate(myjob_id, job_id, cal_type, pts_2d, pts_3d):
    time_s = time.time()
    float_2d = []
    float_3d = []
    l.get().w.info('prepare generate jobid {} cal_type {} '.format(job_id, cal_type))
    if cal_type == '3D' and len(pts_3d) < 16:
        return finish_query(job_id, -301)
    elif cal_type == '2D' and len(pts_2d) < 8:
        return finish_query(job_id, -301), None

    if cal_type == '2D3D' or cal_type == '3D':
        for val in pts_3d:
            if float(val) < 0:
                return finish_query(job_id, -302), None
            else:
                float_3d.append(float(val))

    if cal_type == '2D3D' or cal_type == '2D':
        for val in pts_2d:
            if float(val) < 0:
                return finish_query(job_id, -302), None
            else:
                float_2d.append(float(val))

    preset1 = Group(myjob_id)
    result, root_path = DbManager.getRootPath(job_id)
    if result < 0:
        return finish_query(job_id, result), None

    result = preset1.create_group(
        root_path, df.DEFINITION.run_mode, 'colmap_db')
    if result < 0:
        return finish_query(job_id, result), None

    status_update(myjob_id, 20)
    preset1.read_cameras()
    result = preset1.generate_points(job_id, cal_type, float_2d, float_3d)
    if result < 0:
        return finish_query(job_id, result), None

    time_e = time.time() - time_s
    l.get().w.critical("Spending time total (sec) : {}".format(time_e))
    status_update(job_id, 50)
    if not os.path.exists(os.path.join(root_path, 'output')):
        os.makedirs(os.path.join(root_path, 'output'))

    result = preset1.export(job_id, cal_type)
    if result < 0:
        return finish_query(job_id, result), None
    status_update(myjob_id, 80)
    return 0, preset1


def generate_pts(myjob_id, job_id, cal_type, pts_2d, pts_3d):
    l.get().w.info("Generate pst start : {} cal_type {} ".format(job_id, cal_type))
    status_update(job_id, 10)
    result, preset = prepare_generate(
        myjob_id, job_id, cal_type, pts_2d, pts_3d)
    save_point_image(preset)
    status_update(myjob_id, 100)
    return result


def analysis_mode(job_id, cal_type, pts_2d, pts_3d, world_pts):
    float_world = []
    result, preset = prepare_generate(job_id, cal_type, pts_2d, pts_3d)
    if result < 0:
        return result

    for wp in world_pts:
        float_world.append(float(wp))

    if cal_type == '3D' and len(world_pts) < 8:
        return -305

    preset.generate_extra_point(cal_type, float_world)
    preset.generate_adjust()
    return 0
