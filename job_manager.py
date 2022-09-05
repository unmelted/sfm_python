import os
import psutil
import psycopg2 as pg
import time
from definition import DEFINITION as df
from logger import Logger as l


class JobManager(object):
    instance = None

    @staticmethod
    def get():
        if JobManager.instance == None:
            JobManager.instance = JobManager()

        return JobManager.instance

    def __init__(self):
        self.conn = pg.connect("dbname=autocalib user=admin password=1234")
        self.cursur = self.conn.cursor()
        self.job_db = 'job_manager'

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
        self.conn.commit()

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
                t = c[ii] + ' = \'' + str(v[ii]) + '\' ,'
                q += t

        l.get().w.info("Update Query: {} ".format(q))

        self.cursur.execute(q)
        self.conn.commit()

    def Watcher(self):
        while (True):
            time.sleep(1.5)
            self.check_pid()

    def check_pid(self):
        count, pids = self.getActiveJobs()
        if count == 0:
            return 0

#        pid.0 job_id pid.1 python pid pid.2 colmap pid

        for pid in pids:
            p = None
            job_id = None
            try:
                p = psutil.Pocess(pid)
                print(p)
                if self.check_canceldjob(job_id) == True:
                    self.fcancel_preprocess(job_id, p)
            except psutil.NoSuchProcess:
                result = self.changeJobStatus(pid)

            except psutil.AccessDenied:
                l.get().w.critical("Acess Deineid to SystemProcess")
                result = -23

        return result

    def check_canceledjob(self, job_id):
        return True

    def cancel_preprocess(self, job_id, p):
        p.terminate()
        return 0

    def getActiveJobs(self):
        count = 0
        pids = []
        q = self.sql_list['query_getactivejobs']
        l.get().w.info("Get activejobs Query: {} ".format(q))

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if len(rows) == 0:
            return 0, 0
        else:
            l.get().w.debug("active jobs : {} ".format(rows[0][0]))
            count = rows[0][0]

        for i in range(0, count):
            pids.append(rows[i][0])
            pids.append(rows[i][1])

        print("active pids : ", pids)
        return count, pids

    def changeJobStatus(self, pid):
        pass

    def countActiveJobs(self):
        count = 0
        q = self.sql_list['query_countactivejobs']
        l.get().w.info("Get activejobs Query: {} ".format(q))

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if len(rows) == 0:
            return 0, 0
        else:
            l.get().w.debug("active jobs : {} ".format(rows[0][0]))
            count = rows[0][0]

        return count

    def checkJobsUnderLimit(self):
        curJobs = self..countActiveJobs()
        if curJobs < df.DEFINITION.job_limit:
            return True
        else:
            return False

    def insertNewJob(self, job_id, pid1=None, pid2=None):
        self.insert(
            'job_manager', job_id=job_id, pid1=pid1, pid2=pid2)

    def updatJobManager(self, job_id, pid1=None, pid2=None, ):
        self.update(
            'job_manager', job_id=job_id, pid1=pid1, pid2=pid2)
