
import json
import cv2
import glob
import sys
import os
import math
from camera_sim import *
from group_adjust import GroupAdjust 
from group_adjust_ex import GroupAdjustEx
from logger import Logger as l
from world import *

def prepare_video_job(from_path, to_path):

    if not os.path.exists(to_path):
        os.makedirs(to_path)

    video_files = sorted(glob.glob(os.path.join(from_path, '*.mp4')))

    pick_frame = 1
    if len(video_files) < 5:
        return -102

    for video in video_files:
        filename = video[video.rfind('/') + 1:]
        print(filename)
        filename = filename[0:filename.rfind('_')] + '.jpg'

        cam = cv2.VideoCapture(video)
        cam.set(cv2.CAP_PROP_POS_FRAMES, pick_frame)
        ret, frame = cam.read()
        if not ret:
            return -103

        target = os.path.join(to_path, filename)
        print("create : ", target)
        cv2.imwrite(target, frame)
        cam.release()

    return 0


def get_camera_list(from_path):
    filename = os.path.join(from_path, "file_list.txt")
    file = open(filename, 'r')
    lines = file.readlines()
    lists = []
    for line in lines:
        lists.append(line.split('_')[0])

    print(lists)
    return lists


def get_adjust_info(from_path, camera, resize=1):
    result = False
    filename = os.path.join(from_path, "UserPointData.adj")

    with open(filename, "r") as json_file:
        from_data = json.load(json_file)

    for j in range(len(from_data["adjust_list"])):
        if from_data["adjust_list"][j]["dsc_id"] == camera.name:
            camera.adjust_file = from_data["adjust_list"][j]["adjust"]
            result = True

    return result


def get_pts_info(from_path, camera, group_limit):
    result = False
    filename = os.path.join(from_path, "UserPointData.pts")
    with open(filename, "r") as json_file:
        from_data = json.load(json_file)

    for j in range(len(from_data["points"])):
        # print("check ..", from_data["points"][j]["dsc_id"], camera.name)
        if from_data["points"][j]["dsc_id"] == camera.name:
            if from_data["points"][j]["Group"] != group_limit:
               return False
            print("camera : ", camera.name)
            camera.pts_3d[0][0] = from_data['points'][j]['pts_3d']['X1']
            camera.pts_3d[0][1] = from_data['points'][j]['pts_3d']['Y1']
            camera.pts_3d[1][0] = from_data['points'][j]['pts_3d']['X2']
            camera.pts_3d[1][1] = from_data['points'][j]['pts_3d']['Y2']
            camera.pts_3d[2][0] = from_data['points'][j]['pts_3d']['X3']
            camera.pts_3d[2][1] = from_data['points'][j]['pts_3d']['Y3']
            camera.pts_3d[3][0] = from_data['points'][j]['pts_3d']['X4']
            camera.pts_3d[3][1] = from_data['points'][j]['pts_3d']['Y4']
            camera.rotate_x = from_data['points'][j]['pts_3d']['CenterX']
            camera.rotate_y = from_data['points'][j]['pts_3d']['CenterY']       
            camera.focal = from_data['points'][j]['FocalLength']

            camera.pts_2d[0][0] = from_data['points'][j]['pts_2d']['UpperPosX']
            camera.pts_2d[0][1] = from_data['points'][j]['pts_2d']['UpperPosY']
            # camera.pts_2d[1][0] = from_data['points'][j]['pts_2d']['MiddlePosX']
            # camera.pts_2d[1][1] = from_data['points'][j]['pts_2d']['MiddlePosY']
            camera.pts_2d[1][0] = from_data['points'][j]['pts_2d']['LowerPosX']
            camera.pts_2d[1][1] = from_data['points'][j]['pts_2d']['LowerPosY']

            print("3d : ", camera.pts_3d, camera.rotate_x, camera.rotate_y)
            print("2d : ", camera.pts_2d)
            result = True
            break

    return result


def get_rotate_point(center_x, center_y, point_x, point_y, radian):
    # print("rotate point input .. ", center_x, center_y, point_x, point_y, radian)
    delx = point_x - center_x
    dely = point_y - center_y

    cos_ = math.cos(radian)
    sin_ = math.sin(radian)

    ret_x = delx * cos_ - dely * sin_
    ret_y = delx * sin_ + dely * cos_

    ret_x = ret_x + center_x
    ret_y = ret_y + center_y

    print(ret_x, ret_y)
    return ret_x, ret_y


def get_scale_point(center_x, center_y, point_x, point_y, scale):
    # print("scale point input .. ", center_x, center_y, point_x, point_y, scale)
    delx = point_x - center_x
    dely = point_y - center_y

    ret_x = delx * (1 / scale)
    ret_y = dely * (1 / scale)

    ret_x = ret_x + center_x
    ret_y = ret_y + center_y

    return ret_x, ret_y


def cal_inv_calib(info):
    crns = list(range(8))

    crns[0] = (info["RectMargin"]["Left"])
    crns[1] = (info["RectMargin"]["Top"])
    crns[2] = (info["RectMargin"]["Left"]) + (info["RectMargin"]["Width"])
    crns[3] = (info["RectMargin"]["Top"])
    crns[4] = (info["RectMargin"]["Left"]) + (info["RectMargin"]["Width"])
    crns[5] = (info["RectMargin"]["Top"]) + (info["RectMargin"]["Height"])
    crns[6] = (info["RectMargin"]["Left"])
    crns[7] = (info["RectMargin"]["Top"]) + (info["RectMargin"]["Height"])

    # print(crns)

    for i in range(len(crns)):
        if i % 2 == 0:
            crns[i] = crns[i] - (info["AdjustX"])
        else:
            crns[i] = crns[i] - (info["AdjustY"])

        if i % 2 == 1:
            s_x, s_y = get_scale_point(info["RotateX"], info["RotateY"], crns[i - 1], crns[i], info["Scale"])
            t_x, t_y = get_rotate_point(info["RotateX"], info["RotateY"], s_x, s_y, -info["Angle"])

            crns[i - 1] = (t_x)
            crns[i] = (t_y)

            # if isflip == True:
            #     crns[i-1] = 3840 - int(t_x)
            #     crns[i] = 1920 - int(t_y)
            print("ceil apply : ", math.ceil(crns[i - 1]), math.ceil(crns[i]))
            if math.ceil(crns[i - 1]) < 0 or math.ceil(crns[i - 1]) >= 3840:
                print("WARN X------------------------ ", math.ceil(crns[i - 1]))
            elif math.ceil(crns[i]) < 0 or math.ceil(crns[i]) >= 2160:
                print("WARN y------------------------ ", math.ceil(crns[i]))

    print("--- inver calib calculation")
    print(crns)

    return crns


def scale_image(camera, sacle = 1.0):

    camera.image_width = int(camera.image_width / scale)
    camera.image_height = int(camera.image_height / scale)
    camera.view.image_width = camera.image_width
    camera.view.image_height = camera.image_height
    camera.image = cv2.resize(camera.image, (int(camera.image_width), int(camera.image_height)))

def calibration(cameras, world, flip) :
    adjust = GroupAdjust(cameras, world.get_world() , None, flip, None)
    if cal_type == '3D':
        adjust.calculate_extra_point_3d()
    else :
        adjust.calculate_rotatecenter('2D')

    adjust.calculate_radian()
    adjust.calculate_scaleshift(calibtype='ave', standard_index=standard_index)  # for type4
    left, right, top, bottom, width, height = adjust.calculate_margin()

    for camera in cameras:
        # print("-----------------")
        # print("      ", camera.name)
        # print("-----------------")
        # l.get().w.debug("camera {} scale {} adjustx {} ajdusty {} radin {} angle {}  ".format(
        #     camera.name, camera.scale, camera.adjust_x, camera.adjust_y, camera.radian, camera.radian * math.pi / 180))
        # print("---------------- From file ")
        # l.get().w.debug("camera {} scale {} adjustx {} ajdusty {} radin {} angle {}  ".format(
        #     camera.name, camera.adjust_file["Scale"], camera.adjust_file["AdjustX"], camera.adjust_file["AdjustY"], camera.adjust_file["Angle"], camera.adjust_file["Angle"] * math.pi / 180))

        if scale != 1.0 :
            scale_image(camera, scale) 

        camera.adj_image = adjust.adjust_image(out_path, camera, scale)
        # cv2.imshow("CAL", camera.adj_image)
        # cv2.imshow("INV", camera.image)
        # cv2.waitKey()
    
    adjust.adjust_pts(out_path, cameras, scale)

    return adjust


''' Main Process Start '''
# 'calibration', 'common_area', 'position_swipe', 'inverse_calib', 'livepd_crop'
#simulation_mode = ['calibration', 'position_swipe']
simulation_mode = ['calibration', 'common_area', 'livepd_crop']


from_path = '../simulation/Cal3D_085658'
to_path = '../simulation/Cal3D_085658'
out_path = '../simulation/Cal3D_085658/output/'
#prepare_video_job(from_path, to_path)

if not os.path.exists(out_path):
    os.makedirs(out_path)

lists = get_camera_list(from_path)
files = sorted(glob.glob(os.path.join(to_path, '*.jpg')))
isflip = True
group_limit = "Group1"
cal_type = '3D'
world_pts = [714.0, 383.0, 714.0, 781.0, 91.0, 781.0, 91.0, 383.0] #SBA basket ball Cal3D_085658
# world_pts = [771, 461, 659, 448, 659, 349, 771, 337] #Cal3D_131840

print(world_pts)

# standard = ['001024']  # 2D
#standard = ['021119']
standard = []
world = World()
world.set_world(world_pts)
cameras = []
standard_index = []

scale = 2.0
index = 0

for item in lists:
    print("start : ", item)
    # target = file.split('/')[-1][:-4]

    ncam = Camera(item)
    bpts = get_pts_info(to_path, ncam, group_limit)

    if bpts == False:
        continue

    if cal_type == '2D' :
        ncam.pts_extra = ncam.pts_2d

    if 'inverse_calib' in simulation_mode:
        binfo = get_adjust_info(to_path, ncam, 2)
        if binfo == False:
            print("target is skipped. No data..")
            continue

    file = os.path.join(to_path, item + '.jpg')
    img = cv2.imread(file)

    ncam.set_extra_info(img.shape[1], img.shape[0], cal_type)
    ncam.image = img

    if ncam.name in standard:
        standard_index.append(index)

    cameras.append(ncam)
    index += 1

margin = []
adjustEx = None

if 'calibration' in simulation_mode :
    adjustBase = calibration(cameras, world, isflip)
    margin = [adjustBase.left, adjustBase.top, adjustBase.width, adjustBase.height]


if 'common_area' in simulation_mode : 
    adjustEx = GroupAdjustEx()
    adjustEx.set_world(world_pts, isflip, scale)
    poly = adjustEx.calculate_projection(out_path, cameras)
    adjustEx.calculate_back_projection(out_path, cameras, poly)
    adjustEx.calculate_polygon_to_raw(out_path, cameras, margin)


if 'position_swipe_inf' in simulation_mode :
    if adjustEx == None : 
        adjustEx = GroupAdjustEx()
        adjustEx.set_world(world_pts, isflip, scale)    

    while(True) :
        insert = input(" input point, zoom ")
        print(insert)

        if insert == 'q' :
            break
        else :
            in_list = insert.split(',')
            x = in_list[0]
            y = in_list[1]
            zoom = in_list[2]
            print("input point, zoom " , x, y, zoom )
            first = True
            base =cameras[0].adj_pts3d
            print("first channel base : ", base )
            y = int(y) + 59
            for camera in cameras :
                print(camera.name)
                if first == True :                    
                    first = False

                print(y)
                mobile_show = adjustEx.calculate_swipe_position(base, camera, x, y, zoom, first)
                cv2.imshow("Mobile", mobile_show)
                cv2.waitKey()                


if 'livepd_crop' in simulation_mode :
    point_cnt = 2
    points = []
    insert_pt = 0
    first = cameras[0].image.copy()

    if isflip == True :
        first = cv2.flip(first, -1)

    prev = None
    for i, pt in enumerate(cameras[0].adj_polygon_toraw) :
        print(pt)
        cv2.circle(first, (int(pt[0][0]), int(pt[0][1])), 7, (255, 0, 255), -1)
        if i > 0 :
            cv2.line(first, (int(pt[0][0]), int(pt[0][1])), (int(prev[0][0]), int(prev[0][1])), (255, 255, 0), 5)
        prev = pt

    cv2.line(first, (int(cameras[0].adj_polygon_toraw[0][0][0]), int(cameras[0].adj_polygon_toraw[0][0][1])), (int(prev[0][0]), int(prev[0][1])), (0, 255, 255), 5)

    running = True

    def onMouse(event, x, y, flags, param) :
        if event == cv2.EVENT_LBUTTONDOWN:
            if (len(points)) > 3 :
                points.clear()

            points.append(x)
            points.append(y)
            cv2.circle(first, (x, y), 5, (255, 0, 255), -1)                
            if (len(points)) > 3 :
                cv2.rectangle(first, (points[0], points[1]), (points[2], points[3]), (255, 0, 0), 3)

    cv2.namedWindow("LIVEPD")            
    cv2.setMouseCallback("LIVEPD", onMouse)

    while(running) :
        cv2.imshow("LIVEPD", first)
        key = cv2.waitKey()     

        if key == ord('q'):
            running = False


    print('insert fhinish ', points)
    center = []
    center.append((points[0] + points[2] ) / 2)
    center.append((points[1] + points[3] ) / 2)

    width = max(points[0], points[2]) - min(points[0], points[2])
    height = max(points[1], points[3]) - min(points[1], points[3])
    print('insert width / height ', width, height)

    if adjustEx == None : 
        adjustEx = GroupAdjustEx()
        adjustEx.set_world(world_pts, isflip, scale)    

    base = cameras[0].adj_pts3d
    bfirst = True

    for camera in cameras :
        print(camera.name)
        mobile_show = adjustEx.calculate_livepd_crop(base, camera, points, center, width, height, bfirst)
        cv2.imshow("Mobile", mobile_show)
        cv2.waitKey()                
        if bfirst == True :                    
            bfirst = False

