import os
import time
from datetime import datetime
import gc
from multiprocessing import Process, Queue
import json
from flask import jsonify
from camera_group import *

from logger import Logger as l
# from db_layer import NewPool
from job_manager import JobManager, JobActivity
from db_manager import DbManager
from intrn_util import *
from auto_calib import Autocalib


class Commander(object):
    # dbm = DbManager()
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

        # obj : param list. 0: jobid, 1:ip address, 2:callback function
        if obj == None:
            return finish(obj, -21)

        l.get().w.debug('receive query {} {}'.format(query, obj[0], obj[1]))

        if query == df.TaskCategory.AUTOCALIB_STATUS:
            status, result = DbManager.getJobStatus(obj[0])

        elif query == df.TaskCategory.GET_PAIR:
            result, image1, image2 = get_pairname(obj[0], obj[1])
            status = 100
            if result == 0:
                contents.append(image1)
                contents.append(image2)

        elif query == df.TaskCategory.AUTOCALIB_CANCEL:
            result = JobActivity.checkJobStatusForCancel(obj[0])
            if result == 0:
                print('can push cancel ')
                JobActivity.pushCancelJob(int(obj[0]))
            else:
                l.get().w.info('push cancle is failed result {} '.format(result))
                # return status, result, contents

        elif query == df.TaskCategory.GET_RESULT:
            result, contents = get_result(obj[0])
            status = 100

        if query != df.TaskCategory.AUTOCALIB_STATUS and query != df.TaskCategory.GET_PAIR :
            DbManager.insert_requesthistory(
                int(obj[0]), obj[1], query, None)
        elif query == df.TaskCategory.GET_PAIR :
            DbManager.insert_requesthistory(int(obj[0]), obj[2], query, None)

        l.get().w.debug('return result status {} result {} contents {} '.format(
            status, result, contents))

        return status, result, contents

    @classmethod
    def add_task(cls, task, obj):
        print("commander add task is called ", cls.cmd_que)
        if JobActivity.checkJobsUnderLimit() == True:
            job_id = DbManager.getJobIndex() + 1
            cls.cmd_que.put((task, job_id, obj))
            l.get().w.info("Alloc job id {} ".format(job_id))
            return job_id
        else:
            return -22

    @classmethod
    def processor(cls, task, job_id, obj):
        # dbm = DbManager()
        result = 0
        status = 0
        contents = []
        l.get().w.info("Task Proc start : {} ".format(job_id))
        print(obj[0]["config"])
        mobj = obj[0]["config"].replace('\'', '\"')
        jobj = json.loads(mobj)
        print(jobj["scale"], jobj["pair"], jobj["preprocess"])
        jconfig = jobj

        if task == df.TaskCategory.AUTOCALIB:
            l.get().w.info("{} Task Autocalib start obj : {} {} ".format(
                job_id, obj[0]["input_dir"], obj[0]["group"], jobj["scale"]))
            desc = obj[1]
            DbManager.insert_requesthistory(job_id, obj[1], task, desc)
            p = Process(target=calculate, args=(
                obj[0]["input_dir"], job_id, obj[0]["group"], jconfig, obj[1]))
            p.start()
            print("--------------AUTOCALIB1-------------")
            print(os.getpid())
            print("------------------------------")

        elif task == df.TaskCategory.GENERATE_PTS:
            l.get().w.info(
                " Task Generate start obj : {} {} ".format(obj[0], obj[1]))
            if len(obj[0]['pts_2d']) > 7 and len(obj[0]['pts_3d']) > 15:
                cal_type = '2D3D'
            elif len(obj[0]['pts_2d']) > 7 and len(obj[0]['pts_3d']) < 15:
                cal_type = '2D'
            elif len(obj[0]['pts_2d']) < 7 and len(obj[0]['pts_3d']) > 15:
                cal_type = '3D'
            else:
                result = -304
                status = 0
                return status, result, contents

            jconfig['scale'] = DbManager.getParentScale(obj[0]['job_id'])[1]
            DbManager.insert_requesthistory(job_id, obj[1], task, None)
            p = Process(target=generate, args=(job_id, obj[0]['job_id'], obj[1], cal_type, obj[0]['pts_2d'],
                                               obj[0]['pts_3d'], jconfig, obj[0]['image1'], obj[0]['image2'], obj[0]['world']))
            p.start()

        elif task == df.TaskCategory.ANALYSIS:
            DbManager.insert_requesthistory(
                job_id, obj[1], task, obj[2]['world'])
            p = Process(target=analysis, args=(
                job_id, obj[2]['job_id'], cal_type, obj[2]['world']))
            p.start()


def calculate(input_dir, job_id, group, config, ip):
    print("calculated mode started pid : ", os.getpid())
    JobActivity.insertNewJob(job_id, os.getpid())
    print("--------------AUTOCALIB2-------------")
    print(os.getpid())
    print("------------------------------")
    print("calcuate config : ", config['scale'])
    ac = Autocalib(input_dir, job_id, group, config, ip)
    ac.run()
    del ac
    ac = None
    JobActivity.updateJob(job_id, 'complete')


def generate(myjob_id, job_id, ip, cal_type, pts_2d, pts_3d, config, image1, image2, world=[]):
    print("generate mode started pid : ", os.getpid())
    # dbm = DbManager()
    JobActivity.insertNewJob(myjob_id, os.getpid())
    print("generate main ---- ", config)
    DbManager.insert_newcommand_gen(myjob_id, job_id, ip, df.TaskCategory.GENERATE_PTS.name,
                                'None', config, image1, image2)
    result = generate_pts(myjob_id, job_id, cal_type,
                          pts_2d, pts_3d, config, image1, image2, world)
    JobActivity.updateJob(myjob_id, 'complete')


# job_id is job_id for generate
def analysis(myjob_id, job_id, cal_type, world_pts):
    print("analysis mode started pid : ", os.getpid())
    JobActivity.insertNewJob(myjob_id, os.getpid())
    analysis_mode(myjob_id, job_id, cal_type, world_pts)
    JobActivity.updateJob(myjob_id, 'complete')


def prepare_generate(myjob_id, job_id, cal_type, pts_2d, pts_3d, image1, image2, config):
    # dbm = DbManager()
    time_s = time.time()
    float_2d = []
    float_3d = []
    total_pt = []
    l.get().w.info('prepare generate jobid {} cal_type {} scale {}'.format(
        job_id, cal_type, config['scale']))
    scale_factor = 1.0 if config['scale'] == 'full' else 2.0

    if cal_type == '3D' and len(pts_3d) < 16:
        return finish_query(myjob_id, -301)
    elif cal_type == '2D' and len(pts_2d) < 8:
        return finish_query(myjob_id, -301), None

    if cal_type == '2D3D' or cal_type == '3D':
        for val in pts_3d:
            if float(val) < 0:
                return finish_query(myjob_id, -302), None
            else:
                float_3d.append(float(val) / scale_factor)

    if cal_type == '2D3D' or cal_type == '2D':
        for val in pts_2d:
            if float(val) < 0:
                return finish_query(myjob_id, -302), None
            else:
                float_2d.append(float(val) / scale_factor)

    DbManager.insert_adjustData(myjob_id, job_id, pts_2d, pts_3d)

    preset1 = Group(myjob_id)
    result, root_path = DbManager.getRootPath(job_id)
    if result < 0:
        return finish_query(myjob_id, result), None

    result = preset1.create_group(
        df.TaskCategory.GENERATE_PTS, root_path, df.DEFINITION.run_mode, config['scale'], 'colmap_db')
    if result < 0:
        return finish_query(myjob_id, result), None

    status_update(myjob_id, 20)
    preset1.read_cameras()
    result = preset1.generate_points(
        job_id, cal_type, config, float_2d, float_3d, image1, image2)
    if result < 0:
        return finish_query(job_id, result), None

    time_e = time.time() - time_s
    l.get().w.critical("Spending time total (sec) : {}".format(time_e))
    status_update(myjob_id, 50)
    if not os.path.exists(os.path.join(root_path, 'output')):
        os.makedirs(os.path.join(root_path, 'output'))

    result = preset1.export(myjob_id, job_id, cal_type, config['scale'])
    if result < 0:
        return finish_query(job_id, result), None
    status_update(myjob_id, 80)
    return 0, preset1


def generate_pts(myjob_id, job_id, cal_type, pts_2d, pts_3d, config, image1, image2, pts_world):
    l.get().w.info("Generate pst start : {} cal_type {} ".format(job_id, cal_type))
    status_update(myjob_id, 10)
    result, preset = prepare_generate(
        myjob_id, job_id, cal_type, pts_2d, pts_3d, image1, image2, config)
    save_point_image(preset, myjob_id)
    status_update(myjob_id, 100)

    if cal_type == '2D':
        preset.generate_extra_point('2D', None)
    elif cal_type == '3D':
        if len(pts_world) >= 8:
            float_world = []
            for wp in pts_world:
                float_world.append(float(wp))

            DbManager.insert_adjustData2(myjob_id, job_id, pts_world)
            preset.generate_extra_point('3D', float_world)
        else:
            l.get().w.debug("Can't generate extra point. (No world)")
            return result

    elif cal_type == '2D3D':
        preset.generate_extra_point('2D', None)

    left, top, width, height = preset.generate_adjust(myjob_id)
    DbManager.insert_adjustData3(myjob_id, job_id, left, top, width, height)
    return result


def analysis_mode(myjob_id, job_id, cal_type, world_pts):
    float_world = []
    result, preset = prepare_generate(job_id, cal_type, world_pts)
    # preset = Group(myjob_id)
    result, root_path = DbManager.getRootPath(job_id)
    if result < 0:
        return finish_query(job_id, result), None

    result = preset.create_group(
        root_path, df.DEFINITION.run_mode, 'colmap_db')
    if result < 0:
        return finish_query(job_id, result), None

    if result < 0:
        return result

    for wp in world_pts:
        float_world.append(float(wp))

    if cal_type == '3D' and len(world_pts) < 8:
        return -305

    preset.generate_extra_point(cal_type, float_world)
    left, top, width, height = preset.generate_adjust(myjob_id)
    return 0
