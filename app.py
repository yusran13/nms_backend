import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta
from bson import ObjectId
from flask import Flask, jsonify, make_response, request, current_app
from functools import update_wrapper
from flask_restful import Api
from flask_restful import Resource
from pymongo import errors
from bson.json_util import dumps
import random
from collector.discover_device import ExportingThread
from pymongo import MongoClient
from api_controller.topology_generator_api import TopologyGeneratorAPI
from api_controller.device_controller import DeviceController
from multiprocessing import Pool
from api_controller.link_controller import LinkController
from api_controller.dashboard_controller import DashboardController
from api_controller.intellegent_log import IntellegentLog
from api_controller.netflow_controller import Netflow
from api_controller.backup_restore import backup_process, restore_process
from flask_cors import CORS, cross_origin


exporting_threads = {}

app = Flask(__name__)
api = Api(app)
CORS(app)

config = {
    "development": "config.DevelopmentConfig",
    "production": "config.ProductionConfig",
    "jawdat_public": "config.JawdatPublic",
    "default": "config.DevelopmentConfig"
}

config_name = os.getenv('NMS_CONFIG', 'default')
app.config.from_object(config[config_name])

BASE_API_URL = '/api'

app.url_map.strict_slashes = False

# Data DB settings. centralized mongo config.
mongo_client = MongoClient(app.config['DB_SERVER'], app.config['DB_PORT'], connect=False)
mongo_db = getattr(mongo_client, app.config['DB_COLLECTION'])
mongo_db.authenticate(app.config['DB_USERNAME'], app.config['DB_PASSWORD'])


#Logger config
formatter = logging.Formatter("[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
dir_path = os.path.dirname(os.path.realpath(__file__))
handler = RotatingFileHandler(dir_path+'/log/access.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(formatter)
# TODO: Check if debug log has been throw to log file
# TODO: Separate access.log and error.log
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)
log.addHandler(handler)

### decorator for allowing Access-Control-Allow-Origin from any requester
def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

alert_severity = {
    "0": "emergencies",
    "1": "alerts",
    "2": "critical",
    "3": "errors",
    "4": "warnings",
    "5": "notifications",
    "6": "informational",
    "7": "debugging"
}

#Endpoint API for add New Device Location/Group
# TODO: Partial, keysensitive harus nonaktif ketika pencarian!!
class AddLocation(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        location = request.json
        device_controller = DeviceController(mongo_db, app.logger)
        result = device_controller.add_new_location(location)
        return make_response(jsonify(result))
api.add_resource(AddLocation, BASE_API_URL + '/location/add')

#All location in list (name only) - DONE
class LocationList(Resource):
    @crossdomain(origin='*')
    def get(self):
        try:
            location_list = list(mongo_db.list_location.distinct("name"))
            return make_response(dumps(location_list), 200)

        except errors.PyMongoError as e:
            raise
api.add_resource(LocationList, BASE_API_URL + '/location/list')

#All location in list (all detail) - DONE
class LocationListDetail(Resource):
    @crossdomain(origin='*')
    def get(self):
        try:
            location_list = list(mongo_db.list_location.find())
            return make_response(dumps(location_list), 200)

        except errors.PyMongoError as e:
            raise
api.add_resource(LocationListDetail, BASE_API_URL + '/location/detail')

#Edit location - DONE
class EditLocation(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        try:
            parms = request.json
            mongo_db.list_location.update_one({"_id":ObjectId(id)}, {"$set":parms})
            return make_response(dumps(True), 200)

        except errors.PyMongoError as e:
            raise
api.add_resource(EditLocation, BASE_API_URL + '/location/edit/<string:id>')

#Delete location - DONE
class DeleteLocation(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        try:
            parms = request.json
            print(parms)
            mongo_db.list_location.delete_one({"_id": ObjectId(id)})
            return make_response(dumps(True), 200)

        except errors.PyMongoError as e:
            raise
api.add_resource(DeleteLocation, BASE_API_URL + '/location/remove/<string:id>')

#Endpoint API for discover device via SNMP - DONE
class DiscoverDevice(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):

        parms = request.json
        type = parms["type"] if "type" in parms.keys() else ""
        start = parms["start"] if "start" in parms.keys() else ""
        end = parms["end"] if "end" in parms.keys() else ""
        subnetmask = parms["subnetmask"] if "subnetmask" in parms.keys() else ""
        community = parms["community"] if "community" in parms.keys() else ""
        print(parms)
        global exporting_threads
        thread_id = random.randint(0, 10000)
        exporting_threads[thread_id] = ExportingThread(type,start,end,subnetmask,community, mongo_db, app.logger)
        exporting_threads[thread_id].start()
        job = {
            "job_id": thread_id
        }
        return make_response(dumps(job))

api.add_resource(DiscoverDevice, BASE_API_URL + '/device/discover')

#Endpoint API for monitoring discover progress - DONE
class DiscoverProgress(Resource):
    @crossdomain(origin='*')
    def get(self, thread_id):
        global exporting_threads
        a= str(exporting_threads[thread_id].progress)
        discovered_list = exporting_threads[thread_id].discovered_list
        count = len(discovered_list)

        job = {
            "progress": a,
            "device_list": discovered_list,
            "device_count":count
        }
        return make_response(dumps(job))

api.add_resource(DiscoverProgress, BASE_API_URL + '/progress/<int:thread_id>')

#Endpoint API for saving device list from SNMP discover progress - DONE
class SaveDevice (Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        device_controller = DeviceController(mongo_db, app.logger)
        device_controller.save_device_list(parms["device_list"])
        return make_response(jsonify(True), 200)
api.add_resource(SaveDevice, BASE_API_URL + '/save')

#Endpoint API for add manually single device - DONE
class AddDevice(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        device = request.json
        app.logger.info(device)
        device_controller = DeviceController(mongo_db, app.logger)
        result = device_controller.add_single_device(device)
        if result:
            return make_response(dumps(True), 200)
        else:
            return make_response(jsonify(False), 500)

api.add_resource(AddDevice, BASE_API_URL + '/device/add')

#CRUD - Endpoint API for Edit/Update device - DONE
class EditDevice(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        parms = request.json
        if "location" in parms.keys():
            device_controller = DeviceController(mongo_db, app.logger)
            location_id = device_controller.get_location_id(parms["location"])
            parms["location_id"] = location_id
            del parms["location"]
        if "hostname" in parms.keys():
            del parms["hostname"]
        try:
            mongo_db.list_devices.update_one({"_id": ObjectId(id)}, {"$set": parms})
            return make_response(jsonify(True), 200)
        except errors.PyMongoError as e:
            raise

api.add_resource(EditDevice, BASE_API_URL + '/device/edit/<string:id>')

#INVENTORY - Endpoint API for for search device by hostname - DONE
class SearchDevice(Resource):
    @crossdomain(origin='*')
    def get(self, hostname):
        device_found = []
        search_result = list(mongo_db.list_devices.find({"hostname": {'$regex': hostname, "$options": "-i"}}, {"hostname":1}))
        if len(search_result)>0:
            for device in search_result:
                device_found.append(device["hostname"])
        return make_response(dumps(device_found))

api.add_resource(SearchDevice, BASE_API_URL + '/device/search/<string:hostname>')

#MAIN DASHBOARD - Endpoint API for count status (up/down/total) - DONE
class DeviceStatusSummary(Resource):
    @crossdomain(origin='*')
    def get(self):
        device_controller = DeviceController(mongo_db, app.logger)
        device_status = device_controller.get_device_status_summary()
        return make_response(dumps(device_status))

api.add_resource(DeviceStatusSummary, BASE_API_URL + '/device/status/summary')

#INVENTORY - Endpoint API for gather all device - DONE
class DeviceList(Resource):
    @crossdomain(origin='*')
    def get(self, group_by=None):
        device_controller = DeviceController(mongo_db, app.logger)
        get_all_device = device_controller.get_all_device(group_by=group_by)
        return make_response(dumps(get_all_device))

api.add_resource(DeviceList, BASE_API_URL + '/device/list', BASE_API_URL + '/device/list/<string:group_by>')


#INVENTORY - Endpoint API for gather device detail - DONE
class DeviceDetail(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        device_controller = DeviceController(mongo_db, app.logger)
        print("Detail device")
        device = device_controller.get_device_detail(id)
        if device:
            return make_response(dumps(device))
        else:
            app.logger.warning("Device not found")
            return make_response(dumps(False))

api.add_resource(DeviceDetail, BASE_API_URL + '/device/detail/<string:id>')

#Endpoint API for gather all interface from all devices - DONE
class AllInterface(Resource):
    @crossdomain(origin='*')
    def get(self):
        device_controller = DeviceController(mongo_db, app.logger)
        list_all_interface = device_controller.all_interface_util()
        return make_response(dumps(list_all_interface))

api.add_resource(AllInterface, BASE_API_URL + '/device/interface/all')

#NODE DETAIL - Endpoint API for Interface detail (Packetloss, Util In and Out) - DONE
class InterfaceDetails(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        device_controller = DeviceController(mongo_db, app.logger)
        interface_stat = device_controller.get_device_interface_detail(parms)
        return make_response(dumps(interface_stat))

api.add_resource(InterfaceDetails, BASE_API_URL + '/device/interface/util')

# TODO: Add new API to assign a device into defined location
# TODO: Add new API to delete location, if any device affected to the location, move the device into the undefined location?

#Endpoint API to get link (between two nodes) Packetloss - DONE!
class PacketLoss(Resource):
    @crossdomain(origin='*')
    def get(self):
        tg = TopologyGeneratorAPI(mongo_db, app.logger)
        device_controller = DeviceController(mongo_db, app.logger)
        topology = tg.generate_topology(id_device=None)
        packet_loss = list()
        for edge in topology["edges"]:
            data = device_controller.get_packet_loss(edge["src"]["host"], edge["src"]["interface"], edge["dst"]["host"],
                               edge["dst"]["interface"])
            packet_loss.append(data)

        packet_loss_dict = {
            "data": packet_loss
        }
        return make_response(dumps(packet_loss_dict))

api.add_resource(PacketLoss, BASE_API_URL + '/packetloss')

#Endpoint API to get Device utilization - DONE!
class DeviceUtil(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        device_controller = DeviceController(mongo_db, app.logger)
        device_util = device_controller.device_utilization(id)
        return make_response(dumps(device_util))

api.add_resource(DeviceUtil, BASE_API_URL + '/device/util/<string:id>')

#Endpoint API to get Device Health Summary - Done!
class HealthDeviceSummary(Resource):
    @crossdomain(origin='*')
    def get(self):
        device_controller = DeviceController(mongo_db, app.logger)
        ret_dict = device_controller.device_health_summary()
        return make_response(dumps(ret_dict))

api.add_resource(HealthDeviceSummary, BASE_API_URL + '/device/health/summary')

#NODE DETAIL - Endpoint API to get Device response time from Collector - DONE
class AverageResponseTime(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        device_controller = DeviceController(mongo_db, app.logger)
        response_time = device_controller.get_device_response_time(id)
        return make_response(dumps(response_time))

api.add_resource(AverageResponseTime, BASE_API_URL + '/device/responsetime/<string:id>')

#NODE DETAIL - Endpoint API to get Device average packetloss all interface - DONE
class AveragePacketLoss(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        device_controller = DeviceController(mongo_db, app.logger)
        packet_loss = device_controller.get_device_packetloss(id)
        return make_response(dumps(packet_loss))

api.add_resource(AveragePacketLoss, BASE_API_URL + '/device/packetloss/<string:id>')

#UNUSED?? DELETE IT!!!
class HealthDevice(Resource):
    @crossdomain(origin='*')
    def get(self, _id):
        # device = mongo_db.list_devices.find_one({"_id": ObjectId(_id)})

        #populate most recent timestamp
        treshold_datetime = datetime.now() - timedelta(days=1)
        snmp_device_status = list(
            mongo_db.snmp_device_status.aggregate([
                {
                    "$match": {
                        "device_id": ObjectId(_id),
                        "timestamp": {"$gte": treshold_datetime}
                    }
                },
                {
                    "$sort": {"timestamp": -1}
                },
                {
                    "$limit": 1
                }
            ])
        )
        device_status = None
        if len(snmp_device_status) > 0:
            device_status = snmp_device_status[0]
            memory_util = int(device_status["system_info"]["ciscoMemoryPoolUsed"])*100//(int(device_status["system_info"]["ciscoMemoryPoolUsed"])+int(device_status["system_info"]["ciscoMemoryPoolFree"]))
            device_status["memory_util"] = memory_util
        ret_dict = {
            "device_status": device_status
        }
        return make_response(dumps(ret_dict))

api.add_resource(HealthDevice, BASE_API_URL + '/device/status/<string:_id>')

class BackupConfig(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        device = mongo_db.list_devices.find_one({'_id': ObjectId(id)})

        device['name'] = request.json['name']
        query = {
            'name': device['name'],
            'hostname': device['hostname'] if 'hostname' in device.keys() else device['ip_mgmt'],
            'vendor': device['vendor'],
            'config_path': None,
            'timestamp': None,
            'status': 'PROGRESS',
            'version': request.json['version'],
            'device_id': str(device['_id'])
        }

        print(query)
        input_query = mongo_db.backup_config.insert_one(query)
        id_input = input_query.inserted_id
        backup = backup_process(device)
        if backup['status'] == 'SUCCESS':
            mongo_db.backup_config.update({'_id': ObjectId(id_input)},{'$set': backup['result']})
            # return make_response(dumps({'status': 'SUCCESS'}))
        else:
            mongo_db.backup_config.update({'_id': ObjectId(id_input)},{'$set': {'status' : 'FAILED', 'timestamp' : datetime.now().strftime('%Y/%m/%d-%H:%M:%S')}})
            # return make_response(dumps({'status': 'FAILED'}))

        #Insert Backup activity historical
        history={
            'user': 'jawdat',
            'hostname': device['hostname'],
            'activity': 'Backup Config',
            'status': backup['status'],
            'message': backup['debug'],
            'timestamp': datetime.now(),
        }
        mongo_db.activity_history.insert_one(history)

        return make_response(dumps({'status': backup['status']}))

api.add_resource(BackupConfig, BASE_API_URL + '/conf/backup/<string:id>')

class RestoreConfig(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        backup_file_id = request.json['_id']
        device = mongo_db.list_devices.find_one({'_id' : ObjectId(id) })
        device['config'] = mongo_db.backup_config.find_one({'_id' : ObjectId(backup_file_id)})
        result = restore_process(device)

        # Insert Restore activity historical
        history = {
            'user': 'jawdat',
            'hostname': device['hostname'],
            'activity': 'Restore Config',
            'status': result['status'],
            'message': result['debug'],
            'timestamp': datetime.now(),
        }
        mongo_db.activity_history.insert_one(history)

        return make_response(dumps(result))

api.add_resource(RestoreConfig, BASE_API_URL + '/conf/restore/<string:id>')

class GenerateTopology(Resource):
    @crossdomain(origin='*')
    def get(self, location_id=None):
        tg = TopologyGeneratorAPI(mongo_db, app.logger)
        topology = tg.generate_topology(location_id)
        return make_response(dumps(topology))
api.add_resource(GenerateTopology, BASE_API_URL + '/dashboard/topology/<string:location_id>', BASE_API_URL + '/dashboard/topology')

#Save Topology BaseLine per Location
class SaveTopologyBaseLine(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, location=None):
        parms = request.json
        tg = TopologyGeneratorAPI(mongo_db, app.logger)
        tg.save_baseline(parms)
        return make_response(dumps(True))

api.add_resource(SaveTopologyBaseLine, BASE_API_URL + '/dashboard/topology/baseline')

#List Registered Link
class GetRegisteredLink(Resource):
    @crossdomain(origin='*')
    def get(self):
        link_controller = LinkController(mongo_db, app.logger)
        registeredlink = link_controller.get_registered_link()
        return make_response(dumps(registeredlink))

api.add_resource(GetRegisteredLink,BASE_API_URL + '/link/list')

#Register new Link
class RegisterLink(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        # TODO: Add selection to prevent duplicate link
        link_controller = LinkController(mongo_db, app.logger)
        result = link_controller.register_link(parms)
        return make_response(dumps(result))

api.add_resource(RegisterLink,BASE_API_URL + '/link/register')

#Delete Registered  Link
class DeleteLink(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def get(self, id):
        link_controller = LinkController(mongo_db, app.logger)
        link_controller.delete_registered_link(id)
        return make_response(dumps(True), 200)

api.add_resource(DeleteLink,BASE_API_URL + '/link/delete/<string:id>')
class GetLatencyJitter(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        link_controller = LinkController(mongo_db, app.logger)
        jitter = link_controller.get_latency_jitter(id)
        return make_response(dumps(jitter))

api.add_resource(GetLatencyJitter,BASE_API_URL + '/link/jitter/<string:id>')

#Register Dashboard Monitoring, SHOULD Provide device list and interface perdevice
class RegisterDashboard(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        dashboard_controller = DashboardController(mongo_db, app.logger)
        dashboard_controller.register_dashboard(parms)
        return make_response(dumps(True))
api.add_resource(RegisterDashboard,BASE_API_URL + '/dashboard/register')

#List Dashboard (return Dashboard name and dashboard_id in list)
class DashboardList(Resource):
    @crossdomain(origin='*')
    def get(self):
        # dashboard_controller = DashboardController(mongo_db)
        # result = dashboard_controller.register_dashboard(parms)
        dashboard_list = mongo_db.dashboard.find({}, {"name":1})
        return make_response(dumps(dashboard_list))
api.add_resource(DashboardList, BASE_API_URL + '/dashboard/list')

# API to get dashboard details, will return dashboard details and affected widget
class DashboardDetail(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        # dashboard_controller = DashboardController(mongo_db)
        # result = dashboard_controller.register_dashboard(parms)
        dashboard = mongo_db.dashboard.find_one({"_id": ObjectId(id)})
        return make_response(dumps(dashboard))
api.add_resource(DashboardDetail, BASE_API_URL + '/dashboard/<string:id>')

#API to return dashboard widget data
class WidgetData(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        app.logger.info(parms)
        dashboard_controller = DashboardController(mongo_db, app.logger)
        data = dashboard_controller.widget_data(parms)
        return make_response(jsonify(data))
api.add_resource(WidgetData,BASE_API_URL + '/widget/data')

# TODO: Add new API to delete dashboard
# TODO: Add new API to delete widget in dashboard, also stop the background job, but check it first if no other widget use the job (id)

#API for Intellegent Log
class IntellegentLoging(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        parms = request.json
        intellegent_log = IntellegentLog(mongo_db, app.logger)
        query_result = intellegent_log.search(parms)
        return make_response(jsonify(query_result), 200)
api.add_resource(IntellegentLoging,BASE_API_URL + '/log/search')


#API Netflow Status
class NetflowData(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def get(self, data):
        netflow = Netflow(mongo_db, app.logger)
        result = netflow.static_data(data)
        return make_response(jsonify(result), 200)
api.add_resource(NetflowData, BASE_API_URL + '/netflow/status/<string:data>')


class AlertMessage(Resource):
    @crossdomain(origin='*')
    def get(self, limit):
        limit = limit
        alerts = mongo_db.filtered_syslog.aggregate([
            {"$sort": {"time": 1}},
            {"$limit": limit},
        ])
        alert_list = list(alerts)
        ret_alert_list = list()
        for alert in alert_list:
            td = datetime.now() - alert["time"]
            alert_dict = {
                "desc": alert["message"],
                "time": {
                    "days": td.days,
                    "hours": td.seconds//3600,
                    "minutes": (td.seconds//60)%60
                }
            }
            ip_address = alert["host"]
            device = mongo_db.list_devices.find_one({"ip_address": ip_address}, {"hostname": 1})
            hostname = device["hostname"]
            alert_dict["node"] = hostname
            alert_dict["category"] = alert_severity[alert["severity"]]
            ret_alert_list.append(alert_dict)
        ret_dict = {
            "alert_list": ret_alert_list
        }

        return make_response(dumps(ret_dict))

api.add_resource(AlertMessage, BASE_API_URL + '/alert/list/<int:limit>')

class BackupList(Resource):
    @crossdomain(origin='*')
    def get(self, id):
        backup_list = list(mongo_db.backup_config.aggregate([{'$match' : {'device_id' : id, 'status':'SUCCESS'}},{ '$sort' : {'timestamp' : -1}}]))
        devices_backup = [{'name' : d['name'], 'version' : d['version'] if 'version' in d.keys() else '', 'timestamp' : d['timestamp'], '_id' : str(d['_id'])} for d in backup_list]

        return make_response(dumps({'id' : id, 'backup_list' : devices_backup}))

api.add_resource(BackupList, BASE_API_URL + '/backup/list/<string:id>')

class BackupDel(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        try:
            for _id in request.json:
                backup = mongo_db.backup_config.find_one({'_id' : ObjectId(_id)})
                os.system('rm -f '+backup['config_path'])
                mongo_db.backup_config.remove({'_id' : ObjectId(_id)})

            return make_response(dumps({'status' : 'SUCCESS'}))
        except Exception as msg:
            return make_response(dumps({'status' : 'FAILED', 'debug' : str(msg)}))

api.add_resource(BackupDel, BASE_API_URL + '/backup/del/<string:id>')

class MultiBackup(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self):
        hostname_list = request.json
        device_list = [{'hostname' : h} for h in hostname_list]
        devices = list(mongo_db.list_devices.find({'$or' : device_list }))
        queries = [{'name' : device['hostname']+'_'+datetime.now().strftime('%Y%m%d%H%M%S'),
                     'hostname' : device['hostname'],
                     'vendor' : device['vendor'],
                     'config_path' : None,
                     'timestamp' : None,
                     'status' : 'PROCESS'} for device in devices]

        input_queries = mongo_db.backup_config.insert(queries)

        pool = Pool()
        results = pool.map(backup_process, devices)
        result = []
        for r,q in zip(results, input_queries):
            if r['status'] == 'SUCCESS':
                mongo_db.backup_config.update({'_id' : q}, {'$set' : r['result']})
                del r['result']
            else:
                mongo_db.backup_config.update({'_id' : q},{'$set':{'status':'FAILED', 'timestamp' : datetime.now().strfime('%Y/%m/%d-%H:%M:%S')}})
            result.append(r)
        return make_response(dumps(result))
api.add_resource(MultiBackup, BASE_API_URL + '/conf/backup')

class BackupView(Resource):
    @crossdomain(origin='*')
    @cross_origin()
    def post(self, id):
        device = mongo_db.backup_config.find_one({'_id' : ObjectId(request.json['_id'])})
        config = None
        with open(device['config_path'], 'r') as f:
            config = f.read()

        return make_response(dumps(({'config': config, 'id' : id })))
api.add_resource(BackupView, BASE_API_URL + '/conf/view/<string:id>')

# API to get history activity
class ActivityHistory(Resource):
    @crossdomain(origin='*')
    def get(self):
        activity_list = mongo_db.activity_history.find()
        return make_response(dumps(activity_list))
api.add_resource(ActivityHistory, BASE_API_URL + '/activity/history')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4242))
    app.logger.info("Running NMS Backend with {:s} environment".format(config_name))
    app.run(host="0.0.0.0", debug=True, port=port, threaded=True)
