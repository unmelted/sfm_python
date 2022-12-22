import os
import glob
import shutil
import numpy as np
from mathutil import *
import cv2
from logger import Logger as l
import json
from definition import DEFINITION as defn
from intrn_util import *
from PIL import Image
from db_manager import DbManager


def export_points(preset, output_type, myjob_id, cal_type, scale, target_path=None):
    if output_type == 'dm':
        output_path = os.path.join(preset.root_path, 'output')
        export_points_dm(preset, myjob_id, cal_type,
                         output_path, scale, target_path)

    elif output_type == 'mct':
        export_points_mct(preset, cal_type)


def export_points_mct(preset, cal_type):

    filename = os.path.join(preset.root_path, 'images', defn.pts_file_name)
    with open(filename, 'r') as json_file:
        from_data = json.load(json_file)

    if from_data == None:
        l.get().w.info("Can't open the pts file.")
        return
    point_json = {}
    point_json["stadium"] = "BasketballGround"
    point_json["world_coords"] = {}
    point_json["points"] = []

    for i in range(len(preset.cameras)):
        # for i in range(2) :
        l.get().w.debug("name : {} ".format(preset.cameras[i].view.name))
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        _json = {}
        _json['dsc_id'] = viewname + '_'

        if i < len(from_data['points']):
            _json['pts_2d'] = from_data['points'][i]['pts_2d']
            _json['pts_3d'] = from_data['points'][i]['pts_3d']
        else:
            _json['pts_2d'] = {}
            _json['pts_3d'] = {}

        if cal_type == '3D' or cal_type == '2D3D':
            _json['pts_3d']['X1'] = preset.cameras[i].pts_3d[0][0]
            _json['pts_3d']['Y1'] = preset.cameras[i].pts_3d[0][1]
            _json['pts_3d']['X2'] = preset.cameras[i].pts_3d[1][0]
            _json['pts_3d']['Y2'] = preset.cameras[i].pts_3d[1][1]
            _json['pts_3d']['X3'] = preset.cameras[i].pts_3d[2][0]
            _json['pts_3d']['Y3'] = preset.cameras[i].pts_3d[2][1]
            _json['pts_3d']['X4'] = preset.cameras[i].pts_3d[3][0]
            _json['pts_3d']['Y4'] = preset.cameras[i].pts_3d[3][1]
        if cal_type == '2D' or cal_type == '2D3D':
            _json['pts_2d']['UpperPosX'] = preset.cameras[i].pts_2d[0][0]
            _json['pts_2d']['UpperPosY'] = preset.cameras[i].pts_2d[0][1]
            _json['pts_2d']['LowerPosX'] = preset.cameras[i].pts_2d[1][0]
            _json['pts_2d']['LowerPosY'] = preset.cameras[i].pts_2d[1][1]
            _json['pts_2d']['MiddlePosX'] = -1.0
            _json['pts_2d']['MiddlePosY'] = -1.0

        _json['pts_swipe'] = {"X1": 0, "Y1": 0, "X2": 0, "Y2": 0}
        _json['pts_swipe']['X1'] = -1.0
        _json['pts_swipe']['Y1'] = -1.0
        _json['pts_swipe']['X2'] = -1.0
        _json['pts_swipe']['Y2'] = -1.0

        point_json['points'].append(_json)

        if preset.limit != 0 and i == preset.limit:
            break

    bn_json = json.dumps(point_json, indent=4)
    output = os.path.join(preset.root_path, 'images', 'output_mct.pts')
    ofile = open(output, 'w')
    ofile.write(bn_json)
    ofile.close()


def export_points_dm(preset, myjob_id, cal_type, output_path, scale, target_path):

    scale_factor = 1.0 if scale == 'full' else 2.0
    filename = os.path.join(preset.root_path, 'images', defn.pts_file_name)
    with open(filename, 'r') as json_file:
        from_data = json.load(json_file)

    if from_data == None:
        l.get().w.error("Can't open the pts file.")
        return -12

    l.get().w.info("Write dm pts file.. ")
    new_data = {'points': []}

    for j in range(len(from_data['points'])):
        l.get().w.debug('pts dsc_id : {}'.format(
            from_data['points'][j]['dsc_id']))
        for i in range(len(preset.cameras)):
            viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
            if from_data['points'][j]['dsc_id'] == viewname:
                l.get().w.info('cal_type {} camera view name : {}'.format(
                    cal_type, preset.cameras[i].view.name))
                if cal_type == '3D' or cal_type == '2D3D':
                    from_data['points'][j]['pts_3d']['X1'] = preset.cameras[i].pts_3d[0][0] * scale_factor
                    from_data['points'][j]['pts_3d']['Y1'] = preset.cameras[i].pts_3d[0][1] * scale_factor
                    from_data['points'][j]['pts_3d']['X2'] = preset.cameras[i].pts_3d[1][0] * scale_factor
                    from_data['points'][j]['pts_3d']['Y2'] = preset.cameras[i].pts_3d[1][1] * scale_factor
                    from_data['points'][j]['pts_3d']['X3'] = preset.cameras[i].pts_3d[2][0] * scale_factor
                    from_data['points'][j]['pts_3d']['Y3'] = preset.cameras[i].pts_3d[2][1] * scale_factor
                    from_data['points'][j]['pts_3d']['X4'] = preset.cameras[i].pts_3d[3][0] * scale_factor
                    from_data['points'][j]['pts_3d']['Y4'] = preset.cameras[i].pts_3d[3][1] * scale_factor
                if cal_type == '2D' or cal_type == '2D3D':
                    from_data['points'][j]['pts_2d']['UpperPosX'] = preset.cameras[i].pts_2d[0][0] * scale_factor
                    from_data['points'][j]['pts_2d']['UpperPosY'] = preset.cameras[i].pts_2d[0][1] * scale_factor
                    from_data['points'][j]['pts_2d']['MiddlePosX'] = -1.0
                    from_data['points'][j]['pts_2d']['MiddlePosY'] = -1.0
                    from_data['points'][j]['pts_2d']['LowerPosX'] = preset.cameras[i].pts_2d[1][0] * scale_factor
                    from_data['points'][j]['pts_2d']['LowerPosY'] = preset.cameras[i].pts_2d[1][1] * scale_factor

                new_data['points'].append(from_data['points'][j])
                break

    bn_json = json.dumps(new_data, indent=4)
    DbManager.insert_calibdata(myjob_id, bn_json)

    # outfile = defn.output_pts_file_name[:defn.output_pts_file_name.rfind(
    #     '.')] + str(myjob_id) + defn.output_pts_file_name[defn.output_pts_file_name.rfind('.'):]
    # l.get().w.info("output pts file path {} name {} ".format(output_path, outfile))
    # output = os.path.join(output_path, outfile)
    # ofile = open(output, 'w')
    # ofile.write(bn_json)
    # ofile.close()

    # shutil.copy(output, target_path)
    l.get().w.warn("output pts file copy done to {} ".format(target_path))


def import_answer(filepath, limit):

    with open(filepath, 'r') as json_file:
        json_data = json.load(json_file)

    if json_data == None:
        l.get().w.error("Can't open the pts file.")
        return

    l.get().w.info("import_answer : {} ".format(len(json_data['points'])))
    answer = {}
    for i in range(len(json_data['points'])):
        answer_pt = np.empty((0, 2))
        name = json_data['points'][i]['dsc_id']
        # print("dsc id : ", name)

        pt = np.array([json_data['points'][i]['pts_3d']['X1'],
                      json_data['points'][i]['pts_3d']['Y1']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, pt, axis=0)
        pt = np.array([json_data['points'][i]['pts_3d']['X2'],
                      json_data['points'][i]['pts_3d']['Y2']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, pt, axis=0)

        pt = np.array([json_data['points'][i]['pts_3d']['X3'],
                      json_data['points'][i]['pts_3d']['Y3']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, np.array(pt), axis=0)
        pt = np.array([json_data['points'][i]['pts_3d']['X4'],
                      json_data['points'][i]['pts_3d']['Y4']])
        pt = pt.reshape((1, 2))
        answer_pt = np.append(answer_pt, pt, axis=0)

        pt_6 = False
        if pt_6:
            pt = np.array([json_data['points'][i]['pts_3d']['X5'],
                          json_data['points'][i]['pts_3d']['Y5']])
            pt = pt.reshape((1, 2))
            answer_pt = np.append(answer_pt, np.array(pt), axis=0)
            pt = np.array([json_data['points'][i]['pts_3d']['X6'],
                          json_data['points'][i]['pts_3d']['Y6']])
            pt = pt.reshape((1, 2))
            answer_pt = np.append(answer_pt, pt, axis=0)

        # pt = np.array([json_data['points'][i]['pts_3d']['Center']['X'], json_data['points'][i]['pts_3d']['Center']['Y']])
        # pt = pt.reshape((1, 2))
        # answer_pt = np.append(answer_pt, pt, axis=0)

        answer[name] = answer_pt
        # print(answer[name])
        if limit != 0 and i >= limit-1:
            break

    return answer


def import_camera_pose(preset):
    filename = os.path.join(preset.root_path, 'cameras', 'pose_colmap.json')
    l.get().w.info("import_camera pose {}".format(filename))

    with open(filename, 'r') as json_file:
        json_data = json.load(json_file)

    # for i in range(len(json_data["pose"])) :
    for i in range(11):
        poseR = np.empty((0))
        poseT = np.empty((0))
        l.get().w.debug("import camera i : {}".format(i))

        for r in json_data["pose"][i]["R"]:
            poseR = np.append(poseR, np.array(r).reshape((1)), axis=0)

        for t in json_data["pose"][i]["T"]:
            poseT = np.append(poseT, np.array(t).reshape((1)), axis=0)

        # poseR = poseR.reshape((3,3))
        poseR = quaternion_to_rotation(poseR)
        poseT = poseT.reshape((3, 1))
        l.get().w.debug(poseR)
        l.get().w.debug(poseT)
        cam = preset.cameras[i]
        cam.R = poseR
        cam.t = poseT
        cam.K = preset.K
        cam.calculate_p()


def save_ex_answer_image(preset):

    output_path = os.path.join(preset.root_path, 'output')
    for i in range(len(preset.cameras)):
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        file_name = os.path.join(output_path, viewname + "_ans.jpg")
        gt_int = preset.answer[viewname].astype(np.int32)

        for j in range(preset.cameras[i].pts.shape[0]):
            gt_pt = gt_int[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(
                gt_pt[0]), int(gt_pt[1])), 5, (0, 255, 0), -1)

            if j > 0:
                cv2.line(preset.cameras[i].view.image,
                         gt_int[j-1], gt_int[j], (255, 0, 0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image,
                         gt_int[j], gt_int[0], (255, 255, 0), 3)

        l.get().w.info(file_name)
        cv2.imwrite(file_name, preset.cameras[i].view.image)


def save_point_image(preset, myjob_id):
    output_path = os.path.join(preset.root_path, 'output')
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    review_path = os.path.join(defn.output_pts_image_dir, str(myjob_id))
    if not os.path.exists(review_path): 
        os.makedirs(review_path)

    print('save_point_image review_path : ', review_path)

    for i in range(len(preset.cameras)):
        viewname = get_viewname(preset.cameras[i].view.name, preset.ext)
        file_name = os.path.join(output_path, viewname + "_pt.jpg")

        print(preset.cameras[i].pts_3d.shape[0],
              preset.cameras[i].pts_2d.shape[0], preset.cameras[i].pts_extra.shape[0])

        for j in range(preset.cameras[i].pts_3d.shape[0]):
            pt_int = preset.cameras[i].pts_3d.astype(np.int32)
            pt_3d = preset.cameras[i].pts_3d[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(
                pt_3d[0]), int(pt_3d[1])), 5, (0, 255, 0), -1)

            if j > 0:
                cv2.line(preset.cameras[i].view.image,
                         pt_int[j-1], pt_int[j], (255, 0, 0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image,
                         pt_int[j], pt_int[0], (255, 255, 0), 3)
                cv2.circle(preset.cameras[i].view.image, (int(
                    pt_3d[0]), int(pt_3d[1])), 5, (0, 255, 255), -1)

        for j in range(preset.cameras[i].pts_2d.shape[0]):
            pt_int = preset.cameras[i].pts_2d.astype(np.int32)
            pt_2d = preset.cameras[i].pts_2d[j, :]
            cv2.circle(preset.cameras[i].view.image, (int(
                pt_2d[0]), int(pt_2d[1])), 5, (0, 255, 0), -1)

            if j > 0:
                cv2.line(preset.cameras[i].view.image,
                         pt_int[j-1], pt_int[j], (255, 0, 0), 3)
            if j == (preset.cameras[i].pts.shape[0] - 1):
                cv2.line(preset.cameras[i].view.image,
                         pt_int[j], pt_int[0], (255, 255, 0), 3)

        if (preset.cameras[i].pts_extra.shape[0]) > 1:
            pt_ex = preset.cameras[i].pts_extra
            cv2.circle(preset.cameras[i].view.image, (int(
                pt_ex[0][0]), int(pt_ex[0][1])), 5, (0, 255, 0), -1)
            cv2.circle(preset.cameras[i].view.image, (int(
                pt_ex[1][0]), int(pt_ex[1][1])), 5, (0, 255, 0), -1)
            #cv2.circle(preset.cameras[i].view.image, (int(pt_ex[2][0]), int(pt_ex[2][1])), 5, (0, 255, 0), -1)
            cv2.line(preset.cameras[i].view.image, (int(pt_ex[0][0]), int(pt_ex[0][1])), (int(pt_ex[1][0]), int(pt_ex[1][1])),
                     (255, 0, 0), 3)
            print("extra point ! :",  int(pt_ex[0][0]), int(
                pt_ex[0][1]), int(pt_ex[1][0]), int(pt_ex[1][1]))

        l.get().w.info(file_name)
        output = cv2.resize(preset.cameras[i].view.image, (1280, 720))
        cv2.imwrite(file_name, output)
        shutil.copy(file_name, review_path)


def import_json(path):
    json_file = open(path, 'r')
    json_data = json.load(json_file)
    return json_data


def make_cam_list_in_pts(from_path, group_id):
    cam_inpts = []
    filename = os.path.join(from_path, defn.pts_file_name)
    with open(filename, 'r') as json_file:
        _data = json.load(json_file)

    if _data == None:
        l.get().w.error("Can't open the pts file (for find camera list in group")
        return -12, 0

    count = 0
    for i in range(len(_data["points"])):
        if _data["points"][i]["Group"] == group_id:
            cam_inpts.append(_data["points"][i]["dsc_id"])
            count += 1

    l.get().w.debug(cam_inpts)
    return count, cam_inpts


def get_camera_list_in_both(from_path, group_id, ext):
    image_names = []

    img_files = sorted(glob.glob(os.path.join(from_path, '*.' + ext)))
    result, cam_inpts = make_cam_list_in_pts(from_path, group_id)
    if result < 0:
        return result, None, None

    for img_file in img_files:
        cam_id = img_file[img_file.rfind('/')+1:-1 * len(ext) - 1]
        print(cam_id)
        if cam_id.rfind('_') == -1:
            pass
        else:
            cam_id = cam_id[:cam_id.rfind('_')]
        print('get_camera_list_in_both cam_id : ', cam_id)

        if cam_id in cam_inpts:
            image_names.append(img_file)
        else:
            target = img_file
            print('this file is not in group. remove.', target)
            os.remove(target)

    if len(image_names) == result:
        l.get().w.info("Image file = dsc_id in pts file same count")
    else:
        l.get().w.info("Image file != dsc_id in pts file cam count is different")

    return 0, image_names, cam_inpts


def get_caemra_info(from_path, cam_ids):
    filename = os.path.join(from_path, defn.pts_file_name)
    with open(filename, 'r') as json_file:
        _data = json.load(json_file)

    for cam in cam_ids:
        for i in range(len(_data["points"])):
            if cam == _data["points"][i]["dsc_id"]:
                cam_model = _data["points"][i]["ModelName"]
                lens_model = _data["points"][i]["LensName"]
                # don't use now
                focal_length = _data["points"][i]["FocalLnegth"]
                break


def get_info(from_path, group_id, ext):

    result, image_names, cam_ids = get_camera_list_in_both(
        from_path, group_id, ext)
    if result != 0:
        return result, None

    #result = get_caemra_info(cam_ids)

    return 0, image_names


def get_initpair(root_path):
    id1 = -1
    id2 = -1

    filename = os.path.join(root_path, defn.initpair_file)
    if not os.path.exists(filename):
        return -152, id1, id2

    initpair = open(filename, 'r')
    line = initpair.readlines()[0]
    ids = line.split()
    l.get().w.debug(ids)
    if len(ids) < 2:
        return -153, id1, id2

    id1 = ids[0]
    id2 = ids[1]
    return 0, id1, id2
