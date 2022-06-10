import os
import glob
import numpy as np
import cv2
import logging
import json

from mathutil import quaternion_rotation_matrix


def export_points(preset, mode):
    if mode == 'dm' :
        export_points_dm(preset)
    elif mode == 'mct' :
        export_points_mct(preset)

def export_points_mct(preset) :

    filename = os.path.join(preset.root_path, 'images', 'answer.pts')
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    if from_data == None:
        logging.info("Can't open the pts file.") 
        return
    point_json = {}
    point_json["stadium"] = "BasketballGround"
    point_json["world_coords"] = {}
    point_json["points"] = []

    # for i in range(len(preset.cameras)) :
    for i in range(2) :
        print("name : ", preset.cameras[i].view.name)
        _json = {}
        _json['dsc_id'] = preset.cameras[i].view.name[:-4]

        _json['pts_2d'] = from_data['points'][i]['pts_2d']
        _json['pts_3d'] = from_data['points'][i]['pts_3d']

        _json['pts_2d']['Upper'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_2d']['Upper']['IsEmpty'] = False
        _json['pts_2d']['Upper']['X'] = -1.0
        _json['pts_2d']['Upper']['Y'] = -1.0
        _json['pts_2d']['Middle'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_2d']['Middle']['IsEmpty'] = False
        _json['pts_2d']['Middle']['X'] = -1.0
        _json['pts_2d']['Middle']['Y'] = -1.0
        _json['pts_2d']['Lower'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_2d']['Lower']['IsEmpty'] = False
        _json['pts_2d']['Lower']['X'] = -1.0
        _json['pts_2d']['Lower']['Y'] = -1.0

        _json['pts_3d']['Point1'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_3d']['Point1']['IsEmpty'] = False
        _json['pts_3d']['Point1']['X'] = round(preset.cameras[i].pts[0][0], 2)
        _json['pts_3d']['Point1']['Y'] = round(preset.cameras[i].pts[0][1], 2)
        _json['pts_3d']['Point2'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_3d']['Point2']['IsEmpty'] = False
        _json['pts_3d']['Point2']['X'] = round(preset.cameras[i].pts[1][0], 2)
        _json['pts_3d']['Point2']['Y'] = round(preset.cameras[i].pts[1][1], 2)
        _json['pts_3d']['Point3'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_3d']['Point3']['IsEmpty'] = False
        _json['pts_3d']['Point3']['X'] = round(preset.cameras[i].pts[2][0], 2)
        _json['pts_3d']['Point3']['Y'] = round(preset.cameras[i].pts[2][1], 2)
        _json['pts_3d']['Point4'] = {"IsEmpty":None,"X":0,"Y":0}
        _json['pts_3d']['Point4']['IsEmpty'] = False
        _json['pts_3d']['Point4']['X'] = round(preset.cameras[i].pts[3][0], 2)
        _json['pts_3d']['Point4']['Y'] = round(preset.cameras[i].pts[3][1], 2)
        
        _json['pts_swipe'] = {"X1" : 0, "Y1":0, "X2": 0 , "Y2": 0}
        _json['pts_swipe']['X1']=-1.0
        _json['pts_swipe']['Y1']=-1.0
        _json['pts_swipe']['X2']=-1.0
        _json['pts_swipe']['Y2']=-1.0

        point_json['points'].append(_json)

        if preset.limit != 0 and i == preset.limit :
            break                

    bn_json = json.dumps(point_json,indent=4)
    output = os.path.join(preset.root_path, 'images', 'output_mct.pts')    
    ofile = open(output, 'w')
    ofile.write(bn_json)
    ofile.close()

def import_camera_list() :
    pass

def export_points_dm(preset) :

    filename = os.path.join(preset.root_path, 'images', 'UserPointData.pts')
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    if from_data == None:
        logging.info("Can't open the pts file.") 
        return

    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):    
        os.makedirs(output_path)

    json_data = {}
    json_data["RecordName"] = from_data["RecordName"]
    json_data["PreSetNumber"] = from_data["PreSetNumber"]    
    json_data["worlds"] = from_data["worlds"]        
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

        point_json['pts_2d'] = {}
        point_json['pts_3d'] = {}

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
    output = os.path.join(preset.root_path, 'output', 'AutoCalib.pts')    
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

        pt_6 = False
        if pt_6 : 
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

def import_camera_pose(preset) :
    filename = os.path.join(preset.root_path, 'cameras', 'pose_colmap.json')    
    print("import_camera pose " , filename)

    with open(filename, 'r') as json_file :
        json_data = json.load(json_file)

    # for i in range(len(json_data["pose"])) :
    for i in range(11) :
        poseR = np.empty((0))
        poseT = np.empty((0))
        print("import camera i : ", i)

        for r in json_data["pose"][i]["R"] :
            poseR = np.append(poseR, np.array(r).reshape((1)), axis = 0)

        for t in json_data["pose"][i]["T"] :
            poseT = np.append(poseT, np.array(t).reshape((1)), axis = 0)

        # poseR = poseR.reshape((3,3))
        poseR = quaternion_rotation_matrix(poseR)
        poseT = poseT.reshape((3,1))        
        print(poseR)
        print(poseT)
        cam = preset.cameras[i]
        cam.R = poseR
        cam.t = poseT
        cam.K = preset.K
        cam.calculate_p()


def save_point_image(preset) :

    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):    
        os.makedirs(output_path)

    for i in range(len(preset.cameras)) :
        viewname = preset.cameras[i].view.name[:-4]
        if preset.ext == 'tiff':
            viewname = preset.cameras[i].view.name[:-8]

        file_name = os.path.join(output_path, viewname +"_pt.png")
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

def import_sql_json(path) :
    json_file = open(path, 'r')
    json_data = json.load(json_file)
    return json_data

def import_colmap_cmd_json(path) :
    json_file = open(path, 'r')
    json_data = json.load(json_file)
    return json_data


def import_group_info(group_id):
    pass 

def get_camera_list_by_group(from_path, group_id) :
    image_names = []

    files = sorted(glob.glob(from_path))
    ptsfiles = import_group_info(group_id)

    for img in files :
        if img in ptsfiles:
            image_names.append(img)
    

    return image_names