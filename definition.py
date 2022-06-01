import os
import logging



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