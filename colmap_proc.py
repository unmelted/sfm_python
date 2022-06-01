import os
import subprocess
import time

from extn_util import * 

class Colmap(object) : 
    def __init__ (self, root_path) :
        self.root_path = root_path
        self.colmap_cmd = import_colmap_cmd_json(os.path.join(os.getcwd(), 'json', 'calib_colmap.json'))

    def recon_command(self) :
            # result = subprocess.run([colmap_cmd["auto_recon_cmd"] + colmap_cmd["auto_recon_param1"] + self.root_path + colmap_cmd["auto_recon_param2"] + os.path.join(self.root_path, 'images')], capture_output=True, shell=True)
            # print(result.returncode)
            ''' automatic recon''' 
            '''
            call_colmap = subprocess.Popen([self.colmap_cmd["auto_recon_cmd"] + self.colmap_cmd["auto_recon_param1"] + self.root_path + self.colmap_cmd["auto_recon_param2"] + os.path.join(self.root_path, 'images')], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            call_colmap.wait()
            result = call_colmap.poll()
            print("Exit : ", result)
            '''
            dbpath = os.path.join(self.root_path, 'colmap.db')
            imgpath = os.path.join(self.root_path, 'images')
            outpath = os.path.join(self.root_path, 'sparse')

            call_colmap = subprocess.Popen([self.colmap_cmd["extract_cmd"] + self.colmap_cmd["extract_param1"] + dbpath + self.colmap_cmd["extract_param2"] + imgpath], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            call_colmap.wait()
            result = call_colmap.poll()

            if result != 0 :
                print("Extract Feature Error : ", result)
                return -1

            call_colmap = subprocess.Popen([self.colmap_cmd["matcher_cmd"] + self.colmap_cmd["matcher_param1"] + dbpath], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            call_colmap.wait()
            result = call_colmap.poll()

            if result != 0 :
                print("Matcher Error : ", result)
                return -2
            
            if not os.path.exists(os.path.join(self.root_path, 'sparse')):
                os.makedirs(os.path.join(self.root_path, 'sparse'))

            print(self.colmap_cmd["mapper_cmd"] + self.colmap_cmd["mapper_param1"] + dbpath + self.colmap_cmd["mapper_param2"] + imgpath + self.colmap_cmd["mapper_param3"] + outpath)
            call_colmap = subprocess.Popen([self.colmap_cmd["mapper_cmd"] + self.colmap_cmd["mapper_param1"] + dbpath + self.colmap_cmd["mapper_param2"] + imgpath + self.colmap_cmd["mapper_param3"] + outpath], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            call_colmap.wait()
            result = call_colmap.poll()

            if result != 0 :
                print("Mapper Error : ", result)
                return -3

            return result

    def cvt_colmap_model(self, dbcur):
            modelpath = os.path.join(self.root_path, 'sparse/0')
            call_colmap = subprocess.Popen([self.colmap_cmd["model_cvt_cmd"] + self.colmap_cmd["model_cvt_param1"] +  modelpath + self.colmap_cmd["model_cvt_param2"] + self.root_path + self.colmap_cmd["model_cvt_param3"] + " TXT"], stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            call_colmap.wait()
            result = call_colmap.poll()
            print("Exit : ", result)

            if result != 0 :
                print("Model Convert Error : ", result)
                return -4

            return result
