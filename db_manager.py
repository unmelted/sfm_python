import os
import threading
import sqlite3
from extn_util import *
from logger import Logger as l
from definition import DEFINITION as df
from db_manager_sq import DbManagerSQ as SQ
from db_manager_pg import DbManagerPG as PG


class DbManager(object):
    instance_sq = None
    instance_pg = None
    type = 'pg'

    @staticmethod
    def get(type=None):
        if DbManager.instance_sq is None:
            DbManager.instance_sq = SQ()
        if DbManager.instance_pg is None:
            DbManager.instance_pg = PG()

        if DbManager.type == 'sq':
            return DbManager.instance_sq
        elif DbManager.type == 'pg':
            return DbManager.instance_pg
        else:
            return DbManager.instance_pg

    def getRootPath(self, id):
        q = self.sql_list['query_root_path'] + \
            str(id) + self.sql_list['query_root_path_ex']
        self.cursur.execute(q)
        rows = self.cursur.fetchall()
        l.get().w.debug(rows)
        if rows == None or len(rows) == 0:
            return -151, None

        return 0, rows[0][0]

    def getJobIndex(self):
        index = 0
        self.cursur.execute(self.sql_list['query_job_id'])
        rows = self.cursur.fetchone()
        if rows == None:
            return df.base_index
        if len(rows) == 0:
            return df.base_index

        index = rows[0]
        return index

    def getJobStatus(self, id):
        q = self.sql_list['query_status'] + str(id)
        l.get().w.info("Get Status Query: {} ".format(q))

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("status : {} {} ".format(
                str(rows[0][0]), str(rows[0][1])))

        return rows[0][0], rows[0][1]

    def getPair(self, id):
        q = self.sql_list['query_getpair'] + str(id)
        l.get().w.info("Get Pair Query: {} ".format(q))

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

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

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if len(rows) > 1:
            return -201, 0
        else:
            l.get().w.debug("target path : {} ".format(rows[0][0]))

        return 0, rows[0][0]
