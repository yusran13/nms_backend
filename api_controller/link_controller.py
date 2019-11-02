from __future__ import division
import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from flask_restful import Resource
from device_controller import DeviceController
from bson import ObjectId


class LinkController(Resource):

    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def register_link(self, parms):
        self.logger.info(parms)
        try:
            device_controller = DeviceController(self.db, self.logger)
            src_id = device_controller.get_device_id(parms["src_host"])
            dst_id = device_controller.get_device_id(parms["dst_host"])
            data = {
                "src_id": src_id,
                "src_if": parms["src_if"] if "src_if" in parms.keys() else "",
                "src_ip": parms["src_ip"] if "src_ip" in parms.keys() else "",
                "dst_id": dst_id,
                "dst_if": parms["dst_if"] if "dst_if" in parms.keys() else "",
                "dst_ip": parms["dst_ip"] if "dst_ip" in parms.keys() else "",
            }
            self.db.link_devices.insert(data)
            return True
        except:
            return False

    def delete_registered_link (self, id):
        self.db.link_devices.delete_one({ "_id":ObjectId(id)})

    def get_registered_link(self):
        registered_link = []
        device_controller = DeviceController(self.db, self.logger)
        list_registered_link = list(self.db.link_devices.find())
        for link in list_registered_link:
            src_host = device_controller.get_device_by_id(link["src_id"])["hostname"]
            dst_host = device_controller.get_device_by_id(link["dst_id"])["hostname"]
            data = {}
            data["src_host"] = src_host
            data["dst_host"] = dst_host
            data["src_ip"] = link["src_ip"]
            data["dst_ip"] = link["dst_ip"]
            data["src_if"] = link["src_if"]
            data["dst_if"] = link["dst_if"]
            data["id_link"] = link["_id"]
            registered_link.append(data)
        return registered_link

    def latency_jitter_calculation(self, list_latency):
        self.logger.info("Latency = "+str(list_latency))
        total_latency = sum(list_latency)
        total_delta = 0
        for loop in range(0,len(list_latency)-1):
            delta = abs(list_latency[loop]-list_latency[loop+1])
            total_delta = total_delta +delta

        if len(list_latency) != 0:
            latency = float(total_latency / len(list_latency))
            jitter = float(total_delta / (len(list_latency)-1))
            latency = round(latency, 2)
            jitter = round(jitter, 2)
        else:
            latency = 0
            jitter = 0

        return latency, jitter

    def save_jitter(self, data):
        self.db.jitter.insert_one(data)

    def get_link_data_by_id(self, id):
        link = self.db.link_devices.find_one({"_id": id})
        if link:
            return link

    def get_latency_jitter(self, id):
        link_registered = self.db.link_devices.find_one({"_id": ObjectId(id)})

        device_controller = DeviceController(self.db, self.logger)
        src_host = device_controller.get_device_by_id(link_registered["src_id"])["hostname"]
        dst_host = device_controller.get_device_by_id(link_registered["dst_id"])["hostname"]

        latency_jitter = list(self.db.jitter.aggregate([
            {
                "$match": {"id_link": ObjectId(id)}
            },
            {
                "$sort": {"timestamp": -1}
            },
            {
                "$limit": 10
            },
            {
                "$project":{
                    "latency": 1,
                    "jitter": 1,
                    "timestamp":1,
                    "_id":0
                }
            }

        ]))

        for data in latency_jitter:
            data["timestamp"] = "{:d}:{:02d}".format(data["timestamp"].hour, data["timestamp"].minute)
        link_registered["src_host"] = src_host
        link_registered["dst_host"] = dst_host
        del link_registered["src_id"]
        del link_registered["dst_id"]
        del link_registered["_id"]
        latency_jitter.reverse()
        link_registered["latency_jitter"] = latency_jitter

        return link_registered



