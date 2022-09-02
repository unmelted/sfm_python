import os
import psycopg2 as pg
from extn_util import *
from logger import Logger as l
from definition import DEFINITION as df


class DbManagerPG(object):
    instance = None

    @staticmethod
    def getInstance(type=None):
        if DbManager.instance is None:
            DbManager.instance = DbManager()

            return DbManager.instance

    def __init__(self):
        self.cmd_db = 'command'
        self.log_db = 'log'
        self.calib_history_db = 'calib_history'
        self.sql_list = import_json(os.path.join(
            os.getcwd(), 'json', df.calib_pg_file))
        self.db_name = df.main_db_name
        if not os.path.exists(os.path.join(os.getcwd(), 'db')):
            os.makedirs(os.path.join(os.getcwd(), 'db'))

        self.conn = pg.connect("dbname=autocalib user=admin password=1234")
        self.cursur = self.conn.cursor()

        create = ["create_command_db",
                  "create_request_history", "create_hw_info"]
        for i in create:
            print(self.sql_list[i])
            self.cursur.execute(self.sql_list[i])

        self.conn.commit()

    def insert(self, table, **k):
        # print(k)
        q = 'INSERT INTO ' + table
        c = '('
        v = 'VALUES ('
        for i in k:
            c += ' ' + i + ', '
            v += '\'' + str(k[i]) + '\', '
        c = c[:-2] + ')'
        v = v[:-2] + ')'

        q = q + c + v
        l.get().w.info("Inser Query: {} ".format(q))

        self.cursur.execute(q)
        print("insert query finish ")
        # self.conn.commit()

    def update(self, table, **k):
        q = 'UPDATE ' + table + ' SET '
        c = []
        v = []

        for i in k:
            c.append(i)
            v.append(k[i])

        for ii in range(len(c)):
            if ii == len(c) - 1:
                q = q[:-2]
                q += 'WHERE ' + c[ii] + ' = ' + str(v[ii])
            else:
                t = c[ii] + ' = \"' + str(v[ii]) + '\" ,'
                q += t

        l.get().w.info("Update Query: {} ".format(q))

        self.cursur.execute(q)
        self.conn.commit()

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
