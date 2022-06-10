import os
from enum import Enum
import logging

class TaskCategory(Enum):
    INIT                    = 0 
    AUTOCALIB               = 100
    AUTOCALIB_STATUS        = 200
    VISUALIZE               = 300
    FINISH                  = 1

class CommandMode(Enum):
    PREPROCESS          = 10
    FEATURE             = 20
    MATCHER             = 30
    MAPPER              = 40
    BA                  = 50
    HALF                = 55
    MODEL_CONVERT       = 60
    GENERATE_PTS        = 70
    FULL                = 75
    PTS_ERROR_ANALYSIS  = 80
    VISUALIZE           = 90


def get_err_msg(err_code) :
    msg = None
    msg_pair = {
         0 : "ERR NONE",
         100 : "Comepelete",

        -1 : "PROC ERR",
        -11 : "Create Preset Error",
        -21 : "Input value is invalid",

        -101 : "Error on Autocalib Init. (create group)",
        -102 : "Video (Camera) file is too small count",
        -103 : "Making Snapshot error",
        -104 : "There is no model info in root_dir",
        -105 : "Can't access to input directory",
        -106 : "There is no pts file",
        -107 : "Can't read images",
        -140 : "Convert model error ",
        -141 : "Camera info duplicated with image name",

        -201 : "Query job_is is ambigous"

    }

    if err_code in msg_pair : 
        msg = msg_pair[err_code]
    else : 
        msg = 'None'

    return msg