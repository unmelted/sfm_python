import os
from multiprocessing.dummy import Process
from flask import Flask
from flask import request, jsonify
from flask_restx import fields, Resource, Api, reqparse
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

        parser = reqparse.RequestParser()
        parser.add_argument('input_dir', type=str)
        args = parser.parse_args()
        
        print(args['input_dir'])
        job_id = Commander.getInstance().add_task(df.TaskCategory.AUTOCALIB, (args['input_dir']))

        result = {
            'status': 0,
            'job_id': job_id,
            'message': 'SUCCESS',
        }

        return result

jobid = api.model('jobid' , {
    'job_id' : fields.Integer,
})

@api.route('/exodus/autocalib/status')
@api.doc()
class calib_status(Resource) : 
    @api.expect(jobid)
    def post(self, jid=jobid):

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        args = parser.parse_args()
        
        print(args['job_id'])
        print("calib status  .. : " ,Commander.getInstance())        
        status, result = Commander.getInstance().send_query(df.TaskCategory.AUTOCALIB_STATUS, (args['job_id']))
        msg = df.get_err_msg(result)

        result = {
            'job_id': args['job_id'],
            'status' : status,
            'result' : result,
            'message': msg,
        }

        return result


analysis = api.model('jobid' , {
    'job_id' : fields.Integer,
    'mode' : fields.String,
})

@api.route('/exodus/autocalib/analysis')
@api.doc()
class calib_analysis(Resource) : 
    @api.expect(analysis)
    def post(self, an=analysis):

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        args = parser.parse_args()
        
        print(args['job_id'])
        print(args['mode'])
        result = 0 
        if args['job_id'] == df.TaskCategory.VISUALIZE.name :
            result = Commander.getInstance().send_query(df.TaskCategory.VISUALIZE, (args['job_id']))

        elif args['job_id'] == df.TaskCategory.ANALYSIS.name :
            result = Commander.getInstance().send_query(df.TaskCategory.ANALYSIS, (args['job_id']))
            
        msg = df.get_err_msg(result)
        result = {
            'job_id': args['job_id'],
            'progress' : result,
            'message': msg,
        }

        return result
if __name__ == '__main__':    
    pr = Process(target=Commander.getInstance().Receiver, args=(Commander.getInstance().index,))
    pr.start()
    app.run(debug=False, host='0.0.0.0', port=9000)

