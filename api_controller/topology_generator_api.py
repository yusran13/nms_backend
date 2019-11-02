import pymongo
import pprint
from bson.objectid import ObjectId
from datetime import datetime
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from collector.topology_generator import TopologyGenerator
from pymongo import MongoClient
from device_controller import DeviceController


class TopologyGeneratorAPI:

    def __init__(self, db_construct, logger):
        self.db = db_construct
        self.logger = logger

    def get_latest_single_neighbor_data(self, hostname):
        neighbor_data_list = ""
        try:
            neighbor_data_list = list(self.db.device_neighbor.find({"device_id": hostname}).sort("timestamp", pymongo.DESCENDING))
        except pymongo.errors as e:
            print("Failed get neighbor data from database for device{:s}".format(hostname))
            print(e.message)
        if neighbor_data_list:
            return neighbor_data_list[0]
        else:
            return None

    def get_latest_neighbor_data(self, device=None):
        device_list = list()
        neigbor_data_list = list()
        try:
            if device:
                device_list = self.db.list_devices.find({"location_id": device["location_id"]})
                if device_list:
                    for device in device_list:
                        if device["status"] != "DOWN":
                            neighbor_data = self.get_latest_single_neighbor_data(device["hostname"])
                            if neighbor_data:
                                neigbor_data_list.append(neighbor_data)
            else:
                # to be done: get all border device
                device_list = self.db.list_devices.find({})
                if device_list:
                    for device in device_list:
                        if device["status"] != "DOWN":
                            border_device = self.is_border_device(device)
                            if border_device["result"] and border_device["neighbor_data"]:
                                neigbor_data_list.append(border_device["neighbor_data"])
        except pymongo.errors as e:
            print(e.message)

        return neigbor_data_list

    def generate_topology(self, location_id=None):
        device = ""
        base_line_topology = ""
        if location_id:
            base_line_topology_list = ""
            try:
                # device_controller = DeviceController(self.db, self.logger)
                # location_id = device_controller.get_location_id(location)
                # device = self.db.list_devices.find_one({"_id": ObjectId(id_device)})
                device = self.db.list_devices.find_one({"location_id": location_id})
                if device:
                    base_line_topology_list = list(self.db.topology_baseline.find({"location_id": location_id}).sort("timestamp", pymongo.DESCENDING))
                else:
                    error_data={
                        "status": False,
                        "message": "Location with submitted ID is not found"
                    }
                    return error_data
            except pymongo.errors as e:
                print(e.message)
            if base_line_topology_list:
                base_line_topology = base_line_topology_list[0]
        else:
            base_line_topology_list = ""
            try:
                base_line_topology_list = list(self.db.topology_baseline.find({"location_id": "GLOBAL"}).sort("timestamp", pymongo.DESCENDING))
            except pymongo.errors as e:
                print(e.message)
            if base_line_topology_list:
                base_line_topology = base_line_topology_list[0]

        neighbor_data = self.get_latest_neighbor_data(device)
        # print(neighbor_data)
        tg = TopologyGenerator()
        conn_table = tg.generateConnectionTable(neighbor_data)
        new_topology = tg.generateTopology(conn_table)
        for device in neighbor_data:
            if device["device_id"] not in new_topology["nodes"]:
                new_topology["nodes"].append(device["device_id"])

        topology = tg.mergeTopology(new_topology, base_line_topology)
	if location_id:
		topology["location_id"]= location_id
		topology["location"]= self.db.list_location.find_one({"_id": ObjectId(location_id)},{"name": 1, "_id": 0})["name"]
	else:
		topology["location_id"]= "GLOBAL"
		topology["location"] = "GLOBAL"
        return topology

    def save_baseline(self, parms):
        device_controller = DeviceController(self.db, self.logger)
        # parms["location_id"] = device_controller.get_location_id(parms["location"])
        parms["timestamp"] = datetime.now()
        # del parms["location"]
        self.db.topology_baseline.insert_one(parms)

    def get_location_by_hostname(self, hostname):
        hostname = hostname.split(".")[0]
        # print hostname
        device = self.db.list_devices.find_one({"hostname": hostname})
        device_controller = DeviceController(self.db, self.logger)
        if device:
            # return device["location"]
            location_name = device_controller.get_location_name(device["location_id"])
            return location_name
        else:
            return None

    def is_border_device(self, device):
        try:
            neighbor_data = self.get_latest_single_neighbor_data(device["hostname"])
            location_set = set()
            device_controller = DeviceController(self.db, self.logger)
            location_name = device_controller.get_location_name(device["location_id"])
            if(neighbor_data):
                neighbors = neighbor_data["neighbors"]
                # location_set.add(device["location"])
                location_set.add(location_name)
                for neighbor in neighbors:
                    location = self.get_location_by_hostname(neighbor["device_id"])
                    if location:
                        location_set.add(location)
            if len(location_set) > 1:
                return {"result": 1, "neighbor_data": neighbor_data}
            else:
                return {"result": 0, "neighbor_data": neighbor_data}

        except pymongo.errors as e:
            print(e.message)
