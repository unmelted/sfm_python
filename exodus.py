import os
import time
from datetime import datetime
import gc
from multiprocessing import Process, Queue
import json
from camera_group import *
import definition as df
from logger import Logger as l
from db_layer import NewPool
from job_manager import JobManager
from db_manager import DbManager
from intrn_util import *
from auto_calib import Autocalib


def NewProcessBase():
    return DbManager.get(NewPool.get()), JobManager.get(NewPool.get())


class Commander(object):
    instance = None

    @staticmethod
    def get():
        if Commander.instance is None:
            Commander.instance = Commander()
        return Commander.instance

    def __init__(self):
        self.cmd_que = Queue()
        self.index = 0
        self.db, self.job = NewProcessBase()
        print("Commander initialized.")

    def Receiver(self):
        print("receiver start")
        self.db, self.job = NewProcessBase()
        print("new pool")
        while True:
            if (self.index % 100000 == 0):
                self.index = 0
            time.sleep(0.2)

            if (self.cmd_que.empty() is False):
                task, obj = self.cmd_que.get()
                self.processor(task, obj)

    def init_connection(self):
        self.db, self.job = NewProcessBase()
        print("init_connection OK ")

    def send_query(self, query, obj):
        result = 0
        status = 0
        contents = []
        if obj == None:
            return finish(obj, -21)

        l.get().w.debug('receive query {} {}'.format(query, obj[0]))

        if query == df.TaskCategory.AUTOCALIB_STATUS:
            status, result = self.db.getJobStatus(obj[0])

        elif query == df.TaskCategory.GET_PAIR:
            result, image1, image2 = get_pair(obj[0])
            status = 100
            if result == 0:
                contents.append(image1)
                contents.append(image2)

        elif query == df.TaskCategory.AUTOCALIB_CANCEL:
            result = self.job.checkJobStatusForCancel(obj[0])
            print("cancle job result : ", result)
            if result == 0:
                print('can push cancel ')
                self.job.pushCancelJob(int(obj[0]))
            else:
                l.get().w.info('push cancle is failed result {} '.format(result))
                return status, result, contents

        if query != df.TaskCategory.AUTOCALIB_STATUS:
            if len(obj) > 2:
                self.db.insert_requesthistory(
                    int(obj[0]), obj[1], query, json.dumps(obj[2]))

            else:
                self.db.insert_requesthistory(int(obj[0]), obj[1], query, None)

        return status, result, contents

    def add_task(self, task, obj):

        if self.job.checkJobsUnderLimit() == True:
            self.cmd_que.put((task, obj))
            self.index = self.db.getJobIndex() + 1
            l.get().w.info("Alloc job id {} ".format(self.index))
            return self.index
        else:
            return -22

    # def task_process(self, task, obj, index):
    #     result = 0
    #     status = 0
    #     contents = []
    #     l.get().w.info("Task Proc start : {} ".format(index))

    #     if task == df.TaskCategory.AUTOCALIB:
    #         l.get().w.info("{} Task Autocalib start obj : {} {} ".format(
    #             index, obj[0], obj[1]))
    #         p = Process(target=calculate, args=(
    #             obj[0], index, obj[1], obj[2]))
    #         p.start()
    #         p.join()

    #         desc = obj[0] + obj[1]
    #         df.DBM.getInstance('pg').insert('request_history', job_id=index,
    #                                            requestor=obj[2], task=task, desc=desc)
    #     elif task == df.TaskCategory.ANALYSIS or task == df.TaskCategory.GENERATE_PTS:
    #         status = 100
    #         l.get().w.info(
    #             " Task Generate start obj : {} {} ".format(obj[0], obj[2]))
    #         if len(obj[2]['pts_2d']) > 7 and len(obj[2]['pts_3d']) > 15:
    #             cal_type = '2D3D'
    #         elif len(obj[2]['pts_2d']) > 7 and len(obj[2]['pts_3d']) < 15:
    #             cal_type = '2D'
    #         elif len(obj[2]['pts_2d']) < 7 and len(obj[2]['pts_3d']) > 15:
    #             cal_type = '3D'
    #         else:
    #             result = -304
    #             status = 0
    #             return status, result, contents

    #         if task == df.TaskCategory.ANALYSIS:
    #             pass
    #         elif task == df.TaskCategory.GENERATE_PTS:
    #             pass

    def processor(self, task, obj):
        result = 0
        status = 0
        contents = []
        l.get().w.info("Task Proc start : {} ".format(self.index))

        if task == df.TaskCategory.AUTOCALIB:
            l.get().w.info("{} Task Autocalib start obj : {} {} ".format(
                self.index, obj[0], obj[1]))
            desc = obj[1]
            self.db.insert_requesthistory(self.index, obj[2], task, desc)
            p = Process(target=calculate, args=(
                obj[0], self.index, obj[1], obj[2]))
            p.start()
            # print("--------------AUTOCALIB1-------------")
            # print(os.getpid())
            # print("------------------------------")

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
            self.db.insert_requesthistory(self.index, obj[2], task, desc)

            if task == df.TaskCategory.ANALYSIS:
                p = Process(target=analysis, args=(self.index, obj[0], cal_type, obj[2]['pts_2d'],
                                                   obj[2]['pts_3d'], obj[2]['world']))
                p.start()
                # p.join()

            elif task == df.TaskCategory.GENERATE_PTS:
                p = Process(target=generate, args=(self.index, obj[0], cal_type, obj[2]['pts_2d'],
                                                   obj[2]['pts_3d'], obj[2]['world']))
                p.start()
                # p.join()


def calculate(input_dir, job_id, group, ip):
    print("calculated mode started pid : ", os.getpid())
    db, job = NewProcessBase()
    job.get().insertNewJob(job_id, os.getpid())
    print("--------------AUTOCALIB2-------------")
    print(os.getpid())
    print("------------------------------")

    ac = Autocalib(input_dir, job_id, group, ip, db)
    ac.run()
    del ac
    ac = None
    job.get().updateJob(job_id, 'complete')


def generate(myjob_id, job_id, cal_type, pts_2d, pts_3d):
    print("generate mode started pid : ", os.getpid())
    db, job = NewProcessBase()
    job.get().insertNewJob(job_id, os.getpid())
    result = generate_pts(job_id, cal_type, pts_2d, pts_3d, db)
    job.get().updateJob(job_id, 'complete')


def analysis(myjob_id, job_id, cal_type, pts_2d, pts_3d, world_pts):
    print("analysis mode started pid : ", os.getpid())
    db, job = NewProcessBase()
    job.get().insertNewJob(job_id, os.getpid())
    analysis_mode(job_id, cal_type, pts_2d, pts_3d, world_pts, db)
    job.get().updateJob(job_id, 'complete')


def prepare_generate(job_id, cal_type, pts_2d, pts_3d, db):
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

    preset1 = Group()
    result, root_path = db.getRootPath(job_id)
    if result < 0:
        return finish_query(job_id, result), None

    result = preset1.create_group(
        root_path, df.DEFINITION.run_mode, 'colmap_db')
    if result < 0:
        return finish_query(job_id, result), None

    preset1.read_cameras()
    result = preset1.generate_points(job_id, cal_type, float_2d, float_3d)
    if result < 0:
        return finish_query(job_id, result), None

    time_e = time.time() - time_s
    l.get().w.critical("Spending time total (sec) : {}".format(time_e))

    if not os.path.exists(os.path.join(root_path, 'output')):
        os.makedirs(os.path.join(root_path, 'output'))

    result = preset1.export(job_id, cal_type)
    if result < 0:
        return finish_query(job_id, result), None

    return 0, preset1


def generate_pts(job_id, cal_type, pts_2d, pts_3d, db):
    l.get().w.info("Generate pst start : {} cal_type {} ".format(job_id, cal_type))
    result, preset = prepare_generate(job_id, cal_type, pts_2d, pts_3d, db)
    save_point_image(preset)
    return result


def analysis_mode(job_id, cal_type, pts_2d, pts_3d, world_pts, db):
    float_world = []
    result, preset = prepare_generate(job_id, cal_type, pts_2d, pts_3d, db)
    if result < 0:
        return result

    for wp in world_pts:
        float_world.append(float(wp))

    if cal_type == '3D' and len(world_pts) < 8:
        return -305

    preset.generate_extra_point(cal_type, float_world)
    preset.generate_adjust()
    return 0
