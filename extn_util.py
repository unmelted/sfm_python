import os
import glob
import numpy as np
from mathutil import quaternion_rotation_matrix
import cv2
from logger import Logger as l
import json
from definition import DEFINITION as df

def export_points(preset, output_type, output_path, job_id):
    if output_type == 'dm' :
        export_points_dm(preset, output_path, job_id)
    elif output_type == 'mct' :
        export_points_mct(preset)

def export_points_mct(preset) :

    filename = os.path.join(preset.root_path, 'images', df.pts_file_name)
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    if from_data == None:
        l.get().w.info("Can't open the pts file.") 
        return
    point_json = {}
    point_json["stadium"] = "BasketballGround"
    point_json["world_coords"] = {}
    point_json["points"] = []

    for i in range(len(preset.cameras)) :
    # for i in range(2) :
        l.get().w.debug("name : {} ".format(preset.cameras[i].view.name))
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        _json = {}
        _json['dsc_id'] = viewname

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

def export_points_dm(preset, output_path, job_id) :

    filename = os.path.join(preset.root_path, 'images', df.pts_file_name)
    with open(filename, 'r') as json_file :
        from_data = json.load(json_file)

    if from_data == None:
        l.get().w.error("Can't open the pts file.") 
        return -12

    for j in range(len(from_data['points'])) :
        l.get().w.debug('pts dsc_id : {}'.format(from_data['points'][j]['dsc_id']))
        for i in range(len(preset.cameras)) :
            viewname = get_viewname(preset.cameras[i].view.name, preset.ext)            
            if from_data['points'][j]['dsc_id'] == viewname:
                l.get().w.info('camera view name : {}'.format(preset.cameras[i].view.name))
                from_data['points'][j]['pts_3d']['X1'] = preset.cameras[i].pts[0][0]
                from_data['points'][j]['pts_3d']['Y1'] = preset.cameras[i].pts[0][1]
                from_data['points'][j]['pts_3d']['X2'] = preset.cameras[i].pts[1][0]
                from_data['points'][j]['pts_3d']['Y2'] = preset.cameras[i].pts[1][1]
                from_data['points'][j]['pts_3d']['X3'] = preset.cameras[i].pts[2][0]
                from_data['points'][j]['pts_3d']['Y3'] = preset.cameras[i].pts[2][1]
                from_data['points'][j]['pts_3d']['X4'] = preset.cameras[i].pts[3][0]
                from_data['points'][j]['pts_3d']['Y4'] = preset.cameras[i].pts[3][1]

                from_data['points'][j]['pts_3d']['Point1']['X'] = preset.cameras[i].pts[0][0]
                from_data['points'][j]['pts_3d']['Point1']['Y'] = preset.cameras[i].pts[0][1]
                from_data['points'][j]['pts_3d']['Point2'] = {"IsEmpty":None,"X":0,"Y":0}
                from_data['points'][j]['pts_3d']['Point2']['IsEmpty'] = False
                from_data['points'][j]['pts_3d']['Point2']['X'] = preset.cameras[i].pts[1][0]
                from_data['points'][j]['pts_3d']['Point2']['Y'] = preset.cameras[i].pts[1][1]
                from_data['points'][j]['pts_3d']['Point3'] = {"IsEmpty":None,"X":0,"Y":0}
                from_data['points'][j]['pts_3d']['Point3']['IsEmpty'] = False
                from_data['points'][j]['pts_3d']['Point3']['X'] = preset.cameras[i].pts[2][0]
                from_data['points'][j]['pts_3d']['Point3']['Y'] = preset.cameras[i].pts[2][1]
                from_data['points'][j]['pts_3d']['Point4'] = {"IsEmpty":None,"X":0,"Y":0}
                from_data['points'][j]['pts_3d']['Point4']['IsEmpty'] = False
                from_data['points'][j]['pts_3d']['Point4']['X'] = preset.cameras[i].pts[3][0]
                from_data['points'][j]['pts_3d']['Point4']['Y'] = preset.cameras[i].pts[3][1]                                
                break;

        '''
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
        '''

    outfile = df.output_pts_file_name[:df.output_pts_file_name.rfind('.')] + str(job_id) + df.output_pts_file_name[df.output_pts_file_name.rfind('.'):]
    l.get().w.info("output pts file path {} name {} ".format(output_path, outfile))

    bn_json = json.dumps(from_data,indent=4)
    output = os.path.join(output_path, outfile)    
    ofile = open(output, 'w')
    ofile.write(bn_json)
    ofile.close()

def import_answer(filepath, limit):

    with open(filepath, 'r') as json_file :
        json_data = json.load(json_file)

    if json_data == None:
        l.get().w.error("Can't open the pts file.") 
        return

    l.get().w.info("import_answer : {} ".format(len(json_data['points'])))
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
        if limit != 0 and i < limit :
            break           
    
    return answer

def import_camera_pose(preset) :
    filename = os.path.join(preset.root_path, 'cameras', 'pose_colmap.json')    
    l.get().w.info("import_camera pose " , filename)

    with open(filename, 'r') as json_file :
        json_data = json.load(json_file)

    # for i in range(len(json_data["pose"])) :
    for i in range(11) :
        poseR = np.empty((0))
        poseT = np.empty((0))
        l.get().w.debug("import camera i : ", i)

        for r in json_data["pose"][i]["R"] :
            poseR = np.append(poseR, np.array(r).reshape((1)), axis = 0)

        for t in json_data["pose"][i]["T"] :
            poseT = np.append(poseT, np.array(t).reshape((1)), axis = 0)

        # poseR = poseR.reshape((3,3))
        poseR = quaternion_rotation_matrix(poseR)
        poseT = poseT.reshape((3,1))        
        l.get().w.debug(poseR)
        l.get().w.debug(poseT)
        cam = preset.cameras[i]
        cam.R = poseR
        cam.t = poseT
        cam.K = preset.K
        cam.calculate_p()


def save_ex_answer_image(preset) :

    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):    
        os.makedirs(output_path)

    for i in range(len(preset.cameras)) :
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        file_name = os.path.join(output_path, viewname +"_ans.png")
        gt_int = preset.answer[viewname].astype(np.int32)

        for j in range(preset.cameras[i].pts.shape[0]) :
            gt_pt = gt_int[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(gt_pt[0]), int(gt_pt[1])), 5, (0, 255, 0), -1)

            if j > 0 :
                cv2.line(preset.cameras[i].view.image, gt_int[j-1], gt_int[j], (255,0,0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image, gt_int[j], gt_int[0], (255,255,0), 3)

        l.get().w.info(file_name)
        cv2.imwrite(file_name, preset.cameras[i].view.image)


def save_point_image(preset) :

    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):    
        os.makedirs(output_path)

    for i in range(len(preset.cameras)) :
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        file_name = os.path.join(output_path, viewname +"_pt.png")
        pt_int = preset.cameras[i].pts.astype(np.int32)            

        for j in range(preset.cameras[i].pts.shape[0]) :
            pt_2d = preset.cameras[i].pts[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(pt_2d[0]), int(pt_2d[1])), 5, (0, 255, 0), -1)

            if j > 0 :
                cv2.line(preset.cameras[i].view.image, pt_int[j-1], pt_int[j], (255,0,0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image, pt_int[j], pt_int[0], (255,255,0), 3)

        l.get().w.info(file_name)
        cv2.imwrite(file_name, preset.cameras[i].view.image)



def get_viewname(name, ext):
    viewname = None

    if name.rfind('_') == -1 :
        viewname = name[:-1 * (len(ext) + 1)]
    else :
        viewname = name[:name.rfind('_')]

    return viewname


def import_json(path) :
    json_file = open(path, 'r')
    json_data = json.load(json_file)
    return json_data


def make_cam_list_in_pts(from_path, group_id):
    cam_inpts = []
    filename = os.path.join(from_path, df.pts_file_name)
    with open(filename, 'r') as json_file :
        _data = json.load(json_file)

    if _data == None:
        l.get().w.error("Can't open the pts file (for find camera list in group") 
        return -12, 0

    count = 0 
    for i in range(len(_data["points"])) :
        if _data["points"][i]["Group"] == group_id :
            cam_inpts.append(_data["points"][i]["dsc_id"])
            count += 1

    print(cam_inpts)
    return count, cam_inpts


def get_camera_list_in_both(from_path, group_id, ext) :
    image_names = []

    img_files = sorted(glob.glob(os.path.join(from_path, '*.' + ext)))
    result, cam_inpts = make_cam_list_in_pts(from_path, group_id)
    if result < 0 :
        return result, None, None

    for img_file in img_files :
        cam_id = img_file[img_file.rfind('/')+1:-1 * len(ext) -1]
        if cam_id.rfind('_') == 0:
            pass
        else :
            cam_id = cam_id[:cam_id.rfind('_')]

        if cam_id in cam_inpts:
            image_names.append(img_file)
    
    if len(image_names) == result :
        l.get().w.info("Image file = dsc_id in pts file same count")
    else :
        l.get().w.info("Image file != dsc_id in pts file cam count is different")
        
    return 0, image_names, cam_inpts

def get_caemra_info(from_path, cam_ids) :
    filename = os.path.join(from_path, df.pts_file_name)
    with open(filename, 'r') as json_file :
        _data = json.load(json_file)

    for cam in cam_ids :
        for i in range(len(_data["points"])):
            if cam == _data["points"][i]["dsc_id"] :
                cam_model = _data["points"][i]["ModelName"]
                lens_model = _data["points"][i]["LensName"]
                focal_length = _data["points"][i]["FocalLnegth"] # don't use now
                # DbManager.getInstance().insert('hw_info', type='camera', name=cam_model)
                # DbManager.getInstance().insert('hw_info', type='lense', name=lens_model)
                break

def get_info(from_path, group_id, ext) :

    result, image_names, cam_ids = get_camera_list_in_both(from_path, group_id,ext)
    if result != 0 :
        return result, None

    #result = get_caemra_info(cam_ids)

    return 0, image_names