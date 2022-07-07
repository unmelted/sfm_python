import os
from multiprocessing.dummy import Process
from flask import Flask
from flask import request, jsonify
from flask_restx import fields, Resource, Api, reqparse, marshal
import json
import definition as df
from exodus import *

app = Flask(__name__)
api = Api(app, version='0.1', title='AUTO CALIB.', description='exodus from slavery')
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'

recon_args = api.model('recon_args' , {
    'input_dir' : fields.String
})

@api.route('/exodus/autocalib')
@api.doc()
class calib_run(Resource) : 
    @api.expect(recon_args)
    def post(self, model=recon_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor " , ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('input_dir', type=str)
        args = parser.parse_args()
        
        print(args['input_dir'])
        job_id = Commander.getInstance().add_task(df.TaskCategory.AUTOCALIB, (args['input_dir'], ip_addr))

        result = {
            'status': 0,
            'job_id': job_id,
            'message': 'SUCCESS',
        }

        return result


gen_args = api.model('gen_args' , {
    "job_id" : fields.Integer,
    "type" : fields.String,    
    "pts" : fields.List(fields.Float)
})

@api.route('/exodus/generate')
@api.doc()
class generate_points(Resource) :
    @api.expect(gen_args)
    # @api.marshal_with(gen_args)
    def post(self, model=gen_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor " , ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        parser.add_argument('type', type=str)        
        parser.add_argument('pts', default=list, action='append')
        args = parser.parse_args()
        job_id = args['job_id']
        print(args['type'])
        print(args['pts'])

        status, result = Commander.getInstance().send_query(df.TaskCategory.GENERATE_PTS, (args['job_id'], ip_addr, args))

        result = {
            'job_id': job_id,
            'status' : status,
            'result' : result
        }

        return result


jobid = api.model('jobid' , {
    'job_id' : fields.Integer,
})

@api.route('/exodus/autocalib/status/<int:jobid>')
@api.doc()
class calib_status(Resource) : 
    @api.expect()
    def get(self, jobid=jobid):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor " , ip_addr)

        # parser = reqparse.RequestParser()
        # parser.add_argument('job_id', type=int)
        # args = parser.parse_args()
        
        print(jobid)
        # print("calib status  .. : " ,Commander.getInstance())        
        status, result = Commander.getInstance().send_query(df.TaskCategory.AUTOCALIB_STATUS, (jobid, ip_addr))
        msg = df.get_err_msg(result)

        result = {
            'job_id': jobid,
            'status' : status,
            'result' : result,
            'message': msg,
        }

        return result


analysis = api.model('analysis' , {
    'job_id' : fields.Integer,
    'mode' : fields.String,
})

@api.route('/exodus/autocalib/analysis')
@api.doc()
class calib_analysis(Resource) : 
    @api.expect(analysis)
    def post(self, an=analysis):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor " , ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        parser.add_argument('mode', type=str)        
        args = parser.parse_args()
        
        print(args['job_id'])
        print(args['mode'])
        result = Commander.getInstance().send_query(df.TaskCategory.ANALYSIS , (args['job_id'], ip_addr))

        msg = df.get_err_msg(result)
        result = {
            'job_id': args['job_id'],
            'progress' : result,
            'message': msg,
        }

        return result


file_args = api.model('file_args' , {
    'config_file' : fields.String
})

@api.route('/exodus/autocalib/read_config')
@api.doc()
class read_config(Resource) : 
    @api.expect(file_args)
    def post(self, an=file_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor " , ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('config_file', type=str)        
        args = parser.parse_args()
        
        print(args['config_file'])
        result = Commander.getInstance().send_query(args['config_file'], ip_addr)

        result = {
            'result' : result,
        }

        return result    

if __name__ == '__main__':    
    pr = Process(target=Commander.getInstance().Receiver, args=(Commander.getInstance().index,))
    pr.start()
    app.run(debug=False, host='0.0.0.0', port=9000)

