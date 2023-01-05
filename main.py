import os
from multiprocessing import Process, Queue
from flask import Flask
from flask import request, jsonify
from flask_restx import fields, Resource, Api, reqparse, marshal
import definition as df
from exodus import *
from db_layer import NewPool, DBLayer

app = Flask(__name__)
api = Api(app, version='0.1', title='AUTO CALIB.',
          description='exodus from slavery')
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'
# cmd_que = Queue()

recon_args = api.model('recon_args', {
    'input_dir': fields.String,  # directory in storage
    'group': fields.String,  # 캘리브레이션 진행할 그룹
    'config': fields.Raw({"type": "String"}, io="rw")
})


@api.route('/exodus/autocalib')
@api.doc()
class calib_run(Resource):
    @api.expect(recon_args)
    def post(self, model=recon_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('input_dir', type=str)
        parser.add_argument('group', type=str)
        parser.add_argument('config', type=str)
        args = parser.parse_args()

        print(args['config'])
        # cmd_que.put((df.TaskCategory.AUTOCALIB,
        #             (args['input_dir'], args['group'], ip_addr)))

        job_id = Commander.add_task(df.TaskCategory.AUTOCALIB,
                                    (args, ip_addr))

        result = {
            'status': 0,
            'job_id': job_id,
            'message': '',
        }

        if job_id < 0:
            message = df.get_err_msg(job_id)
            result = {
                'status': -1,
                'job_id': job_id,
                'message': message,
            }
        else:
            result = {
                'status': 0,
                'job_id': job_id,
                'message': 'SUCCESS',
            }

        return result


gen_args = api.model('gen_args', {
    "job_id": fields.Integer,
    "pts_2d": fields.List(fields.Float),
    "pts_3d": fields.List(fields.Float),
    "world": fields.List(fields.Float),
    "image1": fields.String,
    "image2": fields.String,
    'config': fields.Raw({"type": "String"}, io="r")
})


@api.route('/exodus/generate')
@api.doc()
class generate_points(Resource):
    @api.expect(gen_args)
    # @api.marshal_with(gen_args)
    def post(self, model=gen_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        parser.add_argument('pts_2d', default=list, action='append')
        parser.add_argument('pts_3d', default=list, action='append')
        parser.add_argument('world', default=list, action='append')
        parser.add_argument('image1', type=str)
        parser.add_argument('image2', type=str)
        parser.add_argument('config', type=str)
        args = parser.parse_args()
        job_id = args['job_id']
        print(args['pts_2d'])
        print(args['pts_3d'])
        print(args['world'])
        print(args['image1'])
        print(args['image2'])
        print(args['config'])
        job_id = Commander.add_task(
            df.TaskCategory.GENERATE_PTS, (args, ip_addr))

        result = {
            'status': 0,
            'job_id': job_id,
            'message': 'SUCCESS',
        }

        return result


pt_args = api.model('pt_args', {
    "job_id": fields.Integer,
    "image": fields.String,
    "track_x1": fields.Float,
    "track_y1": fields.Float,
    "track_x2": fields.Float,
    "track_y2": fields.Float,
    'config': fields.Raw({"type": "String"}, io="r")
})


@api.route('/exodus/position_tracking')
@api.doc()
class position_tracking(Resource):
    @api.expect(pt_args)
    def post(self, model=pt_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('job_id', type=int)
        parser.add_argument('image', type=str)
        parser.add_argument('track_x1', type=int)
        parser.add_argument('track_y1', type=int)
        parser.add_argument('track_x2', type=int)
        parser.add_argument('track_y2', type=int)
        parser.add_argument('config', type=str)
        args = parser.parse_args()
        print(args['job_id'])
        print(args['image'])
        print(args['track_x1'])
        print(args['track_y1'])
        print(args['track_x2'])
        print(args['track_y2'])
        print(args['config'])
        job_id = args['job_id']
        image = args['image']
        tcx1 = args['track_x1']
        tcy1 = args['track_y1']
        tcx2 = args['track_x2']
        tcy2 = args['track_y2']
        tcfg = args['config']

        job_id = Commander.add_task(
            df.TaskCategory.POSITION_TRACKING, (args, ip_addr))

        result = {
            'status': 0,
            'job_id': job_id,
            'message': 'SUCCESS',
        }

        return result


jobid = api.model('jobid', {
    'job_id': fields.Integer,
})


@ api.route('/exodus/autocalib/status/<int:jobid>')
@ api.doc()
class calib_status(Resource):
    @ api.expect()
    def get(self, jobid=jobid):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        print(jobid)
        status, result, _ = Commander.send_query(
            df.TaskCategory.AUTOCALIB_STATUS, [jobid, ip_addr])
        msg = df.get_err_msg(result)

        result = {
            'job_id': jobid,
            'status': status,
            'result': result,
            'message': msg,
        }

        return result


@api.route('/exodus/autocalib/cancel/<int:jobid>')
@api.doc()
class cancel_job(Resource):
    @api.expect()
    def delete(self, jobid=jobid):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        print(jobid)
        _, result, _ = Commander.send_query(
            df.TaskCategory.AUTOCALIB_CANCEL, [jobid, ip_addr])
        msg = df.get_err_msg(result)

        result = {
            'job_id': jobid,
            'result': result,
            'message': msg,
        }

        return result


@api.route('/exodus/autocalib/getpair/<job_id>/<pair>')
@api.doc()
class get_pair(Resource):
   # @api.expect()
    def get(self, job_id, pair):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)
        print(job_id)
        print(pair)

        pair1 = None
        pair2 = None

        status, result, contents = Commander.send_query(
            df.TaskCategory.GET_PAIR, [job_id, pair, ip_addr])
        msg = df.get_err_msg(result)
        if result == 0:
            pair1 = contents[0]
            pair2 = contents[1]
            print("returned pair image : ", pair1, pair2)

        result = {
            'job_id': job_id,
            'result': result,
            'message': msg,
            'first_image': pair1,
            'second_image': pair2,
        }

        return result


@api.route('/exodus/autocalib/getresult/<int:jobid>')
@api.doc()
class get_result(Resource):
    @api.expect()
    def get(self, jobid=jobid):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)
        print(jobid)

        status, result, contents = Commander.send_query(
            df.TaskCategory.GET_RESULT, [jobid, ip_addr])
        msg = df.get_err_msg(result)

        result = {
            'job_id': jobid,
            'result': result,
            'message': msg,
            'contents': contents,
        }

        return result


@api.route('/exodus/autocalib/getgeninfo/<int:jobid>')
@api.doc()
class get_geninfo(Resource):
    @api.expect()
    def get(self, jobid=jobid):
        ip_addr = request.environ['REMOTE_ADDR']
        print("get gen info ip of requestor ", ip_addr)

        print(jobid)
        status, result, contents = Commander.send_query(
            df.TaskCategory.GET_GENINFO, [jobid, ip_addr])
        msg = df.get_err_msg(result)

        result = {
            'result': result,
            'message': msg,
            'image': contents[0],
            'use_width': contents[1],
            'use_height': contents[2],
        }

        return result


@api.route('/exodus/autocalib/getversion')
@api.doc()
class get_result(Resource):
    @api.expect()
    def get(self):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        ver = df.DEFINITION().get_version()
        print('getversion return :', ver)
        result = {
            'version': ver,
        }
        return result


file_args = api.model('file_args', {
    'config_file': fields.String
})


@api.route('/exodus/autocalib/read_config')
@api.doc()
class read_config(Resource):
    @api.expect(file_args)
    def post(self, an=file_args):
        ip_addr = request.environ['REMOTE_ADDR']
        print("ip of requestor ", ip_addr)

        parser = reqparse.RequestParser()
        parser.add_argument('config_file', type=str)
        args = parser.parse_args()

        print(args['config_file'])
        status, result, _ = Commander.send_query(
            args['config_file'], ip_addr)

        result = {
            'result': result,
        }

        return result


if __name__ == '__main__':
    np = NewPool()
    DBLayer.initialize(np.getConn())

    que = Commander.getque()
    pr = Process(target=Commander.receiver, args=(que, ))
    jr = Process(target=JobManager.Watcher)

    pr.start()
    jr.start()
    app.run(debug=False, host='0.0.0.0', port=9000)
