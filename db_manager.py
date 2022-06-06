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

        self.conn = sqlite3.connect(os.path.join(os.getcwd(), 'db', self.db_name), isolation_level=None, check_same_thread=False)
        self.cursur = self.conn.cursor()        

        create = ["create_command_db", "create_log_db", "create_calib_history"]
        for i in create :
            # print(self.sql_list[i])
            self.cursur.execute(self.sql_list[i])
        
    def insert(self, table, **k) :
        # print(k)
        q = 'INSERT INTO ' + table
        c = '('
        v = 'VALUES ('
        for i in k :
            c += '\'' + i + '\', '
            v += '\'' + str(k[i]) + '\', '
        c = c[:-2] + ')'
        v = v[:-2] + ')'

        q = q + c + v
        # print("insert query : ", q)
        self.cursur.execute(q)
        self.conn.commit()

    def update(self, table, **k) :
        q = 'UPDATE ' + table + ' SET '
        c = []
        v = []

        for i in k :
            c.append(i)
            v.append(k[i])

        for ii in range(len(c)) :
            if ii == len(c) - 1:
                q += 'WHERE ' + c[ii] + ' = ' + str(v[ii])
            else :
                t = c[ii] + ' = \"' + str(v[ii]) + '\"'
                q += t

        print("update query : ", q)
        self.cursur.execute(q)
        self.conn.commit()

    def getRootPath(self, id) :
        q = "SELECT root_path FROM command where job_id = " + str(id) + " ORDER BY datetime DESC "
        print("get rootpath query : " , q)
        self.cursur.execute(q)
        rows = self.cursur.fetchall()
                
        return rows[0][0]

    def getJobStatus(self, id) :
        q = "SELECT status FROM command where job_id = " + str(id)
        print("job status query : " , q)
        self.cursur.execute(q)
        rows = self.cursur.fetchall()
        
        if len(rows) > 1 :
            return -201
        else : 
            print(rows[0][0])
                
        return rows[0][0]