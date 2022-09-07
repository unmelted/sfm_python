import os
import json
import sqlite3
from logger import Logger as l
from db_manager import DbManager


class DbManagerSQ(DbManager):
    instance = None
    calib_sq_file = 'calib_sq.json'

    def __init__(self):
        json_file = open(os.path.join(
            os.getcwd(), 'json', self.calib_sq_file), 'r')
        self.sql_list = json.load(json_file)
        self.db_name = self.main_db_name
        if not os.path.exists(os.path.join(os.getcwd(), 'db')):
            os.makedirs(os.path.join(os.getcwd(), 'db'))

        self.conn = sqlite3.connect(os.path.join(
            os.getcwd(), 'db', self.db_name), isolation_level=None, check_same_thread=False)
        self.cursur = self.conn.cursor()

        create = ["create_command_db",
                  "create_request_history", "create_hw_info"]
        for i in create:
            # print(self.sql_list[i])
            self.cursur.execute(self.sql_list[i])

    def insert(self, table, **k):
        # print(k)
        q = 'INSERT INTO ' + table
        c = '('
        v = 'VALUES ('
        for i in k:
            c += '\'' + i + '\', '
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
