import os
from enum import Enum
import logging


class TaskCategory(Enum):
    INIT                    = 0 
    AUTOCALIB               = 100
    AUTOCALIB_STATUS        = 200
    FINISH                  = 1
    
def get_err_msg(err_code) :
    msg = None
    msg_pair = {
        0 : "ERR NONE",
        -1 : "PROC ERR"
    }

    if err_code in msg_pair : 
        msg = msg_pair[err_code]
    else : 
        msg = 'None'

    return msg