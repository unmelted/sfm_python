import os
import sqlite3
from extn_util import * 

class DbManager(object) :

    def __init__(self, root_path):
        self.sql_list = import_sql_json(os.path.join(root_path, 'calib_sql.json'))        
        self.db_name = 'autoclalib.db'
        if not os.path.exists(os.path.join(root_path, 'db')):
            os.makedirs(os.path.join(root_path, 'db')) 

        self.conn = sqlite3.connect(os.path.join(root_path, 'db', self.db_name), isolation_level = None)
        self.cursur = self.conn.cursor()        

        self.cursur.execute(self.sql_list["create_cameras"])


    def read_cameras(self):
        pass