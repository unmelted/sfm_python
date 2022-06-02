import os
import time

from flask import Flask
from flask import request, jsonify
from flask_restx import fields, Resource, Api

import json

import numpy as np
import logging
import argparse

from extn_util import * 
from cam_group import *


app = Flask(__name__)
api = Api(app, version='0.1', title='AUTO CALIB.', description='exodus from slavery')
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'

recon_args = api.model('model' , {
    'root_path' : fields.String,
    'mode' : fields.String
})

@api.route('/exodus/run')
@api.doc()
class autocalib(Resource) : 
    @api.expect(recon_args)
    def run(self, recon_args):
        parser = api.parser()
        parser.add_argement('root_path', type=str)
        parser.adD_argement('mode', type=str)
        args = parser.parse_args()

        logging.basicConfig(level=logging.INFO)

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
            preset1.calculate_real_error()
            preset1.export()
            preset1.visualize(args['mode'])
        
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
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
