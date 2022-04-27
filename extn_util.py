import os
import numpy as np
import cv2
import logging
import json


def export_points(preset):

    filename = os.path.join(preset.root_path, 'images', 'answer.pts')
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    output = os.path.join(preset.root_path, 'images', 'output.pts')
    
    if json_data == None:
        logging.info("Can't open the pts file.") 
        return

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
    json_data['points'] = from_data['points']

    for i in range(len(preset.cameras)) :
        print("name : ", preset.cameras[i].view.name)
        json_data['points'][i]['dsc_id'] = preset.cameras[i].view.name
        json_data['points'][i]['point_index'] = 1
        json_data['points'][i]['framenum'] = 181
        json_data['points'][i]['camfps'] = 30
        json_data['points'][i]['flip'] = 0
        json_data['points'][i]['Group'] = "Group1"
        json_data['points'][i]['Width'] = preset.cameras[i].view.image_width
        json_data['points'][i]['Height'] = preset.cameras[i].view.image_height
        json_data['points'][i]['infection_point'] = 0
        json_data['points'][i]['swipe_base_length'] = -1.0
        json_data['points'][i]['ManualOffesetY'] = 0
        json_data['points'][i]['FocalLength'] = preset.cameras[i].focal

        json_data['points'][i]['pts_2d'] = from_data['points'][i]['pts_2d']
        json_data['points'][i]['pts_3d'] = from_data['points'][i]['pts_3d']

        json_data['points'][i]['pts_2d']['Upper'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_2d']['Upper']['IsEmpty'] = False
        json_data['points'][i]['pts_2d']['Upper']['X'] = from_data['points'][i]['pts_2d']['UpperPosX']
        json_data['points'][i]['pts_2d']['Upper']['Y'] = from_data['points'][i]['pts_2d']['UpperPosY']
        json_data['points'][i]['pts_2d']['Middle'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_2d']['Middle']['IsEmpty'] = False
        json_data['points'][i]['pts_2d']['Middle']['X'] = from_data['points'][i]['pts_2d']['MiddlePosX']
        json_data['points'][i]['pts_2d']['Middle']['Y'] = from_data['points'][i]['pts_2d']['MiddlePosY']
        json_data['points'][i]['pts_2d']['Lower'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_2d']['Lower']['IsEmpty'] = False
        json_data['points'][i]['pts_2d']['Lower']['X'] = from_data['points'][i]['pts_2d']['LowerPosX']
        json_data['points'][i]['pts_2d']['Lower']['Y'] = from_data['points'][i]['pts_2d']['LowerPosY']

        json_data['points'][i]['pts_3d']['Point1'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_3d']['Point1']['IsEmpty'] = False
        json_data['points'][i]['pts_3d']['Point1']['X'] = preset.cameras[i].pts_3D[0, :0]
        json_data['points'][i]['pts_3d']['Point1']['Y'] = preset.cameras[i].pts_3D[0, :1]
        json_data['points'][i]['pts_3d']['Point2'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_3d']['Point2']['IsEmpty'] = False
        json_data['points'][i]['pts_3d']['Point2']['X'] = preset.cameras[i].pts_3D[1, :0]
        json_data['points'][i]['pts_3d']['Point2']['Y'] = preset.cameras[i].pts_3D[1, :1]
        json_data['points'][i]['pts_3d']['Point3'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_3d']['Point3']['IsEmpty'] = False
        json_data['points'][i]['pts_3d']['Point3']['X'] = preset.cameras[i].pts_3D[2, :0]
        json_data['points'][i]['pts_3d']['Point3']['Y'] = preset.cameras[i].pts_3D[2, :1]
        json_data['points'][i]['pts_3d']['Point4'] = {"IsEmpty":None,"X":0,"Y":0}
        json_data['points'][i]['pts_3d']['Point4']['IsEmpty'] = False
        json_data['points'][i]['pts_3d']['Point4']['X'] = preset.cameras[i].pts_3D[3, :0]
        json_data['points'][i]['pts_3d']['Point4']['Y'] = preset.cameras[i].pts_3D[3, :1]
        
        json_data['points'][i]['pts_swipe'] = {"X1" : 0, "Y1":0, "X2": 0 , "Y2": 0}
        json_data['points'][i]['pts_swipe']['X1']=-1.0
        json_data['points'][i]['pts_swipe']['Y1']=-1.0
        json_data['points'][i]['pts_swipe']['X2']=-1.0
        json_data['points'][i]['pts_swipe']['Y2']=-1.0


def import_answer(filepath):

    with open(filepath, 'r') as json_file :
        json_data = json.load(json_file)

    if json_data == None:
        logging.info("Can't open the pts file.") 
        return

    print("import_answer : " , len(json_data['points']))
    answer = {}
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
