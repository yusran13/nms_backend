import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, make_response
from flask_restful import Api, Resource
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from bson.json_util import dumps
from collector.device_snmp_collector import DeviceSNMPCollector
from collector.device_snmp_saved import SNMPCollector
import os
app = Flask(__name__)
api = Api(app)


config = {
    "development": "config.DevelopmentConfig",
    "production": "config.ProductionConfig",
    "jawdat_public": "config.JawdatPublic",
    "default": "config.DevelopmentConfig"
}


config_name = os.getenv('NMS_CONFIG', 'default')
app.config.from_object(config[config_name])

mongo_client = MongoClient(app.config['DB_SERVER'], app.config['DB_PORT'], connect=False)
mongo_db = getattr(mongo_client, app.config['DB_COLLECTION'])
mongo_db.authenticate(app.config['DB_USERNAME'], app.config['DB_PASSWORD'])

#Logger config
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s - {%(pathname)s:%(lineno)d}', datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
dir_path = os.path.dirname(os.path.realpath(__file__))
handler = RotatingFileHandler(dir_path+'/log/background.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)
log.addHandler(handler)

scheduler = BackgroundScheduler()
scheduler.start()

saver = SNMPCollector(mongo_db, app.logger)
# TODO: Background job use fix IP MGMT as parameter, device_id only for identifier in DB
def snmp_collector(device, device_id, data_type, int_name=None):
    host = DeviceSNMPCollector(device, app.logger)
    if data_type == "cpu":
        cpu = host.get_cpu_snmp()
        data = {
            "cpu": cpu,
            "device_id": device_id
        }
        # Only save data if not none
        if cpu != None:
            saver.cron_cpu(data)

    elif data_type == "memory":
        memory_used, memory_free = host.get_memory_snmp()
        data = {
            "memory_used": memory_used,
            "memory_free": memory_free,
            "device_id": device_id
        }
        # Only save data if not none
        if memory_used != None:
            saver.cron_memory(data)

    elif data_type == "interface_util":
        interface_util = host.get_spesific_interface(int_name)
        # Only save data if not none
        if interface_util:
            app.logger.info("Data Interface not none")
            data = {
                "interface_util": interface_util,
                "device_id": device_id,
                "interface_name": int_name
            }
            saver.cron_int_util(data)


    elif data_type == "interface_pl":
        packet_loss = host.get_interface_packetloss(int_name)

        # TODO: tobe delete, only for demo
        import random
        packet_loss = dict()
        packet_loss["packet_loss_in"] = random.randint(10, 40)
        packet_loss["packet_loss_out"] = random.randint(10, 40)

        # Only save data if not none
        if packet_loss:
            app.logger.info("Data Interface not none")
            data = {
                "device_id": device_id,
                "interface_name": int_name,
                "packet_loss_in": packet_loss["packet_loss_in"],
                "packet_loss_out": packet_loss["packet_loss_out"]
            }
            saver.cron_int_pl(data)

class AddNewJob(Resource):
    def post(self):
        parms = request.json
        app.logger.info(parms)
        # snmp_collector(parms["device"], parms["device_id"], parms["data_type"], int_name= parms["int_name"] if "int_name" in parms.keys() else None)
        scheduler.add_job(func=snmp_collector, id=parms["job_id"], name=parms["widget_name"], trigger="interval", seconds=10, args=[parms["device"], parms["device_id"], parms["data_type"], parms["int_name"]])
        return make_response(dumps(True))
api.add_resource(AddNewJob, '/api/job/new')

class RemoveJob(Resource):
    def post(self):
        parms = request.json
        print parms
        scheduler.add_job(func=snmp_collector, name=parms["name"], trigger="interval", seconds=parms["interval"],
                          args=[parms["data"]])
        return make_response(dumps(True))
api.add_resource(RemoveJob, '/api/job/remove')

class BackgroundJobList(Resource):
    def get(self):
        app.logger.info(scheduler.get_jobs())
        return make_response(dumps(True))
api.add_resource(BackgroundJobList, '/api/job/list')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4243))
    app.logger.info("Running background service with {:s} environment".format(config_name))
    #LOAD JOB SAVED FROM DB
    jobs = list(mongo_db.jobs.find())
    for job in jobs:
        #start scheduled based on db
        if "int_name" in job.keys():
            function_parms = [job["device"], job["device_id"], job["data_type"], job["int_name"]]
        else:
            function_parms = [job["device"], job["device_id"], job["data_type"]]

        scheduler.add_job(func=snmp_collector, id=str(job["_id"]), name=job["widget_name"], trigger="interval", seconds=10, args=function_parms)
    app.run(host="0.0.0.0", debug=False, port=port, threaded=True)
