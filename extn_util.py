import os
import numpy as np
import cv2
import logging
import json


def export_points(preset):

    filename = os.path.join(preset.root_path, 'images', 'answer.pts')
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    if from_data == None:
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
    json_data['points'] = []

    for i in range(len(preset.cameras)) :
        print("name : ", preset.cameras[i].view.name)

        point_json = {}
        point_json['dsc_id'] = preset.cameras[i].view.name
        point_json['point_index'] = 1
        point_json['framenum'] = 181
        point_json['camfps'] = 30
        point_json['flip'] = 0
        point_json['Group'] = "Group1"
        point_json['Width'] = preset.cameras[i].view.image_width
        point_json['Height'] = preset.cameras[i].view.image_height
        point_json['infection_point'] = 0
        point_json['swipe_base_length'] = -1.0
        point_json['ManualOffesetY'] = 0
        point_json['FocalLength'] = preset.cameras[i].focal

        point_json['pts_2d'] = from_data['points'][i]['pts_2d']
        point_json['pts_3d'] = from_data['points'][i]['pts_3d']

        point_json['pts_2d']['Upper'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_2d']['Upper']['IsEmpty'] = False
        point_json['pts_2d']['Upper']['X'] = -1.0
        point_json['pts_2d']['Upper']['Y'] = -1.0
        point_json['pts_2d']['Middle'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_2d']['Middle']['IsEmpty'] = False
        point_json['pts_2d']['Middle']['X'] = -1.0
        point_json['pts_2d']['Middle']['Y'] = -1.0
        point_json['pts_2d']['Lower'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_2d']['Lower']['IsEmpty'] = False
        point_json['pts_2d']['Lower']['X'] = -1.0
        point_json['pts_2d']['Lower']['Y'] = -1.0

        point_json['pts_3d']['Point1'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_3d']['Point1']['IsEmpty'] = False
        point_json['pts_3d']['Point1']['X'] = preset.cameras[i].pts[0][0]
        point_json['pts_3d']['Point1']['Y'] = preset.cameras[i].pts[0][1]
        point_json['pts_3d']['Point2'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_3d']['Point2']['IsEmpty'] = False
        point_json['pts_3d']['Point2']['X'] = preset.cameras[i].pts[1][0]
        point_json['pts_3d']['Point2']['Y'] = preset.cameras[i].pts[1][1]
        point_json['pts_3d']['Point3'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_3d']['Point3']['IsEmpty'] = False
        point_json['pts_3d']['Point3']['X'] = preset.cameras[i].pts[2][0]
        point_json['pts_3d']['Point3']['Y'] = preset.cameras[i].pts[2][1]
        point_json['pts_3d']['Point4'] = {"IsEmpty":None,"X":0,"Y":0}
        point_json['pts_3d']['Point4']['IsEmpty'] = False
        point_json['pts_3d']['Point4']['X'] = preset.cameras[i].pts[3][0]
        point_json['pts_3d']['Point4']['Y'] = preset.cameras[i].pts[3][1]
        
        point_json['pts_swipe'] = {"X1" : 0, "Y1":0, "X2": 0 , "Y2": 0}
        point_json['pts_swipe']['X1']=-1.0
        point_json['pts_swipe']['Y1']=-1.0
        point_json['pts_swipe']['X2']=-1.0
        point_json['pts_swipe']['Y2']=-1.0

        json_data['points'].append(point_json)

        if preset.limit != 0 and i == preset.limit :
            break                

    bn_json = json.dumps(json_data,indent=4)
    output = os.path.join(preset.root_path, 'images', 'output.pts')    
    ofile = open(output, 'w')
    ofile.write(bn_json)
    ofile.close()

def import_answer(filepath, limit):

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
        
        pt = np.array([json_data['points'][i]['pts_3d']['X5'], json_data['points'][i]['pts_3d']['Y5']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, np.array(pt), axis=0)        
        pt = np.array([json_data['points'][i]['pts_3d']['X6'], json_data['points'][i]['pts_3d']['Y6']])
        pt = pt.reshape((1, 2))        
        answer_pt = np.append(answer_pt, pt, axis=0)
        
        
        # pt = np.array([json_data['points'][i]['pts_3d']['Center']['X'], json_data['points'][i]['pts_3d']['Center']['Y']])
        # pt = pt.reshape((1, 2))        
        # answer_pt = np.append(answer_pt, pt, axis=0)


        answer[name] = answer_pt
        # print(answer[name])
        if limit != 0 and i == limit :
            break           
    
    return answer

def save_point_image(preset) :

    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):    
        os.makedirs(output_path)

    for i in range(len(preset.cameras)) :
        file_name = os.path.join(output_path, preset.cameras[i].view.name +"_pt.png")        
        pt_int = preset.cameras[i].pts.astype(np.int32)            

        for j in range(preset.cameras[i].pts.shape[0]) :
            pt_2d = preset.cameras[i].pts[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(pt_2d[0]), int(pt_2d[1])), 5, (0, 255, 0), -1)

            if j > 0 :
                cv2.line(preset.cameras[i].view.image, pt_int[j-1], pt_int[j], (255,0,0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image, pt_int[j], pt_int[0], (255,255,0), 3)

        print(file_name)
        cv2.imwrite(file_name, preset.cameras[i].view.image)