import os
from logger import Logger as l
from db_layer import DBLayer, BaseQuery


class DbManager(BaseQuery):
    instance = None

    def __init__(self, connection):
        self.conn = connection
        print("db manager : ", self.conn)
        self.loadjson()

    @staticmethod
    def get(connection=None):
        if DbManager.instance == None and connection != None:
            DbManager.conn = connection
            DbManager.instance = DbManager(connection)
        elif DbManager.instance == None and connection == None:
            print('DbManager Get fail. connection is necessary')
            return -1

        return DbManager.instance

    def status_update(self, job_id, status):
        q = self.update('command', status=status, job_id=job_id)
        result = DBLayer().queryWorker(self.conn, 'update', q)

    def status_update_withresult(self, status, msg, result, job_id):
        q = self.update('command', status=100, result_msg=msg,
                        result_id=result, job_id=job_id)
        result = DBLayer().queryWorker(self.conn, 'update', q)

    def insert_requesthistory(self, job_id, ip, query, etc):
        q = self.insert('request_history', job_id=job_id,
                        requestor=ip, task=query, etc=etc)
        result = DBLayer().queryWorker(self.conn, 'insert', q)

    def getRootPath(self, id):
        q = self.sql_list['query_root_path'] + \
            str(id) + self.sql_list['query_root_path_ex']
        rows = DBLayer().queryWorker(self.conn, 'select-all', q)
        l.get().w.debug(rows)
        if rows == None or len(rows) == 0:
            return -151, None

        return 0, rows[0][0]

    def getJobIndex(self):
        from definition import DEFINITION as defn
        index = 0
        rows = DBLayer().queryWorker(self.conn, 'select-one',
                                     self.sql_list['query_job_id'])

        if rows == None:
            return defn .base_index
        if len(rows) == 0:
            return defn.base_index

        index = rows[0]
        return index

    def getJobStatus(self, id):
        q = self.sql_list['query_status'] + str(id)
        l.get().w.info("Get Status Query: {} ".format(q))

        rows = DBLayer().queryWorker(self.conn, 'select-all', q)

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("status : {} {} ".format(
                str(rows[0][0]), str(rows[0][1])))

        return rows[0][0], rows[0][1]

    def getPair(self, id):
        q = self.sql_list['query_getpair'] + str(id)
        l.get().w.info("Get Pair Query: {} ".format(q))

        rows = DBLayer().queryWorker(self.conn, 'select-all', q)

        if len(rows) > 1:
            return -201, None, None
        elif rows[0][0] == None or rows[0][1] == None or rows[0][0] == '' or rows[0][1] == '':
            return -144, None, None
        else:
            l.get().w.info("Get Pair success : {} {}".format(
                rows[0][0], rows[0][1]))

        return 0, rows[0][0], rows[0][1]

    def getTargetPath(self, id):
        q = self.sql_list['query_gettarget'] + str(id)
        l.get().w.info("Get targetpath Query: {} ".format(q))

        rows = DBLayer().queryWorker(self.conn, 'select-all', q)

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("target path : {} ".format(rows[0][0]))

        return 0, rows[0][0]
