import os
import psutil
import time
import json
from definition import DEFINITION as defn
from logger import Logger as l
from db_layer import NewPool, DBLayer, BaseQuery


class JobManager(BaseQuery):
    instance = None
    conn = None

    def __init__(self, connection):
        self.conn = connection  # NewPool().get()
        print("job manager : ", self.conn)
        self.loadjson()

    @staticmethod
    def get(connection=None):
        if JobManager.instance == None and connection != None:
            JobManager.conn = connection
            JobManager.instance = JobManager(connection)
        elif JobManager.instance == None and connection == None:
            print('JobManager Get fail. connection is necessary')
            return -1

        return JobManager.instance

    @staticmethod
    def Watcher(self):
        while (True):
            time.sleep(1.5)
            self.check_pid()
            print(".. ")

    def check_pid(self):
        count, jids, pid1s, pid2s = self.getActiveJobs()
        if count == 0:
            return 0

        cids = self.getCancelJobs()
        for i in range(len(jids)):
            p = None
            job_id = jids[i]
            if job_id in cids:
                self.cancelProcess(job_id, pid1s[i], pid2s[i])

        return 0

    def getCancelJobs(self):
        cids = []
        q = self.sql_list['query_getcanceljobs']
        l.get().w.debug("Get canceljobs Query: {} ".format(q))

        rows = DBLayer().queryWorker(self.conn, 'select-all', q)

        for i in range(len(rows)):
            cids.append(int(rows[i][0]))

        print("getCancelJob : ", cids)
        return cids

    def cancelProcess(self, job_id, pid1, pid2):

        pid = pid2
        if pid < 0:
            l.get().w.critical("cancel malfuction minus pid: {} ".format(job_id))
            q = self.update('job_manager', cancel='done',
                            cancel_date='NOW()', complete='done', complete_date='NOW()', job_id=job_id)
            resutl = DBLayer().queryWorker(self.conn, 'update', q)
            return

        try:
            p = psutil.Process(pid)
            print(p)
            p.terminate()
        except psutil.NoSuchProcess:
            print("NoSuchProcess : ", pid)
            l.get().w.info("No such process pid {}. already disappeared.".format(pid))

        except psutil.AccessDenied:
            l.get().w.critical("Acess Deineid to SystemProcess")
            result = -23

        # q = self.sql_list['query_deletejobs'] + str(job_id)
        # l.get().w.debug("delte jobs Query: {} ".format(q))
        # self.cursur2.execute(q)
        # self.conn2.commit()
        q = self.update('job_manager', cancel='done',
                        cancel_date='NOW()', complete='done', complete_date='NOW()', job_id=job_id)
        result = DBLayer().queryWorker(self.conn, 'update', q)
        return 0

    def getActiveJobs(self):
        count = 0
        jids = []
        pid1s = []
        pid2s = []
        q = self.sql_list['query_getactivejobs']
        rows = DBLayer().queryWorker(self.conn, 'select-all', q)

        if len(rows) == 0:
            return 0, 0, 0, 0
        else:
            count = len(rows)

        for i in range(0, count):
            jids.append(rows[i][0])
            if rows[i][1] != 'None':
                pid1s.append(int(rows[i][1]))
            else:
                pid1s.append(-1)
            if rows[i][2] != 'None':
                pid2s.append(int(rows[i][2]))
            else:
                pid2s.append(-1)

        print("active jids : ", jids)
        print("active pids : ", pid1s)
        print("active pids : ", pid2s)
        print("active pids count : ", count)
        return count, jids, pid1s, pid2s

    def pushCancelJob(self, job_id):
        q = self.update('job_manager', cancel='try', job_id=job_id)
        result = DBLayer().queryWorker(self.conn, 'update', q)

    def countActiveJobs(self):
        q = self.sql_list['query_countactivejobs']
        l.get().w.info("Count activejobs Query: {} ".format(q))
        rows = DBLayer().queryWorker(self.conn, 'select-one', q)

        if len(rows) == 0:
            return 0
        else:
            l.get().w.debug("active jobs : {} ".format(rows[0]))
            count = rows[0]

        return count

    def checkJobsUnderLimit(self):
        curJobs = self.countActiveJobs()
        if curJobs < defn.job_limit:
            return True
        else:
            return False

    def checkJobStatusForCancel(self, job_id):
        q = self.sql_list['query_jobstatusforcancel'] + str(job_id)
        l.get().w.info("Jobstatus Query before cancel: {} ".format(q))
        print(q)
        rows = DBLayer().queryWorker(self.conn, 'select-one', q)

        print(rows[0], rows[1], rows[2])
        if len(rows) == 0:
            return -151
        else:
            #cancel / complete / pid2
            if rows[0] == None and rows[1] == 'running' and rows[2] != None:
                return 0
            else:
                if rows[0] != None:
                    return -401
                if rows[2] == None:
                    return -402
                return -202

    def insertNewJob(self, job_id, pid1=None):
        q = self.insert('job_manager', job_id=job_id,
                        pid1=pid1, pid2='None', complete='running')
        result = DBLayer().queryWorker(self.conn, 'insert', q)

    def updateJob(self, job_id, type, param=None):
        if type == 'complete':
            q = self.update('job_manager', complete='done',
                            complete_date='NOW()', job_id=job_id)
        elif type == 'updatepid2':
            q = self.update('job_manager', pid2=param,  job_id=job_id)

        result = DBLayer().queryWorker(self.conn, 'update', q)
