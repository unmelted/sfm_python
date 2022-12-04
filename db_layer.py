import os
import time
# import psycopg as pg
from psycopg_pool import ConnectionPool
import json
from logger import Logger as l

keepalive_kwargs = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 5,
    "keepalives_count": 5,
}
# connection_pool = pool.ThreadedConnectionPool(
#     1, 50, host='127.0.0.1', database='autocalib', user='admin', password='1234', **keepalive_kwargs)


class NewPool(object):
    cs = "dbname=%s user=%s password=%s host=%s" % ('autocalib', 'admin', '1234', '127.0.0.1')

    def __init__(self) :            
        # conninfo = pg.conninfo.conninfo_to_dict(dbname='autocalib', user='admin', password='1234') # v2
        self.connection_pool = ConnectionPool(self.cs, max_size=50, num_workers=10)
        self.pid = os.getpid()

    # @staticmethod
    # def get():
    #     con = connection_pool.getconn()
    #     print("New Pool return : ", con)
    #     return con

    def __exit__(self):
        print('new pool exit! ')
        self.connection_pool.putconn()


    def getConn(self):
        # con = pg.connect(database='autocalib', user='admin', password='1234', host='127.0.0.1')
        # con = cls.connection_pool.connection() #v2
        # print("connect return : ", con)
        if self.pid == os.getpid() :
            return self.connection_pool
        else :
            print('process is different need to crate connection pool again')
            self.connection_pool = ConnectionPool(self.cs, max_size= 50, num_workers=10)
            return self.connection_pool


    # def release(cls, conn):
    #     cls.connection_pool.putconn(conn)


class BaseQuery(object):

    def loadjson(self):
        json_file = open(os.path.join(
            os.getcwd(), 'json', 'calib_pg.json'), 'r')
        sql_list = json.load(json_file)
        return sql_list

    def insert(table, **k):
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
        if table != 'calib_data' :
            l.get().w.info("Inser Query: {} ".format(q))
        return q

    def update(table, **k):
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
                t = c[ii] + ' = \'' + str(v[ii]) + '\' ,'
                q += t

        l.get().w.info("Update Query: {} ".format(q))
        return q


class DBLayer(object):
    cs = "dbname=%s user=%s password=%s host=%s" % ('autocalib', 'admin', '1234', '127.0.0.1')    
    connection_pool = ConnectionPool(cs, max_size=50, num_workers=10)
    pid = os.getpid()    

    @staticmethod
    def getConn():
        # con = pg.connect(database='autocalib', user='admin', password='1234', host='127.0.0.1')
        # con = cls.connection_pool.connection() #v2
        # print("connect return : ", con)
        if DBLayer.pid == os.getpid() :
            return DBLayer.connection_pool
        else :
            print('process is different need to crate connection pool again')
            DBLayer.pid = os.getpid()
            DBLayer.connection_pool = ConnectionPool(DBLayer.cs, max_size= 50, num_workers=10)
            return DBLayer.connection_pool

    @staticmethod
    def initialize(connection):
        json_file = open(os.path.join(
            os.getcwd(), 'json', 'calib_pg.json'), 'r')
        sql_list = json.load(json_file)

        create = ["create_command_db",
                  "create_request_history", "create_job_manager", "create_generate_data", "create_point_data"]

        for i in create:
            # print(self.sql_list[i])
            DBLayer.queryWorker('create', sql_list[i])

        # NewPool.release(connection)

    @staticmethod
    def queryWorker(type, query):
        # l.get().w.info("query worker : {}".format(query))

        with DBLayer.getConn().connection() as conn :
            with conn.cursor() as cur:
                cur.execute(query)
                # print("--------------queryworker", os.getpid(), cur )

                result = -1

                if type == 'select-one':
                    result = cur.fetchone()
                elif type == 'select-all':
                    result = cur.fetchmany()
                else:  # insert , update
                    conn.commit()
                    result = 0

                # cursor = connection.cursor(cursor_factory=extras.NamedTupleCursor) #v2
                # print("query worker : ", connection, cursor)
                # cursor.execute(query) #v2

                # if type == 'select-one':
                #     result = cursor.fetchone()
                # elif type == 'select-all':
                #     result = cursor.fetchall()
                # else:  # insert , update
                #     conn.commit()
                #     result = 0
                # # print(result)
                # cursor.close()
                return result
