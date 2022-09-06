from logger import Logger as l


class DbManager(object):
    main_db_name = 'autocalib.db'

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
        from definition import DEFINITION as defn
        index = 0
        self.cursur.execute(self.sql_list['query_job_id'])
        rows = self.cursur.fetchone()
        if rows == None:
            return defn .base_index
        if len(rows) == 0:
            return defn.base_index

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
