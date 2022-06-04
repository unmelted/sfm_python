import os
import sqlite3
from extn_util import * 

class DbManager(object) :
    instance = None

    @staticmethod
    def getInstance():
        if DbManager.instance is None :
            DbManager.instance = DbManager()
        return DbManager.instance

    def __init__(self):
        self.cmd_db = 'command'
        self.log_db = 'log'
        self.calib_history_db = 'calib_history'
        self.sql_list = import_sql_json(os.path.join(os.getcwd(), 'json', 'calib_sql.json'))
        self.db_name = 'autoclalib.db'
        if not os.path.exists(os.path.join(os.getcwd(), 'db')):
            os.makedirs(os.path.join(os.getcwd(), 'db')) 

        self.conn = sqlite3.connect(os.path.join(os.getcwd(), 'db', self.db_name), isolation_level = None)
        self.cursur = self.conn.cursor()        

        create = ["create_command_db", "create_log_db", "create_calib_history"]
        for i in create :
            self.cursur.execute(self.sql_list[i])
        
    def insert(self, table, **k) :
        q = 'INSERT INTO ' + table
        c = '('
        v = 'VALUES ('
        for i in k :
            c += i[0]
            v += i[1]
        c += ')'
        v += ')'

        q = q + c + v
        print("insert query : ", q)
        self.cursur.execute(q)

    def update(self, table, **k) :
        q = 'UPDATE ' + table + ' SET '
        c = []
        v = []

        for i in k :
            c.append(i[0])
            v.append(i[1])

        for ii in range(len(c)) :
            t = c[ii] + " = " + v[ii]
            q += t
            if ii == len(c) - 1:
                q += "WHERE " + c[ii] + " = " + v[ii]

        print("update query : ", q)
        self.sursur.execute(q)

    def getJobStatus(self, id) :
        self.cursur.execute(self.sql_list["query_status"], (id))
