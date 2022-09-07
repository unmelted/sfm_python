
from db_manager import DbManager as DB
from db_manager_sq import DbManagerSQ as SQ
from db_manager_pg import DbManagerPG as PG


class DBM(object):
    instance_sq = None
    instance_pg = None
    db_type = 'pq'  # pg = postgresql sq = sqlite

    @staticmethod
    def get(type=None):
        if DBM.instance_sq is None:
            DBM.instance_sq = SQ()
        if DBM.instance_pg is None:
            DBM.instance_pg = PG()

        if DBM.db_type == 'pq':
            return DBM.instance_pg
        elif DBM.db_type == 'sq':
            return DBM.instance_sq
        else:
            return DBM.instance_pg
