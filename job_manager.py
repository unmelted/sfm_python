import os
import psutil
import psycopg2 as pg
import time
import json
from definition import DEFINITION as defn
from logger import Logger as l
from db_manager_pg import DbManagerPG


class JobManager(DbManagerPG):
    instance = None

    @staticmethod
    def get():
        if JobManager.instance == None:
            JobManager.instance = JobManager()

        return JobManager.instance

    def __init__(self):
        self.conn = pg.connect("dbname=autocalib user=admin password=1234")
        self.cursur = self.conn.cursor()
        json_file = open(os.path.join(
            os.getcwd(), 'json', self.calib_pg_file), 'r')
        self.sql_list = json.load(json_file)

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
        self.cursur.execute(q)
        rows = self.cursur.fetchall()
        for i in range(len(rows)):
            cids.append(int(rows[i][0]))

        print("getCancelJob : ", cids)
        return cids

    def cancelProcess(self, job_id, pid1, pid2):

        for i in [0, 1]:
            pid = pid1 if i == 0 else pid2
            if pid == -1:
                continue
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
        self.update('job_manager', cancel='done',
                    cancel_date='NOW()', complete='done', complete_date='NOW()', job_id=job_id)
        return 0

    def getActiveJobs(self):
        count = 0
        jids = []
        pid1s = []
        pid2s = []
        q = self.sql_list['query_getactivejobs']
        l.get().w.debug("Get activejobs Query: {} ".format(q))
        self.cursur.execute(q)
        rows = self.cursur.fetchall()

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
        self.update('job_manager', cancel='try', job_id=job_id)

    def countActiveJobs(self):
        count = 0
        q = self.sql_list['query_countactivejobs']
        l.get().w.info("Count activejobs Query: {} ".format(q))

        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if len(rows) == 0:
            return 0, 0
        else:
            l.get().w.debug("active jobs : {} ".format(rows[0][0]))
            count = rows[0][0]

        return count

    def checkJobsUnderLimit(self):
        curJobs = self.countActiveJobs()
        if curJobs < defn.job_limit:
            return True
        else:
            return False

    def checkJobStatus(self, job_id):
        q = self.sql_list['query_jobstatus'] + str(job_id)
        l.get().w.info("Jobstatus Query before cancel: {} ".format(q))
        print(q)
        self.cursur.execute(q)
        rows = self.cursur.fetchone()
        print(rows)
        print(rows[0], rows[1])
        if len(rows) == 0:
            return -151
        else:
            if rows[0] == None:
                print("same none")
            if rows[1] == 'running':
                print("same running")
                return 0
            else:
                return -202

    def insertNewJob(self, job_id, pid1=None, pid2=None):
        self.insert('job_manager', job_id=job_id, pid1=pid1,
                    pid2=pid2, complete='running')
