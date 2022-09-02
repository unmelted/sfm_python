import os
import threading
import sqlite3
from extn_util import *
from logger import Logger as l
from definition import DEFINITION as df
from db_manager_sq import DbManagerSQ as SQ
from db_manager_pg import DbManagerPG as PG


class DbManager(object):
    instance_sq = None
    instance_pg = None

    @staticmethod
    def getInstance(type=None):
        if DbManager.instance_sq is None:
            DbManager.instance_sq = SQ()
        if DbManager.instance_pg is None:
            DbManager.instance_pg = PG()

        if type == 'sq':
            return DbManager.instance_sq
        elif type == 'pg':
            return DbManager.instance_pg
        else:
            return DbManager.instance_pg
