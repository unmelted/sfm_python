import os
from logger import Logger as l
import definition as df
from db_layer import NewPool, DBLayer, BaseQuery

class DbManager(BaseQuery):
    # conn = NewPool().getConn()    
    sql_list = BaseQuery.loadjson(None)

    @classmethod
    def status_update(cls, job_id, status):
        q = BaseQuery.update('command', status=status, job_id=job_id)
        result = DBLayer.queryWorker( 'update', q)

    @classmethod
    def status_update_withresult(cls, status, msg, result, job_id):
        q = BaseQuery.update('command', status=100, result_msg=msg,
                             result_id=result, job_id=job_id)
        result = DBLayer.queryWorker( 'update', q)

    @classmethod
    def insert_requesthistory(cls, job_id, ip, query, etc):
        q = BaseQuery.insert('request_history', job_id=job_id,
                             requestor=ip, task=query, etc=etc)
        result = DBLayer.queryWorker( 'insert', q)

    @classmethod
    def insert_calibdata(cls, job_id, output):
        q = BaseQuery.insert('calib_data', job_id=job_id, result=output)
        result = DBLayer.queryWorker( 'insert', q)

    @classmethod
    def insert_newcommand(cls, job_id, parent_id, ip, task, input_dir, mode, cam_list):
        q = BaseQuery.insert('command', job_id=job_id, parent_job=parent_id, requestor=ip, task=task,
                             input_path=input_dir, mode=df.DEFINITION.run_mode, cam_list=df.DEFINITION.cam_list)
        result = DBLayer.queryWorker( 'insert', q)

    @classmethod
    def update_command_pair(cls, image1, image2, job_id):
        q = BaseQuery.update('command', image_pair1=image1,
                             image_pair2=image2, job_id=job_id)
        result = DBLayer.queryWorker( 'update', q)

    @classmethod
    def update_command_path(cls, root_path, job_id):
        q = BaseQuery.update('command', root_path=root_path, job_id=job_id)
        result = DBLayer.queryWorker( 'update', q)

    @classmethod
    def getRootPath(cls, id):
        q = cls.sql_list['query_root_path'] + \
            str(id) + cls.sql_list['query_root_path_ex']
        rows = DBLayer.queryWorker( 'select-all', q)
        l.get().w.debug(rows)
        if rows == None or len(rows) == 0:
            return -151, None

        return 0, rows[0][0]

    @classmethod
    def getJobIndex(cls):
        from definition import DEFINITION as defn
        index = 0
        rows = DBLayer.queryWorker( 'select-one',
                                   cls.sql_list['query_job_id'])

        if rows == None:
            return defn .base_index
        if len(rows) == 0:
            return defn.base_index

        index = rows[0]        
        return index

    @classmethod
    def getJobStatus(cls, id):
        q = cls.sql_list['query_status'] + str(id)
        l.get().w.info("Get Status Query: {} ".format(q))
        rows = DBLayer.queryWorker( 'select-all', q)

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("status : {} {} ".format(
                str(rows[0][0]), str(rows[0][1])))
            # for row in rows : 
                # print(row)

        return rows[0][0], rows[0][1]

    @classmethod
    def getPair(cls, id):
        q = cls.sql_list['query_getpair'] + str(id)
        l.get().w.info("Get Pair Query: {} ".format(q))

        rows = DBLayer.queryWorker( 'select-all', q)

        if len(rows) > 1:
            return -201, None, None
        elif rows[0][0] == None or rows[0][1] == None or rows[0][0] == '' or rows[0][1] == '':
            return -144, None, None
        else:
            l.get().w.info("Get Pair success : {} {}".format(
                rows[0][0], rows[0][1]))

        return 0, rows[0][0], rows[0][1]

    @classmethod
    def getPts(cls, id):
        q = cls.sql_list['query_getpts'] + str(id)
        l.get().w.info("Get Pts result  Query: {} ".format(q))

        rows = DBLayer.queryWorker( 'select-one', q)

        if len(rows) == 0:
            return -306, None

        return 0, rows[0]

    @classmethod
    def getTargetPath(cls, id):
        q = cls.sql_list['query_gettarget'] + str(id)
        l.get().w.info("Get targetpath Query: {} ".format(q))
        rows = DBLayer.queryWorker( 'select-all', q)

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("target path : {} ".format(rows[0][0]))

        return 0, rows[0][0]

    @classmethod
    def insert_pointtable(cls, job_id, parent_job, pts_2d, pts_3d) :        
        q = BaseQuery.insert('ref_point', job_id=job_id, parent_job=parent_job, pt_2d=pts_2d, pt_3d=pts_3d)
        l.get().w.info("insert pointtable Query: {} ".format(q))        
        result = DBLayer.queryWorker( 'insert', q)
