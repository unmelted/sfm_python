import os
from enum import Enum
import logging


class TaskCategory(Enum):
    INIT                    = 0 
    AUTOCALIB               = 100
    AUTOCALIB_STATUS        = 200
    GENERATE_PTS            = 300
    VISUALIZE               = 400
    ANALYSIS                = 500
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
         100 : "Comeplete",

        -1 : "PROC ERR",
        -11 : "Create Preset Error",
        -12 : "Can't open and read pts file",
        -13 : "Image count is not match with dsc_id in pts",
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
        -142 : "There is no cameras in colmap db",
        -143 : "Command Error during colmap process",
        -144 : "No pair data in db",
        -145 : "Pair data is odd",
        -146 : "No solution",
        -147 : "Multiple soulution ",
        -148 : "Camera in solution is partaily missed",
        -149 : "No image name by image id",
        -150 : "No camera by viewname",
        -151 : "Job id is strange. No information",
        -152 : "No initial pair info file",
        -153 : "Initial pair info is not correct",

        -201 : "Query job_is is ambigous",

        -301 : "Base points should be inserted over 8",

        -501 : "There is no answer for err calculation"
    }

    if err_code in msg_pair : 
        msg = msg_pair[err_code]
    else : 
        msg = 'None'

    return msg


class DEFINITION(object) :

    base_index = 1000
    run_mode = 'colmap'
    cam_list = 'image_folder'     #list_from = ['video_folder' , 'image_folder', 'pts_file', 'colmap_db']    

    init_pair_mode = 'pair' # zero : just #0, #1 camera, pair : selected camera by colmap
    answer_from = 'pts' # pts : UserPointData.pts , input : UserInput through web    

    pts_file_name = 'UserPointData.pts'
    calib_sql_file = 'calib_sql.json'
    main_db_name = 'autocalib.db'
    colmap_db_name = 'colmap.db'

    export_point_type ='mct'  # 'dm', 'mct'
    output_pts_file_name = 'UserPointData_.pts'

    BOT_TOKEN = '5578949849:AAEJHteVLGJnydip3x5eYwJQQgcPymWGu4s'
    CHAT_ID = '1140943041'
    log_viewer_ip = '127.0.0.1'

    feature_ini = 'colmap_feature.ini'
    matcher_ini = 'colmap_matcher.ini'    
    mapper_ini = 'colmap_mapper.ini'

    initpair_file = 'init_pair.txt'


