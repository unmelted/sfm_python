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
    'root_dir' : fields.String,
    'mode' : fields.String,
})

@api.route('/exodus/autocalib')
@api.doc()
class calib_run(Resource) : 
    @api.expect(recon_args)
    def post(self, model=recon_args):

        parser = reqparse.RequestParser()
        parser.add_argument('root_dir', type=str)
        parser.add_argument('mode', type=str)
        args = parser.parse_args()
        
        print(args['root_dir'])
        print(args['mode'])        
        print("calib run .. : " ,Commander.getInstance())
        Commander.getInstance().add_task(df.TaskCategory.AUTOCALIB, (args['root_dir'], args['mode']))

        result = {
            'status': 0,
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
        result = Commander.getInstance().send_query(df.TaskCategory.AUTOCALIB_STATUS, (args['job_id']))
        if result > 0 : 
            msg = df.get_progress_msg(result)            
        else :
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
    print("main.. start : " ,Commander.getInstance())
    app.run(debug=False, host='0.0.0.0', port=9000)

