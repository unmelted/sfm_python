import os
import subprocess
import time
import sqlite3

from extn_util import * 

class Colmap(object) :

    def __init__ (self, root_path) :
        self.root_path = root_path
        self.coldb_path = os.path.join(self.root_path, 'colmap.db')
        self.colmap_cmd = import_colmap_cmd_json(os.path.join(os.getcwd(), 'json', 'calib_colmap.json'))
        self.camera_file = os.path.join(self.root_path, 'cameras.txt')
        self.image_file =  os.path.join(self.root_path, 'images.txt')

    def recon_command(self) :
        # result = subprocess.run([colmap_cmd["auto_recon_cmd"] + colmap_cmd["auto_recon_param1"] + self.root_path + colmap_cmd["auto_recon_param2"] + os.path.join(self.root_path, 'images')], capture_output=True, shell=True)
        # print(result.returncode)
        ''' automatic recon''' 
        '''
        call_colmap = subprocess.Popen([self.colmap_cmd['auto_recon_cmd'] + self.colmap_cmd['auto_recon_param1'] + self.root_path + self.colmap_cmd['auto_recon_param2'] + os.path.join(self.root_path, 'images')], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        call_colmap.wait()
        result = call_colmap.poll()
        print('Exit : ', result)
        '''
        imgpath = os.path.join(self.root_path, 'images')
        outpath = os.path.join(self.root_path, 'sparse')

        call_colmap = subprocess.Popen([self.colmap_cmd['extract_cmd'] + self.colmap_cmd['extract_param1'] + self.coldb_path + self.colmap_cmd['extract_param2'] + imgpath], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        call_colmap.wait()
        result = call_colmap.poll()

        if result != 0 :
            print('Extract Feature Error : ', result)
            return -1

        call_colmap = subprocess.Popen([self.colmap_cmd['matcher_cmd'] + self.colmap_cmd['matcher_param1'] + self.coldb_path], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        call_colmap.wait()
        result = call_colmap.poll()

        if result != 0 :
            print('Matcher Error : ', result)
            return -2
        
        if not os.path.exists(os.path.join(self.root_path, 'sparse')):
            os.makedirs(os.path.join(self.root_path, 'sparse'))

        print(self.colmap_cmd['mapper_cmd'] + self.colmap_cmd['mapper_param1'] + self.coldb_path + self.colmap_cmd['mapper_param2'] + imgpath + self.colmap_cmd['mapper_param3'] + outpath)
        call_colmap = subprocess.Popen([self.colmap_cmd['mapper_cmd'] + self.colmap_cmd['mapper_param1'] + self.coldb_path + self.colmap_cmd['mapper_param2'] + imgpath + self.colmap_cmd['mapper_param3'] + outpath], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        call_colmap.wait()
        result = call_colmap.poll()

        if result != 0 :
            print('Mapper Error : ', result)
            return -3

        return result

    def cvt_colmap_model(self, dbcur):
        modelpath = os.path.join(self.root_path, 'sparse/0')
        call_colmap = subprocess.Popen([self.colmap_cmd['model_cvt_cmd'] + self.colmap_cmd['model_cvt_param1'] +  modelpath + self.colmap_cmd['model_cvt_param2'] + self.root_path + self.colmap_cmd['model_cvt_param3'] + ' TXT'], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        call_colmap.wait()
        result = call_colmap.poll()
        print('Exit : ', result)

        if result != 0 :
            print('Model Convert Error : ', result)
            return -4

        conn = sqlite3.connect(self.coldb_path, isolation_level = None)
        cursur = conn.cursor()        
        colms = ['image TEXT', 'focal_length REAL', 'qw REAL', 'qx REAL', 'qy REAL', 'qz REAL', 'skew REAL', 'tx REAL', 'ty REAL', 'tz REAL']
        for i, col in enumerate(colms) : 
            cursur.execute('ALTER TABLE cameras ADD COLUMN ' + col)

        cam = open(self.camera_file, 'r')
        img = open(self.image_file, 'r')
        lines = cam.readlines()

        for line in lines : 
            line = line.split()
            if line[0] == '#' : 
                continue
            id = int(line[0])
            focal = float(line[4])
            skew = float(line[7])
            print(id, focal, skew)
            q = ('UPDATE cameras SET focal_length = ?, skew = ? WHERE camera_id = ?')
            cursur.execute(q, (focal, skew, id))

        lines = img.readlines()
        for line in lines:
            line = line.split()
            if line[0] == '#' : 
                continue

            if 'png' in line[-1]: 
                id = int(line[0])
                qw = float(line[1])
                qx = float(line[2])
                qy = float(line[3])
                qz = float(line[4])
                tx = float(line[5])
                ty = float(line[6])
                tz = float(line[7])
                img = str(line[9])
                print(id, qw, qx, qy, qz, tx, ty, tz, img)
                q = ('UPDATE cameras SET qw = ?, qx = ?, qy = ?, qz = ?, tx = ?, ty = ?, tz = ?, image = ?  WHERE camera_id = ?')
                cursur.execute(q, (qw, qx, qy, qz, tx, ty, tz, img, id))

        conn.close()
        return result

        def read_colmap_cameras(self) :
            pass