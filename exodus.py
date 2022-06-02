import os
import time

from flask import Flask
from flask import request, jsonify
from flask_restx import fields, Resource, Api, reqparse

import json

import numpy as np
import logging
import argparse

from extn_util import * 
from cam_group import *


app = Flask(__name__)
api = Api(app, version='0.1', title='AUTO CALIB.', description='exodus from slavery')
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'

recon_args = api.model('recon_args' , {
    'root_dir' : fields.String,
    'mode' : fields.String
})

@api.route('/exodus/autocalib')
@api.doc()
class autocalib(Resource) : 
    @api.expect(recon_args)
    def post(self, model=recon_args):
        time_s = time.time()        
        parser = reqparse.RequestParser()
        parser.add_argument('root_dir', type=str)
        parser.add_argument('mode', type=str)
        args = parser.parse_args()

        logging.basicConfig(level=logging.INFO)

        print(args['root_dir'])
        print(args['mode'])        
        preset1 = Group()

        if args['mode'] == 'colmap' :
            ret = preset1.create_group_colmap(args['root_dir']) 
        else:
            ret = preset1.create_group(args['root_dir'])

        if( ret < 0 ):
            logging.error("terminated. ")
            return 0

        if args['mode'] == 'sfm' : 
            preset1.run_sfm()
            preset1.generate_points(args['mode'])    
            preset1.calculate_real_error()
            preset1.export()
            preset1.visualize()

        elif args['mode'] == 'vis' :
            preset1.read_cameras(args['mode'])
            # import_camera_pose(preset1)        
            preset1.visualize(args['mode'])

        elif args['mode'] == 'eval':
            preset1.read_cameras(args['mode'])
            # import_camera_pose(preset1)
            preset1.generate_points(args['mode'])            
            preset1.calculate_real_error()
            preset1.export()
            preset1.visualize(args['mode'])

        elif args['mode'] == 'test' :
            preset1.calculate_real_error()

        elif args['mode'] == 'colmap' :
            preset1.read_cameras(args['mode'])        
            preset1.generate_points(args['mode'])    
            # preset1.calculate_real_error()
            preset1.export()
#            preset1.visualize(args['mode'])
        
        time_e = time.time() - time_s
        print("Spending time total (sec) :", time_e)
        
        return 0

    # def set_args(parser):

    #     parser.add_argument('--root_dir', action='store', type=str, dest='root_dir',
    #                         help='root directory containing the images/ folder')
    #     parser.add_argument('--mode', action='store', type=str, dest='mode', default='sfm',
    #                     help='select mode sfm , visualize')

''' file mode main '''
# if __name__ == '__main__':

#     parser = argparse.ArgumentParser()
#     set_args(parser)
#     args = parser.parse_args()
#     run(args)


if __name__ == '__main__':
    
    app.run(host="0.0.0.0", port=9000)

