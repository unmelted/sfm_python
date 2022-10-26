import os
import time
import psycopg2 as pg
from psycopg2 import pool, extras
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
    connection_pool = pool.ThreadedConnectionPool(
        1, 50, host='127.0.0.1', database='autocalib', user='admin', password='1234')

    # @staticmethod
    # def get():
    #     con = connection_pool.getconn()
    #     print("New Pool return : ", con)
    #     return con

    @classmethod
    def getConnection(cls):
        # con = pg.connect(database='autocalib', user='admin', password='1234', host='127.0.0.1')
        con = cls.connection_pool.getconn()
        print("connect return : ", con)
        return con

    @classmethod
    def release(cls, conn):
        cls.connection_pool.putconn(conn)


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
    @staticmethod
    def initialize(connection):
        json_file = open(os.path.join(
            os.getcwd(), 'json', 'calib_pg.json'), 'r')
        sql_list = json.load(json_file)

        create = ["create_command_db",
                  "create_request_history", "create_job_manager", "create_generate_data"]

        for i in create:
            # print(self.sql_list[i])
            DBLayer.queryWorker(connection, 'create', sql_list[i])

        NewPool.release(connection)

    @staticmethod
    def queryWorker(connection, type, query):
        # l.get().w.info("query worker : {}".format(query))
        result = -1
        cursor = connection.cursor(cursor_factory=extras.NamedTupleCursor)
        # print("query worker : ", connection, cursor)
        cursor.execute(query)

        if type == 'select-one':
            result = cursor.fetchone()
        elif type == 'select-all':
            result = cursor.fetchall()
        else:  # insert , update
            connection.commit()
            result = 0
        # print(result)
        cursor.close()
        NewPool.releae(connection)
        return result
