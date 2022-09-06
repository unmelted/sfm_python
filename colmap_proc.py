from socket import inet_aton
import sys
import os
import cv2
import time
import threading
import queue
import json
from datetime import datetime
import subprocess
import numpy as np
import sqlite3
from mathutil import *
from extn_util import *
from intrn_util import *
from logger import Logger as l
from definition import DEFINITION as df


IS_PYTHON3 = sys.version_info[0] >= 3
MAX_IMAGE_ID = 2**31 - 1


def _monitor_readline(process, q):
    while True:
        bail = True
        if process.poll() is None:
            bail = False
        out = ""
        if sys.version_info[0] >= 3:
            out = process.stdout.readline().decode('utf-8')
        else:
            out = process.stdout.readline()
        q.put(out)
        if q.empty() and bail:
            break


def shell_cmd(cmd):
    # Kick off the command
    process = subprocess.Popen(
        cmd, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print("------------------------------")
    print(process.pid)
    print("------------------------------")
    for line in iter(process.stdout.readline, b''):
        print(line)
    process.stdout.close()
    process.wait()

    '''
    # Create the queue instance
    q = queue.Queue()
    # Kick off the monitoring thread
    thread = threading.Thread(target=_monitor_readline, args=(process, q))
    thread.daemon = True
    thread.start()
    start = datetime.now()
    while True:
        bail = True
        if process.poll() is None:
            bail = False
            # Re-set the thread timer
            start = datetime.now()
        out = ""
        while not q.empty():
            out += q.get()
        if out:
            print(out)

        # In the case where the thread is still alive and reading, and
        # the process has exited and finished, give it up to 3 seconds
        # to finish reading
        if bail and thread.is_alive() and (datetime.now() - start).total_seconds() < 1:
            bail = False
        if bail:
            break
        '''
    return 0


class Colmap(object):

    def __init__(self, root_path):
        self.root_path = root_path
        self.coldb_path = os.path.join(self.root_path, df.colmap_db_name)
        self.job_id = get_current_job()
        self.camera_file = os.path.join(self.root_path, 'cameras.txt')
        self.image_file = os.path.join(self.root_path, 'images.txt')
        self.conn = sqlite3.connect(self.coldb_path, isolation_level=None)
        self.cursur = self.conn.cursor()
        json_file = open(os.path.join(
            os.getcwd(), 'json', 'calib_colmap.json'), 'r')
        self.colmap_cmd = json.load(json_file)

    def recon_command(self, cam_count):
        imgpath = os.path.join(self.root_path, 'images')
        outpath = os.path.join(self.root_path, 'sparse')
        cmd = self.colmap_cmd['extract_cmd'] + self.colmap_cmd['extract_param1'] + \
            self.coldb_path + self.colmap_cmd['extract_param2'] + imgpath
        # cmd = self.colmap_cmd['extract_cmd'] +  self.colmap_cmd['common_param'] + os.path.join(self.root_path, df.feature_ini)
        shell_cmd(cmd)
        l.get().w.info("Colmap : Extract Done")

        result = self.check_keypoints()
        if result < 0:
            return result

        status_update_quiet(get_current_job(), 40)
        cmd = self.colmap_cmd['matcher_cmd'] + \
            self.colmap_cmd['matcher_param1'] + self.coldb_path
        # cmd = self.colmap_cmd['matcher_cmd'] + self.colmap_cmd['common_param'] + os.path.join(self.root_path, df.matcher_ini)
        shell_cmd(cmd)
        l.get().w.info("Colmap : Matcher Done")
        status_update_quiet(get_current_job(), 60)
        if not os.path.exists(os.path.join(self.root_path, 'sparse')):
            os.makedirs(os.path.join(self.root_path, 'sparse'))

        cmd = self.colmap_cmd['mapper_cmd'] + self.colmap_cmd['mapper_param1'] + self.coldb_path + \
            self.colmap_cmd['mapper_param2'] + imgpath + \
            self.colmap_cmd['mapper_param3'] + outpath
        # cmd = self.colmap_cmd['mapper_cmd'] + self.colmap_cmd['common_param'] + os.path.join(self.root_path, df.mapper_ini)
        shell_cmd(cmd)
        result = 0
        l.get().w.info("Colmap : Mapper Done")

        status_update_quiet(get_current_job(), 80)
        result = self.check_solution(cam_count)

        return result

    def check_solution(self, cam_count, nullcheck=False):
        model = glob.glob(os.path.join(self.root_path, 'sparse'))
        if len(model) == 0:
            return -146
        elif len(model) > 1:
            return -147
        else:
            if nullcheck == False:
                q = ('SELECT camera_id FROM cameras')
            else:
                q = ('SELECT camera_id FROM cameras WHERE image IS NOT NULL')

            self.cursur.execute(q)
            rows = self.cursur.fetchall()

            if len(rows) != cam_count:
                l.get().w.error("Colmap solution cam count is not match with images")
                return -148
            else:
                return 0

    def check_keypoints(self):
        q = ('SELECT rows FROM keypoints ORDER BY rows')
        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        min = rows[0][0]
        max = rows[len(rows) - 1]
        # print("check keypoints : ", min, max)
        if min < df.feature_minimum:
            return -154

        return 0

    def cvt_colmap_model(self, ext):
        modelpath = os.path.join(self.root_path, 'sparse/0')
        call_colmap = subprocess.Popen([self.colmap_cmd['model_cvt_cmd'] + self.colmap_cmd['model_cvt_param1'] + modelpath + self.colmap_cmd['model_cvt_param2'] +
                                       self.root_path + self.colmap_cmd['model_cvt_param3'] + ' TXT'], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        call_colmap.wait()
        result = call_colmap.poll()

        if result != 0:
            l.get().w.error("Model Convert Error : {}".format(result))
            return -140

        self.cursur.execute('PRAGMA table_info(cameras)')
        rows = self.cursur.fetchall()
        need_alter = True
        for row in rows:
            if 'image' in row:
                l.get().w.warn("Already altered table!")
                need_alter = False

        if need_alter == True:
            colms = ['image TEXT', 'focal_length REAL', 'qw REAL', 'qx REAL',
                     'qy REAL', 'qz REAL', 'skew REAL', 'tx REAL', 'ty REAL', 'tz REAL']
            for i, col in enumerate(colms):
                self.cursur.execute('ALTER TABLE cameras ADD COLUMN ' + col)

        cam = open(self.camera_file, 'r')
        img = open(self.image_file, 'r')
        lines = cam.readlines()

        for line in lines:
            line = line.split()
            if line[0] == '#':
                continue
            id = int(line[0])
            focal = float(line[4])
            skew = float(line[7])
            # print(id, focal, skew)
            q = ('UPDATE cameras SET focal_length = ?, skew = ? WHERE camera_id = ?')
            self.cursur.execute(q, (focal, skew, id))
            l.get().w.debug("execute update  : {}".format(id))

        lines = img.readlines()
        for line in lines:
            line = line.split()
            if line[0] == '#':
                continue
            # print(line[9])
            if ext in line[9]:
                id = int(line[8])
                qw = float(line[1])
                qx = float(line[2])
                qy = float(line[3])
                qz = float(line[4])
                tx = float(line[5])
                ty = float(line[6])
                tz = float(line[7])
                img = str(line[9])

                q = ('UPDATE cameras SET qw = ?, qx = ?, qy = ?, qz = ?, tx = ?, ty = ?, tz = ?, image = ?  WHERE camera_id = ?')
                self.cursur.execute(q, (qw, qx, qy, qz, tx, ty, tz, img, id))
                l.get().w.debug("execute update 2 : {} {}".format(img, id))

        return result

    def read_colmap_cameras(self, cameras):

        for cam in cameras:
            q = ('SELECT qw, qx, qy, qz, tx, ty, tz FROM cameras WHERE image = \'')
            self.cursur.execute(q + str(cam.view.name) + '\'')
            row = self.cursur.fetchall()

            if row == None:
                l.get().w.error('no cameras in db')
                return -142

            if len(row) > 1:
                l.get().w.error("read colmap data is odd")
                return -141

            poseR = np.empty((0))
            poseT = np.empty((0))
            camK = np.zeros((3, 3), dtype=np.float64)

            poseR = np.append(poseR, np.array(row[0][0]).reshape((1)), axis=0)
            poseR = np.append(poseR, np.array(row[0][1]).reshape((1)), axis=0)
            poseR = np.append(poseR, np.array(row[0][2]).reshape((1)), axis=0)
            poseR = np.append(poseR, np.array(row[0][3]).reshape((1)), axis=0)
            poseT = np.append(poseT, np.array(row[0][4]).reshape((1)), axis=0)
            poseT = np.append(poseT, np.array(row[0][5]).reshape((1)), axis=0)
            poseT = np.append(poseT, np.array(row[0][6]).reshape((1)), axis=0)

            poseRT = quaternion_to_rotation(poseR)
            poseEU = quaternion_to_euler(poseR) * 180 / np.pi
            poseT = poseT.reshape((3, 1))

            q = ('SELECT focal_length, skew, width, height  FROM cameras WHERE image = \'')
            self.cursur.execute(q + str(cam.view.name) + '\'')
            row = self.cursur.fetchall()
            camK[0][0] = row[0][0]
            camK[0][1] = row[0][1]
            camK[0][2] = int(row[0][2]/2)
            camK[1][1] = row[0][0]
            camK[1][2] = int(row[0][3]/2)
            camK[2][2] = 1

            cam.R = poseRT
            cam.t = poseT
            cam.K = camK
            cam.focal = row[0][0]
            cam.calculate_p()
            # print("camera pose : ", cam.view.name)
            # print(poseEU)
            # print(cam.t)
            # print(cam.K)

        return 0

    def import_colmap_cameras(self, file_names):

        result = self.check_solution(len(file_names), True)
        if result < 0:
            return result, None
        image_names = []

        q = ('SELECT image FROM cameras')
        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        if rows == None:
            l.get().w.error('no cameras in db')
            return -142, None

        for file in file_names:
            file_name = file[file.rfind('/')+1:]
            l.get().w.debug(file_name)
            for row in rows:
                if row[0] in file_name:
                    image_names.append(file)
                    break

        return 0, image_names

    def visualize_colmap_model(self):
        l.get().w.info('visualize colmap model')
        image_path = os.path.join(self.root_path, 'images')
        subprocess.Popen([self.colmap_cmd['visualize_cmd'] + self.colmap_cmd['visualize_param1'] + self.root_path +
                         self.colmap_cmd['visualize_param2'] + self.coldb_path + self.colmap_cmd['visualize_param3'] + image_path], shell=True)

    def modify_pair_table(self):
        self.cursur.execute('PRAGMA table_info(two_view_geometries)')
        rows = self.cursur.fetchall()
        need_alter = True
        for row in rows:
            if 'image1' in row or 'image2' in row:
                l.get().w.warn("Already altered table!")
                need_alter = False

        if need_alter == True:
            colms = ['image1 TEXT', 'image2 TEXT']
            for i, col in enumerate(colms):
                self.cursur.execute(
                    'ALTER TABLE two_view_geometries ADD COLUMN ' + col)
                self.cursur.execute('ALTER TABLE matches ADD COLUMN ' + col)

        q = ('SELECT pair_id FROM two_view_geometries')
        self.cursur.execute(q)
        rows = self.cursur.fetchall()

        for row in rows:
            pair_id = int(row[0])
            img1_id, img2_id = self.pair_id_to_image_ids(pair_id)
            img1_id = (int(img1_id))
            img2_id = (int(img2_id))
            # print("image id : ", img1_id , img2_id)
            self.cursur.execute(
                'SELECT name FROM images WHERE image_id = ?', (img1_id,))
            row = self.cursur.fetchone()
            img1 = row[0]
            self.cursur.execute(
                'SELECT name FROM images WHERE image_id = ?', (img2_id,))
            row = self.cursur.fetchone()
            img2 = row[0]

            q = ('UPDATE two_view_geometries SET image1 = ?, image2 = ? WHERE pair_id = ?')
            self.cursur.execute(q, (img1, img2, pair_id))
            q = ('UPDATE matches SET image1 = ?, image2 = ? WHERE pair_id = ?')
            self.cursur.execute(q, (img1, img2, pair_id))
            l.get().w.debug(
                "pair_id {}  update 2 : {} {}".format(row[0], img1, img2))

    def make_sequential_homography(self, cameras, answer, ext):
        view_name = get_viewname(cameras[0].view.name, ext)
        cameras[0].pts = answer[view_name]

        print("make sequential homography func start. ")
        for i in range(1, len(cameras)):
            str1 = '\'' + str(cameras[i-1].view.name) + '\''
            str2 = '\'' + str(cameras[i].view.name) + '\''

            q = ('SELECT H FROM two_view_geometries WHERE image1 = ' +
                 str1 + ' and image2 = ' + str2)
            print(q)
            self.cursur.execute(q)
            row = self.cursur.fetchone()

            if row == None:
                l.get().w.error('no pair_id in db')
                return -144

            homo = self.blob_to_array(row[0], np.float64, shape=(3, 3))
            view1_name = get_viewname(cameras[i-1].view.name, ext)
            # view2_name = get_viewname(cameras[i].view.name, ext)
            # homo_answer, _ = cv2.findHomography(answer[view1_name], answer[view2_name], 1)
            print("prior pts : ", cameras[i-1].pts)
            print("prior answer ", answer[view1_name])
            print("input pts : ", np.array(cameras[i-1].pts))
            print("input answer : ", np.array(answer[view1_name]))

            new_view1 = np.array([cameras[i-1].pts])

            repro_points = cv2.perspectiveTransform(src=new_view1, m=homo)[0]
            cameras[i].pts = repro_points
            print("repro_points : ", cameras[i].pts)

        return 0

    def image_ids_to_pair_id(self, image_id1, image_id2):
        if image_id1 > image_id2:
            image_id1, image_id2 = image_id2, image_id1
        return image_id1 * MAX_IMAGE_ID + image_id2

    def pair_id_to_image_ids(self, pair_id):
        # print("received pair_id : ", pair_id)
        image_id2 = pair_id % MAX_IMAGE_ID
        image_id1 = (pair_id - image_id2) / MAX_IMAGE_ID
        return image_id1, image_id2

    def array_to_blob(self, array):
        if IS_PYTHON3:
            return array.tostring()
        else:
            return np.getbuffer(array)

    def blob_to_array(self, blob, dtype, shape=(-1,)):
        if IS_PYTHON3:
            return np.fromstring(blob, dtype=dtype).reshape(*shape)
        else:
            return np.frombuffer(blob, dtype=dtype).reshape(*shape)

    def getImagNamebyId(self, id):
        q = ('SELECT name FROM images  WHERE image_id =  ' + str(id))
        # print(q)
        self.cursur.execute(q)
        row = self.cursur.fetchone()

        if row == None:
            l.get().w.error('no image name by image id')
            return -149, None
        # print("image name {} by id {} ".format(row[0], id))

        return 0, row[0]
