
import numpy as np
import cv2
import logging
import json


def export_points(preset):

    json_data = {
            "RecordName" : None,
            "PreSetNumber" : 0,
            "worlds" : [
                {
                        
                    "group":None,
                    "stadium":None,
                    "world_coords":None
                }
            ]
                ,
            "points" : None
        }
    json_data['worlds'][0]['group'] = "Group1"
    json_data['worlds'][0]['stadium'] = preset.world.stadium


def import_answer(filepath):
    answer = {}

    with open(filepath, 'r') as json_file :
        json_data = json.load(json_file)

    if json_data == None:
        logging.info("Can't open the pts file.") 
        return

    print("import_answer : " , len(json_data['points']))

    for i in range(len(json_data['points'])):
        answer_pt = np.empty((0,2))
        name = json_data['points'][i]['dsc_id']
        print("dsc id : ", name)

        pt = np.array([json_data['points'][i]['pts_3d']['X1'], json_data['points'][i]['pts_3d']['Y1']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, pt, axis=0)
        pt = np.array([json_data['points'][i]['pts_3d']['X2'], json_data['points'][i]['pts_3d']['Y2']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, pt, axis=0)        

        pt = np.array([json_data['points'][i]['pts_3d']['X3'], json_data['points'][i]['pts_3d']['Y3']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, np.array(pt), axis=0)        
        pt = np.array([json_data['points'][i]['pts_3d']['X4'], json_data['points'][i]['pts_3d']['Y4']])
        pt = pt.reshape((1, 2))        
        answer_pt = np.append(answer_pt, pt, axis=0)
        pt = np.array([json_data['points'][i]['pts_3d']['Center']['X'], json_data['points'][i]['pts_3d']['Center']['Y']])
        pt = pt.reshape((1, 2))        
        answer_pt = np.append(answer_pt, pt, axis=0)


        answer[name] = answer_pt
        # print(answer[name])
    
    return answer
