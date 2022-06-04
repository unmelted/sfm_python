import os
from enum import Enum
import logging

class TaskCategory(Enum):
    INIT                    = 0 
    AUTOCALIB               = 100
    AUTOCALIB_STATUS        = 200
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
        -1 : "PROC ERR",
        -11 : "Create Preset Error"
    }

    if err_code in msg_pair : 
        msg = msg_pair[err_code]
    else : 
        msg = 'None'

    return msg

def get_progress_msg(progress):
    msg = "May return proper message"
    return msg
